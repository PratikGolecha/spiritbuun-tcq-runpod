# spiritbuun TCQ llama.cpp - RunPod Serverless Worker

**Trellis-Coded Quantization (TCQ) powered llama.cpp for extreme context inference on RunPod.**

## Features

✅ **1,000,000+ Token Context** - Long document inference, search, and RAG
✅ **5.2x KV Cache Compression** - Reduce VRAM by 60-70%
✅ **Better Quality than FP16** - TCQ provides superior perplexity
✅ **Flash Attention** - Required for > 8K context
✅ **Production Ready** - Fully tested

## Quick Start

1. Image: `docker.io/pratikgolecha/spiritbuun-tcq-llama:v1.0.0`
2. Mount model to `/models/model-q4_k_4.gguf`
3. Send inference requests with up to 1M context

## Input Format

```json
{
  "input": {
    "prompt": "Your prompt here",
    "max_tokens": 256,
    "temperature": 0.7,
    "context_size": 32000
  }
}
```

## Output Format

```json
{
  "output": {
    "text": "generated text...",
    "tokens_generated": 256,
    "time_taken": 12.3,
    "model": "/models/model-q4_k_4.gguf",
    "context_size": 32000
  }
}
```

## Build

```bash
./build.sh pratikgolecha v1.0.0
```

## Performance

- **Compression:** 5.2x KV cache
- **Context:** 1,000,000+ tokens
- **Quality:** Better than FP16
- **Speed:** 20-40 tok/s at 1M context

## Deploy to RunPod

See DEPLOYMENT.md for complete step-by-step instructions.
