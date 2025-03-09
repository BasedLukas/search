# AWS Lambda Search API
Hacked together API endpoint that runs on lambda and uses brave api and a few others to create an API endpoint for MCP servers to access.

## Test Locally
```bash
docker build  --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} --build-arg GROQ_API_KEY=${GROQ_API_KEY} -t search-api-lambda .
docker run -p 9000:8080 search-api-lambda
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"queryStringParameters": {"q": "what is python"}, "httpMethod": "GET", "path": "/"}'
```

## Deployment to AWS Lambda
Set your API key, then build and deploy
```
./build_and_deploy_to_lambda.sh
```
Go to AWS and chose the latest tag as the lambda function

# Test the deployed API
export MY_API_KEY=""
curl -X GET "https://example.invalid" \
  -H "x-api-key: ${MY_API_KEY}"