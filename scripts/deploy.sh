#!/bin/bash
set -e

REGION="ap-southeast-2"
STACK_NAME="cooking-assistant"

echo "Deploying to AWS region: $REGION"

# Deploy CloudFormation
echo "1. Deploying CloudFormation stack..."
aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://infrastructure/cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "Waiting for stack creation..."
aws cloudformation wait stack-create-complete \
  --stack-name $STACK_NAME \
  --region $REGION

# Get bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
  --output text)

echo "2. Indexing recipes to S3..."
export RECIPES_BUCKET=$BUCKET
export AWS_REGION=$REGION
python scripts/index_recipes.py

echo "3. Uploading UI to S3..."
aws s3 cp src/templates/index.html s3://$BUCKET/ui/index.html

echo "4. Updating Lambda function..."
cd src
zip -r function.zip lambda_function.py
aws lambda update-function-code \
  --function-name ${STACK_NAME}-chatbot \
  --zip-file fileb://function.zip \
  --region $REGION
cd ..

# Get API endpoint
API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

echo ""
echo "✅ Deployment complete!"
echo "🌐 Visit: $API_ENDPOINT"
