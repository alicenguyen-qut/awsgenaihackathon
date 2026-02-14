#!/bin/bash

set -e

echo "==========================================="
echo "  EC2 Deployment (Cost Optimized)"
echo "==========================================="
echo ""

# Configuration
REGION="ap-southeast-2"
STACK_NAME="cooking-assistant-ec2-stack"
BUCKET_NAME="cooking-assistant-data-$(date +%s)"

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
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

PUBLIC_IP=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text)

WEBSITE_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
  --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`S3Bucket`].OutputValue' \
  --output text)

SSH_COMMAND=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`SSHCommand`].OutputValue' \
  --output text)

# Download private key
echo "Downloading EC2 private key..."
aws ec2 describe-key-pairs \
  --key-names cooking-assistant-key \
  --region $REGION \
  --include-public-key \
  --query 'KeyPairs[0].KeyMaterial' \
  --output text > cooking-assistant-key.pem 2>/dev/null || echo "Key pair already exists locally"
chmod 400 cooking-assistant-key.pem 2>/dev/null || true

echo ""
echo "==========================================="
echo "  Deployment Complete!"
echo "==========================================="
echo ""
echo "🎉 Your app will be available at:"
echo "   $WEBSITE_URL"
echo ""
echo "📊 Resources created:"
echo "   - CloudFormation stack: $STACK_NAME"
echo "   - EC2 instance: $INSTANCE_ID"
echo "   - Public IP: $PUBLIC_IP"
echo "   - S3 bucket: $S3_BUCKET"
echo "   - Key pair: cooking-assistant-key"
echo ""
echo "🔧 SSH access:"
echo "   $SSH_COMMAND"
echo ""
echo "📊 Monitor your instance:"
echo "   https://console.aws.amazon.com/ec2/home?region=$REGION#Instances:"
echo ""
echo "💰 Estimated cost: ~\$8-12/month"
echo ""
echo "⏳ Note: Instance is starting up, app may take 2-3 minutes to be ready"
echo ""