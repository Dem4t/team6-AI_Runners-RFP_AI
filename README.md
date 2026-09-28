# RFP AI — Intelligent RFP Extraction System

AI-powered system for extracting structured information from Request for Proposal (RFP) documents using a local vision-language model, FastAPI, React, and NVIDIA NeMo Guardrails.

The system is designed to process RFP PDF documents, detect potential prompt-injection attempts, extract predefined fields into structured JSON, and expose the results through a web interface.

---

## Overview

The system provides an end-to-end RFP extraction pipeline:

```text
RFP PDF
   │
   ▼
React Web Interface
   │
   ▼
FastAPI API
   │
   ├── PDF Security Check
   │       ├── Regex-based detection
   │       └── NVIDIA NeMo Guardrails
   │
   ▼
Lift Vision Model / vLLM
   │
   ▼
Structured JSON
   │
   ├── Post-inference security validation
   │
   ▼
Web Interface
```

---

## Key Features

* PDF upload and processing
* Structured RFP information extraction
* Local vLLM model serving
* Vision-based PDF processing
* NVIDIA NeMo Guardrails
* Prompt-injection detection
* Pre-inference security validation
* Post-inference security validation
* JSON output
* Markdown benchmark outputs
* Field-level accuracy evaluation
* Token and latency tracking
* Kubernetes deployment manifests
* Prometheus and Grafana monitoring
* React/Vite web interface

---

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* PyMuPDF
* pypdf
* Requests
* Pydantic
* NVIDIA NeMo Guardrails

### AI / Inference

* Lift Vision Model
* vLLM
* OpenAI-compatible API

### Frontend

* React
* Vite
* JavaScript
* CSS

### Infrastructure

* Docker
* Kubernetes
* NVIDIA GPU
* Prometheus
* Grafana

---

## Project Structure

```text
.
├── benchmark/
│   ├── model_client.py
│   ├── model_endpoint.py
│   ├── pdf_parser.py
│   ├── prompts.py
│   ├── run_benchmark.py
│   ├── schema.py
│   └── test_model_client.py
│
├── benchmark_outputs/
│   ├── *.json
│   ├── *.md
│   └── field_accuracy_report.json
│
├── data/
│   ├── ground_truth/
│   │   ├── RFP_01.json
│   │   ├── RFP_02.json
│   │   ├── RFP_03.json
│   │   ├── RFP_04.json
│   │   └── RFP_05.json
│   │
│   └── rfps/
│       └── *.pdf
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── guardrails_config/
│   ├── config.yml
│   └── rails.co
│
├── monitoring/
│   ├── compose.yaml
│   ├── dashboard.json
│   └── prometheus.yml
│
├── Dockerfile.web
├── lift-k8s.yaml
├── rfp-web-k8s.yaml
├── requirements.txt
├── web_container.py
└── README.md
```

---

## RFP Fields

The extraction schema currently contains 17 predefined fields, including:

1. Submission Deadline
2. Deadline for Questions / Inquiries
3. RFP Contact
4. Submission Method / Portal
5. Contract Term / Duration
6. Scope of Deliverables / Services
7. Mandatory Submission Requirements
8. Mandatory Technical Requirements
9. Evaluation Criteria & Weighting
10. Minimum Score Threshold
11. Pricing Structure
12. Insurance Requirements
13. Vendor Experience / Qualifications
14. Number of References Required
15. Data Security / Privacy Requirements
16. Data Hosting / Residency Requirements
17. Vendor Demonstration Requirement

The schema is defined in:

```text
benchmark/schema.py
```

---

## Security

Security validation is implemented in multiple layers.

### 1. Deterministic Prompt-Injection Detection

The API checks uploaded PDF text against known patterns such as:

* Ignore previous instructions
* Disregard the schema
* Bypass security
* Print the system prompt
* Execute unrelated code

### 2. NVIDIA NeMo Guardrails

NeMo Guardrails performs semantic checks before model inference.

The configuration is located in:

```text
guardrails_config/config.yml
guardrails_config/rails.co
```

### 3. Post-Inference Validation

Extracted fields are checked again before being returned to the frontend.

If a security violation is detected, the API blocks the response instead of returning the extracted content.

---

## API

### Health Check

```http
GET /health
```

Example:

```json
{
  "status": "active",
  "model": "/home/ubuntu/models/lift",
  "endpoint": "http://localhost:8000/v1",
  "guardrails_active": true
}
```

### Extract RFP

```http
POST /api/v1/extract
```

Upload a PDF using the `file` form field.

Example response:

```json
{
  "status": "success",
  "filename": "example.pdf",
  "latency_seconds": 12.4,
  "tokens_used": 2048,
  "extracted_fields": {
    "Submission Deadline": "...",
    "RFP Contact": "...",
    "Scope of Deliverables / Services": "..."
  }
}
```

---

## Running the Backend

Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The application expects the local vLLM server to expose an OpenAI-compatible API on:

```text
http://localhost:8000/v1
```

Start the API from the `benchmark` directory:

```bash
cd benchmark
uvicorn model_endpoint:app --host 0.0.0.0 --port 8081
```

API documentation:

```text
http://localhost:8081/docs
```

Health check:

```text
http://localhost:8081/health
```

---

## Running the Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite development server normally runs on:

```text
http://localhost:5173
```

For a production build:

```bash
npm run build
```

---

## Running the Benchmark

The benchmark processes the RFP files located in:

```text
data/rfps/
```

and compares the model output against:

```text
data/ground_truth/
```

Run:

```bash
python3 benchmark/run_benchmark.py
```

Generated results are stored in:

```text
benchmark_outputs/
```

The benchmark records:

* Field accuracy
* Per-RFP accuracy
* Latency
* Input tokens
* Output tokens
* Total tokens
* Field-level failures

The field-level report is generated as:

```text
benchmark_outputs/field_accuracy_report.json
```

---

## Kubernetes Deployment

The project includes Kubernetes manifests for the model and web application.

### Create namespace

```bash
kubectl create namespace rfp-ai
```

### Deploy the model

```bash
kubectl apply -f lift-k8s.yaml
```

Verify:

```bash
kubectl get pods -n rfp-ai
kubectl get svc -n rfp-ai
```

The model service exposes port:

```text
8000
```

### Deploy the web application

```bash
kubectl apply -f rfp-web-k8s.yaml
```

Verify:

```bash
kubectl get pods -n rfp-ai
kubectl get svc -n rfp-ai
```

The web application uses:

```text
8081
```

The web deployment communicates with the model through the Kubernetes service:

```text
lift-serving.rfp-ai.svc.cluster.local:8000
```

---

## Docker Web Application

The web application can be packaged using:

```bash
docker build -f Dockerfile.web -t rfp-web:0.1 .
```

The container runs:

```text
FastAPI + React
```

on port:

```text
8081
```

The container expects:

```text
MODEL_BASE_URL
```

to point to the model's OpenAI-compatible `/v1` endpoint.

Example:

```bash
export MODEL_BASE_URL=http://localhost:8000/v1
```

---

## Monitoring

The project includes Prometheus and Grafana configuration under:

```text
monitoring/
```

Start monitoring services:

```bash
cd monitoring
docker compose up -d
```

Prometheus:

```text
http://localhost:9090
```

Grafana:

```text
http://localhost:3000
```

The Grafana dashboard monitors infrastructure and vLLM metrics such as:

* GPU utilization
* GPU memory
* GPU temperature
* CPU usage
* RAM usage
* Active requests
* Waiting requests
* Request completion
* Generated tokens
* Prompt tokens
* Token throughput
* Request completion rate
* Cache activity
* Preemptions

Dashboard configuration:

```text
monitoring/dashboard.json
```

Prometheus configuration:

```text
monitoring/prometheus.yml
```

---

## Environment Variables

Create a local `.env` file when environment-specific configuration is required.

Do not commit secrets to Git.

Example:

```env
MODEL_BASE_URL=http://localhost:8000/v1
```

The repository already ignores `.env` files through `.gitignore`.

---

## Development Notes

The project uses a locally hosted model rather than relying on an external model API for the primary extraction pipeline.

The model endpoint follows the OpenAI-compatible vLLM API format.

The frontend communicates with the FastAPI backend, while the backend handles:

1. PDF upload
2. PDF text extraction for security inspection
3. Prompt-injection detection
4. NeMo Guardrails validation
5. Vision-model inference
6. Structured JSON validation
7. Post-inference security checks
8. Response generation

---

## Current Architecture

```text
                    ┌─────────────────────┐
                    │     React / Vite    │
                    │     Frontend        │
                    └──────────┬──────────┘
                               │
                               │ HTTP
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │   RFP API :8081     │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
          ┌─────────────────┐   ┌──────────────────┐
          │ Security Layer  │   │ PDF Processing   │
          │ Regex + NeMo    │   │ PyMuPDF / pypdf  │
          └────────┬────────┘   └────────┬─────────┘
                   │                     │
                   └──────────┬──────────┘
                              ▼
                    ┌─────────────────────┐
                    │    Lift / vLLM      │
                    │      :8000           │
                    └──────────┬──────────┘
                               │
                               ▼
                       Structured JSON
```

---

## Team Project

**Project:** RFP AI

**Repository:** `team6-AI_Runners-RFP_AI`

The project was developed as part of an AI infrastructure / AI engineering project focusing on model serving, RFP document extraction, security, benchmarking, and observability.

---

## License

Add the appropriate project or organizational license here if required.
