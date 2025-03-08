# AWS Lambda Search API
Hacked together API endpoint that runs on lambda and uses brave api and a few others to create an API endpoint for MCP servers to access.

## Test Locally
```bash
docker build  --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} -t search-api-lambda .
docker run -p 9000:8080 search-api-lambda
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"queryStringParameters": {"q": "what is python"}, "httpMethod": "GET", "path": "/"}'
```

## Deployment to AWS Lambda
# Login to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.us-east-1.amazonaws.com

# Set your API key
export BRAVE_API_KEY=""

# Setup buildx for cross-platform building
docker buildx rm mybuilder || true
docker buildx create --name mybuilder --use

# Build for AMD64 (AWS Lambda architecture) and load locally
docker buildx build --platform=linux/amd64 \
  --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} \
  -t getdelv:latest \
  --load .

# Verify architecture is correct
docker inspect getdelv:latest --format='{{.Architecture}}'

# Tag and push to ECR
docker tag getdelv:latest 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest
docker push 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest

# Go to AWS and update lambda to use the latest tag

# Test the deployed API
curl -X GET "https://example.invalid" \
  -H "x-api-key: [api key]"