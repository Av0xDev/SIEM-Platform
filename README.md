# SIEM Platform

A Security Information and Event Management (SIEM) platform built with a polyglot microservices architecture.

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │           SIEM Platform              │
                        └─────────────────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                           │
       ┌──────▼──────┐          ┌────────▼───────┐         ┌───────▼──────┐
       │  Frontend   │          │ Backend Python  │         │ Backend Java │
       │ React/Vite  │          │  Flask :5000    │         │ Spring :8080 │
       │   :3001     │          └────────┬───────┘         └───────┬──────┘
       └─────────────┘                   │                         │
                                         ▼                         │
       ┌─────────────┐          ┌─────────────────┐       ┌───────▼──────┐
       │ Backend PHP │          │   PostgreSQL     │       │   MongoDB    │
       │ Apache:8000 │          │     :5432        │       │    :27017    │
       └─────────────┘          └─────────────────┘       └─────────────┘
       ┌─────────────┐          ┌─────────────────┐
       │ Backend Ruby│          │     Redis        │
       │ Puma  :3000 │          │     :6379        │
       └─────────────┘          └─────────────────┘
```

## Features

- Real-time security event ingestion and correlation
- Multi-language microservices (Python, Java, PHP, Ruby)
- React dashboard with live alerting
- PostgreSQL for structured data, MongoDB for logs, Redis for caching/queues
- JWT authentication across all services
- Webhook integrations (PHP service)
- Scheduled reporting (Ruby service)

## Quick Start

```bash
cp .env.example .env
# Edit .env with your secrets
docker compose up -d
```

Access the dashboard at http://localhost:3001

## Services

| Service | Port | Language | Role |
|---------|------|----------|------|
| frontend | 3001 | React/Vite | Dashboard UI |
| backend-python | 5000 | Flask | Core API & event processing |
| backend-java | 8080 | Spring Boot | Auth & analytics |
| backend-php | 8000 | PHP/Apache | Webhooks & integrations |
| backend-ruby | 3000 | Sinatra/Puma | Scheduler & reporting |
| postgres | 5432 | PostgreSQL | Structured data |
| mongodb | 27017 | MongoDB | Log storage |
| redis | 6379 | Redis | Cache & queues |

## Development Setup

### Python
```bash
cd backend-python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
FLASK_ENV=development flask run
```

### Java
```bash
cd backend-java
mvn spring-boot:run
```

### PHP
```bash
cd backend-php
composer install
php -S localhost:8000 -t public/
```

### Ruby
```bash
cd backend-ruby
bundle install
bundle exec puma
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See [.env.example](.env.example) for all variables. Key secrets to rotate before deployment:
- `POSTGRES_PASSWORD`, `MONGO_PASSWORD`, `REDIS_PASSWORD`
- `SECRET_KEY`, `JWT_SECRET`, `WEBHOOK_SECRET`

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment](docs/deployment.md)
- [Development](docs/development.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for vulnerability disclosure policy.

## License

MIT License.
