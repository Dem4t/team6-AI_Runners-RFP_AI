#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

MODEL_NAME="${MODEL_NAME:-$HOME/models/lift}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_DTYPE="${VLLM_DTYPE:-bfloat16}"
VLLM_GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.85}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-32768}"

if [[ ! -d "$MODEL_NAME" ]]; then
  echo "Model path does not exist: $MODEL_NAME"
  echo "Set MODEL_NAME in .env"
  exit 1
fi

if ! python -c "import vllm" >/dev/null 2>&1; then
  echo "vLLM is not installed."
  echo "Run: pip install -r requirements-vllm.txt"
  exit 1
fi

echo "Starting vLLM"
echo "Model: $MODEL_NAME"
echo "Port:  $VLLM_PORT"

exec python -m vllm serve "$MODEL_NAME" \
  --dtype "$VLLM_DTYPE" \
  --gpu-memory-utilization "$VLLM_GPU_MEMORY_UTILIZATION" \
  --max-model-len "$VLLM_MAX_MODEL_LEN" \
  --host "$VLLM_HOST" \
  --port "$VLLM_PORT"
