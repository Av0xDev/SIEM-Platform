# API Documentation

## Authentication

All protected endpoints require `Authorization: Bearer <JWT>` header. Obtain tokens from the Java service.

### POST /api/auth/login (Java :8080)
```json
Request:  { "email": "user@example.com", "password": "secret" }
Response: { "token": "<jwt>", "expires_in": 3600 }
```

---

## Python Service (:5000)

### GET /health
Returns `{ "status": "ok" }`

### GET /api/events
Query recent events. Params: `limit`, `offset`, `severity`.

### POST /api/events
Ingest a new event.
```json
{ "source": "firewall", "severity": "high", "message": "Port scan detected", "metadata": {} }
```

### GET /api/alerts
List active alerts.

### POST /api/alerts/:id/resolve
Mark an alert resolved.

---

## Java Service (:8080)

### GET /actuator/health
Spring Boot health endpoint.

### POST /api/auth/login
Issue JWT (see above).

### GET /api/analytics/summary
Returns event counts by severity for the last 24 hours.

---

## PHP Service (:8000)

### GET /health
Returns `{"status":"ok"}`

### POST /webhooks/generic
Receive generic webhook payloads. Validates `X-Hub-Signature-256` HMAC header.

### POST /webhooks/pagerduty
PagerDuty event integration endpoint.

---

## Ruby Service (:3000)

### GET /health
Returns `{"status":"ok"}`

### POST /api/reports/generate
Trigger an on-demand report. Body: `{ "type": "daily_summary", "email": "ops@example.com" }`

---

## Frontend (:3001)

Static React SPA served by Nginx. All API calls proxied through Nginx to backend services.
