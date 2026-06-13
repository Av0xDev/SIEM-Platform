.PHONY: help setup install install-all dev docker-up docker-down docker-build test lint format clean

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)===================================================$(NC)"
	@echo "$(BLUE)SIEM Platform - Available Commands$(NC)"
	@echo "$(BLUE)===================================================$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make setup              # Run automated setup"
	@echo "  make docker-up          # Start services with Docker"
	@echo "  make dev                # Start frontend in dev mode"
	@echo "  make test               # Run all tests"
	@echo ""

setup: ## Run automated setup script
	@echo "$(BLUE)Running automated setup...$(NC)"
	@bash setup.sh

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install

install-python: ## Install Python backend dependencies
	@echo "$(BLUE)Installing Python backend dependencies...$(NC)"
	@cd backend-python && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

install-java: ## Install Java backend dependencies
	@echo "$(BLUE)Installing Java backend dependencies...$(NC)"
	@cd backend-java && mvn clean install -q

install-ruby: ## Install Ruby backend dependencies
	@echo "$(BLUE)Installing Ruby backend dependencies...$(NC)"
	@cd backend-ruby && bundle install

install-php: ## Install PHP backend dependencies
	@echo "$(BLUE)Installing PHP backend dependencies...$(NC)"
	@cd backend-php && composer install

install-all: install-frontend install-python install-java install-ruby install-php ## Install all dependencies
	@echo "$(GREEN)✓ All dependencies installed$(NC)"

dev: ## Start frontend in development mode
	@echo "$(BLUE)Starting frontend in development mode...$(NC)"
	@cd frontend && npm run dev

dev-python: ## Start Python backend
	@echo "$(BLUE)Starting Python backend...$(NC)"
	@cd backend-python && . venv/bin/activate && python app.py

dev-java: ## Start Java backend
	@echo "$(BLUE)Starting Java backend...$(NC)"
	@cd backend-java && mvn spring-boot:run

dev-ruby: ## Start Ruby backend
	@echo "$(BLUE)Starting Ruby backend...$(NC)"
	@cd backend-ruby && ruby app.rb

dev-php: ## Start PHP backend
	@echo "$(BLUE)Starting PHP backend...$(NC)"
	@cd backend-php && php -S localhost:8081

build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	@cd frontend && npm run build

build-all: ## Build all components
	@echo "$(BLUE)Building all components...$(NC)"
	@cd frontend && npm run build
	@cd backend-java && mvn clean install -q
	@echo "$(GREEN)✓ All components built$(NC)"

test: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd frontend && npm run test

test-all: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@echo "Frontend tests..."
	@cd frontend && npm test
	@echo "$(BLUE)Python tests...$(NC)"
	@cd backend-python && pytest
	@echo "$(BLUE)Java tests...$(NC)"
	@cd backend-java && mvn test -q
	@echo "$(BLUE)Ruby tests...$(NC)"
	@cd backend-ruby && rspec
	@echo "$(GREEN)✓ All tests passed$(NC)"

lint: ## Lint frontend code
	@echo "$(BLUE)Linting frontend code...$(NC)"
	@cd frontend && npm run lint

format: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	@cd frontend && npm run format

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build

docker-up: ## Start services with Docker Compose
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo ""
	@echo "Access the services at:"
	@echo "  Frontend:    http://localhost:3001"
	@echo "  Java API:    http://localhost:8080"
	@echo "  Python API:  http://localhost:5000"

docker-down: ## Stop Docker services
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@docker-compose down

docker-logs: ## View Docker logs
	@echo "$(BLUE)Docker logs:$(NC)"
	@docker-compose logs -f

docker-restart: ## Restart Docker services
	@echo "$(BLUE)Restarting Docker services...$(NC)"
	@docker-compose restart

docker-clean: ## Clean Docker containers and volumes
	@echo "$(BLUE)Cleaning Docker containers and volumes...$(NC)"
	@docker-compose down -v

clean-frontend: ## Clean frontend build artifacts
	@echo "$(BLUE)Cleaning frontend...$(NC)"
	@cd frontend && rm -rf node_modules dist build

clean-python: ## Clean Python build artifacts
	@echo "$(BLUE)Cleaning Python backend...$(NC)"
	@cd backend-python && rm -rf venv __pycache__ .pytest_cache *.pyc

clean-java: ## Clean Java build artifacts
	@echo "$(BLUE)Cleaning Java backend...$(NC)"
	@cd backend-java && mvn clean -q

clean-ruby: ## Clean Ruby build artifacts
	@echo "$(BLUE)Cleaning Ruby backend...$(NC)"
	@cd backend-ruby && rm -rf vendor Gemfile.lock

clean: clean-frontend clean-python clean-java clean-ruby ## Clean all build artifacts
	@echo "$(GREEN)✓ All build artifacts cleaned$(NC)"

env-setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env file created$(NC)"; \
	else \
		echo "$(RED).env file already exists$(NC)"; \
	fi

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@echo ""
	@echo "Frontend:     http://localhost:3001"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:3001 || echo "  Status: Not running"
	@echo ""
	@echo "Java API:     http://localhost:8080/health"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:8080/health || echo "  Status: Not running"
	@echo ""
	@echo "Python API:   http://localhost:5000/health"
	@curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:5000/health || echo "  Status: Not running"

docs: ## View documentation
	@echo "$(BLUE)Available Documentation:$(NC)"
	@echo "  README.md       - Project overview"
	@echo "  QUICK_START.md  - Quick start guide"
	@echo "  INSTALL.md      - Detailed installation guide"
	@echo "  docs/           - Architecture and API documentation"

.DEFAULT_GOAL := help
