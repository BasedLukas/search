#!/bin/bash
# deploy-lambda.sh - Robust script for building and deploying AWS Lambda container

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
ECR_REPO="000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv"
AWS_REGION="us-east-1"
IMAGE_TAG="latest"
BUILD_TAG="lambda-build"  # Temporary tag for local use

# Check if BRAVE_API_KEY is set
if [ -z "$BRAVE_API_KEY" ]; then
    echo "Error: BRAVE_API_KEY environment variable is not set"
    echo "Please set it with: export BRAVE_API_KEY=your-api-key-here"
    exit 1
fi

echo "=== Setting up Docker buildx ==="
# Remove existing builder if exists
docker buildx rm lambda-builder 2>/dev/null || true
# Create new builder
docker buildx create --name lambda-builder --use

echo "=== Logging into AWS ECR ==="
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO

echo "=== Building container for amd64 architecture ==="
docker buildx build \
  --platform=linux/amd64 \
  --build-arg BRAVE_API_KEY=$BRAVE_API_KEY \
  -t $BUILD_TAG \
  --load .

echo "=== Verifying image architecture ==="
ARCH=$(docker inspect $BUILD_TAG --format='{{.Architecture}}')
if [ "$ARCH" != "amd64" ]; then
    echo "Error: Built architecture is $ARCH, expected amd64"
    exit 1
fi
echo "Architecture verified: $ARCH"

echo "=== Tagging and pushing to ECR ==="
docker tag $BUILD_TAG $ECR_REPO:$IMAGE_TAG
docker push $ECR_REPO:$IMAGE_TAG

echo "=== Deployment complete ==="
echo "Image pushed to: $ECR_REPO:$IMAGE_TAG"
echo ""
echo "Next steps:"
echo "1. Go to AWS Lambda console and update the function to use the latest image"
echo "2. Test the API with:"
echo "   curl -X GET \"https://example.invalid" \\"
echo "     -H \"x-api-key: [your-api-key]\""
