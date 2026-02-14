# AWS Deployment Guide

## Architecture

```
User → EC2 (Flask App) → Amazon Bedrock (Claude + Titan)
           ↓
        S3 Bucket
        ├── embeddings/    (Recipe embeddings)
        ├── recipes/       (Recipe texts)
        ├── sessions/      (User data)
        └── uploads/       (User files)
```

## Deploy

```bash
bash scripts/deploy.sh
```

**CloudFormation deploys:**
- EC2 t3.micro instance with Flask app
- S3 bucket for all data storage
- Security Group (HTTP, HTTPS, SSH)
- IAM Role (S3 + Bedrock permissions)
- EC2 Key Pair for SSH access

**Script also:**
- Indexes recipes to S3 from local machine
- EC2 auto-indexes on startup

Access: `http://<public-ip>` (shown after deployment)

## Cleanup

```bash
bash scripts/cleanup.sh
```

Deletes all resources and stops charges.

## Monitoring

**SSH to instance:**
```bash
ssh -i cooking-assistant-key.pem ec2-user@<public-ip>
```

**View logs:**
```bash
sudo journalctl -u cooking-assistant -f
```

**Restart app:**
```bash
sudo systemctl restart cooking-assistant
```

## Troubleshooting

**App not responding:**
- SSH to instance and check logs
- Verify security group allows port 80

**Recipe search not working:**
- Re-run: `python3 scripts/index_recipes.py`
- Check Bedrock model access in AWS Console

**User data not persisting:**
- Check IAM role has S3 permissions
- Review app logs for S3 errors

## Update Code

```bash
ssh -i cooking-assistant-key.pem ec2-user@<public-ip>
cd awsgenaihackathon
git pull
sudo systemctl restart cooking-assistant
```

## Cost

- EC2 t3.micro: ~$8.76/month
- S3 storage: ~$1-3/month
- Bedrock: Pay per request (~$15-25/month)

**Total: ~$25-35/month**

Stop EC2 when not in use to save ~$8/month.