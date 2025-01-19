#!/bin/bash

# Set variables for source directory, destination, and app service
SOURCE_DIR="./"
DESTINATION="search:/path/to/project"
SERVICE_NAME="app"
SERVICE_FILE="app.service"

# Use rsync to sync files, excluding unnecessary directories and files
rsync -avz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --include='data/' \
    --include='data/__init__.py' \
    --include='data/search.py' \
    --exclude='data/*' \
    $SOURCE_DIR $DESTINATION

# SSH into the server, navigate to the application directory, and restart the app service
ssh search << EOF
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    sudo cp nginx.conf /etc/nginx/sites-enabled/

    sudo systemctl enable nginx
    sudo systemctl restart nginx

    sudo cp $SERVICE_FILE /etc/systemd/system/$SERVICE_FILE
    sudo systemctl daemon-reload
    sudo systemctl start $SERVICE_NAME
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl restart $SERVICE_NAME
    
    sudo systemctl status nginx
    sudo systemctl status $SERVICE_NAME
    echo "Deployment completed."
EOF

