.PHONY: install run deploy clean help

install:
	@echo "Installing Python dependencies..."
	@uv pip install -r requirements.txt

run:
	@echo "Running app..."
	@python src/app.py

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
	@echo "  make install   - Install Python dependencies"
	@echo "  make run       - Run app locally"
	@echo "  make deploy    - Deploy to EC2 (Cost Optimized ~\$8-12/month)"
	@echo "  make clean     - Clean up cache files"
	@echo "  make cleanup   - Delete all AWS resources"
	@echo "  make help      - Show this help message"
	@echo ""
	@echo "Configuration:"
	@echo "  Edit .env file to set USE_AWS=true or USE_AWS=false"
	@echo ""
