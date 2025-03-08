# AWS Lambda Search API
Hacked together API endpoint that runs on lambda and uses brave api and a few others to create an API endpoint for MCP servers to access.

## Test Locally
```bash
docker build  --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} -t search-api-lambda .
docker run -p 9000:8080 search-api-lambda
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"queryStringParameters": {"q": "what is python"}, "httpMethod": "GET", "path": "/"}'
```

## Deployment to AWS Lambda

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.us-east-1.amazonaws.com
export BRAVE_API_KEY=""
docker buildx create --use
docker buildx build --platform linux/amd64 --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} -t getdelv --load .
docker tag getdelv:latest 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest
docker push 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest
# go to aws and update lambda to tag latest
curl -X GET "https://example.invalid" \
  -H "x-api-key: [api key]"
```
