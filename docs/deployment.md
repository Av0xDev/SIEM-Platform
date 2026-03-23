# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2+
- 4 GB RAM minimum (8 GB recommended)
- Ports 3001, 5000, 8080, 8000, 3000, 5432, 27017, 6379 available

## Docker Deployment

```bash
git clone <repo-url> && cd SIEM-Platform
cp .env.example .env
# Set strong passwords and secrets in .env
docker compose up -d
docker compose ps   # verify all services healthy
```

## Production Considerations

1. **Secrets** — never commit `.env`. Use a secrets manager (Vault, AWS Secrets Manager).
2. **TLS** — place a reverse proxy (Nginx/Traefik) with TLS in front; do not expose services directly.
3. **Firewall** — restrict database ports (5432, 27017, 6379) to internal network only.
4. **Backups** — schedule `pg_dump` and `mongodump` to offsite storage.
5. **Resource limits** — add `deploy.resources.limits` to each service in docker-compose.yml.
6. **Log rotation** — configure Docker log driver with `max-size` and `max-file`.

## Environment Configuration

Copy `.env.example` to `.env` and update every `changeme` value before first run.

## Monitoring

- Python `/health`, Java `/actuator/health`, PHP `/health`, Ruby `/health` endpoints are wired into Docker health checks.
- Integrate with Prometheus by adding `prom/prometheus` service and scraping `/metrics` endpoints.
- Use Grafana for dashboards.
