# AWS Deployment Summary

## ✅ Files Ready for Deployment

All AWS-related files have been reviewed and updated:

### 1. Lambda Function (`src/lambda_function.py`)
- ✅ Uses modular structure (utils/, models/)
- ✅ All API endpoints implemented
- ✅ Bedrock RAG integration
- ✅ S3-based user data storage
- ✅ Region: ap-southeast-2

### 2. Infrastructure (`infrastructure/cloudformation.yaml`)
- ✅ S3 bucket for storage
- ✅ Lambda function with proper IAM roles
- ✅ API Gateway with catch-all route
- ✅ Bedrock permissions configured

### 3. Deployment Scripts
- ✅ `scripts/deploy.sh` - Full deployment
- ✅ `scripts/update_lambda.sh` - Lambda-only updates
- ✅ `scripts/index_recipes.py` - Recipe indexing

### 4. Bedrock RAG (`src/models/bedrock_rag.py`)
- ✅ Titan Embeddings V2 (1024-dim)
- ✅ Claude 3 Haiku for responses
- ✅ Vector similarity search
- ✅ User profile integration

### 5. Utilities
- ✅ `utils/config.py` - Configuration
- ✅ `utils/helpers.py` - User data functions
- ✅ `utils/responses.py` - Mock responses
- ✅ `utils/recommendations.py` - Nutrition logic
- ✅ `utils/analytics.py` - Analytics calculations

## 🚀 How to Deploy

### Prerequisites
```bash
# 1. Configure AWS CLI
aws configure
# Enter: Access Key, Secret Key, Region: ap-southeast-2

# 2. Enable Bedrock models in AWS Console
# - Go to Bedrock → Model access
# - Enable: Claude 3 Haiku, Titan Embeddings V2
```

### Deploy in 3 Steps

```bash
# Step 1: Make scripts executable
chmod +x scripts/*.sh

# Step 2: Deploy everything
./scripts/deploy.sh

# Step 3: Get your app URL (from script output)
# https://xxxxx.execute-api.ap-southeast-2.amazonaws.com/prod
```

### Update Lambda Code Only
```bash
./scripts/update_lambda.sh
```

## 📋 What Gets Deployed

1. **S3 Bucket** - Stores:
   - User data (JSON files)
   - Recipe documents
   - Recipe embeddings
   - UI files (HTML/JS)

2. **Lambda Function** - Handles:
   - All API endpoints
   - Bedrock RAG queries
   - User authentication
   - Nutrition tracking
   - Chat management

3. **API Gateway** - Provides:
   - HTTPS endpoint
   - CORS configuration
   - Route to Lambda

4. **IAM Roles** - Permissions for:
   - Bedrock model invocation
   - S3 read/write
   - CloudWatch logs

## 🔍 Testing Deployment

```bash
# Get API endpoint
export API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name cooking-assistant \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

# Test UI
curl $API_ENDPOINT

# Test chat
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "suggest a healthy breakfast"}'

# View logs
aws logs tail /aws/lambda/cooking-assistant-chatbot --follow
```

## 💰 Estimated Costs

**Light usage (100 users, 10 queries/day):** ~$1-2/month
- Lambda: ~$1
- Bedrock: ~$0.10
- S3: ~$0.05
- API Gateway: ~$0.03

**Medium usage (1000 users, 10 queries/day):** ~$10-15/month

## 📚 Documentation

- **Full deployment guide:** `AWS_DEPLOY.md`
- **Features documentation:** `FEATURES.md`
- **Local development:** `README.md`

## 🔧 Troubleshooting

**Issue:** Lambda timeout
```bash
# Increase timeout in cloudformation.yaml
Timeout: 120
```

**Issue:** Bedrock access denied
```bash
# Enable models in AWS Console
# Bedrock → Model access → Enable Claude 3 Haiku & Titan V2
```

**Issue:** Module not found
```bash
# Redeploy Lambda with dependencies
./scripts/update_lambda.sh
```

## 🎯 Next Steps After Deployment

1. ✅ Test the app at your API Gateway URL
2. ✅ Monitor CloudWatch logs
3. ✅ (Optional) Index recipes: `python scripts/index_recipes.py`
4. ✅ Set up cost alerts in AWS Console
5. ✅ Configure custom domain (optional)

## 🗑️ Delete All Resources (Zero Cost)

```bash
./scripts/cleanup.sh
```

This will delete:
- ✅ CloudFormation stack
- ✅ Lambda function
- ✅ API Gateway
- ✅ S3 bucket and ALL data
- ✅ IAM roles

**Result:** Zero AWS costs

---

## 📞 Support

**View real-time logs:**
```bash
aws logs tail /aws/lambda/cooking-assistant-chatbot --follow
```

**Check deployment status:**
```bash
aws cloudformation describe-stacks --stack-name cooking-assistant
```

**Delete everything:**
```bash
aws cloudformation delete-stack --stack-name cooking-assistant
```

---

**Region:** ap-southeast-2 (Sydney)
**Stack Name:** cooking-assistant
**Runtime:** Python 3.11
