#!/bin/bash
set -e

DOCKER_USERNAME="${1:-YOUR_DOCKER_USERNAME}"
IMAGE_NAME="spiritbuun-tcq-llama"
VERSION="${2:-v1.0.0}"
PLATFORM="linux/amd64"

echo "Building spiritbuun TCQ for RunPod"
echo "Docker Hub: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"

if [ "$DOCKER_USERNAME" = "YOUR_DOCKER_USERNAME" ]; then
    echo "❌ Error: Please set DOCKER_USERNAME"
    echo "Usage: ./build.sh <docker_username> [version]"
    exit 1
fi

echo "📦 Building Docker image..."
docker buildx build \
    --platform ${PLATFORM} \
    -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} \
    -t ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
    --push \
    .

echo "✅ Build successful!"
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
