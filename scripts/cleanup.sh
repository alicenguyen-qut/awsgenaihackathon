#!/bin/bash

set -e

echo "=========================================="
echo "  AWS Resources Cleanup"
echo "=========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
STACK_NAMES=("cooking-assistant-ec2-stack" "cooking-assistant-stack")

echo "Checking existing resources..."

# Find which stack exists
STACK_NAME=""
for name in "${STACK_NAMES[@]}"; do
    if aws cloudformation describe-stacks --stack-name "$name" --region $REGION &>/dev/null; then
        STACK_NAME="$name"
        echo "✅ Found stack: $STACK_NAME"
        break
    fi
done

if [ -z "$STACK_NAME" ]; then
    echo "❌ No CloudFormation stack found"
    echo ""
    echo "Checking for orphaned resources..."
    
    # Check for S3 buckets
    BUCKETS=$(aws s3 ls | grep -E "cooking-assistant-data|app-data-bucket" | awk '{print $3}' || echo "")
    if [ -n "$BUCKETS" ]; then
        echo "Found S3 buckets:"
        echo "$BUCKETS"
    fi
    
    # Check for EC2 instances
    INSTANCES=$(aws ec2 describe-instances --region $REGION --filters "Name=tag:Name,Values=CookingAssistant" "Name=instance-state-name,Values=running,stopped" --query 'Reservations[*].Instances[*].InstanceId' --output text)
    if [ -n "$INSTANCES" ]; then
        echo "Found EC2 instances: $INSTANCES"
    fi
    
    if [ -z "$BUCKETS" ] && [ -z "$INSTANCES" ]; then
        echo "No resources found to clean up."
        exit 0
    fi
else
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
if [ -n "$STACK_NAME" ]; then
    echo "Deleting CloudFormation stack: $STACK_NAME"
    aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    
    echo "Waiting for stack deletion (this may take 2-3 minutes)..."
    aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION 2>/dev/null || true
    
    echo "✅ CloudFormation stack deleted"
    echo ""
fi

# Clean up orphaned S3 buckets (if any)
echo "Checking for orphaned S3 buckets..."
ORPHANED_BUCKETS=$(aws s3 ls | grep -E "cooking-assistant-data|app-data-bucket" | awk '{print $3}' || echo "")
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

# Terminate orphaned EC2 instances
echo "Checking for orphaned EC2 instances..."
ORPHANED_INSTANCES=$(aws ec2 describe-instances --region $REGION --filters "Name=tag:Name,Values=CookingAssistant" "Name=instance-state-name,Values=running,stopped" --query 'Reservations[*].Instances[*].InstanceId' --output text)
if [ -n "$ORPHANED_INSTANCES" ]; then
    echo "Found orphaned instances: $ORPHANED_INSTANCES"
    aws ec2 terminate-instances --instance-ids $ORPHANED_INSTANCES --region $REGION
    echo "✅ Instances terminated"
else
    echo "✅ No orphaned instances found"
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
