.PHONY: install run run-local run-aws deploy clean help

install:
	@uv venv
	@echo "Installing Python dependencies..."
	@uv pip install -r requirements.txt

run-local:
	@echo "Running locally WITHOUT AWS (mock mode)..."
	@echo "No AWS credentials needed - uses mock data responses"
	@USE_AWS=false python src/app.py

run-aws:
	@echo "Running locally WITH AWS Bedrock + S3..."
	@echo "Requires: AWS credentials configured"
	@USE_AWS=true python src/app.py

run: run-local

deploy:
	@echo "Deploying to EC2 (Cost Optimized)..."
	@bash scripts/deploy.sh

clean:
	@echo "Cleaning up cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov

cleanup:
	@echo "Cleaning up AWS resources..."
	@bash scripts/cleanup.sh

help:
	@echo "Personal Cooking Assistant - Available Commands:"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make run-local  - Run WITHOUT AWS (mock/fallback mode)"
	@echo "  make run-aws    - Run WITH AWS Bedrock + S3 embeddings"
	@echo "  make run        - Alias for run-local"
	@echo "  make deploy     - Deploy to AWS (~\$$8-12/month)"
	@echo "  make clean      - Clean up cache files"
	@echo "  make cleanup    - Delete all AWS resources"
	@echo "  make help       - Show this help message"
	@echo ""
	@echo "Local Testing Modes:"
	@echo "  run-local: No AWS needed, uses mock responses"
	@echo "  run-aws:   Requires AWS CLI configured with Bedrock access"
	@echo ""
