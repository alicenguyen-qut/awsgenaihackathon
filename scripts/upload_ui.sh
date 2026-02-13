#!/bin/bash
set -e

BUCKET=$1

if [ -z "$BUCKET" ]; then
    echo "Usage: ./upload_ui.sh <bucket-name>"
    exit 1
fi

echo "Uploading UI to S3..."
aws s3 cp ../src/templates/index.html s3://$BUCKET/ui/index.html
aws s3 cp ../src/frontend/js/auth.js s3://$BUCKET/ui/js/auth.js
aws s3 cp ../src/frontend/js/chat.js s3://$BUCKET/ui/js/chat.js
aws s3 cp ../src/frontend/js/messages.js s3://$BUCKET/ui/js/messages.js
aws s3 cp ../src/frontend/js/files.js s3://$BUCKET/ui/js/files.js
aws s3 cp ../src/frontend/js/ui.js s3://$BUCKET/ui/js/ui.js

echo "UI uploaded successfully!"
