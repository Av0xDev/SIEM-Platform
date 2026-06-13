# SIEM Platform Installation Guide

This guide provides instructions for installing and running the SIEM Platform, which consists of multiple microservices written in different technologies.

## Project Structure

The SIEM Platform is a multi-service application with the following components:

- **Frontend**: React + Vite web application (Port 3001)
- **Backend (Python)**: Flask-based log processing and correlation service (Port 5000)
- **Backend (Java)**: Spring Boot security analytics and API gateway (Port 8080)
- **Backend (PHP)**: Webhook and integration service
- **Backend (Ruby)**: Additional processing service

## Prerequisites

Before starting the installation, ensure you have the following tools installed on your system:

### Required Tools
- **Node.js** (v18 or higher): Install from https://nodejs.org/
- **Python** (3.9 or higher): Install from https://www.python.org/
- **Java** (JDK 17 or higher): Install from https://www.oracle.com/java/technologies/downloads/
- **Ruby** (2.7 or higher): Install from https://www.ruby-lang.org/
- **PHP** (8.0 or higher): Install from https://www.php.net/
- **Docker** (optional, for containerized deployment)
- **Docker Compose** (optional, for multi-container orchestration)

### Optional Tools
- **Git**: For version control
- **npm**: Package manager for Node.js (comes with Node.js)
- **pip**: Package manager for Python (comes with Python)
- **maven**: Build tool for Java (can be auto-installed with Java)
- **gem**: Package manager for Ruby (comes with Ruby)
- **composer**: Dependency manager for PHP

## Installation Methods

### Method 1: Automated Setup Script (Recommended)

Run the automated setup script to install all dependencies:

```bash
# Make the script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

This script will:
1. Check for required tools
2. Install all Node.js dependencies
3. Install all Python dependencies
4. Install all Java dependencies
5. Install all Ruby dependencies
6. Install all PHP dependencies
7. Create necessary configuration files

### Method 2: Manual Installation by Component

#### Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev

# Or build for production
npm run build

# Run tests
npm run test

# Lint code
npm run lint
```

#### Python Backend Setup

```bash
cd backend-python

# Create a virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

#### Java Backend Setup

```bash
cd backend-java

# Build with Maven
mvn clean install

# Run the application
mvn spring-boot:run

# Or run the JAR file
java -jar target/siem-platform-1.0.0.jar
```

#### Ruby Backend Setup

```bash
cd backend-ruby

# Install Bundler if not already installed
gem install bundler

# Install dependencies
bundle install

# Run the application
ruby app.rb
```

#### PHP Backend Setup

```bash
cd backend-php

# Install Composer if not already installed
# Visit https://getcomposer.org/download/ or run:
# curl -sS https://getcomposer.org/installer | php

# Install dependencies
composer install

# The PHP application requires a PHP server to run
# For development:
php -S localhost:8081
```

### Method 3: Docker Compose (Containerized)

```bash
# Build and start all services
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f <service-name>
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory using `.env.example` as a template:

```bash
cp .env.example .env
```

Configure the environment variables based on your setup:

```env
# Frontend Configuration
REACT_APP_API_URL=http://localhost:8080/api
VITE_API_URL=http://localhost:8080/api

# Python Backend Configuration
FLASK_ENV=development
DATABASE_URL=mongodb://localhost:27017/siem
POSTGRES_URL=postgresql://localhost:5432/siem
SECRET_KEY=your-secret-key-here

# Java Backend Configuration
SERVER_PORT=8080
SPRING_DATA_MONGODB_URI=mongodb://localhost:27017/siem
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/siem
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=password

# Ruby Backend Configuration
RACK_ENV=development
PORT=3000

# PHP Backend Configuration
ENVIRONMENT=development
DB_HOST=localhost
DB_USER=root
DB_PASS=password
```

### Database Setup

The platform requires:
- **MongoDB**: For log storage and correlations
- **PostgreSQL**: For structured data and analytics

#### MongoDB Setup

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally from https://www.mongodb.com/try/download/community
```

#### PostgreSQL Setup

```bash
# Using Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=siem \
  -e POSTGRES_PASSWORD=siem_password \
  -e POSTGRES_DB=siem \
  --name postgres \
  postgres:latest

# Or install locally from https://www.postgresql.org/download/
```

## Running the Full Application

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3001
# API: http://localhost:8080
# Python Service: http://localhost:5000
```

### Running Services Individually

Open multiple terminal windows and run each service:

**Terminal 1 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 2 - Python Backend:**
```bash
cd backend-python
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

**Terminal 3 - Java Backend:**
```bash
cd backend-java
mvn clean install
mvn spring-boot:run
```

**Terminal 4 - Ruby Backend (optional):**
```bash
cd backend-ruby
bundle install
ruby app.rb
```

**Terminal 5 - PHP Backend (optional):**
```bash
cd backend-php
composer install
php -S localhost:8081
```

## Verification

After installation, verify that all services are running:

1. **Frontend**: Visit http://localhost:3001
2. **Python API**: Visit http://localhost:5000/health
3. **Java API**: Visit http://localhost:8080/swagger-ui.html (Swagger documentation)
4. **PHP Service**: Visit http://localhost:8081/health.php

## Troubleshooting

### Port Already in Use

If a port is already in use, you can:
1. Change the port in the application configuration
2. Kill the process using the port:
   - Linux/macOS: `lsof -ti:PORT | xargs kill -9`
   - Windows: `netstat -ano | findstr :PORT` then `taskkill /PID <PID> /F`

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
mongo --eval "db.adminCommand('ping')"

# Or for newer MongoDB versions
mongosh --eval "db.adminCommand('ping')"
```

### Python Virtual Environment Issues

```bash
# Remove old virtual environment
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Java Compilation Errors

```bash
# Ensure Java 17 is installed
java -version

# Clear Maven cache
mvn clean

# Rebuild
mvn clean install
```

### Node.js Dependency Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf frontend/node_modules
cd frontend
npm install
```

## Running Tests

### Frontend Tests
```bash
cd frontend
npm test
```

### Python Tests
```bash
cd backend-python
pytest
```

### Java Tests
```bash
cd backend-java
mvn test
```

### Ruby Tests
```bash
cd backend-ruby
bundle install
rspec
```

## Linting and Code Quality

### Frontend Linting
```bash
cd frontend
npm run lint
npm run format
```

### Python Linting
```bash
cd backend-python
pip install flake8 black
flake8 .
black .
```

### Java Linting
```bash
cd backend-java
mvn checkstyle:check
```

## Next Steps

1. Review the README.md for architecture and feature documentation
2. Check the docs/ directory for API documentation
3. Set up your IDE/editor for development
4. Review the existing code structure and coding standards
5. Start developing features or fixes

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the GitHub issues
3. Consult the documentation in the docs/ directory
4. Open a new issue with detailed information about your problem

## Additional Resources

- Frontend: [Vite Documentation](https://vitejs.dev/), [React Documentation](https://react.dev/)
- Python: [Flask Documentation](https://flask.palletsprojects.com/), [PyMongo Documentation](https://pymongo.readthedocs.io/)
- Java: [Spring Boot Documentation](https://spring.io/projects/spring-boot), [Maven Documentation](https://maven.apache.org/)
- Ruby: [Sinatra Documentation](https://sinatrarb.com/), [Bundler Documentation](https://bundler.io/)
- PHP: [PHP Documentation](https://www.php.net/docs.php)
- Databases: [MongoDB Documentation](https://docs.mongodb.com/), [PostgreSQL Documentation](https://www.postgresql.org/docs/)
