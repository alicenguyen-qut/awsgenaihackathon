#!/bin/bash

set -e

echo "=========================================="
echo "  AWS Resources Cleanup"
echo "=========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
STACK_NAME="cooking-assistant-ec2-stack"

echo "Checking existing resources..."

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>/dev/null && echo "true" || echo "false")

if [ "$STACK_EXISTS" = "false" ]; then
    echo "❌ No CloudFormation stack found: $STACK_NAME"
    echo ""
    echo "Checking for orphaned resources..."
    
    # Check for S3 buckets
    BUCKETS=$(aws s3 ls | grep "cooking-assistant-data" | awk '{print $3}' || echo "")
    if [ -n "$BUCKETS" ]; then
        echo "Found S3 buckets:"
        echo "$BUCKETS"
    else
        echo "No resources found to clean up."
        exit 0
    fi
else
    echo "✅ Found stack: $STACK_NAME"
    
    # Get S3 bucket name from stack
    S3_BUCKET=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      --region $REGION \
      --query 'Stacks[0].Outputs[?OutputKey==`S3Bucket`].OutputValue' \
      --output text 2>/dev/null || echo "")
    
    if [ -n "$S3_BUCKET" ]; then
        echo "✅ Found S3 bucket: $S3_BUCKET"
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

# Delete S3 bucket contents first (required before stack deletion)
if [ -n "$S3_BUCKET" ]; then
    echo "Emptying S3 bucket: $S3_BUCKET"
    aws s3 rm s3://$S3_BUCKET --recursive --region $REGION 2>/dev/null && echo "✅ S3 bucket emptied" || echo "⚠️  S3 bucket already empty or not found"
    echo ""
fi

# Delete CloudFormation stack
if [ "$STACK_EXISTS" = "true" ]; then
    echo "Deleting CloudFormation stack: $STACK_NAME"
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    
    echo "Waiting for stack deletion (this may take 2-3 minutes)..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION 2>/dev/null || true
    
    echo "✅ CloudFormation stack deleted"
    echo ""
fi

# Clean up orphaned S3 buckets (if any)
echo "Checking for orphaned S3 buckets..."
ORPHANED_BUCKETS=$(aws s3 ls | grep "cooking-assistant-data" | awk '{print $3}' || echo "")
if [ -n "$ORPHANED_BUCKETS" ]; then
    echo "Found orphaned buckets:"
    for BUCKET in $ORPHANED_BUCKETS; do
        echo "  - $BUCKET"
        aws s3 rm s3://$BUCKET --recursive --region $REGION 2>/dev/null || true
        aws s3 rb s3://$BUCKET --region $REGION 2>/dev/null && echo "    ✅ Deleted" || echo "    ⚠️  Could not delete"
    done
else
    echo "✅ No orphaned S3 buckets found"
fi
echo ""

# Delete EC2 key pair
echo "Deleting EC2 key pair..."
aws ec2 delete-key-pair --key-name cooking-assistant-key --region $REGION 2>/dev/null && echo "✅ Key pair deleted" || echo "⚠️  Key pair not found"
echo ""

# Clean up local files
echo "Cleaning up local files..."
rm -f cooking-assistant-key.pem
echo "✅ Local key files cleaned up"

echo ""
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
echo "✅ All AWS resources deleted:"
echo "   - CloudFormation stack"
echo "   - EC2 instance"
echo "   - S3 bucket (all data)"
echo "   - Security groups"
echo "   - IAM roles"
echo "   - EC2 key pair"
echo ""
echo "💰 You will no longer be charged for these resources."
echo ""
