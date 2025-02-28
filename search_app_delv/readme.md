## DEVELOPMENT 
`gunicorn --workers 1 --bind localhost:5000  --log-level=info --capture-output application:app`

## TO DEPLOY
* comment out dev in .env
run:
`upload.sh` to upload index files to s3
`deploy.sh` to deploy to ec2

##### key update for new ec2 instance
ssh-keygen -f "/path/to/project" -R "127.0.0.1"