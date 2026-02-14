.PHONY: install run run-aws deploy clean help

install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

run:
	@echo "Running Flask app in LOCAL mode..."
	@python src/app.py

run-aws:
	@echo "Running Flask app with AWS Bedrock..."
	@USE_AWS=true python src/app.py

deploy:
	@echo "Deploying to AWS..."
	@bash scripts/deploy_full.sh

clean:
	@echo "Cleaning up cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov

help:
	@echo "Personal Cooking Assistant - Available Commands:"
	@echo ""
	@echo "  make install   - Install Python dependencies"
	@echo "  make run       - Run app locally (mock data, no AWS)"
	@echo "  make run-aws   - Run app with AWS Bedrock RAG"
	@echo "  make deploy    - Deploy to AWS (full stack)"
	@echo "  make clean     - Clean up cache files"
	@echo "  make help      - Show this help message"
	@echo ""
