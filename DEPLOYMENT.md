# AI Cooking Assistant - AWS Deployment Guide

## Features Deployed to AWS

✅ **User Authentication** - Login/register with password hashing  
✅ **Profile Photos** - Upload and display profile pictures  
✅ **Daily Nutrition Tracking** - Log meals, view stats, analytics  
✅ **Session Management** - Persistent user sessions  
✅ **Chat Functionality** - AI-powered recipe suggestions  
✅ **S3 Storage** - User data, photos, and embeddings  

## AWS Services Used

1. **Amazon Bedrock** - Claude 3 Haiku (LLM) + Titan Embeddings
2. **S3** - User data, photos, recipe embeddings (~$700/month savings vs OpenSearch!)
3. **AWS Lambda** - Backend API with session management
4. **API Gateway** - REST API with CORS support
5. **IAM Roles** - Secure permissions

## Quick Deployment

### 1. Enable Bedrock Models
```bash
# Go to AWS Console > Bedrock > Model access (ap-southeast-2 region)
# Enable: Claude 3 Haiku and Titan Embeddings v1
```

### 2. Deploy Everything
```bash
chmod +x scripts/deploy_full.sh
./scripts/deploy_full.sh
```

### 3. Access Your App
The script will output your live URL:
```
✅ Deployment complete!
🌐 Your app is live at: https://xxxxxxxxxx.execute-api.ap-southeast-2.amazonaws.com/prod
```

## Manual Deployment Steps

### 1. Deploy Infrastructure
```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yaml \
  --stack-name cooking-assistant \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-southeast-2
```

### 2. Get Stack Outputs
```bash
export RECIPES_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name cooking-assistant \
  --region ap-southeast-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`RecipesBucket`].OutputValue' \
  --output text)

export API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name cooking-assistant \
  --region ap-southeast-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)
```

### 3. Upload UI Files
```bash
aws s3 cp src/templates/index.html s3://$RECIPES_BUCKET/ui/index.html
aws s3 cp src/frontend/ s3://$RECIPES_BUCKET/ui/frontend/ --recursive
```

### 4. Deploy Lambda Function
```bash
cd src
zip -r ../function.zip lambda_function.py
aws lambda update-function-code \
  --function-name cooking-assistant-chatbot \
  --zip-file fileb://function.zip \
  --region ap-southeast-2
cd .. && rm function.zip
```

### 5. Index Recipes (Optional)
```bash
python scripts/index_recipes.py
```

## Quick Updates

For code-only updates:
```bash
chmod +x scripts/deploy_lambda.sh
./scripts/deploy_lambda.sh
```

## Data Storage Structure

```
S3 Bucket:
├── users/
│   ├── {user-id}.json          # User data, nutrition logs, settings
│   └── ...
├── photos/
│   ├── {user-id}_profile.jpg   # Profile photos
│   └── ...
├── ui/
│   ├── index.html              # Main UI
│   └── frontend/js/            # JavaScript files
└── embeddings/
    └── recipe_embeddings.json  # Recipe vector embeddings
```

## Key Differences from Local Version

- **Session Management**: Uses headers instead of Flask sessions
- **File Upload**: Base64 encoding for Lambda compatibility
- **Data Storage**: S3 instead of local JSON files
- **Static Assets**: Served from S3 instead of Flask static files

## Cost Optimization

💰 **S3 vs OpenSearch Serverless**: ~$700/month savings!  
📊 **Lambda**: Pay per request (very cost-effective for low traffic)  
🔍 **In-memory vector search**: No additional search service costs  

## Troubleshooting

**Login issues**: Check CloudWatch logs for Lambda errors  
**Photo upload fails**: Verify S3 permissions in IAM role  
**API errors**: Check API Gateway logs and Lambda function logs  

**Your full-featured cooking assistant is now running on AWS! 🍳**
