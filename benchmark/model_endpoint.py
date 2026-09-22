# model_endpoint.py

import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # IMPORT CORS

# Import your existing extraction engine
from model_client import LiftModelClient
from schema import LIFT_SCHEMA

# Initialize the FastAPI app
app = FastAPI(
    title="RFP Intelligence API",
    description="API for extracting structured JSON data from uploaded RFP PDFs using the Lift Vision Model.",
    version="1.0.0"
)

# Enable CORS so the React frontend can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connects to your local vLLM instance
client = LiftModelClient(endpoint_url="http://localhost:8000/v1")

@app.post("/api/v1/extract", summary="Upload an RFP PDF and extract structured JSON")
async def extract_rfp(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_pdf_path = None

    try:
        # 2. Save the uploaded file temporarily to disk 
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_pdf_path = Path(tmp.name)

        # 3. Process the file using your existing client
        result = client.extract_from_pdf(temp_pdf_path, LIFT_SCHEMA)

        # 4. Handle model or extraction errors
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        # 5. Return the extracted JSON payload to the user
        extracted_data = result.get("response") or {}
        
        # Inject standard metadata for the API consumer
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "latency_seconds": round(result.get("latency_seconds", 0), 2),
            "tokens_used": result.get("total_tokens", 0),
            "extracted_fields": extracted_data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        # 6. Clean up: Delete the temporary PDF from the server
        if temp_pdf_path and temp_pdf_path.exists():
            os.remove(temp_pdf_path)

# Optional health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "active", "model": client.name, "endpoint": client.endpoint_url}