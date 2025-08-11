.PHONY: install test clean build help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest

lint: ## Run linting
	poetry run flake8 notion_uploader/
	poetry run black --check notion_uploader/

format: ## Format code
	poetry run black notion_uploader/
	poetry run isort notion_uploader/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

install-cli: ## Install the CLI tool
	poetry install

uninstall-cli: ## Uninstall the CLI tool
	pip uninstall notion-uploader -y 