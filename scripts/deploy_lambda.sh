#!/bin/bash

# Quick Lambda deployment for code updates
set -e

echo "🚀 Updating Lambda function..."

cd src
zip -r ../function.zip lambda_function.py
cd ..

aws lambda update-function-code \
    --function-name cooking-assistant-chatbot \
    --zip-file fileb://function.zip \
    --region ap-southeast-2

rm -f function.zip

echo "✅ Lambda function updated!"