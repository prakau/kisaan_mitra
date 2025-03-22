# Weather Module Development Makefile

.PHONY: help setup test lint format clean coverage install update-deps

help:
	@echo "Available commands:"
	@echo "  setup         - Initial setup for development"
	@echo "  test          - Run tests"
	@echo "  lint          - Run code linting"
	@echo "  format        - Format code"
	@echo "  clean         - Clean up cache and test files"
	@echo "  coverage      - Run tests with coverage report"
	@echo "  install       - Install dependencies"
	@echo "  update-deps   - Update dependencies"

setup: install
	python manage.py makemigrations weather
	python manage.py migrate
	python manage.py collectstatic --no-input

test:
	pytest

lint:
	flake8 .
	mypy .
	isort . --check-only
	black . --check

format:
	isort .
	black .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

coverage:
	pytest --cov=. --cov-report=html
	@echo "Coverage report available at htmlcov/index.html"

install:
	pip install -r requirements.txt

update-deps:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

# Development workflow targets
.PHONY: dev-setup dev-update check-all

dev-setup: setup
	pre-commit install
	@echo "Development environment setup complete"

dev-update: update-deps
	pre-commit autoupdate
	@echo "Development dependencies updated"

check-all: format lint test coverage
	@echo "All checks completed"

# Database targets
.PHONY: migrate makemigrations showmigrations

migrate:
	python manage.py migrate weather

makemigrations:
	python manage.py makemigrations weather

showmigrations:
	python manage.py showmigrations weather

# Cache management
.PHONY: clear-cache

clear-cache:
	python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Documentation targets
.PHONY: docs serve-docs

docs:
	cd docs && make html
	@echo "Documentation built in docs/_build/html/"

serve-docs:
	cd docs/_build/html && python -m http.server 8000

# Continuous Integration targets
.PHONY: ci-check ci-test

ci-check: lint test
	@echo "CI checks passed"

ci-test:
	pytest --junitxml=test-results/junit.xml
	coverage xml
	@echo "CI tests completed"

# Security checks
.PHONY: security-check

security-check:
	bandit -r .
	safety check

# Type checking and static analysis
.PHONY: type-check

type-check:
	mypy .
	pytype .

# Performance profiling
.PHONY: profile

profile:
	python -m cProfile -o profile.stats $(file)
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(50)"

# Default target
.DEFAULT_GOAL := help