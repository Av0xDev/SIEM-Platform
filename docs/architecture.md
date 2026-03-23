# Architecture

## System Overview

The SIEM Platform is a polyglot microservices application for collecting, correlating, and alerting on security events.

## Services

| Service | Tech | Responsibility |
|---------|------|----------------|
| frontend | React 18 / Vite / Nginx | Dashboard, alert viewer, user management UI |
| backend-python | Flask, SQLAlchemy, Celery | Core event ingestion, correlation engine, REST API |
| backend-java | Spring Boot 3, Spring Security | Authentication, JWT issuance, analytics queries |
| backend-php | PHP 8.2, Apache | Webhook receivers, third-party integrations |
| backend-ruby | Sinatra, Puma, Sidekiq | Scheduled reports, digest emails |
| postgres | PostgreSQL 15 | Users, alerts, rules, audit logs |
| mongodb | MongoDB 6 | Raw event log storage |
| redis | Redis 7 | Session cache, task queues, rate-limiting |

## Data Flow

```
External Source ──► PHP Webhook ──► Python Core API ──► MongoDB (raw logs)
                                          │
                                   Correlation Engine
                                          │
                                   PostgreSQL (alerts)
                                          │
                              Java Analytics / Auth
                                          │
                                   React Frontend
```

## Security Architecture

- All inter-service traffic on isolated `siem-network` bridge; only required ports exposed to host.
- JWT tokens issued by Java service, validated by Python and Ruby services.
- Secrets injected via environment variables, never hard-coded.
- PHP webhook endpoints validate HMAC signatures using `WEBHOOK_SECRET`.
- Redis protected with password authentication.
- PostgreSQL and MongoDB credentials rotated per environment.

## Database Schema (PostgreSQL)

```
users          (id, email, password_hash, role, created_at)
alerts         (id, severity, source, message, rule_id, created_at, resolved_at)
rules          (id, name, query, threshold, window_seconds, enabled)
audit_logs     (id, user_id, action, resource, ip, timestamp)
```
