#!/bin/bash

# AI Cooking Assistant - AWS Deployment Script
set -e

echo "🍳 Deploying AI Cooking Assistant to AWS..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

# Set region
export AWS_REGION=ap-southeast-2
echo "📍 Using region: $AWS_REGION"

# Deploy CloudFormation stack
echo "🏗️  Deploying infrastructure..."
aws cloudformation deploy \
    --template-file infrastructure/cloudformation.yaml \
    --stack-name cooking-assistant \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $AWS_REGION

# Get outputs
echo "📋 Getting stack outputs..."
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text)

export API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

echo "📦 S3 Bucket: $RECIPES_BUCKET"
echo "🌐 API Endpoint: $API_ENDPOINT"

# Upload UI files
echo "📤 Uploading UI to S3..."
aws s3 cp src/templates/index.html s3://$RECIPES_BUCKET/ui/index.html
aws s3 cp src/frontend/ s3://$RECIPES_BUCKET/ui/frontend/ --recursive

# Index recipes (if they exist)
if [ -d "data" ]; then
    echo "📚 Indexing recipes..."
    python scripts/index_recipes.py || echo "⚠️  Recipe indexing failed (optional)"
fi

# Package and deploy Lambda
echo "📦 Packaging Lambda function..."
cd src
zip -r ../function.zip lambda_function.py
cd ..

echo "🚀 Updating Lambda function..."
aws lambda update-function-code \
    --function-name cooking-assistant-chatbot \
    --zip-file fileb://function.zip \
    --region $AWS_REGION

# Clean up
rm -f function.zip

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your app is live at: $API_ENDPOINT"
echo ""
echo "📝 Features deployed:"
echo "   • User authentication & sessions"
echo "   • Profile photo upload"
echo "   • Daily nutrition tracking"
echo "   • Chat functionality"
echo "   • S3-based data storage"
echo ""
echo "🔧 To update just the Lambda code:"
echo "   ./scripts/deploy_lambda.sh"