#!/bin/bash

# AI Cooking Assistant - Complete AWS Deployment
set -e

echo "🍳 AI Cooking Assistant - AWS Deployment"
echo "=========================================="

# Check AWS CLI
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Run 'aws configure' first."
    exit 1
fi

# Set region
export AWS_REGION=${AWS_REGION:-ap-southeast-2}
echo "📍 Region: $AWS_REGION"

# Step 1: Deploy infrastructure
echo ""
echo "Step 1/5: Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file infrastructure/cloudformation.yaml \
    --stack-name cooking-assistant \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $AWS_REGION

# Step 2: Get outputs
echo ""
echo "Step 2/5: Getting stack outputs..."
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$RECIPES_BUCKET" ]; then
    echo "   ❌ Failed to get bucket name. Stack may have failed."
    echo "   Check CloudFormation console for errors."
    exit 1
fi

export API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

export LAMBDA_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunction`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$LAMBDA_FUNCTION" ]; then
    echo "   ❌ Failed to get Lambda function name."
    exit 1
fi

echo "   S3 Bucket: $RECIPES_BUCKET"
echo "   API Endpoint: $API_ENDPOINT"
echo "   Lambda Function: $LAMBDA_FUNCTION"

# Step 3: Package Lambda
echo ""
echo "Step 3/5: Packaging Lambda function..."
cd src
rm -rf package lambda.zip
mkdir -p package

# Install dependencies
pip install -q --index-url https://pypi.org/simple -r ../requirements.txt -t package/

# Copy source files
cp lambda_function.py package/
cp -r models package/
cp -r utils package/

# Create zip
cd package
zip -q -r ../lambda.zip .
cd ..
rm -rf package

echo "   ✓ Lambda package created ($(du -h lambda.zip | cut -f1))"

# Step 4: Deploy Lambda
echo ""
echo "Step 4/5: Deploying Lambda function..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION \
    --zip-file fileb://lambda.zip \
    --region $AWS_REGION > /dev/null

rm lambda.zip
cd ..

echo "   ✓ Lambda deployed"

# Step 5: Upload UI
echo ""
echo "Step 5/5: Uploading UI files..."
aws s3 cp src/frontend/templates/index.html s3://$RECIPES_BUCKET/ui/index.html --quiet
aws s3 sync src/frontend/js/ s3://$RECIPES_BUCKET/ui/frontend/js/ --quiet --delete

echo "   ✓ UI uploaded"

# Optional: Index recipes
if [ -d "data" ] && [ "$(ls -A data/*.txt 2>/dev/null)" ]; then
    echo ""
    echo "📚 Indexing recipes (optional)..."
    python scripts/index_recipes.py || echo "   ⚠️  Recipe indexing skipped"
fi

# Summary
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "🌐 Your app: $API_ENDPOINT"
echo ""
echo "📝 Next steps:"
echo "   1. Enable Bedrock models in AWS Console:"
echo "      - Claude 3 Haiku"
echo "      - Titan Embeddings V2"
echo "   2. Test the app at the URL above"
echo "   3. Monitor logs: aws logs tail /aws/lambda/$LAMBDA_FUNCTION --follow"
echo ""
echo "🔧 Update Lambda only: ./scripts/deploy_lambda.sh"
echo ""
