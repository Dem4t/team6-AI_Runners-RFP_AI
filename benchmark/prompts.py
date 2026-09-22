import json
from schema import FIELDS

# =========================================================
# 1. FIELD-SPECIFIC EXTRACTION INSTRUCTIONS
# =========================================================

FIELD_INSTRUCTIONS = {
    "submission_deadline": (
        "Extract the official proposal/bid submission deadline (also called Closing Date, Due Date, or Bid Receipt Time). "
        "Preserve exact date, exact time, and timezone when explicitly stated. "
        "Do not confuse with the intent-to-bid or question deadlines."
    ),
    "deadline_for_questions": (
        "Extract the deadline for submitting vendor questions, inquiries, "
        "clarifications, or requests for information (RFI). "
        "Preserve exact date, exact time, and timezone."
    ),
    "rfp_contact": (
        "Extract the official RFP/procurement contact person (Buyer, Procurement Officer, SPOC). "
        "You MUST include the contact email associated with them. Do NOT substitute the general proposal submission email "
        "unless it is also explicitly identified as the official procurement contact."
    ),
    "submission_method": (
        "Extract exactly how and where the proposal must be submitted (e.g., portal name, specific email, physical address, Bonfire, MERX). "
        "Prefer the actual submission destination/URL/Email over general instructions. Keep the answer concise."
    ),
    "contract_term": (
        "Extract the COMPLETE contract term structure. "
        "Look for implementation phase, initial/base term, licensing/support period, consulting milestones, "
        "start/end dates, renewal options, and maximum total duration."
    ),
    "scope_of_deliverables": (
        "Extract the primary services, consulting, products, or deliverables requested. "
        "Look for the 'Statement of Work (SOW)', 'Project Scope', or 'Services Required' sections. "
        "Provide a concise summary of the main objective rather than a granular feature list."
    ),
    "mandatory_submission_requirements": (
        "Extract documents, forms, schedules, appendices, certifications, or signed addenda "
        "explicitly required to be submitted in the proposal package. "
        "Preserve appendix/section references exactly when available."
    ),
    "mandatory_technical_requirements": (
        "Extract mandatory technical, functional, or security requirements. "
        "If the RFP explicitly states mandatory requirements are defined in a specific section, "
        "exhibit, or appendix, extract that cross-reference and summarize the categories."
    ),
    "evaluation_criteria": (
        "Extract ALL evaluation criteria, categories, and their corresponding weights/points. "
        "Preserve the criterion names and numeric weights. "
        "Return ONE FLAT STRING only. Never return an array, list, dictionary, or nested JSON object. "
        "Example format: 'Technical Capability (50 pts), Consultant Experience (15 pts), Pricing (35 pts). Total: 100 pts.'"
    ),
    "minimum_score_threshold": (
        "Extract any explicit minimum score, passing score, technical threshold, "
        "or pass/fail condition required to advance in the evaluation process. "
        "This includes non-numeric conditions such as 'satisfactory reference checks' "
        "or 'mandatory pass/fail'. If no explicit threshold exists, return null."
    ),
    "pricing_requirements": (
        "Extract the main pricing submission instructions. "
        "Include currency, taxes, fixed/firm/hourly rates, pricing structure, "
        "and required pricing workbook/schedule appendices. Preserve important monetary details."
    ),
    "minimum_insurance_requirements": (
        "Extract all explicitly required insurance (e.g., CGL, Professional Liability, Cyber), "
        "Workers Compensation, WCB clearance, WSIB, or WorkSafe requirements. "
        "Look closely for 'Workers Compensation' or 'WCB' even if general commercial insurance isn't mentioned."
    ),
    "vendor_experience_qualifications": (
        "Extract required vendor, company, consultant, or key personnel experience. "
        "Look for 'Proponent Qualifications' or 'Company Profile'. "
        "Preserve exact thresholds (e.g., '5 years', '3 similar projects'). "
        "Include required industry experience (e.g., municipal, university, ERP readiness)."
    ),
    "number_of_references_required": (
        "Extract the REQUIRED NUMBER of references. "
        "Always preserve the quantity (e.g., '3 references', 'minimum of 2'). "
        "Also include conditions such as 'similar scope', 'last 5 years', or public-sector requirements."
    ),
    "data_security_privacy_requirements": (
        "Extract explicit security, cybersecurity, privacy, compliance, encryption, "
        "identity/access, SSO/MFA, and data protection requirements. "
        "Include named laws (e.g., FOIP, PIPEDA), standards (e.g., SOC 2, ISO 27001), or required assessments."
    ),
    "data_hosting_residency_requirements": (
        "Extract explicit data hosting, storage, residency, jurisdiction, or data-center requirements "
        "(e.g., 'Data must reside in Canada'). If a specific appendix contains these requirements, extract the cross-reference."
    ),
    "vendor_demonstration_requirement": (
        "Extract whether demonstrations, presentations, interviews, or proof-of-concepts "
        "are required/requested. You MUST include the exact scoring weight/points assigned to the demo if stated. "
        "Include mandatory/optional status and shortlisting rules."
    )
}

# =========================================================
# 2. GLOBAL PRE-COMPUTATION
# =========================================================

def _generate_json_template() -> str:
    template = "{\n"
    for i, field in enumerate(FIELDS):
        is_last = i == len(FIELDS) - 1
        template += f'  "{field}": null{"" if is_last else ","}\n'
    template += "}"
    return template

def _generate_field_instructions() -> str:
    return "\n".join(
        f'{index}. "{field}": {FIELD_INSTRUCTIONS.get(field, "Extract explicitly stated information.")}'
        for index, field in enumerate(FIELDS, start=1)
    )

PRECOMPILED_JSON_TEMPLATE = _generate_json_template()
PRECOMPILED_FIELD_INSTRUCTIONS = _generate_field_instructions()

# =========================================================
# 3. MAIN EXTRACTION PROMPT
# =========================================================

def create_extraction_prompt(rfp_text: str) -> str:
    return f"""You are an expert Cybersecurity and Procurement extraction AI. Your task is to extract critical intelligence from the provided RFP (Request for Proposal) document. 
The document may be for a software implementation, or it may be for professional consulting services. Read carefully and adapt to the terminology used.

==================================================
NON-NEGOTIABLE OUTPUT RULES
==================================================
1. Every field value MUST be either a flat STRING or JSON null.
2. NEVER return arrays `[]`.
3. NEVER return objects/dictionaries `{{}}` as field values.
4. "evaluation_criteria" MUST be a single flat string.
5. Null Rule: Use `null` ONLY when there is absolutely no explicit supporting information. Do not write "N/A", "None", or "Not specified" inside a string.
6. Absolute Accuracy: Use ONLY information explicitly present in the RFP. Never invent, hallucinate, or infer data.
7. Retain Critical Context: Preserve important dates, time zones, monetary values, percentages, quantities, emails, URLs, and section/appendix cross-references.

==================================================
EXTRACTION INSTRUCTIONS BY FIELD
==================================================
{PRECOMPILED_FIELD_INSTRUCTIONS}

==================================================
EXECUTION INSTRUCTIONS (CHAIN OF THOUGHT)
==================================================
To ensure maximum accuracy:
1. First, briefly analyze the document inside a `<thinking>` XML block. Note the document type, locate key sections, and mentally map out the 17 fields.
2. After your thinking block, output the final extracted data exactly matching the REQUIRED JSON schema inside a standard markdown JSON code block.

==================================================
RFP DOCUMENT
==================================================
<RFP_DOCUMENT>
{rfp_text}
</RFP_DOCUMENT>

==================================================
REQUIRED JSON SCHEMA
==================================================
{PRECOMPILED_JSON_TEMPLATE}
"""

# =========================================================
# 4. JSON REPAIR PROMPT
# =========================================================

def create_json_repair_prompt(raw_response: str) -> str:
    return f"""You are a precise JSON repair utility. Repair the following malformed RFP JSON.

Rules:
1. Preserve all extracted information exactly. Do not invent information.
2. Every field value MUST be a flat string or null.
3. NEVER use arrays `[]` or nested objects `{{}}`. Flatten them into strings if they exist.
4. "evaluation_criteria" MUST be a flat string.
5. Preserve numbers, dates, URLs, emails, and monetary values.
6. Ensure all 17 schema fields exist. Add missing fields as `null`.
7. Remove any fields that are not in the required schema.
8. Output ONLY the raw JSON object inside a ```json block. Do not include a thinking block.

INVALID JSON:
<INVALID_JSON>
{raw_response}
</INVALID_JSON>

REQUIRED SCHEMA:
{PRECOMPILED_JSON_TEMPLATE}
"""