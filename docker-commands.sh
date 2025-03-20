#!/bin/bash

# Set your Docker registry and image name
REGISTRY="kkdevops001"
IMAGE_NAME="compress-ffmpeg"
TAG="latest"
FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"

# Build the Docker image
echo "Building Docker image..."
docker build -t $FULL_IMAGE_NAME .

# Push the image to registry
echo "Pushing image to registry..."
docker push $FULL_IMAGE_NAME

# Run the container
echo "Running container..."
docker run -d \
    -p 8000:8000 \
    -v "$(pwd)/uploads:/app/uploads" \
    -v "$(pwd)/output:/app/output" \
    --name video-compressor \
    kkdevops001/compress-ffmpeg:0.0.1
