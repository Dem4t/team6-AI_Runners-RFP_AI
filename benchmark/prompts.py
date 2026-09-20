import json
from schema import FIELDS

# =========================================================
# 1. FIELD-SPECIFIC EXTRACTION INSTRUCTIONS
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

# =========================================================
# 2. GLOBAL PRE-COMPUTATION (CPU OPTIMIZATION)
# =========================================================
def _generate_json_template() -> str:
    """Builds the strict JSON template once at startup."""
    template = "{\n"
    for i, field in enumerate(FIELDS):
        is_last = (i == len(FIELDS) - 1)
        template += f'  "{field}": null{"" if is_last else ","}\n'
    template += "}"
    return template

def _generate_field_instructions() -> str:
    """Builds the numbered extraction rules once at startup."""
    return "\n".join(
        f'{index}. "{field}": {FIELD_INSTRUCTIONS.get(field, "Extract related information.")}'
        for index, field in enumerate(FIELDS, start=1)
    )

PRECOMPILED_JSON_TEMPLATE = _generate_json_template()
PRECOMPILED_FIELD_INSTRUCTIONS = _generate_field_instructions()

# =========================================================
# 3. PROMPT GENERATORS (LLM OPTIMIZATION)
# =========================================================

def create_extraction_prompt(rfp_text: str) -> str:
    """
    Creates a strict, zero-shot extraction prompt tailored for Qwen2.5.
    Replaces the legacy chunking architecture for single-pass processing.
    """
    return f"""You are a precise data extraction system parsing Request for Proposal (RFP) documents.
Your task is to extract information from ONLY the provided RFP text and output it as a strict JSON object.

CRITICAL INSTRUCTIONS:
1. Extract information only when explicitly supported by the text.
2. If a field is not present or cannot be determined, strictly use null (do not use "N/A" or "None").
3. Preserve exact details: dates, times, emails, URLs, numbers, percentages, and dollar amounts.
4. Escape any internal double quotes within your extracted text (e.g., \\"example\\").
5. OUTPUT FORMAT: Return ONLY valid, raw JSON. Do not include introductory text, conversational filler, or Markdown code fences (```json).

FIELDS TO EXTRACT:
{PRECOMPILED_FIELD_INSTRUCTIONS}

RFP TEXT TO PROCESS:
<RFP_DOCUMENT>
{rfp_text}
</RFP_DOCUMENT>

Return exactly this JSON structure, replacing null with your extracted strings where applicable:
{PRECOMPILED_JSON_TEMPLATE}
""".strip()

def create_json_repair_prompt(raw_response: str) -> str:
    """
    Acts as a fail-safe to format malformed LLM outputs into valid JSON,
    saving the benchmark run from crashing due to syntax errors.
    """
    return f"""You are a JSON repair microservice.
The following text contains data that was supposed to be a strict JSON object, but it contains formatting errors.
Your ONLY job is to output the corrected, strictly valid JSON object.

CRITICAL INSTRUCTIONS:
1. Preserve all extracted information exactly as provided.
2. Fix invalid JSON syntax (add missing commas, escape unescaped double quotes, fix trailing commas).
3. If a required field is missing from the input, set its value to null.
4. OUTPUT FORMAT: Return ONLY valid, raw JSON. Do not include introductory text, explanations, or Markdown code fences (```json).

INVALID INPUT DATA:
<INVALID_JSON>
{raw_response}
</INVALID_JSON>

You must map the repaired data precisely to this schema:
{PRECOMPILED_JSON_TEMPLATE}
""".strip()