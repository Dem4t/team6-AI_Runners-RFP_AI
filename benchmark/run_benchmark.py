import os
from dotenv import load_dotenv
import json
import re
from pathlib import Path


from model_client import ModelClient
from pdf_parser import extract_all_rfps
from prompts import create_chunk_prompt, create_final_prompt, create_json_repair_prompt
from schema import FIELDS

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL_NAME = "gpt-4o"
BASE_URL = "https://api.openai.com/v1"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_ID = "gpt-4o"

if not API_KEY:
    raise ValueError("OPENAI_API_KEY is missing; check the .env file in the project root.")

CHUNK_WORDS = 6000
OVERLAP_WORDS = 500
CHUNK_MAX_TOKENS = 1200
FINAL_MAX_TOKENS = 1800

BASE_DIR = Path(__file__).resolve().parent.parent
RFP_DIR = BASE_DIR / "data" / "rfps"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"

# =========================================================
# 2. Text Chunking
# =========================================================

def chunk_text(text, chunk_words=CHUNK_WORDS, overlap_words=OVERLAP_WORDS):
    words = text.split()
    chunks = []
    start = 0

    if overlap_words >= chunk_words:
        overlap_words = chunk_words - 1

    while start < len(words):
        end = start + chunk_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap_words

    return chunks

# =========================================================
# 3. JSON Extraction
# =========================================================

def extract_json(text):
    if not text:
        return None
    text = text.strip()

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None

def ensure_fields(data):
    if not isinstance(data, dict):
        data = {}
    return {field: data.get(field, None) for field in FIELDS}

# =========================================================
# 4. Normalisation & Comparison Helpers
# =========================================================

def is_null(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "null", "none", "n/a", "na", "not specified"}
    return False

def value_to_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(value_to_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {value_to_text(val)}" for key, val in value.items())
    return str(value)

def normalise_text(value):
    text = value_to_text(value).lower()
    return re.sub(r"\s+", " ", text).strip()

def normalise_number(value):
    text = value_to_text(value).lower().replace(",", "")
    text = text.replace("million", "m").replace("billion", "b").replace("thousand", "k")
    
    parsed_numbers = set()
    for num_str in re.findall(r"\d+(?:\.\d+)?", text):
        try:
            val = float(num_str)
            # Normalise 2000000.00 to 2000000
            parsed_numbers.add(int(val) if val.is_integer() else val)
        except ValueError:
            pass
    return parsed_numbers

def extract_emails(value):
    text = value_to_text(value)
    return {email.lower() for email in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)}

def extract_urls(value):
    text = value_to_text(value)
    return {url.lower().rstrip(".,)") for url in re.findall(r"https?://[^\s]+", text)}

def word_set(value):
    text = normalise_text(value)
    return set(re.findall(r"[a-z0-9]+", text))

def term_recall(ground_truth, prediction, min_recall=0.35):
    gt_words = word_set(ground_truth)
    pred_words = word_set(prediction)
    if not gt_words:
        return True
    recall = len(gt_words & pred_words) / len(gt_words)
    return recall >= min_recall

# =========================================================
# 5. Field Comparison Logic
# =========================================================

def compare_field(ground_truth, prediction):
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

    return term_recall(ground_truth, prediction, min_recall=0.35)

def compare_field_by_name(field, ground_truth, prediction):
    # Uses the robust compare_field for all categories now that floats are handled correctly
    return compare_field(ground_truth, prediction)

# =========================================================
# 6. Load Ground Truth
# =========================================================

def load_ground_truth(index):
    """
    Loads JSON mapped by index and steps into 'extracted_fields' wrapper.
    """
    path = GROUND_TRUTH_DIR / f"RFP_{index:02d}.json"
    if not path.exists():
        return {}
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("extracted_fields", {})

# =========================================================
# 7. Core Benchmark Logic
# =========================================================

def process_rfp(client, rfp_name, rfp_text, ground_truth):
    print(f"\n{'=' * 70}\nProcessing: {rfp_name}\n{'=' * 70}")
    chunks = chunk_text(rfp_text)
    print(f"Chunks: {len(chunks)}")

    chunk_results = []
    total_latency, total_input_tokens, total_output_tokens, total_tokens = 0.0, 0, 0, 0

    for i, chunk in enumerate(chunks, start=1):
        print(f"  Chunk {i}/{len(chunks)}...")
        result = client.generate(create_chunk_prompt(chunk), max_tokens=CHUNK_MAX_TOKENS)
        
        total_latency += result.get("latency_seconds", 0)
        total_input_tokens += result.get("input_tokens", 0)
        total_output_tokens += result.get("output_tokens", 0)
        total_tokens += result.get("total_tokens", 0)

        parsed = extract_json(result.get("response", ""))

        if parsed is None and result.get("response"):
            print("    JSON parsing failed. Trying repair...")
            repair_result = client.generate(create_json_repair_prompt(result["response"]), max_tokens=CHUNK_MAX_TOKENS)
            total_latency += repair_result.get("latency_seconds", 0)
            total_input_tokens += repair_result.get("input_tokens", 0)
            total_output_tokens += repair_result.get("output_tokens", 0)
            total_tokens += repair_result.get("total_tokens", 0)
            parsed = extract_json(repair_result.get("response", ""))

        chunk_results.append(ensure_fields(parsed or {}))

    print("\n  Consolidating chunk results...")
    final_result = client.generate(create_final_prompt(chunk_results), max_tokens=FINAL_MAX_TOKENS)
    
    total_latency += final_result.get("latency_seconds", 0)
    total_input_tokens += final_result.get("input_tokens", 0)
    total_output_tokens += final_result.get("output_tokens", 0)
    total_tokens += final_result.get("total_tokens", 0)

    final_json = extract_json(final_result.get("response", ""))

    if final_json is None and final_result.get("response"):
        print("  Final JSON parsing failed. Trying repair...")
        repair_result = client.generate(create_json_repair_prompt(final_result["response"]), max_tokens=FINAL_MAX_TOKENS)
        total_latency += repair_result.get("latency_seconds", 0)
        total_input_tokens += repair_result.get("input_tokens", 0)
        total_output_tokens += repair_result.get("output_tokens", 0)
        total_tokens += repair_result.get("total_tokens", 0)
        final_json = extract_json(repair_result.get("response", ""))

    final_json = ensure_fields(final_json or {})

    correct = 0
    total = len(FIELDS)
    print("\n  Field comparison:")

    for field in FIELDS:
        gt_value = ground_truth.get(field)
        pred_value = final_json.get(field)
        is_correct = compare_field_by_name(field, gt_value, pred_value)

        if is_correct:
            correct += 1
            print(f"    [OK]    {field}")
        else:
            print(f"    [WRONG] {field}")
            print(f"            GT:   {gt_value}")
            print(f"            Pred: {pred_value}")

    accuracy = (correct / total * 100) if total else 0

    print(f"\n{'-' * 70}")
    print(f"  Accuracy: {correct}/{total} ({accuracy:.2f}%)")
    print(f"  Latency: {total_latency:.4f} seconds")
    print(f"{'-' * 70}")

    return {
        "correct": correct, "total": total, "accuracy": accuracy,
        "latency_seconds": total_latency, "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens, "total_tokens": total_tokens,
        "prediction": final_json
    }

def main():
    print(f"\n{'=' * 70}\nRFP MODEL BENCHMARK\n{'=' * 70}")
    
    client = ModelClient(name=MODEL_NAME, base_url=BASE_URL, api_key=API_KEY, model=MODEL_ID)

    print("\nLoading RFP PDFs...")
    rfps = extract_all_rfps(RFP_DIR)
    rfp_items = sorted(rfps.items(), key=lambda x: x[0])

    overall_metrics = {"correct": 0, "total": 0, "latency": 0.0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    # Map alphabetically sorted PDFs to index-based JSONs (RFP_01, RFP_02...)
    for index, (rfp_name, rfp_text) in enumerate(rfp_items, start=1):
        ground_truth = load_ground_truth(index)
        
        result = process_rfp(client, rfp_name, rfp_text, ground_truth)

        for key in overall_metrics:
            overall_metrics[key] += result.get(key, 0) if key not in ["latency"] else result.get("latency_seconds", 0)

    overall_accuracy = (overall_metrics["correct"] / overall_metrics["total"] * 100) if overall_metrics["total"] else 0

    print(f"\n\n{'=' * 70}\nFINAL BENCHMARK RESULTS\n{'=' * 70}")
    print(f"Model: {MODEL_NAME}\nAccuracy: {overall_metrics['correct']}/{overall_metrics['total']} = {overall_accuracy:.2f}%\n")
    print(f"Total latency: {overall_metrics['latency']:.4f} seconds")
    print(f"Total tokens: {overall_metrics['total_tokens']}\n{'=' * 70}")

if __name__ == "__main__":
    main()