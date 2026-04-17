# Development Setup Guide

## Prerequisites

- Git
- Docker & Docker Compose (v2.0+)
- Node.js 18+ and npm
- Python 3.9+
- Java 17+ and Maven
- Ruby 3.2+

## Quick Start with Docker Compose

The easiest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Av0xDev/SIEM-Platform.git
cd SIEM-Platform

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# Access the application
# Frontend: http://localhost:3001
# Java API: http://localhost:8080
# Python API: http://localhost:5000
# Swagger UI: http://localhost:8080/swagger-ui.html
```

## Local Development Setup

### 1. Python Service

```bash
cd backend-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally (requires MongoDB and PostgreSQL)
flask run
```

### 2. Java Service

```bash
cd backend-java

# Build project
mvn clean install

# Run with Spring Boot
mvn spring-boot:run

# Or run JAR file
java -jar target/siem-platform-1.0.0.jar
```

### 3. React Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server (with hot reload)
npm run dev

# Build for production
npm run build
```

### 4. Ruby Service

```bash
cd backend-ruby

# Install dependencies
bundle install

# Run the service
bundle exec ruby app.rb
```

### 5. PHP Service

```bash
cd backend-php

# Using built-in PHP server
php -S localhost:8000

# Or with Apache (requires Apache installed)
```

### 6. Databases

```bash
# Start PostgreSQL
docker run -d \
  --name siem-postgres \
  -e POSTGRES_USER=siem_user \
  -e POSTGRES_PASSWORD=siem_password_123 \
  -e POSTGRES_DB=siem_db \
  -p 5432:5432 \
  postgres:15-alpine

# Start MongoDB
docker run -d \
  --name siem-mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=siem_user \
  -e MONGO_INITDB_ROOT_PASSWORD=siem_password_123 \
  -e MONGO_INITDB_DATABASE=siem_db \
  -p 27017:27017 \
  mongo:6-alpine
```

## Testing

### Python Tests

```bash
cd backend-python
pip install pytest pytest-cov
pytest --cov=.
pytest -v  # Verbose output
```

### Java Tests

```bash
cd backend-java
mvn test
mvn test -Dtest=SpecificTestClass  # Run specific test
```

### Frontend Tests

```bash
cd frontend
npm test
npm test -- --coverage  # With coverage report
```

### Ruby Tests

```bash
cd backend-ruby
bundle exec rspec
```

## Code Quality

### Python Linting

```bash
cd backend-python
pip install flake8
flake8 . --max-line-length=100
```

### Java Linting

```bash
cd backend-java
mvn checkstyle:check
```

### Frontend Linting

```bash
cd frontend
npm run lint
npm run format  # Auto-fix formatting
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Databases
DATABASE_URL=postgresql://siem_user:siem_password_123@localhost:5432/siem_db
MONGODB_URL=mongodb://siem_user:siem_password_123@localhost:27017/siem_db

# Services
PYTHON_SERVICE_URL=http://localhost:5000
JAVA_SERVICE_URL=http://localhost:8080
RUBY_SERVICE_URL=http://localhost:3000

# Frontend
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080

# Security
JWT_SECRET=your-secret-key-change-in-production
WEBHOOK_SECRET=webhook-secret-key

# Optional
REDIS_URL=redis://localhost:6379
SENTRY_DSN=https://your-sentry-dsn
```

## Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f python

# Stop all services
docker-compose down

# Restart a service
docker-compose restart java

# Run a command in a container
docker-compose exec python bash

# View service status
docker-compose ps
```

## Health Checks

Verify all services are running:

```bash
# Frontend
curl http://localhost:3001

# Java API
curl http://localhost:8080/actuator/health

# Python API
curl http://localhost:5000/health

# PHP Service
curl http://localhost:8000/health.php

# Ruby Service
curl http://localhost:3000/health

# PostgreSQL
psql -h localhost -U siem_user -d siem_db -c "SELECT 1"

# MongoDB
mongosh -u siem_user -p siem_password_123 --authenticationDatabase admin localhost:27017/siem_db
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8080  # On macOS/Linux
netstat -ano | findstr :8080  # On Windows

# Kill process
kill -9 <PID>  # On macOS/Linux
taskkill /PID <PID> /F  # On Windows
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check MongoDB is running
docker-compose ps mongodb

# Rebuild containers
docker-compose down -v
docker-compose up -d
```

### Service Won't Start

```bash
# View detailed logs
docker-compose logs python

# Rebuild image
docker-compose build --no-cache python

# Remove dangling images
docker image prune
```

## IDE Setup

### VS Code Extensions (Recommended)
- Python (ms-python.python)
- Java Extension Pack (vscjava.vscode-java-pack)
- ES7+ React/Redux/React-Native snippets (dsznajder.es7-react-js-snippets)
- Prettier (esbenp.prettier-vscode)
- Docker (ms-azuretools.vscode-docker)

### IntelliJ IDEA
- Built-in support for all languages
- Configure Python interpreter for backend-python
- Configure SDK for backend-java
- Install Node.js plugin for frontend

## Next Steps

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
2. Read [API.md](API.md) for API documentation
3. Check out [Contributing Guidelines](../CONTRIBUTING.md)
4. Explore the codebase

---

For issues or questions, open a GitHub Issue or Discussion.
