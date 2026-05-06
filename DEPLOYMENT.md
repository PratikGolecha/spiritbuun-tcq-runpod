# Deployment Guide - 7 Steps to Live

## Step 1: All Files Created ✓
All 8 files have been created successfully!

## Step 2: Commit and Push to GitHub

```bash
cd ~/inference-worker/spiritbuun-tcq-runpod
git add .
git commit -m "Initial spiritbuun TCQ RunPod worker

- Dockerfile: Production-grade image
- runpod_handler.py: Serverless handler
- requirements.txt: Dependencies
- runpod.json: Hub metadata
- README.md: User documentation
- DEPLOYMENT.md: Deployment guide
- build.sh: Build automation"
git push origin main
```

## Step 3: Build & Push to Docker Hub

```bash
chmod +x build.sh
./build.sh pratikgolecha v1.0.0
```
Build takes 20-30 minutes first time.

## Step 4: Verify Docker Hub

Check: https://hub.docker.com/r/pratikgolecha/spiritbuun-tcq-llama

## Step 5: Create RunPod Endpoint

Go to: https://www.runpod.io/console/serverless
- Click: New Endpoint
- Image: docker.io/pratikgolecha/spiritbuun-tcq-llama:v1.0.0
- GPU: H100 or RTX 6000 Ada
- Mount model to: /models/

## Step 6: Test Endpoint

```bash
curl -X POST https://api.runpod.io/v1/ENDPOINT_ID/run \
  -H "Authorization: Bearer API_KEY" \
  -d '{"input": {"prompt": "Hello", "max_tokens": 100}}'
```

## Step 7: Submit to RunPod Hub

https://hub.runpod.io/ → Submit Template

---

**Total time: 1-2 hours to live!**
