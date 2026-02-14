.PHONY: install run clean help

install:
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

run:
	@echo "Running Flask app in LOCAL mode..."
	@python src/app.py

run-aws:
	@echo "Running Flask app in AWS mode..."
	@USE_AWS=true python src/app.py

deploy:
	@echo "Deploying to AWS..."
	@bash scripts/deploy_full.sh

clean:
	@echo "Cleaning up..."
	@rm -rf __pycache__ src/__pycache__ *.pyc
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

help:
	@echo "Available targets:"
	@echo "  make install   - Install Python dependencies"
	@echo "  make run       - Run app locally (no AWS)"
	@echo "  make run-aws   - Run app with AWS backend"
	@echo "  make deploy    - Deploy to AWS"
	@echo "  make clean     - Clean up cache files"
