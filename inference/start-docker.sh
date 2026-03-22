#!/bin/bash
# Start vLLM using Docker
# Usage: ./start-docker.sh [small]
#   Add "small" argument for 7B model instead of 14B

set -e

cd "$(dirname "$0")"

echo "=============================================="
echo "Starting vLLM via Docker"
echo "=============================================="

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found. Please install Docker."
    exit 1
fi

# Check for NVIDIA container toolkit
if ! docker info 2>/dev/null | grep -q "nvidia"; then
    echo "Warning: NVIDIA container toolkit may not be installed."
    echo "Install with: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
fi

if [ "$1" = "small" ]; then
    echo "Starting smaller model (7B)..."
    docker-compose --profile small up vllm-small
else
    echo "Starting default model (14B)..."
    docker-compose up vllm
fi
