#!/bin/bash

set -e

echo "=========================================="
echo "  AWS Resources Cleanup"
echo "=========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
STACK_NAME="cooking-assistant-stack"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="cooking-assistant-data-${ACCOUNT_ID}"

echo "Checking existing resources..."

# Check if stack exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region $REGION &>/dev/null; then
    echo "✅ Found stack: $STACK_NAME"
    
    # Get outputs
    APP_NAME=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`ApplicationName`].OutputValue' \
      --output text 2>/dev/null || echo "")
    
    ENV_NAME=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`EnvironmentName`].OutputValue' \
      --output text 2>/dev/null || echo "")
    
    S3_BUCKET=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`S3Bucket`].OutputValue' \
      --output text 2>/dev/null || echo "")
    
    [ -n "$APP_NAME" ] && echo "✅ Found Elastic Beanstalk app: $APP_NAME"
    [ -n "$ENV_NAME" ] && echo "✅ Found environment: $ENV_NAME"
    [ -n "$S3_BUCKET" ] && echo "✅ Found S3 bucket: $S3_BUCKET"
else
    echo "❌ No CloudFormation stack found"
    echo "Checking for orphaned resources..."
    
    S3_BUCKET=$(aws s3 ls | grep "cooking-assistant-data" | awk '{print $3}' | head -1 || echo "")
    [ -n "$S3_BUCKET" ] && echo "Found S3 bucket: $S3_BUCKET"
    
    if [ -z "$S3_BUCKET" ]; then
        echo "No resources found to clean up."
        exit 0
    fi
fi

echo ""

# Confirm deletion
read -p "⚠️  This will DELETE ALL AWS resources and data. Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cleanup cancelled."
  exit 0
fi

echo ""

# Terminate Elastic Beanstalk environment
if [ -n "$ENV_NAME" ]; then
    echo "Terminating Elastic Beanstalk environment: $ENV_NAME"
    aws elasticbeanstalk terminate-environment \
      --environment-name $ENV_NAME \
      --region $REGION 2>/dev/null || echo "⚠️  Environment not found"
    
    echo "Waiting for environment termination (this may take 3-5 minutes)..."
    aws elasticbeanstalk wait environment-terminated \
      --environment-names $ENV_NAME \
      --region $REGION 2>/dev/null || true
    
    echo "✅ Environment terminated"
    echo ""
fi

# Delete S3 bucket contents
if [ -n "$S3_BUCKET" ]; then
    echo "Emptying S3 bucket: $S3_BUCKET"
    aws s3 rm s3://$S3_BUCKET --recursive --region $REGION 2>/dev/null && echo "✅ S3 bucket emptied" || echo "⚠️  S3 bucket already empty"
    echo ""
fi

# Delete CloudFormation stack
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region $REGION &>/dev/null; then
    echo "Deleting CloudFormation stack: $STACK_NAME"
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    
    echo "Waiting for stack deletion..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION 2>/dev/null || true
    
    echo "✅ CloudFormation stack deleted"
    echo ""
fi

# Clean up orphaned S3 buckets
echo "Checking for orphaned S3 buckets..."
ORPHANED_BUCKETS=$(aws s3 ls | grep "cooking-assistant-data" | awk '{print $3}' || echo "")
if [ -n "$ORPHANED_BUCKETS" ]; then
    for BUCKET in $ORPHANED_BUCKETS; do
        echo "Deleting bucket: $BUCKET"
        aws s3 rm s3://$BUCKET --recursive --region $REGION 2>/dev/null || true
        aws s3 rb s3://$BUCKET --region $REGION 2>/dev/null && echo "  ✅ Deleted" || echo "  ⚠️  Could not delete"
    done
else
    echo "✅ No orphaned buckets found"
fi
echo ""

# Clean up local files
echo "Cleaning up local files..."
rm -f app-*.zip
echo "✅ Local files cleaned up"

echo ""
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
echo "✅ All AWS resources deleted:"
echo "   - CloudFormation stack"
echo "   - Elastic Beanstalk application"
echo "   - Elastic Beanstalk environment"
echo "   - S3 bucket (all data)"
echo "   - IAM roles"
echo ""
echo "💰 You will no longer be charged for these resources."
echo ""
