#!/bin/bash

# Set your bucket name (either hardcoded or from Terraform output)
PROFILE="quantummed-www-editor"
BUCKET_NAME="openmedgate-com"
DISTRIBUTION_ID=""

# Check if SSO session is valid
if ! aws sts get-caller-identity --profile $PROFILE > /dev/null 2>&1; then
  echo "🔒 AWS SSO session expired or missing. Logging in..."
  aws sso login --profile $PROFILE
else
  echo "🔓 AWS SSO session active. Continuing..."
fi

# Build Hugo site first
echo "🔨 Building Hugo site..."
hugo --minify

# Sync Hugo output (public/) folder to S3 bucket root
aws s3 sync ./public s3://$BUCKET_NAME \
  --delete \
  --cache-control "max-age=3600" \
  --exclude ".DS_Store" \
  --profile $PROFILE

echo "✅ Website files uploaded to s3://$BUCKET_NAME"

aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --profile $PROFILE > /dev/null

echo "✅ CloudFront distribution (id: $DISTRIBUTION_ID) caches invalidated"