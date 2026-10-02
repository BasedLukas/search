#!/bin/bash

set -e  # Exit on error

# Variables
REMOTE_USER="${DELV_REMOTE_USER:?Set DELV_REMOTE_USER}"
REMOTE_HOST="${DELV_REMOTE_HOST:?Set DELV_REMOTE_HOST}"
REMOTE_DIR="${DELV_REMOTE_DIR:?Set DELV_REMOTE_DIR and adapt app.service to match}"
DEPLOY_DIR="$(dirname "$0")/.."

# Rsync options
RSYNC_OPTS=(
  --archive
  --verbose
  --exclude="__pycache__"
  --exclude=".git"
  --exclude=".gitignore"
  --exclude="venv"
  --exclude=".venv"
  --exclude=".env*"
  --exclude="data"
  --exclude="deploy"
  --exclude="backend/*.bin"
  --exclude="backend/*.json"
  --exclude="elastic-start-local"
)

echo "Starting rsync"
# Copy all necessary files
rsync "${RSYNC_OPTS[@]}" "$DEPLOY_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"


# Install system dependencies and uv
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
set -e
export PATH=\$HOME/.local/bin:\$PATH
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip nginx

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure the app directory exists
mkdir -p "$REMOTE_DIR"

# Set up Python environment using uv
if [ ! -d "$REMOTE_DIR/.venv" ]; then
  uv venv "$REMOTE_DIR/.venv"
fi

# Install Python dependencies using uv
uv pip install --python "$REMOTE_DIR/.venv/bin/python" "$REMOTE_DIR"
EOF

# Deploy systemd service
scp "$DEPLOY_DIR/deploy/app.service" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/app.service"
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
sudo mv "$REMOTE_DIR/app.service" /etc/systemd/system/app.service
sudo systemctl daemon-reload
sudo systemctl enable app
sudo systemctl restart app
EOF

# Deploy Nginx configuration
scp "$DEPLOY_DIR/deploy/nginx.conf" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/nginx.conf"
ssh "$REMOTE_USER@$REMOTE_HOST" <<EOF
sudo rm -f /etc/nginx/sites-enabled/default
sudo mv "$REMOTE_DIR/nginx.conf" /etc/nginx/sites-available/app
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app

# Ensure proper permissions and restart Nginx
sudo nginx -t && sudo systemctl reload nginx
EOF

# Print success message
echo "Deployment complete! Access your app at http://$REMOTE_HOST"
echo "view logs: journalctl -u app -f"
