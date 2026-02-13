.PHONY: install install-uv run-local run-aws deploy clean

install-uv:
	@echo "Installing uv..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh

install-env:
	@uv venv
	@echo "Installing Python dependencies with uv..."
	@uv pip install -e .

run-local:
	@echo "Running Flask app locally..."
	@export USE_LOCAL=true && uv run python src/app_local.py

run-aws:
	@echo "Running Flask app with AWS backend..."
	@uv run python src/app.py

deploy:
	@echo "Deploying to AWS..."
	@bash scripts/deploy.sh

clean:
	@echo "Cleaning up..."
	@rm -rf .venv __pycache__ src/__pycache__ *.pyc
	@find . -type d -name "__pycache__" -exec rm -rf {} +

help:
	@echo "Available targets:"
	@echo "  make install-uv   - Install uv package manager"
	@echo "  make install      - Install Python dependencies"
	@echo "  make run-local    - Run app locally (no AWS)"
	@echo "  make run-aws      - Run app with AWS backend"
	@echo "  make deploy       - Deploy to AWS"
	@echo "  make clean        - Clean up cache files"
