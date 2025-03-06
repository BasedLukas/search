# AWS Lambda Search API

This project implements an AWS Lambda function that serves as a REST API endpoint for search queries. The function forwards search requests to an external API, processes the results, and returns them to the client.

## Test Locally
Build the Docker image:
```bash
docker build -t search-api-lambda .
```

3. Test locally:
```bash
docker run -p 9000:8080 search-api-lambda
```

## API Usage

The API accepts GET requests with a query parameter `q` for the search query:

```
GET /?q=your+search+query
```

## Deployment to AWS Lambda

1. Create an ECR repository in AWS
2. Tag and push the Docker image:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 000000000000.dkr.ecr.us-east-1.amazonaws.com
export BRAVE_API_KEY=""
docker buildx create --use
docker buildx build --platform linux/amd64 --build-arg BRAVE_API_KEY=${BRAVE_API_KEY} -t getdelv .
docker tag getdelv:latest 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest
docker push 000000000000.dkr.ecr.us-east-1.amazonaws.com/getdelv:latest
```

3. Create a new Lambda function using the container image
4. Configure API Gateway to trigger the Lambda function
5. Set the required environment variables in the Lambda configuration

```bash
curl -X GET "https://example.invalid" \
  -H "x-api-key: [api key]"
```

## Error Handling

The API returns appropriate HTTP status codes:
- 200: Successful request
- 400: Missing or invalid search query
- 500: Server error or external API failure

## Logging

All requests and errors are logged using AWS CloudWatch Logs.