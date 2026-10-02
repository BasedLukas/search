#!/bin/bash
# deploy-lambda.sh - Robust script for building and deploying AWS Lambda container

set -e  # Exit immediately if a command exits with a non-zero status

# Deployment targets are supplied by the operator. API keys belong in Lambda
# runtime configuration, not container build arguments.
: "${ECR_REPO:?Set ECR_REPO to your own ECR repository URI}"
AWS_REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BUILD_TAG="lambda-build"  # Temporary tag for local use



echo "=== Setting up Docker buildx ==="
# Remove existing builder if exists
docker buildx rm lambda-builder 2>/dev/null || true
# Create new builder
docker buildx create --name lambda-builder --use

echo "=== Logging into AWS ECR ==="
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ECR_REPO%%/*}"

echo "=== Building container for amd64 architecture ==="
docker buildx build \
  --platform=linux/amd64 \
  -t "$BUILD_TAG" \
  --load .

echo "=== Verifying image architecture ==="
ARCH=$(docker inspect "$BUILD_TAG" --format='{{.Architecture}}')
if [ "$ARCH" != "amd64" ]; then
    echo "Error: Built architecture is $ARCH, expected amd64"
    exit 1
fi
echo "Architecture verified: $ARCH"

echo "=== Tagging and pushing to ECR ==="
docker tag "$BUILD_TAG" "$ECR_REPO:$IMAGE_TAG"
docker push "$ECR_REPO:$IMAGE_TAG"

echo "=== Deployment complete ==="
echo "Image pushed to: $ECR_REPO:$IMAGE_TAG"
echo ""
echo "Next steps:"
echo "1. Go to AWS Lambda console and update the function to use the latest image"
echo "2. Configure BRAVE_API_KEY and GROQ_API_KEY in the Lambda runtime."
echo "3. Use test/test_api.py with your own DELV_API_ENDPOINT and MY_API_KEY."
