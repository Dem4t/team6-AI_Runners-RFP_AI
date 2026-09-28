# RFP AI — Intelligent RFP Extraction System

AI-powered system for extracting structured information from Request for Proposal (RFP) PDF documents using a locally hosted vision model, FastAPI, React, vLLM, and NVIDIA NeMo Guardrails.

The project is designed to run **locally** without depending on the team's development server or external AI APIs.

`team6-AI_Runners-RFP_AI`

The project was developed as part of an AI infrastructure / AI engineering project focusing on model serving, RFP document extraction, security, benchmarking, and observability.

### Team Members

- Abdullah-Alqahtani
  https://github.com/Abdullah-Alqhtani
- AmrAlghamidi
  https://github.com/AmrAlghamidi
- Turki Alotaibi
  https://github.com/turki-alotaibi9
---

## Overview

RFP AI provides an end-to-end pipeline for uploading an RFP PDF, validating it against security controls, extracting structured information, and displaying the results through a web interface.

```text
RFP PDF
   ↓
React / Vite
   ↓
FastAPI
   ↓
PDF Security Checks
   ↓
NeMo Guardrails
   ↓
Local vLLM Model
   ↓
Structured JSON
   ↓
Post-Inference Security Validation
   ↓
Web Interface
```

---

## Key Features

* PDF upload and processing
* Structured RFP information extraction
* Local vision-model inference
* OpenAI-compatible vLLM API
* NVIDIA NeMo Guardrails
* Prompt-injection detection
* Pre-inference security validation
* Post-inference security validation
* JSON output
* Benchmark evaluation
* Field-level accuracy reporting
* Kubernetes deployment manifests
* Prometheus and Grafana monitoring
* React/Vite frontend

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

* vLLM
* Lift Vision Model
* OpenAI-compatible API

### Frontend

* React
* Vite
* JavaScript

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
│   └── rfps/
│
├── frontend/
│   ├── public/
│   ├── src/
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

## Extracted RFP Fields

The current schema contains 17 fields:

1. Submission Deadline
2. Deadline for Questions
3. RFP Contact
4. Submission Method
5. Contract Term
6. Scope of Deliverables
7. Mandatory Submission Requirements
8. Mandatory Technical Requirements
9. Evaluation Criteria
10. Minimum Score Threshold
11. Pricing Requirements
12. Minimum Insurance Requirements
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

# Local Development

## Requirements

Install the following before running the project:

* Python 3.10+
* Node.js 20+
* npm
* Git
* vLLM
* A compatible local vision model
* NVIDIA GPU recommended for local model inference

The project does **not** require an external AI API.

---

## 1. Clone the Repository

```bash
git clone https://github.com/Dem4t/team6-AI_Runners-RFP_AI.git
cd team6-AI_Runners-RFP_AI
```

---

## 2. Start the Local Model

The backend expects an OpenAI-compatible vLLM endpoint at:

```text
http://localhost:8000/v1
```

Example:

```bash
vllm serve /path/to/your/model \
  --host 0.0.0.0 \
  --port 8000
```

Verify that vLLM is running:

```bash
curl http://localhost:8000/v1/models
```

Make sure the model is compatible with the project's PDF-to-image extraction workflow.

---

## 3. Configure the Model

The backend supports environment variables so different machines do not need source-code changes.

Default values:

```bash
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/ubuntu/models/lift
```

Example for a different local model:

```bash
export MODEL_BASE_URL=http://localhost:8000/v1
export MODEL_NAME=my-local-model
```

The model name must match the model name exposed by vLLM.

---

# 4. Start the Backend

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
cd benchmark
uvicorn model_endpoint:app --host 0.0.0.0 --port 8081
```

The backend will be available at:

```text
http://localhost:8081
```

Swagger API documentation:

```text
http://localhost:8081/docs
```

Health check:

```text
http://localhost:8081/health
```

---

# 5. Start the Frontend

Open another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

The Vite development server proxies API requests to:

```text
http://localhost:8081
```

Therefore, the frontend does not need a hard-coded backend IP address.

---

# Local Ports

| Component       | Local Address              |
| --------------- | -------------------------- |
| Frontend        | `http://localhost:5173`    |
| FastAPI Backend | `http://localhost:8081`    |
| vLLM            | `http://localhost:8000/v1` |
| Prometheus      | `http://localhost:9090`    |
| Grafana         | `http://localhost:3000`    |

---

# API

## Health Check

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

## Extract RFP

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
    "submission_deadline": "...",
    "rfp_contact": "...",
    "scope_of_deliverables": "..."
  }
}
```

---

# Security

The extraction pipeline contains multiple security layers.

## 1. Deterministic Prompt-Injection Detection

The API checks PDF text against known malicious instruction patterns before model inference.

Examples include attempts to:

* Ignore previous instructions
* Disregard the extraction schema
* Bypass security controls
* Reveal system prompts
* Execute unrelated code

## 2. NVIDIA NeMo Guardrails

The project uses:

```text
guardrails_config/config.yml
guardrails_config/rails.co
```

to perform semantic security validation.

## 3. Post-Inference Validation

Extracted fields are checked again before the response is returned to the frontend.

If a security violation is detected, the response is blocked.

---

# Benchmark

Benchmark inputs are stored in:

```text
data/rfps/
```

Expected outputs are stored in:

```text
data/ground_truth/
```

Run the benchmark:

```bash
python3 benchmark/run_benchmark.py
```

Results are written to:

```text
benchmark_outputs/
```

Field-level accuracy is reported in:

```text
benchmark_outputs/field_accuracy_report.json
```

---

# Monitoring

Monitoring is optional for local development.

Start Prometheus and Grafana:

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

The monitoring stack can collect information related to:

* GPU utilization
* GPU memory
* GPU temperature
* GPU power usage
* CPU utilization
* RAM usage
* Network traffic
* vLLM request activity
* Token usage
* Request completion
* Model serving telemetry

The dashboard is located at:

```text
monitoring/dashboard.json
```

---

# Docker

The repository also contains:

```text
Dockerfile.web
```

for packaging the frontend and FastAPI application.

The container expects a running model endpoint through:

```bash
MODEL_BASE_URL=http://localhost:8000/v1
```

For containerized deployments, make sure the application container can reach the machine or container hosting vLLM.

---

# Kubernetes

Kubernetes manifests are provided for environments that already have a Kubernetes cluster and NVIDIA GPU support.

Files:

```text
lift-k8s.yaml
rfp-web-k8s.yaml
```

These deployment files are separate from the normal local-development workflow.

---

# Configuration

The main backend environment variables are:

```bash
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/ubuntu/models/lift
```

Example:

```bash
export MODEL_BASE_URL=http://localhost:8000/v1
export MODEL_NAME=my-local-model
```

Do not commit private credentials, API keys, or environment-specific secrets.

---

# Local Development Notes

The repository is intentionally configured so that the default development environment uses:

```text
localhost
```

No team-server IP address is required for normal local development.

The project architecture is:

```text
React / Vite
      ↓
FastAPI
      ↓
Security Validation
      ↓
PDF Processing
      ↓
Local vLLM
      ↓
Lift Vision Model
      ↓
Structured JSON
```

---

# Troubleshooting

## Backend cannot connect to the model

Check that vLLM is running:

```bash
curl http://localhost:8000/v1/models
```

Then check the backend configuration:

```bash
echo $MODEL_BASE_URL
echo $MODEL_NAME
```

## Frontend cannot connect to the backend

Check:

```bash
curl http://localhost:8081/health
```

Then start the frontend again:

```bash
cd frontend
npm run dev
```

## Guardrails fail to initialize

Make sure the configuration exists:

```text
guardrails_config/config.yml
guardrails_config/rails.co
```

and that all Python dependencies have been installed:

```bash
pip install -r requirements.txt
```

---

# Project

**RFP AI — AI Runners**

Repository:

```text
team6-AI_Runners-RFP_AI
```

The project focuses on:

* AI-assisted RFP extraction
* Local model serving
* AI security
* Prompt-injection protection
* Benchmarking
* Observability
* Infrastructure deployment
## Team Project

**Project:** RFP AI

**Repository:**
