import json
from typing import List, Dict, Any
from schema import FIELDS

# =========================================================
# FIELD-SPECIFIC EXTRACTION INSTRUCTIONS
# =========================================================

FIELD_INSTRUCTIONS = {
    "submission_deadline": "Extract the official proposal/RFP submission deadline. Include the exact date, time, and timezone if stated. Output as a flat string.",
    "deadline_for_questions": "Extract the deadline for submitting questions, inquiries, or clarifications. Include the exact date, time, and timezone. Output as a flat string.",
    "rfp_contact": "Extract the RFP/procurement contact information. Include the person's name, title, email address, or official contact details when available. Output as a flat string.",
    "submission_method": "Extract how and where the proposal must be submitted (email, portals, URLs). Output as a flat string.",
    "contract_term": "Extract the contract duration and important term details (start/end dates, base term, renewals). Output as a flat string.",
    "scope_of_deliverables": "Extract what the vendor is actually expected to provide. Focus on the requested services, products, and deliverables. Output as a flat string.",
    "mandatory_submission_requirements": "Extract mandatory documents, forms, appendices, or certifications required. Summarize all required items into a single descriptive string. Do NOT use nested JSON objects, dicts, or arrays.",
    "mandatory_technical_requirements": "Extract mandatory technical, functional, security, or system requirements. Output as a single flat string.",
    "evaluation_criteria": "Extract ALL proposal evaluation criteria and their corresponding points/percentages. Format as a single descriptive string. Do NOT use lists or JSON dicts.",
    "minimum_score_threshold": "Extract any explicit minimum score, pass mark, or technical threshold required. If none is explicitly stated, return null.",
    "pricing_requirements": "Extract pricing and cost submission requirements (currency, taxes, fixed rates, schedules). Output as a single flat string.",
    "minimum_insurance_requirements": "Extract required insurance types and minimum coverage amounts (e.g., Commercial General Liability). Output as a flat string.",
    "vendor_experience_qualifications": "Extract required vendor/team experience and qualifications. Output as a single flat string.",
    "number_of_references_required": "Extract the required number of client/vendor references and conditions. Output as a flat string.",
    "data_security_privacy_requirements": "Extract data security, cybersecurity, privacy, compliance, and information protection requirements. Output as a flat string.",
    "data_hosting_residency_requirements": "Extract requirements or preferences related to data hosting location and residency. Output as a flat string.",
    "vendor_demonstration_requirement": "Extract whether a demonstration/presentation is required or requested, and scoring details. Output as a flat string."
}

def _get_json_template() -> str:
    template = "{\n"
    for i, field in enumerate(FIELDS):
        is_last = (i == len(FIELDS) - 1)
        template += f'  "{field}": null{"" if is_last else ","}\n'
    template += "}"
    return template

def create_chunk_prompt(chunk_text: str) -> str:
    field_instructions = "\n".join(
        f'{index}. "{field}": {FIELD_INSTRUCTIONS.get(field, "Extract related information.")}'
        for index, field in enumerate(FIELDS, start=1)
    )
    json_template = _get_json_template()

    return f"""
You are extracting structured information from an RFP document.
Your task is to extract information from ONLY the RFP text provided below.

IMPORTANT RULES:
1. Extract information only when it is supported by the provided text.
2. If a field is not present in this chunk, return null for that field.
3. Preserve important details such as dates, times, emails, URLs, numbers, percentages, and dollar amounts.
4. Output ONLY raw, valid JSON. Start immediately with '{{' and end with '}}'.
5. Do NOT use Markdown code fences (```json).

FIELDS TO EXTRACT:
{field_instructions}

RFP TEXT:
<rfp_chunk>
{chunk_text}
</rfp_chunk>

Return exactly this JSON structure:
{json_template}
""".strip()

def create_final_prompt(extractions: List[Dict[str, Any]]) -> str:
    combined = "\n\n".join(
        f"<extraction_chunk index=\"{i + 1}\">\n"
        f"{json.dumps(result, ensure_ascii=False, indent=2)}\n"
        f"</extraction_chunk>"
        for i, result in enumerate(extractions)
    )

    field_instructions = "\n".join(
        f'{index}. "{field}": {FIELD_INSTRUCTIONS.get(field, "Extract related information.")}'
        for index, field in enumerate(FIELDS, start=1)
    )
    json_template = _get_json_template()

    return f"""
You are consolidating structured information extracted from an RFP.
You will receive multiple extraction results from different chunks of the SAME RFP document.
Your task is to create ONE final JSON object containing the most accurate value for each of the {len(FIELDS)} required fields.

IMPORTANT RULES:
1. Use ONLY information contained in the extraction results below.
2. Combine information from different chunks when they refer to the same requirement.
3. Preserve exact details whenever available (dates, emails, URLs, dollar amounts).
4. If a field is genuinely not supported by any extraction results, return null.
5. Output ONLY raw, valid JSON. Start immediately with '{{' and end with '}}'.
6. Do NOT use Markdown code fences (```json).

FIELDS TO CONSOLIDATE:
{field_instructions}

EXTRACTION RESULTS:
{combined}

Return exactly this JSON structure:
{json_template}
""".strip()

def create_json_repair_prompt(raw_response: str) -> str:
    json_template = _get_json_template()
    return f"""
You are a JSON repair assistant.
The following model response was supposed to contain extracted RFP fields, but it is not valid JSON.
Convert it into valid JSON.

IMPORTANT RULES:
1. Preserve the information from the original response exactly as provided.
2. Fix invalid JSON syntax (missing commas, unescaped quotes).
3. If a required field is missing, output null for that field.
4. Output ONLY raw, valid JSON. Start immediately with '{{' and end with '}}'.

ORIGINAL INVALID RESPONSE:
<invalid_response>
{raw_response}
</invalid_response>

Return exactly this JSON structure:
{json_template}
""".strip()