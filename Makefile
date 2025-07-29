.PHONY: help build run dev stop clean logs health test install

# Default target
help:
	@echo "Viral Pilot User Management Service"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@echo "  install    - Install Python dependencies"
	@echo "  build      - Build Docker image"
	@echo "  run        - Run service with Docker Compose"
	@echo "  dev        - Run service in development mode"
	@echo "  stop       - Stop all services"
	@echo "  clean      - Clean up containers and images"
	@echo "  logs       - View service logs"
	@echo "  health     - Check service health"
	@echo "  test       - Run tests"
	@echo "  shell      - Open shell in running container"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Build Docker image
build:
	@echo "Building Docker image..."
	docker-compose build

# Run with Docker Compose
run:
	@echo "Starting User Management Service..."
	docker-compose up -d

# Development mode
dev:
	@echo "Starting User Management Service in development mode..."
	python main.py

# Stop services
stop:
	@echo "Stopping services..."
	docker-compose down

# Clean up
clean:
	@echo "Cleaning up containers and images..."
	docker-compose down -v --rmi all
	docker system prune -f

# View logs
logs:
	@echo "Viewing service logs..."
	docker-compose logs -f user-management

# Health check
health:
	@echo "Checking service health..."
	curl -f http://localhost:8001/health || echo "Service is not healthy"

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

# Open shell in container
shell:
	@echo "Opening shell in container..."
	docker-compose exec user-management /bin/bash

# Create test user
test-user:
	@echo "Creating test user..."
	curl -X POST http://localhost:8001/user \
		-H "Content-Type: application/json" \
		-d '{"cognito_user_id": "test-user-123", "username": "testuser", "email": "test@example.com"}'

# Check test user status
test-status:
	@echo "Checking test user status..."
	curl http://localhost:8001/user/test-user-123/status

# Get available tiers
tiers:
	@echo "Getting available subscription tiers..."
	curl http://localhost:8001/tiers 