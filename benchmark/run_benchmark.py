import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, Set, List, Tuple

from model_client import ModelClient
from pdf_parser import extract_all_rfps
from prompts import create_extraction_prompt, create_json_repair_prompt
from schema import FIELDS

# =========================================================
# 1. Model Configuration & Tuning
# =========================================================
MODEL_NAME = "Qwen3.5-9B"
BASE_URL = "http://localhost:8000/v1"
API_KEY = "EMPTY"
# Using your local folder name as registered by vLLM
MODEL_ID = "/home/ubuntu/models/Qwen3.5-9B"
# Tuned down to 1200 to maximize available input tokens
MAX_OUTPUT_TOKENS = 1200 

# Performance Tuning: Number of concurrent RFPs to process
CONCURRENT_WORKERS = 10 

# =========================================================
# 2. Project Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
RFP_DIR = BASE_DIR / "data" / "rfps"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

# =========================================================
# 3. Pre-compiled Regular Expressions (CPU Optimization)
# =========================================================
JSON_MD_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", flags=re.IGNORECASE | re.DOTALL)
JSON_FALLBACK_PATTERN = re.compile(r"\{.*\}", flags=re.DOTALL)
WHITESPACE_PATTERN = re.compile(r"\s+")
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s]+")
WORD_PATTERN = re.compile(r"[a-z0-9]+")

# =========================================================
# 4. JSON Extraction
# =========================================================
def extract_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    text = text.strip()

    # Try JSON inside Markdown code block
    match = JSON_MD_PATTERN.search(text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    # Try the complete response as JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try to find a JSON object anywhere inside the response
    match = JSON_FALLBACK_PATTERN.search(text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None

def ensure_fields(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}
    return {field: data.get(field, None) for field in FIELDS}

# =========================================================
# 5. Normalisation Helpers
# =========================================================
def is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "null", "none", "n/a", "na", "not specified"}
    return False

def value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(value_to_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {value_to_text(val)}" for key, val in value.items())
    return str(value)

def normalise_text(value: Any) -> str:
    text = value_to_text(value).lower()
    return WHITESPACE_PATTERN.sub(" ", text).strip()

def normalise_number(value: Any) -> Set[float]:
    text = value_to_text(value).lower().replace(",", "")
    text = text.replace("million", "m").replace("billion", "b").replace("thousand", "k")
    
    parsed_numbers = set()
    for num_str in NUMBER_PATTERN.findall(text):
        try:
            val = float(num_str)
            parsed_numbers.add(int(val) if val.is_integer() else val)
        except ValueError:
            pass
    return parsed_numbers

def extract_emails(value: Any) -> Set[str]:
    return {email.lower() for email in EMAIL_PATTERN.findall(value_to_text(value))}

def extract_urls(value: Any) -> Set[str]:
    return {url.lower().rstrip(".,)") for url in URL_PATTERN.findall(value_to_text(value))}

def word_set(value: Any) -> Set[str]:
    return set(WORD_PATTERN.findall(normalise_text(value)))

def term_recall(ground_truth: Any, prediction: Any, min_recall: float = 0.20) -> bool:
    gt_words = word_set(ground_truth)
    pred_words = word_set(prediction)

    if not gt_words:
        return True

    recall = len(gt_words & pred_words) / len(gt_words)
    return recall >= min_recall

# =========================================================
# 6. Field Comparison
# =========================================================
def compare_field(ground_truth: Any, prediction: Any) -> bool:
    if is_null(ground_truth):
        return is_null(prediction)
    if is_null(prediction):
        return False

    gt_numbers = normalise_number(ground_truth)
    pred_numbers = normalise_number(prediction)
    if gt_numbers and not gt_numbers.issubset(pred_numbers):
        return False

    gt_emails = extract_emails(ground_truth)
    pred_emails = extract_emails(prediction)
    if gt_emails and not gt_emails.issubset(pred_emails):
        return False

    gt_urls = extract_urls(ground_truth)
    pred_urls = extract_urls(prediction)
    if gt_urls and not (gt_urls & pred_urls):
        return False

    return term_recall(ground_truth, prediction, min_recall=0.20)

# =========================================================
# 7. Worker Node: Process One RFP
# =========================================================
def process_rfp(client: ModelClient, rfp_name: str, rfp_text: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    
    # ---------------------------------------------------------
    # DYNAMIC TRUNCATION SAFEGUARD
    # Hard limit at 95,000 characters to safely bypass the 
    # 32,768 token limit even on dense, table-heavy documents.
    # ---------------------------------------------------------
    MAX_INPUT_CHARS = 95000 
    
    if len(rfp_text) > MAX_INPUT_CHARS:
        print(f"WARNING: Truncating '{rfp_name}' from {len(rfp_text)} to {MAX_INPUT_CHARS} characters to stay under 32K token limit.")
        rfp_text = rfp_text[:MAX_INPUT_CHARS]

    # 1. Generate Extraction
    result = client.generate(
        create_extraction_prompt(rfp_text),
        max_tokens=MAX_OUTPUT_TOKENS
    )

    total_latency = result.get("latency_seconds", 0)
    total_input_tokens = result.get("input_tokens", 0)
    total_output_tokens = result.get("output_tokens", 0)
    total_tokens = result.get("total_tokens", 0)
    response_text = result.get("response", "")

    # 2. Parse and optionally repair JSON
    final_json = extract_json(response_text)

    if final_json is None and response_text:
        repair_result = client.generate(
            create_json_repair_prompt(response_text),
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0
        )
        total_latency += repair_result.get("latency_seconds", 0)
        total_input_tokens += repair_result.get("input_tokens", 0)
        total_output_tokens += repair_result.get("output_tokens", 0)
        total_tokens += repair_result.get("total_tokens", 0)
        final_json = extract_json(repair_result.get("response", ""))

    final_json = ensure_fields(final_json or {})
    
    output_dir = BASE_DIR / "benchmark_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. حفظ النتيجة كملف JSON
    json_path = output_dir / f"{rfp_name}_output.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=4, ensure_ascii=False)

    # 2. حفظ النتيجة كملف Markdown
    md_path = output_dir / f"{rfp_name}_output.md"
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(f"# مخرجات النموذج لملف: {rfp_name}\n\n")
        
        if isinstance(final_json, dict):
            for field, text in final_json.items():
                md_file.write(f"### {field}\n")
                if not text or str(text).strip().lower() == "null":
                    md_file.write("*[لم يتم العثور على بيانات]*\n\n")
                else:
                    md_file.write(f"{text}\n\n")
                md_file.write("---\n")
    # 3. Compare with Ground Truth
    correct = 0
    total = len(FIELDS)
    field_results = {}

    for field in FIELDS:
        gt_value = ground_truth.get(field)
        pred_value = final_json.get(field)
        is_correct = compare_field(gt_value, pred_value)
        
        if is_correct:
            correct += 1
        
        field_results[field] = {
            "correct": is_correct,
            "gt": gt_value,
            "pred": pred_value
        }

    return {
        "rfp_name": rfp_name,
        "correct": correct,
        "total": total,
        "accuracy": (correct / total * 100) if total else 0,
        "latency_seconds": total_latency,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "prediction": final_json,
        "field_results": field_results
    }

# =========================================================
# 8. Main Benchmark (Concurrent Execution)
# =========================================================
def load_all_ground_truths(rfp_items: List[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    truths = {}
    for index, (rfp_name, _) in enumerate(rfp_items, start=1):
        path = GROUND_TRUTH_DIR / f"RFP_{index:02d}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                truths[rfp_name] = json.load(f).get("extracted_fields", {})
        else:
            print(f"WARNING: Ground truth not found: {path}")
            truths[rfp_name] = {}
    return truths

def main():
    print(f"\n{'=' * 70}\nRFP MODEL BENCHMARK\n{'=' * 70}")
    print(f"Model: {MODEL_NAME} | URL: {BASE_URL}")
    print(f"Mode: CONCURRENT ({CONCURRENT_WORKERS} Workers)\n{'=' * 70}")

    client = ModelClient(name=MODEL_NAME, base_url=BASE_URL, api_key=API_KEY, model=MODEL_ID)

    # 1. Load Data
    print("\nLoading RFP PDFs and Ground Truths...")
    rfps = extract_all_rfps(RFP_DIR)
    rfp_items = sorted(rfps.items(), key=lambda x: x[0])
    
    if not rfp_items:
        print("ERROR: No RFP PDFs were found.")
        return

    ground_truths = load_all_ground_truths(rfp_items)
    print(f"Found {len(rfp_items)} RFP files. Beginning concurrent generation...\n")

    overall_metrics = {
        "correct": 0, "total": 0, "latency": 0.0, 
        "input_tokens": 0, "output_tokens": 0, "total_tokens": 0
    }

    # 2. Concurrent Processing via ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        future_to_rfp = {
            executor.submit(
                process_rfp, client, rfp_name, rfp_text, ground_truths[rfp_name]
            ): rfp_name 
            for rfp_name, rfp_text in rfp_items
        }

        for future in as_completed(future_to_rfp):
            rfp_name = future_to_rfp[future]
            try:
                result = future.result()
                print(f"[{rfp_name}] Completed | Accuracy: {result['correct']}/{result['total']} ({result['accuracy']:.2f}%) | Latency: {result['latency_seconds']:.2f}s")
                
                overall_metrics["correct"] += result["correct"]
                overall_metrics["total"] += result["total"]
                overall_metrics["latency"] += result["latency_seconds"]
                overall_metrics["input_tokens"] += result["input_tokens"]
                overall_metrics["output_tokens"] += result["output_tokens"]
                overall_metrics["total_tokens"] += result["total_tokens"]
                
            except Exception as exc:
                print(f"[{rfp_name}] generated an exception: {exc}")

    # 3. Final Reporting
    overall_accuracy = (overall_metrics["correct"] / overall_metrics["total"] * 100) if overall_metrics["total"] else 0

    print(f"\n\n{'=' * 70}\nFINAL BENCHMARK RESULTS\n{'=' * 70}")
    print(f"Accuracy: {overall_metrics['correct']}/{overall_metrics['total']} = {overall_accuracy:.2f}%")
    print(f"Cumulative Latency: {overall_metrics['latency']:.4f} seconds (Note: Wall-clock time is much lower due to concurrency)")
    print(f"Total input tokens: {overall_metrics['input_tokens']}")
    print(f"Total output tokens: {overall_metrics['output_tokens']}")
    print(f"Total tokens: {overall_metrics['total_tokens']}\n{'=' * 70}")

if __name__ == "__main__":
    main()