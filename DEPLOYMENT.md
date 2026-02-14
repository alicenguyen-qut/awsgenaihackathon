# AWS Deployment Guide

This guide covers deploying the AI Cooking Assistant to AWS.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Python 3.9+
- S3 bucket for storing recipes and embeddings

## Architecture Overview

```
CloudFront → S3 (Static UI)
    ↓
API Gateway → Lambda → Bedrock (Claude 3 Haiku)
                ↓
              S3 (Recipes, Embeddings, User Data)
```

## Step 1: Prepare Recipe Embeddings

```bash
# Index recipes and generate embeddings
python scripts/index_recipes.py

# This creates embeddings/recipe_embeddings.json
```

## Step 2: Create S3 Bucket

```bash
# Create bucket (replace with your bucket name)
aws s3 mb s3://your-cooking-assistant-bucket

# Upload recipe data
aws s3 sync data/ s3://your-cooking-assistant-bucket/recipes/

# Upload embeddings
aws s3 cp embeddings/recipe_embeddings.json s3://your-cooking-assistant-bucket/embeddings/
```

## Step 3: Deploy Infrastructure

```bash
# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name cooking-assistant \
  --template-body file://infrastructure/cloudformation.yaml \
  --parameters ParameterKey=RecipesBucket,ParameterValue=your-cooking-assistant-bucket \
  --capabilities CAPABILITY_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete --stack-name cooking-assistant
```

## Step 4: Package and Deploy Lambda

```bash
# Package Lambda function
cd src
pip install -r ../requirements.txt -t .
zip -r ../lambda.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

# Upload to Lambda
aws lambda update-function-code \
  --function-name CookingAssistantFunction \
  --zip-file fileb://lambda.zip
```

## Step 5: Upload Frontend to S3

```bash
# Upload UI files
aws s3 cp src/templates/index.html s3://your-cooking-assistant-bucket/ui/
aws s3 sync src/frontend/ s3://your-cooking-assistant-bucket/ui/frontend/

# Make files public (if using S3 static hosting)
aws s3 website s3://your-cooking-assistant-bucket/ \
  --index-document ui/index.html
```

## Step 6: Configure API Gateway

Get your API Gateway endpoint:

```bash
aws cloudformation describe-stacks \
  --stack-name cooking-assistant \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

Update your frontend to use this endpoint (if needed).

## Environment Variables

Set these in Lambda configuration:

- `RECIPES_BUCKET` - Your S3 bucket name
- `AWS_REGION` - Your AWS region (e.g., ap-southeast-2)

## Testing Deployment

```bash
# Test Lambda function
aws lambda invoke \
  --function-name CookingAssistantFunction \
  --payload '{"rawPath": "/api/session", "requestContext": {"http": {"method": "GET"}}}' \
  response.json

cat response.json
```

## Monitoring

### CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/CookingAssistantFunction --follow
```

### Metrics

Monitor in CloudWatch:
- Lambda invocations
- API Gateway requests
- Bedrock API calls
- S3 storage usage

## Cost Optimization

### Current Setup
- **Lambda**: Pay per request (~$0.20 per 1M requests)
- **Bedrock**: Pay per token (~$0.00025 per 1K tokens for Claude Haiku)
- **S3**: ~$0.023 per GB/month
- **API Gateway**: ~$1 per million requests

### Estimated Monthly Cost
- Light usage (100 users, 10 queries/day): ~$5-10/month
- Medium usage (1000 users, 10 queries/day): ~$50-100/month

### Cost Savings vs OpenSearch
- **Without OpenSearch**: ~$5-100/month
- **With OpenSearch**: ~$700+/month
- **Savings**: ~$600-695/month (90%+ reduction)

## Troubleshooting

### Lambda Timeout
Increase timeout in CloudFormation:
```yaml
Timeout: 30  # seconds
```

### Bedrock Access Denied
Enable Bedrock models in AWS Console:
1. Go to Bedrock console
2. Model access → Manage model access
3. Enable Claude 3 Haiku and Titan Embeddings

### CORS Issues
Update API Gateway CORS settings:
```yaml
CorsConfiguration:
  AllowOrigins:
    - '*'
  AllowMethods:
    - GET
    - POST
    - DELETE
  AllowHeaders:
    - Content-Type
    - x-session-id
```

## Updating Deployment

### Update Lambda Code
```bash
bash scripts/deploy_lambda.sh
```

### Update Frontend
```bash
bash scripts/upload_ui.sh
```

### Full Redeployment
```bash
bash scripts/deploy_full.sh
```

## Rollback

```bash
# Delete stack
aws cloudformation delete-stack --stack-name cooking-assistant

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name cooking-assistant
```

## Security Best Practices

1. **Enable encryption**: Use S3 bucket encryption
2. **IAM roles**: Use least-privilege IAM roles
3. **API authentication**: Add API Gateway authentication
4. **Secrets**: Store secrets in AWS Secrets Manager
5. **VPC**: Deploy Lambda in VPC for enhanced security

## Production Checklist

- [ ] Enable CloudWatch alarms
- [ ] Set up backup for S3 data
- [ ] Configure custom domain
- [ ] Enable SSL/TLS
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling
- [ ] Enable AWS WAF for API Gateway
- [ ] Set up monitoring dashboard
- [ ] Document runbooks
- [ ] Test disaster recovery

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review AWS service quotas
3. Verify IAM permissions
4. Test with AWS CLI first
