# RFP AI — Intelligent RFP Extraction System

AI-powered system for extracting structured information from Request for Proposal (RFP) PDF documents using a locally hosted vision model, FastAPI, React, vLLM, and NVIDIA NeMo Guardrails.

The project is designed to run locally without depending on the team's development server or external AI APIs.

---

## Team Members

* **Abdullah Alqahtani** — https://github.com/Abdullah-Alqhtani
* **Amr Alghamidi** — https://github.com/AmrAlghamidi
* **Turki Alotaibi** — https://github.com/turki-alotaibi9

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
* Structured JSON output
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

* vLLM 0.29.0
* Lift Vision Model
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
├── scripts/
│   └── start_vllm.sh
│
├── Dockerfile.web
├── lift-k8s.yaml
├── rfp-web-k8s.yaml
├── requirements.txt
├── requirements-vllm.txt
├── .env.example
├── web_container.py
└── README.md
```

---

# RFP Extraction Schema

The current extraction schema contains 17 fields:

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

For the full local extraction workflow, install:

* Linux recommended for local GPU inference
* Python 3.10+
* Node.js 20+
* npm
* Git
* NVIDIA GPU
* Working NVIDIA drivers
* A compatible local vision model

The repository does **not** include model weights.

The frontend and backend can be started without a running model, but actual RFP extraction requires a working vLLM server and a compatible model.

---

## 1. Clone the Repository

```bash
git clone https://github.com/Dem4t/team6-AI_Runners-RFP_AI.git
cd team6-AI_Runners-RFP_AI
```

---

## 2. Create the Python Environment

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Install vLLM separately:

```bash
pip install -r requirements-vllm.txt
```

Verify the installation:

```bash
python -m vllm --version
```

The repository uses vLLM `0.29.0` for the local model-serving setup.

---

# 3. Configure the Model

Copy the environment template:

```bash
cp .env.example .env
```

The `.env` file contains the model configuration.

Example:

```env
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/ubuntu/models/lift
```

### MODEL_BASE_URL

The backend expects an OpenAI-compatible vLLM endpoint.

Default:

```text
http://localhost:8000/v1
```

### MODEL_NAME

This must match the model path/name that vLLM serves.

Example:

```env
MODEL_NAME=/home/ubuntu/models/lift
```

On another machine, replace it with the actual local model path:

```env
MODEL_NAME=/path/to/your/model
```

Do not commit `.env`.

---

# 4. Start vLLM

The repository provides a startup script:

```bash
bash scripts/start_vllm.sh
```

The script starts vLLM using:

```bash
python -m vllm serve
```

This avoids depending on a globally installed `vllm` executable.

The default configuration is:

```text
Host: 0.0.0.0
Port: 8000
Dtype: bfloat16
GPU Memory Utilization: 0.85
Maximum Model Length: 32768
```

The script reads the model configuration from `.env`.

Verify that the server is running:

```bash
curl http://localhost:8000/v1/models
```

A successful response should contain the models exposed by the vLLM server.

---

# 5. Start the Backend

Open a second terminal.

Navigate to the project:

```bash
cd team6-AI_Runners-RFP_AI
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start FastAPI:

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

# 6. Start the Frontend

Open a third terminal.

Navigate to the frontend:

```bash
cd team6-AI_Runners-RFP_AI/frontend
```

Install frontend dependencies:

```bash
npm ci
```

Start Vite:

```bash
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

This means the frontend does not contain a hard-coded team-server IP.

---

# Local Ports

| Component       | Address                    |
| --------------- | -------------------------- |
| Frontend        | `http://localhost:5173`    |
| FastAPI Backend | `http://localhost:8081`    |
| vLLM            | `http://localhost:8000/v1` |
| Prometheus      | `http://localhost:9090`    |
| Grafana         | `http://localhost:3000`    |

---

# Running the Full Application

Once all services are running:

```text
Browser
   │
   ▼
http://localhost:5173
   │
   │ /api
   ▼
http://localhost:8081
   │
   │ OpenAI-compatible API
   ▼
http://localhost:8000/v1
   │
   ▼
Local Vision Model
```

The user only needs to open:

```text
http://localhost:5173
```

and upload an RFP PDF.

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

---

## Extract RFP

```http
POST /api/v1/extract
```

Upload a PDF using the multipart form field:

```text
file
```

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

The extraction pipeline uses multiple security layers.

## 1. PDF Security Inspection

The uploaded PDF is inspected before model inference.

The system extracts text from the PDF for security analysis.

---

## 2. Deterministic Prompt-Injection Detection

The API checks the document against known malicious instruction patterns.

Examples include:

* Ignore previous instructions
* Disregard the schema
* Bypass security
* Print the system prompt
* Write a Python script

When a detected pattern matches, the request is blocked.

---

## 3. NVIDIA NeMo Guardrails

The project uses NVIDIA NeMo Guardrails for semantic security validation.

Configuration:

```text
guardrails_config/config.yml
guardrails_config/rails.co
```

Guardrails are applied before model inference.

---

## 4. Post-Inference Validation

The generated extraction is checked again before being returned to the frontend.

If a security violation is detected, the API blocks the response.

---

# Benchmark

Benchmark RFP documents are stored in:

```text
data/rfps/
```

Ground-truth results are stored in:

```text
data/ground_truth/
```

Run the benchmark:

```bash
python3 benchmark/run_benchmark.py
```

Results are generated in:

```text
benchmark_outputs/
```

The field-level report is:

```text
benchmark_outputs/field_accuracy_report.json
```

Benchmark results can include:

* Field accuracy
* Per-RFP accuracy
* Latency
* Input tokens
* Output tokens
* Total tokens
* Field-level failures

---

# Monitoring

Monitoring is optional for local development.

The project includes:

* Prometheus
* Grafana
* Node Exporter metrics
* NVIDIA DCGM metrics
* vLLM metrics

Start the monitoring stack:

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

---

## Monitoring Dashboard

The Grafana dashboard is stored in:

```text
monitoring/dashboard.json
```

The monitoring stack can display metrics such as:

* GPU utilization
* GPU memory
* GPU temperature
* GPU power usage
* CPU utilization
* RAM usage
* Network traffic
* vLLM request activity
* Waiting requests
* Completed requests
* Generated tokens
* Prompt tokens
* Token throughput
* Cache activity
* Preemptions

---

# Docker

The repository contains a Docker build for the web application:

```text
Dockerfile.web
```

Build the image:

```bash
docker build -f Dockerfile.web -t rfp-web:0.1 .
```

The application container exposes:

```text
8081
```

The model endpoint is configured through:

```text
MODEL_BASE_URL
```

Example:

```bash
MODEL_BASE_URL=http://localhost:8000/v1
```

When running inside Docker, make sure the container can reach the machine or container hosting vLLM.

---

# Kubernetes

The repository includes Kubernetes manifests for environments with:

* Kubernetes
* NVIDIA GPU support
* A local model available to the cluster

Files:

```text
lift-k8s.yaml
rfp-web-k8s.yaml
```

These manifests are **not required** for normal local development.

The Kubernetes deployment uses the vLLM service internally rather than the local development ports described above.

---

# Environment Variables

The main environment variables are:

```env
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/home/ubuntu/models/lift
```

Machine-specific configuration should be placed in `.env`.

Example for another machine:

```env
MODEL_BASE_URL=http://localhost:8000/v1
MODEL_NAME=/path/to/your/model
```

Do not commit:

* API keys
* passwords
* private endpoints
* `.env` files
* model weights

---

# Troubleshooting

## `vllm: command not found`

Make sure the virtual environment is active:

```bash
source .venv/bin/activate
```

Install the project vLLM dependency:

```bash
pip install -r requirements-vllm.txt
```

Verify:

```bash
python -m vllm --version
```

Then start:

```bash
bash scripts/start_vllm.sh
```

---

## vLLM Cannot Find the Model

Check the configured model path:

```bash
echo $MODEL_NAME
```

Check that the path exists:

```bash
ls -ld "$MODEL_NAME"
```

Or set it manually:

```bash
export MODEL_NAME=/path/to/your/model
```

Then:

```bash
bash scripts/start_vllm.sh
```

---

## vLLM Is Not Responding

Check:

```bash
curl http://localhost:8000/v1/models
```

Also check whether port `8000` is listening:

```bash
ss -lntp | grep 8000
```

---

## Backend Cannot Connect to vLLM

First verify vLLM:

```bash
curl http://localhost:8000/v1/models
```

Then verify the backend:

```bash
curl http://localhost:8081/health
```

Check the configured endpoint:

```bash
echo $MODEL_BASE_URL
```

It should normally be:

```text
http://localhost:8000/v1
```

---

## Frontend Cannot Connect to Backend

Check the backend:

```bash
curl http://localhost:8081/health
```

If it is working, restart Vite:

```bash
cd frontend
npm run dev
```

Then open:

```text
http://localhost:5173
```

---

## NeMo Guardrails Fails to Initialize

Make sure these files exist:

```text
guardrails_config/config.yml
guardrails_config/rails.co
```

Then verify the Python environment:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

# Development Architecture

```text
                    ┌──────────────────────┐
                    │     React / Vite     │
                    │    Frontend :5173    │
                    └──────────┬───────────┘
                               │
                               │ /api
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │     Backend :8081    │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
      ┌─────────────────┐          ┌─────────────────┐
      │ Security Layer  │          │ PDF Processing  │
      │ Regex + NeMo    │          │ PyMuPDF / pypdf │
      └────────┬────────┘          └────────┬────────┘
               │                            │
               └──────────────┬─────────────┘
                              ▼
                    ┌──────────────────────┐
                    │        vLLM          │
                    │      :8000/v1        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Lift Vision Model  │
                    └──────────┬───────────┘
                               │
                               ▼
                        Structured JSON
```

---

# Local-First Configuration

The repository is intentionally configured for local development.

Default services:

```text
Frontend
localhost:5173

Backend
localhost:8081

vLLM
localhost:8000

Prometheus
localhost:9090

Grafana
localhost:3000
```

No team-server IP address is required for normal local development.

---

# Model Weights

Model weights are intentionally **not included in the Git repository** because they are large and environment-specific.

Each developer must provide a compatible local model.

The model path is configured using:

```env
MODEL_NAME=/path/to/your/model
```

---

# Important Note About vLLM

vLLM is intentionally maintained as a separate dependency from the main backend requirements.

Backend dependencies:

```text
requirements.txt
```

Model-serving dependency:

```text
requirements-vllm.txt
```

This keeps the API environment separate from the GPU/model-serving environment while still providing a reproducible local setup.

---

# Quick Start

For a complete local setup:

### Terminal 1 — vLLM

```bash
cd team6-AI_Runners-RFP_AI

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-vllm.txt

cp .env.example .env
```

Set the correct model path in `.env`, then:

```bash
bash scripts/start_vllm.sh
```

---

### Terminal 2 — Backend

```bash
cd team6-AI_Runners-RFP_AI

source .venv/bin/activate

cd benchmark
uvicorn model_endpoint:app --host 0.0.0.0 --port 8081
```

---

### Terminal 3 — Frontend

```bash
cd team6-AI_Runners-RFP_AI/frontend

npm ci
npm run dev
```

Open:

```text
http://localhost:5173
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
* Prompt-injection protection
* AI security
* Benchmarking
* Observability
* Infrastructure deployment
* Local-first development
