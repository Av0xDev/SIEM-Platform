# API Reference

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

All requests require a JWT token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### Get Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400,
  "user": {
    "id": "user-123",
    "username": "admin",
    "role": "admin"
  }
}
```

## Logs

### Ingest Logs

```http
POST /api/v1/logs/ingest
Content-Type: application/json

{
  "logs": [
    {
      "timestamp": "2024-03-23T10:00:00Z",
      "source": "firewall-01",
      "message": "Connection blocked",
      "ip_address": "192.168.1.100",
      "port": 443
    }
  ]
}
```

**Response:**

```json
{
  "status": "success",
  "processed": 1,
  "correlations": 0
}
```

### Query Logs

```http
GET /api/v1/logs?limit=100&offset=0&level=error&source=firewall
```

**Response:**

```json
{
  "logs": [
    {
      "_id": "log-123",
      "timestamp": "2024-03-23T10:00:00Z",
      "source": "firewall-01",
      "message": "Connection blocked",
      "level": "warning",
      "ip_address": "192.168.1.100"
    }
  ],
  "total": 1542,
  "limit": 100,
  "offset": 0
}
```

### Search Logs

```http
GET /api/v1/logs/search?q=malware&limit=50
```

### Get Log Details

```http
GET /api/v1/logs/{id}
```

## Alerts

### Get All Alerts

```http
GET /api/v1/alerts?page=0&size=20&severity=high
```

**Response:**

```json
{
  "alerts": [
    {
      "id": "alert-123",
      "type": "brute_force",
      "severity": "high",
      "source_ip": "192.168.1.100",
      "event_count": 15,
      "created_at": "2024-03-23T10:00:00Z",
      "status": "open"
    }
  ],
  "total": 45,
  "page": 0,
  "size": 20
}
```

### Get Alert Details

```http
GET /api/v1/alerts/{id}
```

### Acknowledge Alert

```http
POST /api/v1/alerts/{id}/acknowledge
Content-Type: application/json

{
  "notes": "Investigating this issue"
}
```

### Resolve Alert

```http
POST /api/v1/alerts/{id}/resolve
Content-Type: application/json

{
  "resolution": "False positive",
  "notes": "Not a security issue"
}
```

## Correlations

### Get Correlations

```http
GET /api/v1/correlations?limit=50
```

**Response:**

```json
{
  "correlations": [
    {
      "id": "corr-123",
      "type": "port_scan",
      "severity": "high",
      "source": "192.168.1.100",
      "ports_scanned": 50,
      "timestamp": "2024-03-23T10:05:00Z",
      "related_logs": ["log-1", "log-2", "log-3"]
    }
  ]
}
```

## Threat Intelligence

### Check IP Reputation

```http
GET /api/v1/threat-intel/check-ip/{ip}
```

**Response:**

```json
{
  "ip": "192.168.1.100",
  "malicious": false,
  "reputation": "trusted",
  "feeds": []
}
```

### Check Domain

```http
GET /api/v1/threat-intel/check-domain/{domain}
```

### Batch Check Indicators

```http
POST /api/v1/threat-intel/check
Content-Type: application/json

{
  "ips": ["192.168.1.100", "10.0.0.1"],
  "domains": ["example.com"],
  "hashes": ["abc123def456"]
}
```

**Response:**

```json
{
  "ips": {
    "192.168.1.100": {
      "malicious": false,
      "reputation": "unknown"
    }
  },
  "domains": {
    "example.com": {
      "malicious": false,
      "reputation": "trusted"
    }
  }
}
```

## Incidents

### Create Incident

```http
POST /api/v1/incidents
Content-Type: application/json

{
  "title": "Brute Force Attack",
  "description": "Multiple failed login attempts",
  "severity": "high",
  "source_ip": "192.168.1.100"
}
```

### Get Incidents

```http
GET /api/v1/incidents?status=open&severity=high
```

### Update Incident

```http
PUT /api/v1/incidents/{id}
Content-Type: application/json

{
  "status": "investigating",
  "assigned_to": "analyst-1"
}
```

### Trigger Response

```http
POST /api/v1/incidents/{id}/respond
Content-Type: application/json

{
  "playbook_id": "isolate_host",
  "parameters": {
    "host_ip": "192.168.1.100"
  }
}
```

**Response:**

```json
{
  "status": "success",
  "action": "isolate_host",
  "execution_time": "2.5s",
  "result": {
    "status": "success",
    "message": "Host isolated successfully"
  }
}
```

## Automation

### Get Available Playbooks

```http
GET /api/v1/playbooks
```

**Response:**

```json
{
  "playbooks": [
    {
      "id": "isolate_host",
      "name": "Isolate Host",
      "description": "Remove host from network",
      "parameters": {
        "host_ip": "string"
      }
    },
    {
      "id": "block_ip",
      "name": "Block IP",
      "description": "Add IP to firewall blocklist",
      "parameters": {
        "source_ip": "string"
      }
    }
  ]
}
```

### Execute Playbook

```http
POST /api/v1/playbooks/{id}/execute
Content-Type: application/json

{
  "incident_id": "incident-123",
  "parameters": {
    "host_ip": "192.168.1.100"
  }
}
```

## Users

### Get Current User

```http
GET /api/v1/users/me
```

### List Users

```http
GET /api/v1/users?role=analyst
```

### Create User

```http
POST /api/v1/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure-password",
  "role": "analyst"
}
```

## Audit

### Get Audit Logs

```http
GET /api/v1/audit?limit=100&user_id=user-123
```

**Response:**

```json
{
  "logs": [
    {
      "id": "audit-123",
      "user_id": "user-123",
      "action": "alert_acknowledged",
      "resource": "alert-456",
      "timestamp": "2024-03-23T10:00:00Z",
      "details": {"notes": "Investigating"}
    }
  ],
  "total": 523
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-03-23T10:00:00Z"
}
```

### Common Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict
- `500` - Internal Server Error

## Rate Limiting

API requests are rate limited to prevent abuse:

- **Standard**: 100 requests per minute
- **Burst**: 500 requests per minute (for authenticated users)

Rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1711270860
```

---

For complete OpenAPI specification, visit `/swagger-ui.html` on the Java service.
