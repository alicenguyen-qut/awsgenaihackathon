#!/bin/bash

# Quick Lambda Update Script
set -e

echo "🚀 Updating Lambda function..."

# Get Lambda function name
export AWS_REGION=${AWS_REGION:-ap-southeast-2}
export LAMBDA_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunction`].OutputValue' \
    --output text 2>/dev/null || echo "cooking-assistant-chatbot")

# Package
cd src
rm -rf package lambda.zip
mkdir -p package

echo "📦 Installing dependencies..."
pip install -q --index-url https://pypi.org/simple -r ../requirements.txt -t package/

echo "📁 Copying source files..."
cp lambda_function.py package/
cp -r models package/
cp -r utils package/

# Remove conflicting files
find package -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find package -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find package -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "🗜️  Creating zip..."
cd package
zip -q -r ../lambda.zip .
cd ..

echo "☁️  Uploading to AWS..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION \
    --zip-file fileb://lambda.zip \
    --region $AWS_REGION > /dev/null

rm -rf package lambda.zip
cd ..

echo "✅ Lambda updated successfully!"
