#!/bin/bash

set -e

echo "==========================================="
echo "  Personal Cooking Assistant - AWS Deployment"
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

# Wait for instance to be running
echo "Waiting for EC2 instance to be ready..."
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
echo "✅ Instance is running"
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

# Index recipes to S3
echo "Indexing recipes to S3..."
export AWS_REGION=$REGION
export RECIPES_BUCKET=$S3_BUCKET
export S3_BUCKET=$S3_BUCKET
python3 scripts/index_recipes.py
echo "✅ Recipes indexed to S3"
echo ""

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
echo "     • Recipe embeddings: s3://$S3_BUCKET/embeddings/"
echo "     • Recipe texts: s3://$S3_BUCKET/recipes/"
echo "     • User sessions: s3://$S3_BUCKET/sessions/"
echo "     • User uploads: s3://$S3_BUCKET/uploads/"
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