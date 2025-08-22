.PHONY: help install install-dev test lint format clean build publish version-patch version-minor version-major

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest tests/ -v

lint: ## Run linters
	ruff check src/ tests/
	mypy src/

format: ## Format code with black
	black src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build: clean ## Build distribution packages
	python -m build

publish: build ## Publish to PyPI
	python -m twine upload dist/*

version-patch: ## Bump patch version (0.1.0 -> 0.1.1)
	@current=$$(grep '__version__' src/core/version.py | cut -d'"' -f2); \
	new=$$(echo $$current | awk -F. '{print $$1"."$$2"."$$3+1}'); \
	sed -i '' "s/__version__ = \"$$current\"/__version__ = \"$$new\"/" src/core/version.py; \
	sed -i '' "s/version = \"$$current\"/version = \"$$new\"/" pyproject.toml; \
	sed -i '' "s/version=\"$$current\"/version=\"$$new\"/" setup.py; \
	echo "Version bumped from $$current to $$new"; \
	git add -A && git commit -m "Bump version to $$new"

version-minor: ## Bump minor version (0.1.0 -> 0.2.0)
	@current=$$(grep '__version__' src/core/version.py | cut -d'"' -f2); \
	new=$$(echo $$current | awk -F. '{print $$1"."$$2+1".0"}'); \
	sed -i '' "s/__version__ = \"$$current\"/__version__ = \"$$new\"/" src/core/version.py; \
	sed -i '' "s/version = \"$$current\"/version = \"$$new\"/" pyproject.toml; \
	sed -i '' "s/version=\"$$current\"/version=\"$$new\"/" setup.py; \
	echo "Version bumped from $$current to $$new"; \
	git add -A && git commit -m "Bump version to $$new"

version-major: ## Bump major version (0.1.0 -> 1.0.0)
	@current=$$(grep '__version__' src/core/version.py | cut -d'"' -f2); \
	new=$$(echo $$current | awk -F. '{print $$1+1".0.0"}'); \
	sed -i '' "s/__version__ = \"$$current\"/__version__ = \"$$new\"/" src/core/version.py; \
	sed -i '' "s/version = \"$$current\"/version = \"$$new\"/" pyproject.toml; \
	sed -i '' "s/version=\"$$current\"/version=\"$$new\"/" setup.py; \
	echo "Version bumped from $$current to $$new"; \
	git add -A && git commit -m "Bump version to $$new"

release: ## Create a new release (after version bump)
	@version=$$(grep '__version__' src/core/version.py | cut -d'"' -f2); \
	git tag -a "v$$version" -m "Release version $$version"; \
	echo "Tagged version v$$version"; \
	echo "Run 'git push origin v$$version' to push the tag"