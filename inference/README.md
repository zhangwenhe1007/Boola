# Boola LLM Inference with vLLM

This directory contains configuration for running the LLM inference server using vLLM.

## Prerequisites

- NVIDIA GPU with CUDA support
- At least 10GB VRAM for 14B model (or 6GB for 7B model)
- CUDA 11.8+ installed
- Python 3.10+ or Docker

## Model Options

| Model | Size | VRAM Required | Quality |
|-------|------|---------------|---------|
| Qwen2.5-14B-Instruct-AWQ | 14B | ~10GB | Best (recommended) |
| Qwen2.5-7B-Instruct-AWQ | 7B | ~6GB | Good (for testing) |

## Quick Start

### Option 1: Native Installation (Recommended for RTX 4090)

```bash
# Install vLLM
pip install vllm

# Start server with 14B model
./start-vllm.sh

# Or start with smaller 7B model
./start-vllm.sh 7b
```

### Option 2: Docker

```bash
# Start with 14B model
./start-docker.sh

# Or start with 7B model
./start-docker.sh small
```

## Verify Server is Running

```bash
# Test the server
python test-vllm.py

# Or manually check
curl http://localhost:8001/v1/models
```

## Connect to Backend

Update your backend `.env` file:

```env
VLLM_BASE_URL=http://localhost:8001/v1
VLLM_MODEL=Qwen/Qwen2.5-14B-Instruct-AWQ
```

## API Usage

vLLM provides an OpenAI-compatible API:

```bash
# Chat completion
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-14B-Instruct-AWQ",
    "messages": [
      {"role": "user", "content": "What is Yale University?"}
    ],
    "max_tokens": 200
  }'
```

## Performance Tuning

### For RTX 4090 (24GB VRAM)

The default configuration is optimized for RTX 4090:

```bash
vllm serve Qwen/Qwen2.5-14B-Instruct-AWQ \
    --quantization awq \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9
```

### For GPUs with Less VRAM

Use the 7B model or reduce context length:

```bash
# 7B model
vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ \
    --quantization awq \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.9

# Or reduce context for 14B
vllm serve Qwen/Qwen2.5-14B-Instruct-AWQ \
    --quantization awq \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.95
```

## Troubleshooting

### CUDA Out of Memory

1. Use smaller model: `./start-vllm.sh 7b`
2. Reduce `--max-model-len` to 2048
3. Increase `--gpu-memory-utilization` to 0.95
4. Close other GPU applications

### Model Download Slow

Models are cached in `~/.cache/huggingface/`. First download may take time.

To pre-download:
```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-AWQ
```

### Server Not Responding

1. Check if model is still loading (can take 1-2 minutes)
2. Check GPU memory: `nvidia-smi`
3. Check server logs for errors

## Alternative Models

Other compatible models you can use:

```bash
# Llama 3.2 8B (good alternative)
vllm serve meta-llama/Llama-3.2-8B-Instruct --max-model-len 4096

# Mistral 7B
vllm serve mistralai/Mistral-7B-Instruct-v0.3 --max-model-len 4096

# DeepSeek (strong reasoning)
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-14B --max-model-len 4096
```

## Resources

- [vLLM Documentation](https://docs.vllm.ai/)
- [Qwen2.5 Models](https://huggingface.co/Qwen)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference) (compatible)
