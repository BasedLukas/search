#!/bin/bash

set -e  # Exit on error

# Variables
REMOTE_USER="ubuntu"
REMOTE_HOST="127.0.0.1"  # Replace with your server's IP or hostname
REMOTE_DIR="/path/to/project"
DEPLOY_DIR="$(dirname "$0")/.."

# Rsync options
RSYNC_OPTS=(
  --archive
  --verbose
  --exclude="__pycache__"
  --exclude=".git"
  --exclude=".gitignore"
  --exclude="venv"
  --exclude="data"
  --exclude="deploy"
)

# Copy all necessary files
rsync "${RSYNC_OPTS[@]}" "$DEPLOY_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

# Install Python and dependencies
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
set -e
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv nginx

# Ensure the app directory exists
mkdir -p "$REMOTE_DIR"

# Set up Python virtual environment
if [ ! -d "$REMOTE_DIR/venv" ]; then
  python3 -m venv "$REMOTE_DIR/venv"
fi

# Install Python dependencies
"$REMOTE_DIR/venv/bin/pip" install --upgrade pip
if [ -f "$REMOTE_DIR/requirements.txt" ]; then
  "$REMOTE_DIR/venv/bin/pip" install -r "$REMOTE_DIR/requirements.txt"
fi
EOF

# Deploy systemd service
scp "$DEPLOY_DIR/deploy/app.service" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/app.service"
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
sudo mv "$REMOTE_DIR/app.service" /etc/systemd/system/app.service
sudo systemctl daemon-reload
sudo systemctl enable app
sudo systemctl restart app
EOF

# Deploy nginx configuration
scp "$DEPLOY_DIR/deploy/nginx.conf" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/nginx.conf"
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
sudo mv "$REMOTE_DIR/nginx.conf" /etc/nginx/sites-available/app
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app
sudo systemctl restart nginx
EOF


# Print success message
echo "Deployment complete! Access your app at https://example.invalid"
