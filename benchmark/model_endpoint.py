# model_endpoint.py

import os
import re
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from nemoguardrails import RailsConfig, LLMRails
from model_client import LiftModelClient
from schema import LIFT_SCHEMA

# NEW: PDF text extraction
from pypdf import PdfReader


app = FastAPI(
    title="Secure RFP Intelligence API",
    description="API for extracting structured JSON data from uploaded RFP PDFs using the Lift Vision Model and NeMo Guardrails.",
    version="1.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = LiftModelClient(endpoint_url="http://localhost:8000/v1")


# ============================================================
# Security Patterns
# ============================================================

JAILBREAK_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+the\s+schema",
    r"bypass\s+security",
    r"print\s+(your\s+)?system\s+prompt",
    r"write\s+a\s+python\s+script"
]


# ============================================================
# NVIDIA NeMo Guardrails
# ============================================================

rails = None

try:
    BASE_DIR = Path(__file__).resolve().parent.parent
    GUARDRAILS_DIR = BASE_DIR / "guardrails_config"

    config = RailsConfig.from_path(str(GUARDRAILS_DIR))
    rails = LLMRails(config)

    print("✅ NVIDIA NeMo Guardrails initialized successfully.")

except Exception as e:
    print(f"⚠️ Warning: NeMo Guardrails failed to load: {e}")


# ============================================================
# NEW: Extract text from PDF for PRE-INFERENCE security check
# ============================================================

def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF so security controls can inspect
    the document before it is sent to the LIFT model.
    """

    try:
        reader = PdfReader(str(pdf_path))

        pages_text = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages_text.append(text)

        return "\n".join(pages_text)

    except Exception as e:
        print(f"⚠️ PDF text extraction failed: {e}")
        return ""


# ============================================================
# NEW: PRE-INFERENCE SECURITY CHECK
# ============================================================

async def pre_inference_security_check(pdf_text: str, filename: str):
    """
    Security check performed BEFORE the PDF reaches LIFT.
    Returns None when allowed, otherwise returns a 403 response.
    """

    # If no text was extracted, we cannot perform a text-based
    # prompt-injection inspection.
    if not pdf_text.strip():
        print("⚠️ [PRE-CHECK] No extractable PDF text found.")
        return None

    # --------------------------------------------------------
    # LAYER 1: Deterministic Regex Check
    # --------------------------------------------------------

    for pattern in JAILBREAK_PATTERNS:

        if re.search(pattern, pdf_text, re.IGNORECASE):

            print(
                f"🚨 [PRE-INFERENCE LAYER 1 BLOCK] "
                f"Prompt injection pattern detected: {pattern}"
            )

            return JSONResponse(
                status_code=403,
                content={
                    "status": "blocked",
                    "filename": filename,
                    "detail": "Blocked by our security controls: prompt injection pattern detected before model inference."
                }
            )

    # --------------------------------------------------------
    # LAYER 2: NVIDIA NeMo Guardrails
    # --------------------------------------------------------

    if rails:

        safety_check_payload = [
            {
                "role": "user",
                "content": pdf_text
            }
        ]

        try:

            safety_response = await rails.generate_async(
                messages=safety_check_payload
            )

            response_text = safety_response.get("content", "")

            print(
                f"🔍 [PRE-INFERENCE NeMo] "
                f"Response: '{response_text}'"
            )

            if "BLOCKED_BY_GUARDRAILS" in response_text:

                print(
                    "🚨 [PRE-INFERENCE LAYER 2 BLOCK] "
                    "NeMo Guardrails blocked the document."
                )

                return JSONResponse(
                    status_code=403,
                    content={
                        "status": "blocked",
                        "filename": filename,
                        "detail": "Blocked by our security controls: NeMo Guardrails detected a policy violation before model inference."
                    }
                )

        except Exception as e:

            print(
                f"⚠️ [PRE-INFERENCE NeMo ERROR] {e}"
            )

            # Fail closed:
            # If the security control cannot run, do not send
            # potentially unsafe content to the model.
            return JSONResponse(
                status_code=503,
                content={
                    "status": "blocked",
                    "filename": filename,
                    "detail": "Security validation could not be completed. The document was not sent to the model."
                }
            )

    return None


# ============================================================
# RFP EXTRACTION ENDPOINT
# ============================================================

@app.post(
    "/api/v1/extract",
    summary="Upload an RFP PDF and extract structured JSON"
)
async def extract_rfp(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    temp_pdf_path = None

    try:

        # ----------------------------------------------------
        # Save uploaded PDF
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp:

            content = await file.read()

            tmp.write(content)

            temp_pdf_path = Path(tmp.name)


        # ====================================================
        # NEW: PRE-INFERENCE SECURITY CHECK
        # ====================================================

        pdf_text = extract_pdf_text(temp_pdf_path)

        security_result = await pre_inference_security_check(
            pdf_text,
            file.filename
        )

        if security_result is not None:
            return security_result


        # ====================================================
        # LIFT MODEL
        # ====================================================
        # The PDF reaches LIFT only after the pre-check passes.

        result = client.extract_from_pdf(
            temp_pdf_path,
            LIFT_SCHEMA
        )

        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )

        extracted_data = result.get("response") or {}


        # ====================================================
        # EXISTING POST-INFERENCE SECURITY VALIDATION
        # ====================================================

        for field_name, value in extracted_data.items():

            if not value or not isinstance(value, str):
                continue


            # ------------------------------------------------
            # LAYER 1: Deterministic Heuristic Check
            # ------------------------------------------------

            for pattern in JAILBREAK_PATTERNS:

                if re.search(
                    pattern,
                    value,
                    re.IGNORECASE
                ):

                    print(
                        f"🚨 [LAYER 1 BLOCK] "
                        f"Match found in field '{field_name}': {pattern}"
                    )

                    return JSONResponse(
                        status_code=403,
                        content={
                            "status": "blocked",
                            "filename": file.filename,
                            "detail": "Blocked by our security controls prompt injection pattern detected."
                        }
                    )


            # ------------------------------------------------
            # LAYER 2: NVIDIA NeMo Guardrails Semantic Check
            # ------------------------------------------------

            if rails:

                safety_check_payload = [
                    {
                        "role": "user",
                        "content": str(value)
                    }
                ]

                safety_response = await rails.generate_async(
                    messages=safety_check_payload
                )

                response_text = safety_response.get(
                    "content",
                    ""
                )

                print(
                    f"🔍 [NeMo Debug] "
                    f"Field: '{field_name}' | "
                    f"Response: '{response_text}'"
                )

                if "BLOCKED_BY_GUARDRAILS" in response_text:

                    return JSONResponse(
                        status_code=403,
                        content={
                            "status": "blocked",
                            "filename": file.filename,
                            "detail": f"Policy Violation in field '{field_name}': {response_text}"
                        }
                    )


        # ====================================================
        # RETURN CLEAN PAYLOAD
        # ====================================================

        return JSONResponse(
            content={
                "status": "success",
                "filename": file.filename,
                "latency_seconds": round(
                    result.get("latency_seconds", 0),
                    2
                ),
                "tokens_used": result.get(
                    "total_tokens",
                    0
                ),
                "extracted_fields": extracted_data
            }
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )


    finally:

        if (
            temp_pdf_path
            and temp_pdf_path.exists()
        ):

            os.remove(temp_pdf_path)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "status": "active",
        "model": client.name,
        "endpoint": client.endpoint_url,
        "guardrails_active": rails is not None
    }

