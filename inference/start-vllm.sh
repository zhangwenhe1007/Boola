#!/bin/bash
# Start vLLM server for Boola
# Usage: ./start-vllm.sh [model_size]
#   model_size: "14b" (default) or "7b" for smaller model

set -e

MODEL_SIZE=${1:-14b}
PORT=${VLLM_PORT:-8001}

echo "=============================================="
echo "Starting vLLM for Boola"
echo "=============================================="

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "Error: nvidia-smi not found. NVIDIA GPU required."
    exit 1
fi

echo "GPU Info:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
echo ""

# Select model based on size
if [ "$MODEL_SIZE" = "7b" ]; then
    MODEL="Qwen/Qwen2.5-7B-Instruct-AWQ"
    echo "Using smaller model (7B) - requires ~6GB VRAM"
else
    MODEL="Qwen/Qwen2.5-14B-Instruct-AWQ"
    echo "Using default model (14B) - requires ~10GB VRAM"
fi

echo "Model: $MODEL"
echo "Port: $PORT"
echo ""

# Check if vllm is installed
if ! command -v vllm &> /dev/null; then
    echo "vLLM not found. Installing..."
    pip install vllm
fi

echo "Starting vLLM server..."
echo "This may take a few minutes on first run (downloading model)..."
echo ""

# Start vLLM with OpenAI-compatible API
vllm serve "$MODEL" \
    --quantization awq \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 \
    --dtype auto \
    --port "$PORT" \
    --host 0.0.0.0

