#!/bin/bash

# AI Cooking Assistant - AWS Cleanup Script
set -e

echo "🗑️  AI Cooking Assistant - AWS Cleanup"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will DELETE all deployed resources!"
echo ""
read -p "Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

export AWS_REGION=${AWS_REGION:-ap-southeast-2}
echo ""
echo "📍 Region: $AWS_REGION"

# Get S3 bucket name
RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text 2>/dev/null || echo "")

# Empty S3 bucket
if [ -n "$RECIPES_BUCKET" ] && aws s3 ls "s3://$RECIPES_BUCKET" 2>/dev/null; then
    echo "🗑️  Emptying S3 bucket..."
    aws s3 rm s3://$RECIPES_BUCKET --recursive --quiet
    aws s3 rb s3://$RECIPES_BUCKET --force 2>/dev/null || true
fi

# Delete CloudFormation stack
echo "🗑️  Deleting CloudFormation stack..."
aws cloudformation delete-stack \
    --stack-name cooking-assistant \
    --region $AWS_REGION

echo "⏳ Waiting for deletion..."
aws cloudformation wait stack-delete-complete \
    --stack-name cooking-assistant \
    --region $AWS_REGION 2>/dev/null || true

echo ""
echo "✅ Cleanup Complete!"
echo ""
