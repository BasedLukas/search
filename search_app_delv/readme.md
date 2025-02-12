run from / 
`gunicorn --workers 1 --bind localhost:5000  --log-level=info --capture-output application:app`


prod, run from /
`deploy.sh`

key update for new ec2 instance
`ssh-keygen -f "/path/to/project" -R "127.0.0.1"`