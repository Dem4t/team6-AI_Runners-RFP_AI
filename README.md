# RFP AI — Model Benchmark

Capstone project for the SDA AI Data Center (AI Infrastructure) Bootcamp, in partnership with Beam Data.

## Overview

This project benchmarks large language models on their ability to extract structured information from Request for Proposal (RFP) documents. The goal is to determine which model(s) — open-weight or proprietary — perform best at this task, so Beam Data can advise clients on model selection for RFP processing, and to establish whether a custom/fine-tuned model is even necessary.

**This is not an RFP-writing project.** The RFP PDFs in this repo are sample *input* documents used to test extraction accuracy — not templates for drafting a new proposal.

## What this project does

1. Deploys one open-weight LLM in Docker, pushed to Kubernetes.
2. Gets API access to two additional models for comparison (three models total, minimum).
3. Runs all three models against five sample RFP documents, extracting a defined list of information fields from each.
4. Scores each model's extracted output against a ground-truth answer key.
5. Measures token usage and latency per model.
6. *(Time permitting)* Load-tests the deployed model.
7. Reports results in a written benchmark report.
8. Verifies the deployed model is live and interactive in AI Hub for the final demo.

Fine-tuning, RAG, and building a full application are explicit **stretch goals only** — not required for the minimum deliverable.

## Models compared

| Role | Model | Notes |
|---|---|---|
| Deployed (Docker → Kubernetes) | Qwen3-8B-Instruct (4-bit quantized) | Apache 2.0 license, 128K context, strong multilingual/Arabic support, fits the 16GB VRAM budget |
| API, no deployment required | OpenAI API — exact model **TBD** | Confirm the current model name/tier against OpenAI's live docs before finalizing; a "mini"-tier model is the fairer size-for-size comparison against an 8B open model |
| Comparison, second open-weight | Llama 3.1 8B Instruct *or* Ministral 8B — **TBD** | Doesn't have to be self-deployed; a hosted inference API is acceptable |

VRAM budget for the self-deployed model: **16GB** (roughly an 8B model at 4-bit quantization). If benchmarking shows a larger model (e.g. 14B) performs meaningfully better, that's worth flagging even if it isn't deployable within budget.

## Sample RFPs used for benchmarking

| # | Organization | Reference No. | Subject |
|---|---|---|---|
| 1 | Rocky View County | RFP 25-004 | ERP Requirements Analysis & Readiness Review |
| 2 | Olds College of Agriculture and Technology | RFP 197-2027 | LMS Platform & Support |
| 3 | City of Medicine Hat | CMH26-85 | Learning Management System (LMS) |
| 4 | Cowichan Tribes (per attached pricing/requirements filenames) | RFP.24.25.04 | Enterprise Resource Planning (ERP) System |
| 5 | University of Saskatchewan | CP-730126 | Generative Artificial Intelligence (AI) Software |

## Fields to extract

> ⚠️ **Not finalized.** The project guidance references "twenty fields" in one section but Appendix A lists only 17. Confirm the final list with Alex/Salman before running the benchmark.

1. Submission Deadline (date & time)
2. Deadline for Questions / Inquiries
3. RFP Contact (name and/or email)
4. Submission Method / Portal
5. Contract Term / Duration (including renewal options)
6. Scope of Deliverables / Services Requested
7. Mandatory Submission Requirements
8. Mandatory Technical Requirements
9. Evaluation Criteria & Weighting (points breakdown by category)
10. Minimum Score Threshold to Advance (where specified)
11. Pricing Structure / Cost Submission Requirements
12. Minimum Insurance Coverage Requirements (type and dollar amount)
13. Required Vendor Experience / Qualifications
14. Number of References Required
15. Data Security / Privacy Compliance Requirements
16. Data Hosting / Residency Requirements (where specified)
17. Vendor Demonstration Requirement

## Repository structure

> Proposed layout — adjust to match what's actually in the repo as it's built out.

```
.
├── data/
│   ├── rfps/                # the 5 sample RFP source PDFs
│   └── ground_truth/        # annotated answer key per RFP (TBD — see Open Questions)
├── deploy/
│   ├── Dockerfile           # serving image (e.g. vLLM + quantized weights)
│   └── k8s/                 # Deployment, Service manifests
├── extraction/
│   ├── prompts/             # extraction prompt / output schema used across all 3 models
│   └── run_extraction.py    # calls each model against each RFP, logs output + tokens + latency
├── scoring/
│   └── score_extraction.py  # compares model output to ground truth
├── report/
│   └── benchmark_report.md  # final write-up
└── README.md
```

## Setup

> Fill in with actual commands once the deployment is built.

**Prerequisites**
- Docker
- Access to a Kubernetes cluster with GPU node(s)
- `kubectl` configured against that cluster
- API key for the OpenAI-comparison model
- (If using a hosted API for the second open-weight model) API key for that provider

**Deploy the self-hosted model**
```bash
# 1. Build the serving image
docker build -t <registry>/rfp-ai-model:latest -f deploy/Dockerfile .

# 2. Push to registry
docker push <registry>/rfp-ai-model:latest

# 3. Deploy to Kubernetes
kubectl apply -f deploy/k8s/

# 4. Verify the endpoint is up
kubectl port-forward svc/<service-name> 8000:8000
curl http://localhost:8000/v1/models
```

**Run the benchmark**
```bash
python extraction/run_extraction.py --rfp-dir data/rfps --output results/
python scoring/score_extraction.py --results results/ --ground-truth data/ground_truth/
```

## Open questions / known gaps

- **Ground truth**: not yet available — needs to be provided by Beamdata or created through annotation before scoring can happen.
- **Field count discrepancy**: "twenty fields" (guidance text) vs. 17 fields (Appendix A) — needs confirmation.
- **Accuracy scoring method**: not specified in the project guidance (exact match? partial credit? rubric?) — needs a decision.
- **AI Hub integration**: how a Kubernetes-deployed model gets surfaced in AI Hub isn't documented — confirm with instructors.
- **GPU provisioning**: whether cluster GPU nodes are already available or need to be provisioned.

## License / Team

Add team members, license, and any Beamdata-specific attribution requirements here.