## DEVELOPMENT 

### Local Development (Mac/Linux)
`gunicorn --workers 1 --bind localhost:5000  --log-level=info --capture-output application:app`

### Docker Development (Recommended for Mac)
```bash
# Build the Docker image
docker build -t search_app .

# Option 1: Run with mounted AWS credentials (recommended)
docker run -p 5001:5000 \
  -v ~/.aws:/root/.aws:ro \
  search_app

# Option 2: Run with AWS environment variables
docker run -p 5001:5000 \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  -e AWS_DEFAULT_REGION=your_region \
  search_app
```

You can then access the application at http://localhost:5001 in your web browser.

Note: Make sure you have valid AWS credentials in `~/.aws/credentials` if using Option 1, or set the correct environment variables if using Option 2.

## TO DEPLOY
* comment out dev in .env
run:
`upload.sh` to upload index files to s3
`deploy.sh` to deploy to ec2

##### key update for new ec2 instance
ssh-keygen -f "/path/to/project" -R "127.0.0.1"