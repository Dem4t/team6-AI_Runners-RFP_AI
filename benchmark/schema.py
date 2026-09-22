# schema.py

FIELDS = [
    "submission_deadline",
    "deadline_for_questions",
    "rfp_contact",
    "submission_method",
    "contract_term",
    "scope_of_deliverables",
    "mandatory_submission_requirements",
    "mandatory_technical_requirements",
    "evaluation_criteria",
    "minimum_score_threshold",
    "pricing_requirements",
    "minimum_insurance_requirements",
    "vendor_experience_qualifications",
    "number_of_references_required",
    "data_security_privacy_requirements",
    "data_hosting_residency_requirements",
    "vendor_demonstration_requirement"
]

LIFT_SCHEMA = {field: None for field in FIELDS}


FIELD_INSTRUCTIONS = {

    "submission_deadline": (
        "Extract the official proposal/bid submission closing deadline. "
        "Include the exact date, time, and timezone. "
        "Look for 'Closing Date', 'Closing Time', 'Submission Deadline', "
        "'Proposal Due Date', 'Bid Submission Deadline', or equivalent wording. "
        "Do not confuse this with the deadline for questions. "
        "If multiple dates appear, identify the actual final proposal submission deadline."
    ),

    "deadline_for_questions": (
        "Extract the exact deadline for vendor questions, inquiries, clarification requests, "
        "or requests for information. Include date, exact time, and timezone. "
        "Do not confuse this with the final proposal submission deadline."
    ),

    "rfp_contact": (
        "Extract the official RFP/procurement contact and exact contact email address. "
        "The email address MUST be copied character-for-character from the document. "
        "Do NOT correct, autocomplete, guess, normalise, or reconstruct an email address. "
        "Before returning the answer, verify every character of the domain and local part "
        "against the visible document. "
        "Pay special attention to repeated letters and common domain names. "
        "If the contact is a department rather than a person, include the department name "
        "and its exact email address. "
        "Do not substitute a submission email for a contact email unless the document "
        "explicitly identifies it as the contact."
    ),

    "submission_method": (
        "Extract the exact proposal submission method and all critical submission details. "
        "Include email address, procurement portal/system name, portal URL, physical address, "
        "required file format, submission instructions, and proposal identification/marking "
        "requirements when explicitly stated. "
        "Email addresses and URLs MUST be copied character-for-character from the document. "
        "Never correct or guess an email address or URL. "
        "Do not confuse the submission method with the RFP contact."
    ),

    "contract_term": (
        "Extract the COMPLETE contract term exactly and comprehensively. "
        "If the document provides both a start date and an end date, ALWAYS include BOTH dates. "
        "If the document provides an initial/base term duration, ALWAYS include it explicitly, "
        "even when it can be calculated from the dates. "
        "Also extract implementation periods, licensing/support periods, renewal options, "
        "extension options, and the maximum possible contract term. "
        "If both dates and duration are provided, preserve all of them rather than replacing "
        "one with another. "
        "For example, if the document states 'September 1, 2025 to August 31, 2030 (5 years)', "
        "the answer must preserve the start date, end date, and 5-year duration. "
        "Do not omit the initial term merely because extension options are also provided. "
        "Preserve exact years/months and extension periods."
    ),

    "scope_of_deliverables": (
        "Extract the primary requested services, products, deliverables, responsibilities, "
        "project objectives, implementation activities, and major work packages. "
        "Use a concise but sufficiently complete summary. "
        "Do not add capabilities or deliverables that are not explicitly stated."
    ),

    "mandatory_submission_requirements": (
        "Extract ALL explicitly mandatory proposal submission items. "
        "Include required forms, signed forms, certifications, appendices, schedules, "
        "pricing forms, declarations, reference forms, proposal sections, and other documents. "
        "Pay attention to 'must', 'shall', 'mandatory', 'required', and submission checklists. "
        "Preserve form names, section numbers, item numbers, and appendix references. "
        "Do not replace several specific mandatory items with a vague summary."
    ),

    "mandatory_technical_requirements": (
        "Extract ALL explicitly mandatory technical, functional, operational, implementation, "
        "system, hosting, compliance, and solution requirements. "
        "Do not select only the most important requirements. "
        "Capture every explicit mandatory requirement that materially defines compliance. "
        "Preserve all numeric thresholds and qualifications, including years of experience, "
        "number of projects, percentages, quantities, limits, certifications, and geographic "
        "requirements. "
        "Pay special attention to mandatory evaluation tables, appendices, technical schedules, "
        "and requirement matrices. "
        "If a mandatory evaluation table lists multiple requirements, include all material "
        "requirements from that table rather than merely saying 'must meet the table'. "
        "Preserve appendix, section, table, and exhibit references when useful."
    ),

    "evaluation_criteria": (
        "Extract the COMPLETE evaluation structure. "
        "Identify every evaluation stage and every criterion that contributes to selection. "
        "For each scored criterion, preserve its exact point value and/or percentage. "
        "Include stage totals and the overall total when explicitly provided. "
        "Include technical evaluation, experience, references, implementation, pricing, "
        "demonstrations, interviews, and other scored components. "
        "Also identify mandatory pass/fail stages separately when they are part of the "
        "evaluation process, but do not assign points to a pass/fail requirement unless "
        "the document explicitly assigns points. "
        "Do not confuse mandatory screening stages with scored evaluation criteria. "
        "Preserve the document's numeric values exactly. "
        "Do not omit criteria merely because they appear in a separate table or appendix."
    ),

    "minimum_score_threshold": (
        "Extract explicit minimum scoring thresholds or explicit advancement thresholds "
        "that require a proposal to achieve a specified score, percentage, or point total "
        "in order to advance to another stage or remain eligible for further evaluation. "
        "Examples include 'minimum technical score of 35 out of 50 points', "
        "'must achieve at least 70%', or 'must obtain 28 points (80%) to advance'. "
        "Preserve the exact score, percentage, points, stage, and advancement condition. "
        ""
        "Do NOT treat ordinary mandatory requirements, mandatory submission requirements, "
        "mandatory technical requirements, or general pass/fail compliance checks as a "
        "minimum score threshold. "
        ""
        "Do NOT extract a general statement such as 'all mandatory requirements must be met' "
        "as a threshold. "
        ""
        "A reference check, interview, demonstration, or other pass/fail condition should "
        "ONLY be extracted here if the document explicitly states that passing that condition "
        "is required to advance, qualify, or remain eligible. "
        ""
        "If the document only lists 'Pass/Fail', 'Yes/No', 'Mandatory', or 'Required' "
        "without explicitly connecting it to advancement, qualification, or eligibility, "
        "do not treat it as a minimum score threshold. "
        ""
        "If multiple explicit numeric or advancement thresholds exist, include all of them. "
        "If the document explicitly says that no minimum threshold exists, return null."
    ),

    "pricing_requirements": (
        "Extract ALL important pricing requirements and constraints. "
        "Include currency, taxes, pricing validity, fixed/firm pricing requirements, "
        "contract duration applicable to pricing, Incoterms, one-time costs, implementation "
        "costs, recurring costs, annual subscription/licensing costs, maintenance/support, "
        "training, optional costs, and required pricing breakdowns. "
        "If the RFP requires itemised pricing, preserve every named pricing category. "
        "For example, distinguish 'Implementation Costs (one-time)' from "
        "'Ongoing LMS Licensing/Support Costs (annual subscription)'. "
        "Do not summarise itemised pricing into a generic statement such as 'provide pricing'. "
        "Preserve CAD/USD/etc., GST/PST/VAT treatment, percentages, monetary amounts, "
        "and Incoterms exactly as stated."
    ),

    "minimum_insurance_requirements": (
        "Extract ALL mandatory insurance and insurance-related requirements. "
        "Include policy type, coverage limit, aggregate limit, per-occurrence limit, "
        "deductible, certificate requirements, Workers' Compensation requirements, "
        "clearance certificates, and other mandatory evidence. "
        "Do not omit requirements merely because they have no monetary coverage amount. "
        "Preserve exact monetary limits."
    ),

    "vendor_experience_qualifications": (
        "Extract ALL required vendor/company/team experience qualifications. "
        "Include minimum years, number of projects, similar-project requirements, "
        "public-sector experience, industry experience, geographic experience, "
        "team qualifications, and other explicit experience thresholds. "
        "Preserve exact numeric requirements. "
        "Do not confuse experience qualifications with the number of references."
    ),

    "number_of_references_required": (
        "Extract the exact number of references required AND every qualification attached "
        "to those references. "
        "Do not stop after identifying the number. "
        "Include whether references must be clients, recent clients, similar projects, "
        "similar scope or size, public-sector clients, or projects completed within a specific "
        "number of years. "
        "Preserve time windows such as 'within the last 5 years'. "
        "Preserve scope/size conditions such as 'similar in scope and size'. "
        "If several reference conditions appear in different sections, combine them into one "
        "complete flat string. "
        "For example, 'minimum of three (3) client references similar in scope & size over "
        "the last 5 years' must retain the number, client requirement, similarity requirement, "
        "and 5-year time condition."
    ),

    "data_security_privacy_requirements": (
        "Extract ALL explicit security, cybersecurity, privacy, compliance, and data protection "
        "requirements. "
        "Include laws, regulations, standards, certifications, encryption, authentication, "
        "access control, logging, breach notification, privacy requirements, SOC 2, ISO 27001, "
        "PIPA, GDPR, and other explicitly stated requirements. "
        "Preserve exact certification levels and standards."
    ),

    "data_hosting_residency_requirements": (
        "Extract ALL requirements concerning data storage, hosting, processing, access, "
        "jurisdiction, residency, or physical data-centre location. "
        "Include country, province/state, cloud region, hosting jurisdiction, data-centre "
        "location, and restrictions on where data may be stored or processed. "
        "Also include explicit requirements in referenced appendices, SaaS forms, security "
        "schedules, or hosting declarations. "
        "If the RFP requires the vendor to disclose hosting locations, include that requirement "
        "even when the actual location is not predetermined."
    ),

    "vendor_demonstration_requirement": (
        "Extract ALL requirements concerning vendor demonstrations, product demonstrations, "
        "solution demonstrations, presentations, or interviews. "
        "Include the evaluation stage, whether the demonstration is mandatory, whether only "
        "shortlisted vendors participate, whether vendors may be called or invited, whether "
        "the demonstration is part of the evaluation, whether a demonstration script or "
        "specific scenarios are required, whether specific capabilities must be demonstrated, "
        "and the exact point weighting if stated. "
        "Preserve the distinction between: "
        "'required', 'will be invited', 'may be called', 'shortlisted vendors', and 'optional'. "
        "If the document says shortlisted proponents may be called for a second-level interview "
        "or product presentation/demonstration, explicitly preserve that conditional shortlist "
        "requirement. "
        "Do not replace a conditional demonstration requirement with a stronger statement that "
        "the demonstration is mandatory for all vendors. "
        "Do not omit demonstration requirements merely because they appear in the evaluation "
        "or selection section."
    )
}


# =============================================================
# JSON TEMPLATE
# =============================================================

def _generate_json_template() -> str:
    template = "{\n"

    for i, field in enumerate(FIELDS):
        is_last = i == len(FIELDS) - 1

        template += (
            f'    "{field}": null'
            f'{"" if is_last else ","}\n'
        )

    template += "}"

    return template


# =============================================================
# FIELD INSTRUCTIONS
# =============================================================

def _generate_field_instructions() -> str:
    return "\n".join(
        f'{index}. "{field}": '
        f'{FIELD_INSTRUCTIONS.get(field, "Extract explicitly stated information.")}'
        for index, field in enumerate(FIELDS, start=1)
    )


PRECOMPILED_JSON_TEMPLATE = _generate_json_template()

PRECOMPILED_FIELD_INSTRUCTIONS = _generate_field_instructions()


# =============================================================
# EXTRACTION PROMPT
# =============================================================

def create_extraction_prompt(rfp_text: str = "") -> str:

    return f"""You are an expert RFP Procurement, Legal, and Technical Extraction AI.

Your job is to extract structured information from the COMPLETE RFP document.

The document may contain relevant information in:

- normal paragraphs
- tables
- evaluation matrices
- appendices
- schedules
- forms
- technical requirement tables
- pricing tables
- mandatory evaluation tables
- security schedules
- SaaS forms
- footnotes
- selection/evaluation sections

You MUST inspect the entire provided document before producing the final answer.

==================================================
CORE EXTRACTION PRINCIPLES
==================================================

1. Extract ONLY information explicitly supported by the document.

2. NEVER hallucinate.

3. NEVER infer missing information.

4. Every field MUST be either:
   - one flat string
   - or JSON null.

5. NEVER return arrays.

6. NEVER return nested objects.

7. Use null only when no explicit supporting information exists.

8. Do not use:
   - "N/A"
   - "None"
   - "Not specified"
   - ""

9. Preserve exact:
   - dates
   - times
   - timezones
   - numbers
   - percentages
   - monetary values
   - email addresses
   - URLs
   - names
   - section numbers
   - appendix names
   - certification names
   - years/months
   - point values

10. If information appears in multiple sections, combine the relevant information into
    one complete flat string.

11. Do not replace specific requirements with vague summaries.

12. When several requirements exist for one field, include all important requirements.

13. Information in tables and appendices has the same importance as information in
    normal paragraphs.

==================================================
CRITICAL EXACT-COPY RULE
==================================================

For emails and URLs:

- Copy them exactly as they appear.
- Do not correct spelling.
- Do not autocomplete domains.
- Do not guess missing characters.
- Do not replace a document email with a similar email.
- Do not change punctuation.
- Do not change the domain.

EMAIL VERIFICATION:

- Visually inspect the complete email address in the document.
- Copy the local part and domain character-by-character.
- Pay special attention to repeated letters and common domain names.
- Do not rely on memory or expected spelling.
- If the same email appears multiple times, compare the occurrences.
- If the document clearly shows "oldscollege.ca", do not transform it into
  "oldscollge.ca" or another spelling.

URL VERIFICATION:

- Copy the complete URL exactly as shown.
- Preserve the protocol, domain, path, query parameters, and punctuation.
- Do not reconstruct or simplify a URL.

Before returning an email or URL, compare it character-by-character with the document.

==================================================
NUMERIC PRESERVATION RULE
==================================================

Never remove important numeric information.

Preserve:

- points
- percentages
- dollar amounts
- years
- months
- quantities
- limits
- thresholds
- number of references
- number of projects
- contract duration
- extension duration

For example:

"35 out of 50 points"

must not become only:

"technical threshold"

==================================================
CONTRACT TERM RULE
==================================================

For contract terms, preserve ALL explicitly stated temporal information.

If the document gives:

- start date
- end date
- initial term duration
- implementation period
- licensing period
- support period
- renewal period
- extension period
- maximum possible term

include all applicable information.

Do NOT replace explicit dates with a calculated duration.

Do NOT replace an explicit duration with dates.

For example:

"September 1, 2025 to August 31, 2030 (5 years)"

must preserve:

- September 1, 2025
- August 31, 2030
- 5 years

==================================================
REFERENCE REQUIREMENT RULE
==================================================

When extracting the number of references, preserve BOTH:

1. The number of references.
2. All qualification conditions attached to those references.

Look specifically for:

- client references
- similar projects
- similar scope
- similar size
- recent projects
- years/months
- public-sector clients
- industry requirements
- satisfactory/pass requirements

For example:

"Minimum of three (3) client references similar in scope & size over the last 5 years"

must preserve all four concepts:

- 3 references
- client references
- similar scope/size
- last 5 years

==================================================
EVALUATION RULE
==================================================

Separate these concepts:

A. Mandatory pass/fail requirements
B. Scored evaluation criteria
C. Minimum scores required to advance
D. Demonstration/interview stages

Do not merge them incorrectly.

For scored criteria, preserve:

- criterion name
- points
- percentage
- stage
- stage total
- overall total

For pass/fail requirements, explicitly identify them as pass/fail.

For minimum thresholds, identify the exact condition required to advance.

IMPORTANT:

A pass/fail or yes/no condition belongs in minimum_score_threshold ONLY when
the document indicates that the condition determines qualification, advancement,
eligibility, or successful completion.

For example:

"Reference Checks: Pass/Fail"

alone does not automatically prove that references are a qualification threshold.

However, if the document says that references must be satisfactory for the vendor
to qualify, advance, or remain eligible, extract that condition as a threshold.

==================================================
DEMONSTRATION RULE
==================================================

When extracting demonstrations, carefully preserve the conditional nature of the requirement.

Distinguish:

- all vendors must demonstrate
- shortlisted vendors must demonstrate
- shortlisted vendors may be called
- vendors will be invited
- vendors may be invited
- demonstration is optional
- demonstration is part of Stage 2
- demonstration receives points
- demonstration is only for clarification

Do not convert "may be called" into "must demonstrate".

Do not convert "shortlisted vendors" into "all vendors".

==================================================
COMPLETENESS RULE
==================================================

For every field, ask internally:

"Is there another section, table, appendix, or schedule containing information
relevant to this field?"

If yes, include the relevant information.

Do not stop after finding the first occurrence.

==================================================
FIELD-SPECIFIC INSTRUCTIONS
==================================================

{PRECOMPILED_FIELD_INSTRUCTIONS}

==================================================
FINAL SELF-CHECK
==================================================

Before returning the JSON, silently verify:

[ ] All 17 fields are present.

[ ] Every value is a flat string or null.

[ ] No arrays exist.

[ ] No nested objects exist.

[ ] Submission deadline is not confused with question deadline.

[ ] Emails are copied exactly character-by-character.

[ ] URLs are copied exactly.

[ ] All important numeric values are preserved.

[ ] Contract term includes BOTH dates when available.

[ ] Contract term includes the explicit initial/base duration when available.

[ ] Contract extensions and maximum possible term are preserved.

[ ] Mandatory technical requirements include all important mandatory thresholds.

[ ] Evaluation criteria contain all scored criteria and point values.

[ ] Minimum thresholds contain explicit advancement conditions.

[ ] Pass/fail conditions are treated as thresholds only when they determine
    qualification, advancement, eligibility, or successful completion.

[ ] Pricing includes currency, taxes, duration, and itemised pricing categories when stated.

[ ] Insurance includes certificate/clearance requirements as well as monetary limits.

[ ] Reference requirements include both the number and all qualification conditions.

[ ] Data hosting requirements include referenced forms/appendices.

[ ] Demonstration requirements preserve whether participation is mandatory,
    conditional, shortlisted, invited, or optional.

[ ] No information has been invented.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this schema:

{PRECOMPILED_JSON_TEMPLATE}
"""