# run_benchmark.py

import json
import re
from pathlib import Path
from typing import Dict, Any, Set, List

from schema import FIELDS, LIFT_SCHEMA
from model_client import LiftModelClient


# =========================================================
# 1. Model Configuration & Tuning
# =========================================================

MODEL_NAME = "/home/ubuntu/models/lift"
BASE_URL = "http://localhost:8000/v1"


# =========================================================
# 2. Project Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RFP_DIR = BASE_DIR / "data" / "rfps"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"
OUTPUT_DIR = BASE_DIR / "benchmark_outputs"


# =========================================================
# 3. Pre-compiled Regular Expressions
# =========================================================

WHITESPACE_PATTERN = re.compile(r"\s+")
NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
URL_PATTERN = re.compile(r"https?://[^\s]+")
WORD_PATTERN = re.compile(r"[a-z0-9]+")


# =========================================================
# 4. JSON Normalisation
# =========================================================

def ensure_fields(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}

    return {
        field: data.get(field, None)
        for field in FIELDS
    }


# =========================================================
# 5. Normalisation Helpers
# =========================================================

def is_null(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return value.strip().lower() in {
            "",
            "null",
            "none",
            "n/a",
            "na",
            "not specified"
        }

    return False


def value_to_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(
            value_to_text(item)
            for item in value
        )

    if isinstance(value, dict):
        return " ".join(
            f"{key} {value_to_text(val)}"
            for key, val in value.items()
        )

    return str(value)


def normalise_text(value: Any) -> str:
    text = value_to_text(value).lower()

    return WHITESPACE_PATTERN.sub(
        " ",
        text
    ).strip()


def normalise_number(value: Any) -> Set[float]:
    text = (
        value_to_text(value)
        .lower()
        .replace(",", "")
    )

    text = (
        text
        .replace("million", "m")
        .replace("billion", "b")
        .replace("thousand", "k")
    )

    word_map = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10"
    }

    for word, digit in word_map.items():
        text = re.sub(
            rf"\b{word}\b",
            digit,
            text
        )

    parsed_numbers = set()

    for num_str in NUMBER_PATTERN.findall(text):
        try:
            val = float(num_str)

            if val.is_integer():
                parsed_numbers.add(int(val))
            else:
                parsed_numbers.add(val)

        except ValueError:
            pass

    return parsed_numbers


def extract_emails(value: Any) -> Set[str]:
    return {
        email.lower()
        for email in EMAIL_PATTERN.findall(
            value_to_text(value)
        )
    }


def extract_urls(value: Any) -> Set[str]:
    return {
        url.lower().rstrip(".,)")
        for url in URL_PATTERN.findall(
            value_to_text(value)
        )
    }


def word_set(value: Any) -> Set[str]:
    return set(
        WORD_PATTERN.findall(
            normalise_text(value)
        )
    )


def term_recall(
    ground_truth: Any,
    prediction: Any,
    min_recall: float = 0.20
) -> bool:

    gt_words = word_set(ground_truth)
    pred_words = word_set(prediction)

    if not gt_words:
        return True

    recall = len(
        gt_words & pred_words
    ) / len(gt_words)

    return recall >= min_recall


# =========================================================
# 6. Field Comparison
# =========================================================

def compare_field(
    ground_truth: Any,
    prediction: Any
) -> bool:

    if is_null(ground_truth):
        return is_null(prediction)

    if is_null(prediction):
        return False

    gt_numbers = normalise_number(
        ground_truth
    )

    pred_numbers = normalise_number(
        prediction
    )

    if gt_numbers and not gt_numbers.issubset(pred_numbers):
        return False

    gt_emails = extract_emails(
        ground_truth
    )

    pred_emails = extract_emails(
        prediction
    )

    if gt_emails and not gt_emails.issubset(pred_emails):
        return False

    gt_urls = extract_urls(
        ground_truth
    )

    pred_urls = extract_urls(
        prediction
    )

    if gt_urls and not (gt_urls & pred_urls):
        return False

    return term_recall(
        ground_truth,
        prediction,
        min_recall=0.10
    )


# =========================================================
# 7. Sequential Worker: Process One RFP
# =========================================================

def process_rfp(
    client: LiftModelClient,
    pdf_path: Path,
    ground_truth: Dict[str, Any]
) -> Dict[str, Any]:

    print(
        f"\n-> Processing file: {pdf_path.name}..."
    )

    # -----------------------------------------------------
    # 1. Model extraction
    # -----------------------------------------------------

    result = client.extract_from_pdf(
        pdf_path,
        LIFT_SCHEMA
    )

    total_latency = result.get(
        "latency_seconds",
        0
    )

    total_input_tokens = result.get(
        "input_tokens",
        0
    )

    total_output_tokens = result.get(
        "output_tokens",
        0
    )

    total_tokens = result.get(
        "total_tokens",
        0
    )

    final_json = ensure_fields(
        result.get("response") or {}
    )

    # -----------------------------------------------------
    # 2. Save JSON output
    # -----------------------------------------------------

    json_path = (
        OUTPUT_DIR /
        f"{pdf_path.name}_output.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            final_json,
            f,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # 3. Save Markdown output
    # -----------------------------------------------------

    md_path = (
        OUTPUT_DIR /
        f"{pdf_path.name}_output.md"
    )

    md_content = [
        f"# مخرجات النموذج لملف: {pdf_path.name}\n\n"
    ]

    for field, text in final_json.items():

        md_content.append(
            f"### {field}\n"
        )

        if (
            not text
            or str(text).strip().lower() == "null"
        ):
            md_content.append(
                "*[لم يتم العثور على بيانات]*\n\n"
            )

        else:
            md_content.append(
                f"{text}\n\n"
            )

        md_content.append(
            "---\n"
        )

    with open(
        md_path,
        "w",
        encoding="utf-8"
    ) as md_file:

        md_file.write(
            "".join(md_content)
        )

    # -----------------------------------------------------
    # 4. Compare with Ground Truth
    # -----------------------------------------------------

    correct = 0
    total = len(FIELDS)

    field_results = {}

    for field in FIELDS:

        gt_value = ground_truth.get(
            field
        )

        pred_value = final_json.get(
            field
        )

        is_correct = compare_field(
            gt_value,
            pred_value
        )

        if is_correct:
            correct += 1

        field_results[field] = {
            "correct": is_correct,
            "gt": gt_value,
            "pred": pred_value
        }

    # -----------------------------------------------------
    # 5. Print failed fields immediately
    # -----------------------------------------------------

    failed_fields = [
        field
        for field in FIELDS
        if not field_results[field]["correct"]
    ]

    if failed_fields:

        print(
            f"\n   FAILED FIELDS "
            f"({len(failed_fields)}):"
        )

        for field in failed_fields:

            gt_value = field_results[field]["gt"]
            pred_value = field_results[field]["pred"]

            print(
                f"\n   [FAIL] {field}"
            )

            print(
                f"          Expected: {gt_value}"
            )

            print(
                f"          Predicted: {pred_value}"
            )

    else:

        print(
            "\n   ALL FIELDS PASSED"
        )

    # -----------------------------------------------------
    # 6. Return complete benchmark result
    # -----------------------------------------------------

    return {
        "rfp_name": pdf_path.name,
        "correct": correct,
        "total": total,
        "accuracy": (
            correct / total * 100
            if total
            else 0
        ),
        "latency_seconds": total_latency,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "prediction": final_json,
        "field_results": field_results
    }


# =========================================================
# 8. Load Ground Truth
# =========================================================

def load_all_ground_truths(
    pdf_files: List[Path]
) -> Dict[str, Dict[str, Any]]:

    truths = {}

    for index, pdf_path in enumerate(
        pdf_files,
        start=1
    ):

        path = (
            GROUND_TRUTH_DIR /
            f"RFP_{index:02d}.json"
        )

        if path.exists():

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                truths[pdf_path.name] = (
                    json.load(f)
                    .get(
                        "extracted_fields",
                        {}
                    )
                )

        else:

            print(
                f"WARNING: Ground truth not found: {path}"
            )

            truths[pdf_path.name] = {}

    return truths


# =========================================================
# 9. Save Field-Level Accuracy Report
# =========================================================

def save_field_accuracy_report(
    all_results: List[Dict[str, Any]]
) -> None:

    field_stats = {}

    # -----------------------------------------------------
    # Calculate statistics for every field
    # -----------------------------------------------------

    for field in FIELDS:

        correct_count = 0
        total_count = 0
        failures = []

        for result in all_results:

            field_result = (
                result["field_results"]
                .get(field)
            )

            if field_result is None:
                continue

            total_count += 1

            if field_result["correct"]:
                correct_count += 1

            else:
                failures.append({
                    "rfp_name": result["rfp_name"],
                    "expected": field_result["gt"],
                    "predicted": field_result["pred"]
                })

        accuracy = (
            correct_count / total_count * 100
            if total_count
            else 0
        )

        field_stats[field] = {
            "correct": correct_count,
            "total": total_count,
            "accuracy": round(
                accuracy,
                2
            ),
            "failures": failures
        }

    # -----------------------------------------------------
    # Save JSON report
    # -----------------------------------------------------

    report_path = (
        OUTPUT_DIR /
        "field_accuracy_report.json"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            field_stats,
            f,
            indent=4,
            ensure_ascii=False
        )

    # -----------------------------------------------------
    # Print field-level summary
    # -----------------------------------------------------

    print(
        f"\n\n{'=' * 70}"
    )

    print(
        "FIELD-LEVEL ACCURACY"
    )

    print(
        f"{'=' * 70}"
    )

    print(
        f"{'Field':<45}"
        f"{'Correct':>10}"
        f"{'Total':>8}"
        f"{'Accuracy':>10}"
    )

    print(
        "-" * 70
    )

    for field in FIELDS:

        stats = field_stats[field]

        print(
            f"{field:<45}"
            f"{stats['correct']:>10}"
            f"{stats['total']:>8}"
            f"{stats['accuracy']:>9.2f}%"
        )

    print(
        "-" * 70
    )

    print(
        f"Report saved to: {report_path}"
    )


# =========================================================
# 10. Main Benchmark
# =========================================================

def main():

    print(
        f"\n{'=' * 70}"
    )

    print(
        "RFP MODEL BENCHMARK (SEQUENTIAL MODE)"
    )

    print(
        f"{'=' * 70}"
    )

    print(
        f"Model: {MODEL_NAME} | URL: {BASE_URL}"
    )

    print(
        f"{'=' * 70}"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    client = LiftModelClient(
        endpoint_url=BASE_URL
    )

    # -----------------------------------------------------
    # Validate RFP directory
    # -----------------------------------------------------

    if not RFP_DIR.exists():

        print(
            f"ERROR: Data directory not found at: {RFP_DIR}"
        )

        return

    pdf_files = sorted(
        RFP_DIR.glob("*.pdf")
    )

    if not pdf_files:

        print(
            "ERROR: No RFP PDFs were found."
        )

        return

    # -----------------------------------------------------
    # Load ground truths
    # -----------------------------------------------------

    ground_truths = load_all_ground_truths(
        pdf_files
    )

    print(
        f"Found {len(pdf_files)} RFP files. "
        "Beginning sequential file-by-file processing...\n"
    )

    # -----------------------------------------------------
    # Overall metrics
    # -----------------------------------------------------

    overall_metrics = {
        "correct": 0,
        "total": 0,
        "latency": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0
    }

    # Store every result so that we can perform
    # field-level analysis after the benchmark.
    all_results = []

    # -----------------------------------------------------
    # Process RFPs sequentially
    # -----------------------------------------------------

    for pdf_path in pdf_files:

        try:

            result = process_rfp(
                client,
                pdf_path,
                ground_truths[pdf_path.name]
            )

            all_results.append(result)

            print(
                f"\n[{result['rfp_name']}] Completed | "
                f"Accuracy: "
                f"{result['correct']}/"
                f"{result['total']} "
                f"({result['accuracy']:.2f}%) | "
                f"Latency: "
                f"{result['latency_seconds']:.2f}s"
            )

            # ---------------------------------------------
            # Update overall metrics
            # ---------------------------------------------

            overall_metrics["correct"] += (
                result["correct"]
            )

            overall_metrics["total"] += (
                result["total"]
            )

            overall_metrics["latency"] += (
                result["latency_seconds"]
            )

            overall_metrics["input_tokens"] += (
                result["input_tokens"]
            )

            overall_metrics["output_tokens"] += (
                result["output_tokens"]
            )

            overall_metrics["total_tokens"] += (
                result["total_tokens"]
            )

        except Exception as exc:

            print(
                f"[{pdf_path.name}] "
                f"generated an exception: {exc}"
            )

    # -----------------------------------------------------
    # Overall accuracy
    # -----------------------------------------------------

    overall_accuracy = (
        overall_metrics["correct"]
        / overall_metrics["total"]
        * 100
        if overall_metrics["total"]
        else 0
    )

    # -----------------------------------------------------
    # Save field-level report
    # -----------------------------------------------------

    if all_results:
        save_field_accuracy_report(
            all_results
        )

    # -----------------------------------------------------
    # Final benchmark results
    # -----------------------------------------------------

    print(
        f"\n\n{'=' * 70}"
    )

    print(
        "FINAL BENCHMARK RESULTS"
    )

    print(
        f"{'=' * 70}"
    )

    print(
        f"Accuracy: "
        f"{overall_metrics['correct']}/"
        f"{overall_metrics['total']} "
        f"= {overall_accuracy:.2f}%"
    )

    print(
        f"Cumulative Latency: "
        f"{overall_metrics['latency']:.4f} seconds"
    )

    print(
        f"Total input tokens: "
        f"{overall_metrics['input_tokens']}"
    )

    print(
        f"Total output tokens: "
        f"{overall_metrics['output_tokens']}"
    )

    print(
        f"Total tokens: "
        f"{overall_metrics['total_tokens']}"
    )

    print(
        f"{'=' * 70}"
    )


# =========================================================
# 11. Entry Point
# =========================================================

if __name__ == "__main__":
    main()
