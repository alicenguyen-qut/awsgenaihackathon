# AWS Deployment Guide

Complete guide to deploy the AI Cooking Assistant to AWS.

## Quick Deploy

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy everything
./scripts/deploy.sh
```

That's it! The script will output your app URL.

## Step-by-Step Deployment

### Step 1: Deploy Infrastructure

```bash
./scripts/deploy.sh
```

This script will:
1. Create CloudFormation stack (S3, Lambda, API Gateway, IAM roles)
2. Package Lambda function with dependencies
3. Upload Lambda code
4. Upload UI files to S3
5. (Optional) Index recipe embeddings

**Expected output:**
```
✅ Deployment Complete!
🌐 Your app: https://xxxxx.execute-api.ap-southeast-2.amazonaws.com/prod
```

### Step 2: Test Your Deployment

```bash
# Get your API endpoint
export API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

# Test the API
curl $API_ENDPOINT

# Test chat endpoint
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "suggest a healthy breakfast"}'
```

### Step 3: Index Recipes (Optional)

```bash
# Set environment variables
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text)

# Run indexing script
python scripts/index_recipes.py
```

This generates embeddings for all recipes in `data/` folder.

## Architecture

```
User Browser
    ↓
API Gateway (HTTPS)
    ↓
Lambda Function (Python 3.11)
    ├── Bedrock (Claude 3.5 Sonnet) - Agentic chat with tool use
    ├── Bedrock (Titan V2) - Embeddings
    └── S3 Bucket
        ├── users/ - User data (JSON)
        ├── recipes/ - Recipe documents
        ├── embeddings/ - Recipe embeddings
        └── ui/ - Frontend files
```

## Project Structure for Lambda

```
lambda.zip
├── lambda_function.py       # Main handler
├── models/
│   ├── __init__.py
│   └── bedrock_rag.py      # RAG implementation
├── utils/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── helpers.py          # Utilities
│   ├── responses.py        # Mock responses
│   ├── recommendations.py  # Nutrition logic
│   └── analytics.py        # Analytics calculations
└── [dependencies]          # boto3, numpy, werkzeug, etc.
```

## Updating Your Deployment

### Update Lambda Code Only

```bash
./scripts/update_lambda.sh
```

Use this when you modify Python code but don't change infrastructure.

### Update UI Only

```bash
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text)

aws s3 cp src/frontend/templates/index.html s3://$RECIPES_BUCKET/ui/index.html
aws s3 sync src/frontend/js/ s3://$RECIPES_BUCKET/ui/frontend/js/ --delete
```

### Full Redeployment

```bash
./scripts/deploy.sh
```

## Monitoring & Debugging

### View Lambda Logs

```bash
# Real-time logs
aws logs tail /aws/lambda/cooking-assistant-chatbot --follow

# Recent logs
aws logs tail /aws/lambda/cooking-assistant-chatbot --since 1h
```

### Check Lambda Function

```bash
# Get function info
aws lambda get-function --function-name cooking-assistant-chatbot

# Test invocation
aws lambda invoke \
  --function-name cooking-assistant-chatbot \
  --payload '{"rawPath": "/api/session", "requestContext": {"http": {"method": "GET"}}}' \
  response.json

cat response.json
```

### Check S3 Bucket

```bash
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
    --output text)

# List contents
aws s3 ls s3://$RECIPES_BUCKET/ --recursive

# Check user data
aws s3 ls s3://$RECIPES_BUCKET/users/
```

## Cost Estimation

### Monthly Costs (Light Usage - 100 users, 10 queries/day)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30K invocations, 512MB, 5s avg | ~$1 |
| API Gateway | 30K requests | ~$0.03 |
| S3 | 1GB storage, 30K requests | ~$0.05 |
| Bedrock Claude Haiku | 300K tokens | ~$0.08 |
| Bedrock Titan Embeddings | 100K tokens | ~$0.01 |
| **Total** | | **~$1.17/month** |

### Monthly Costs (Medium Usage - 1000 users, 10 queries/day)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 300K invocations | ~$10 |
| API Gateway | 300K requests | ~$0.30 |
| S3 | 10GB storage, 300K requests | ~$0.30 |
| Bedrock Claude Haiku | 3M tokens | ~$0.75 |
| Bedrock Titan Embeddings | 1M tokens | ~$0.10 |
| **Total** | | **~$11.45/month** |

**Cost Savings vs OpenSearch:** ~$700/month (90%+ reduction)

## Troubleshooting

### Issue: "Access Denied" for Bedrock

**Solution:** Enable model access in Bedrock console:
1. Go to AWS Console → Bedrock → Model access
2. Enable Claude 3.5 Sonnet and Titan Embeddings V2

### Issue: Lambda timeout

**Solution:** Increase timeout in CloudFormation:
```yaml
Timeout: 60  # Increase to 120 if needed
```

### Issue: "Module not found" in Lambda

**Solution:** Redeploy Lambda with dependencies:
```bash
./scripts/update_lambda.sh
```

### Issue: CORS errors

**Solution:** CloudFormation already configures CORS. Check browser console for specific error.

### Issue: UI not loading

**Solution:** Check S3 upload:
```bash
aws s3 ls s3://$RECIPES_BUCKET/ui/
```

If empty, re-upload:
```bash
aws s3 cp src/frontend/templates/index.html s3://$RECIPES_BUCKET/ui/index.html
```

## Cleanup (Delete Everything)

```bash
./scripts/cleanup.sh
```

This will:
1. Ask for confirmation
2. Empty and delete S3 bucket
3. Delete CloudFormation stack
4. Verify deletion

**Result:** Zero AWS costs

## Security Best Practices

1. **Enable S3 encryption** (already configured)
2. **Use IAM roles** (already configured)
3. **Add API authentication** (optional - add API Gateway authorizer)
4. **Enable CloudWatch alarms** for monitoring
5. **Use AWS WAF** for API Gateway (optional)

## Production Checklist

- [ ] Bedrock models enabled
- [ ] CloudFormation stack deployed
- [ ] Lambda function working
- [ ] UI accessible via API Gateway
- [ ] Recipes indexed (optional)
- [ ] CloudWatch logs enabled
- [ ] Cost alerts configured
- [ ] Backup strategy for S3 data

## Support

**View logs:**
```bash
aws logs tail /aws/lambda/cooking-assistant-chatbot --follow
```

**Check stack status:**
```bash
aws cloudformation describe-stacks --stack-name cooking-assistant
```

**Test locally first:**
```bash
python src/app.py
# Visit http://localhost:5000
```

## Next Steps

1. **Custom domain:** Add Route53 + CloudFront
2. **Authentication:** Add Cognito user pools
3. **Monitoring:** Set up CloudWatch dashboards
4. **CI/CD:** Add GitHub Actions for auto-deployment
5. **Scaling:** Configure Lambda reserved concurrency
