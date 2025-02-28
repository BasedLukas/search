#!/bin/bash
# Upload index files to s3
DEPLOY_DIR="$(dirname "$0")/.."
S3_BUCKET="example-resource"

# Sync index.bin and url_mapping.json to S3
aws s3 cp "$DEPLOY_DIR/backend/index.bin" "$S3_BUCKET/index.bin" --acl bucket-owner-full-control
aws s3 cp "$DEPLOY_DIR/backend/url_mapping.json" "$S3_BUCKET/url_mapping.json" --acl bucket-owner-full-control
