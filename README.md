# SIEM Platform

Enterprise-grade Security Information and Event Management (SIEM) platform with real-time alert correlation, security log aggregation, threat intelligence integration, and incident response automation.

## Quick Start

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Node.js** v18+ ([Download](https://nodejs.org/))
- **Python** 3.9+ ([Download](https://www.python.org/))
- **Java JDK** 17+ ([Download](https://www.oracle.com/java/technologies/downloads/))
- **Ruby** 2.7+ ([Download](https://www.ruby-lang.org/))
- **PHP** 8.0+ ([Download](https://www.php.net/))

### Installation

1. **Automated Setup (Recommended)**

   ```bash
   # Make the setup script executable and run it
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Manual Installation**

   See [INSTALL.md](INSTALL.md) for detailed manual installation instructions for each component.

### Running the Application

**Option A: Using Docker Compose (Easiest)**

```bash
# Start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3001
# - Java API: http://localhost:8080
# - Python API: http://localhost:5000
```

**Option B: Running Services Individually**

Open multiple terminal windows:

```bash
# Terminal 1: Frontend
cd frontend
npm install
npm run dev

# Terminal 2: Python Backend
cd backend-python
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py

# Terminal 3: Java Backend
cd backend-java
mvn spring-boot:run

# Terminal 4: Ruby Backend (Optional)
cd backend-ruby
bundle install
ruby app.rb

# Terminal 5: PHP Backend (Optional)
cd backend-php
composer install
php -S localhost:8081
```

### Using npm Scripts

```bash
# Install all dependencies
npm run install:all

# Run frontend in development mode
npm run dev

# Build all components
npm run build:all

# Run tests
npm run test:all

# Start services with Docker
npm run docker:up
```

## Project Structure

```
SIEM-Platform/
├── frontend/              # React + Vite web application
├── backend-python/        # Flask log processing service
├── backend-java/          # Spring Boot API gateway
├── backend-ruby/          # Sinatra-based service
├── backend-php/           # PHP webhook service
├── docs/                  # Documentation
├── INSTALL.md            # Detailed installation guide
├── setup.sh              # Automated setup script
├── docker-compose.yml    # Docker container orchestration
├── package.json          # Root npm scripts
└── .env.example          # Environment configuration template
```

## Architecture

The SIEM Platform uses a microservices architecture with the following components:

- **Frontend**: React-based web UI for dashboards and alerts
- **Python Backend**: Handles log ingestion, parsing, and correlation
- **Java Backend**: Provides REST API and analytics
- **Ruby Backend**: Event processing and automation
- **PHP Backend**: Webhook and third-party integrations

All services communicate via REST APIs and WebSockets for real-time updates.

## Databases

The platform uses:
- **MongoDB**: For log storage and flexible data models
- **PostgreSQL**: For structured analytics and relational data

Both are automatically set up via Docker Compose or can be installed separately.

## Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

See the file for all available configuration options.

## Documentation

- [INSTALL.md](INSTALL.md) - Detailed installation and configuration guide
- [docs/](docs/) - API documentation and architecture guides

## Features

- 🔒 Real-time security log aggregation from multiple sources
- 🔍 Advanced alert correlation and threat detection
- 🧠 Threat intelligence integration
- 📊 Security analytics and dashboards
- 🤖 Incident response automation
- 🔌 Extensible webhook system for integrations
- 📈 Scalable microservices architecture
- 🐳 Docker support for easy deployment

## Development

### Running Tests

```bash
# Frontend tests
cd frontend && npm test

# Python tests
cd backend-python && pytest

# Java tests
cd backend-java && mvn test

# Ruby tests
cd backend-ruby && rspec
```

### Code Quality

```bash
# Lint frontend
npm run lint

# Format frontend code
npm run format

# Python linting
cd backend-python && flake8 .
```

## Docker Commands

```bash
# Build services
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart <service-name>
```

## Troubleshooting

See [INSTALL.md](INSTALL.md) for troubleshooting common issues.

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For questions and support:
- Check the [documentation](docs/)
- Review the [installation guide](INSTALL.md)
- Open an issue on GitHub
