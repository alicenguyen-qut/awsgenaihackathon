.PHONY: install run deploy clean help

install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

run:
	@echo "Running Flask app (mode set in .env)..."
	@python src/app.py

deploy:
	@echo "Deploying to AWS..."
	@bash scripts/deploy.sh

clean:
	@echo "Cleaning up cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache .coverage htmlcov

help:
	@echo "Personal Cooking Assistant - Available Commands:"
	@echo ""
	@echo "  make install   - Install Python dependencies"
	@echo "  make run       - Run app (USE_AWS set in .env file)"
	@echo "  make deploy    - Deploy to AWS (full stack)"
	@echo "  make clean     - Clean up cache files"
	@echo "  make help      - Show this help message"
	@echo ""
	@echo "Configuration:"
	@echo "  Edit .env file to set USE_AWS=true or USE_AWS=false"
	@echo ""
