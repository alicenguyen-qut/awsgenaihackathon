#!/bin/bash

set -e

echo "=========================================="
echo "  AWS Resources Cleanup"
echo "=========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
APP_RUNNER_STACK="cooking-assistant-stack"
EC2_STACK="cooking-assistant-ec2-stack"
REPO_NAME="cooking-assistant"

# Check which stacks exist
APP_RUNNER_EXISTS=$(aws cloudformation describe-stacks --stack-name $APP_RUNNER_STACK --region $REGION 2>/dev/null && echo "true" || echo "false")
EC2_EXISTS=$(aws cloudformation describe-stacks --stack-name $EC2_STACK --region $REGION 2>/dev/null && echo "true" || echo "false")

echo "Checking existing resources..."
echo "App Runner stack exists: $APP_RUNNER_EXISTS"
echo "EC2 stack exists: $EC2_EXISTS"
echo ""

if [ "$APP_RUNNER_EXISTS" = "false" ] && [ "$EC2_EXISTS" = "false" ]; then
    echo "No CloudFormation stacks found to delete."
    exit 0
fi

# Confirm deletion
read -p "⚠️  This will delete ALL AWS resources (CloudFormation stacks, S3 buckets, EC2 instances, ECR repository). Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cleanup cancelled."
  exit 0
fi

echo ""

# Delete App Runner stack if exists
if [ "$APP_RUNNER_EXISTS" = "true" ]; then
    echo "Deleting App Runner CloudFormation stack..."
    aws cloudformation delete-stack --stack-name $APP_RUNNER_STACK --region $REGION
    echo "Waiting for App Runner stack deletion..."
    aws cloudformation wait stack-delete-complete --stack-name $APP_RUNNER_STACK --region $REGION
    echo "✅ App Runner CloudFormation stack deleted"
    echo ""
fi

# Delete EC2 stack if exists
if [ "$EC2_EXISTS" = "true" ]; then
    echo "Deleting EC2 CloudFormation stack..."
    aws cloudformation delete-stack --stack-name $EC2_STACK --region $REGION
    echo "Waiting for EC2 stack deletion..."
    aws cloudformation wait stack-delete-complete --stack-name $EC2_STACK --region $REGION
    echo "✅ EC2 CloudFormation stack deleted"
    echo ""
fi

# Delete ECR repository
echo "Deleting ECR repository..."
aws ecr delete-repository \
  --repository-name $REPO_NAME \
  --region $REGION \
  --force 2>/dev/null && echo "✅ ECR repository deleted" || echo "⚠️  ECR repository not found"

# Clean up local files
echo ""
echo "Cleaning up local files..."
rm -f cooking-assistant-key.pem
rm -f ${REPO_NAME}-key.pem
echo "✅ Local key files cleaned up"

echo ""
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
echo "All AWS resources have been deleted."
echo ""
