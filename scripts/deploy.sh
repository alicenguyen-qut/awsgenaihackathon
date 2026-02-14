#!/bin/bash

set -e

echo "==========================================="
echo "  Personal Cooking Assistant - AWS Deployment"
echo "==========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
STACK_NAME="cooking-assistant-stack"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="cooking-assistant-data-${ACCOUNT_ID}"
APP_VERSION="v$(date +%s)"

echo "Region: $REGION"
echo "Stack: $STACK_NAME"
echo "S3 Bucket: $BUCKET_NAME"
echo ""

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    S3BucketName=$BUCKET_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo ""
echo "✅ CloudFormation deployment complete!"
echo ""

# Get outputs
echo "Getting deployment details..."
APP_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationName`].OutputValue' \
  --output text)

ENV_NAME=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`EnvironmentName`].OutputValue' \
  --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`S3Bucket`].OutputValue' \
  --output text)

# Index recipes to S3 (optional - skip if dependencies missing)
echo "Indexing recipes to S3..."
export AWS_REGION=$REGION
export RECIPES_BUCKET=$S3_BUCKET
export S3_BUCKET=$S3_BUCKET
if python3 scripts/index_recipes.py 2>/dev/null; then
  echo "✅ Recipes indexed to S3"
else
  echo "⚠️  Recipe indexing skipped (run manually later if needed)"
fi
echo ""

# Create application bundle
echo "Creating application bundle..."
zip -r app-${APP_VERSION}.zip . \
  -x "*.git*" "sessions/*" "uploads/*" "*.pyc" "__pycache__/*" "*.DS_Store" "app-*.zip" \
  > /dev/null
echo "✅ Application bundle created"
echo ""

# Upload to S3
echo "Uploading application to S3..."
S3_KEY="versions/app-${APP_VERSION}.zip"
aws s3 cp app-${APP_VERSION}.zip s3://${S3_BUCKET}/${S3_KEY} --region $REGION --no-progress
echo "✅ Application uploaded"
echo ""

# Create application version
echo "Creating Elastic Beanstalk application version..."
aws elasticbeanstalk create-application-version \
  --application-name $APP_NAME \
  --version-label $APP_VERSION \
  --source-bundle S3Bucket="${S3_BUCKET}",S3Key="${S3_KEY}" \
  --region $REGION \
  > /dev/null
echo "✅ Application version created"
echo ""

# Deploy to environment
echo "Deploying to Elastic Beanstalk environment..."
aws elasticbeanstalk update-environment \
  --application-name $APP_NAME \
  --environment-name $ENV_NAME \
  --version-label $APP_VERSION \
  --region $REGION \
  > /dev/null
echo "✅ Deployment initiated"
echo ""

# Wait for environment to be ready
echo "Waiting for environment to be ready (this may take 3-5 minutes)..."
aws elasticbeanstalk wait environment-updated \
  --application-name $APP_NAME \
  --environment-names $ENV_NAME \
  --region $REGION

# Get URL
URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`EnvironmentURL`].OutputValue' \
  --output text)

# Cleanup local zip
rm -f app-${APP_VERSION}.zip

echo ""
echo "==========================================="
echo "  Deployment Complete!"
echo "==========================================="
echo ""
echo "🎉 Your app is available at:"
echo "   http://$URL"
echo ""
echo "📊 Resources created:"
echo "   - CloudFormation stack: $STACK_NAME"
echo "   - Elastic Beanstalk app: $APP_NAME"
echo "   - Environment: $ENV_NAME"
echo "   - S3 bucket: $S3_BUCKET"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: aws elasticbeanstalk request-environment-info --environment-name $ENV_NAME --info-type tail --region $REGION"
echo "   Monitor: https://console.aws.amazon.com/elasticbeanstalk/home?region=$REGION#/environment/dashboard?applicationName=$APP_NAME&environmentId=$ENV_NAME"
echo ""
echo "💰 Estimated cost: ~\$8-12/month"
echo ""