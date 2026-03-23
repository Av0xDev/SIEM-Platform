# Development Setup

## Prerequisites

- Docker & Docker Compose (for databases)
- Python 3.11+, Java 17+, PHP 8.2+, Ruby 3.2+, Node 20+

## Start infrastructure only

```bash
docker compose up -d postgres mongodb redis
```

## Python (Flask)

```bash
cd backend-python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # adjust DB_HOST=localhost
FLASK_ENV=development flask run --port 5000
```

## Java (Spring Boot)

```bash
cd backend-java
mvn spring-boot:run -Dspring-boot.run.profiles=dev
```

## PHP (Apache/built-in)

```bash
cd backend-php
composer install
php -S localhost:8000 -t public/
```

## Ruby (Sinatra/Puma)

```bash
cd backend-ruby
bundle install
PYTHON_SERVICE_URL=http://localhost:5000 bundle exec puma -p 3000
```

## Frontend (Vite)

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## Running Tests

```bash
# Python
cd backend-python && pytest

# Java
cd backend-java && mvn test

# PHP
cd backend-php && vendor/bin/phpunit

# Ruby
cd backend-ruby && bundle exec rspec

# Frontend
cd frontend && npm test
```
