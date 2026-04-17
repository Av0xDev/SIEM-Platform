# Architecture Documentation

## System Overview

The SIEM Platform is built on a microservices architecture with specialized components for security monitoring, log processing, and incident response.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                   │
│         • Dashboard • Alerts • Threat Intelligence           │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
      WebSocket         REST API           REST API
         │                  │                  │
┌────────▼────────┐ ┌──────▼──────────────┐ ┌─▼──────────────┐
│ Nginx Reverse   │ │  Java Service      │ │  PHP Service   │
│ Proxy           │ │  (Port 8080)       │ │  (Port 8000)   │
└────────┬────────┘ └────────┬───────────┘ └──┬──────────────┘
         │                   │                 │
     ┌───▼───────────────────▼─────────┬──────▼────────┐
     │  Python Service (Port 5000)     │  Ruby Service │
     │  • Log Parser & Normalizer      │  (Port 3000)  │
     │  • Correlation Engine           │  • Automation │
     │  • Threat Intelligence          │  • Playbooks  │
     └──────┬────────────────────────┬──┴───────────────┘
            │                        │
    ┌───────▼──────────────────────▼──┐
    │   PostgreSQL + MongoDB           │
    │   • Users, Alerts, Incidents     │
    │   • Raw Logs, Correlations       │
    └─────────────────────────────────┘
```

## Component Descriptions

### 1. Frontend (React + Vite)
- **Purpose**: User interface for SIEM operations
- **Port**: 3001
- **Features**:
  - Real-time dashboard with WebSocket updates
  - Log viewer with advanced search
  - Alert management interface
  - Threat intelligence display
  - Incident response controls
- **Technology**: React 18, Vite, Chart.js, Socket.io

### 2. Java Service (Spring Boot)
- **Purpose**: Primary API gateway and core business logic
- **Port**: 8080
- **Features**:
  - User management and RBAC
  - Alert management
  - Incident tracking
  - REST API for all operations
  - PostgreSQL integration
  - OpenAPI/Swagger documentation
- **Database**: PostgreSQL (structured data)

### 3. Python Service (Flask)
- **Purpose**: Log processing and correlation engine
- **Port**: 5000
- **Features**:
  - Multi-format log parser (syslog, JSON, CEF, LEEF)
  - Log normalization
  - Real-time correlation engine
  - Threat intelligence enrichment
  - WebSocket server for live updates
  - Anomaly detection
- **Database**: MongoDB (raw logs and events)

### 4. PHP Service (Apache)
- **Purpose**: Webhook receiver for third-party integrations
- **Port**: 8000
- **Features**:
  - REST endpoint for webhook ingestion
  - Request validation
  - Event forwarding to Python service
  - Integration with external tools

### 5. Ruby Service (Sinatra)
- **Purpose**: Incident response automation
- **Port**: 3000
- **Features**:
  - Playbook execution engine
  - Automated response actions
  - Webhook integration
  - Scheduled correlation tasks
  - Escalation handling

### 6. Nginx Reverse Proxy
- **Purpose**: Central entry point, request routing, SSL termination
- **Port**: 80, 443
- **Features**:
  - Load balancing
  - WebSocket proxy
  - Security headers
  - Rate limiting
  - Gzip compression

### 7. PostgreSQL
- **Purpose**: Relational data storage
- **Tables**:
  - users, roles (RBAC)
  - alerts, incidents
  - audit_logs
  - threat_feeds

### 8. MongoDB
- **Purpose**: NoSQL storage for flexible data
- **Collections**:
  - logs (raw logs from all sources)
  - events (processed events)
  - correlations (detected patterns)
  - audit_trail

## Data Flow

### Log Ingestion Flow
1. External sources send logs to PHP webhook service
2. PHP validates and forwards to Python service
3. Python parser identifies log format (syslog, JSON, CEF, LEEF)
4. Parser normalizes log to standard schema
5. Log enriched with threat intelligence
6. Correlation engine checks for patterns
7. Results stored in MongoDB
8. Frontend notified via WebSocket

### Alert Correlation Flow
1. Python service receives parsed logs
2. Correlation engine groups related events
3. Detects patterns (brute force, port scan, data exfiltration)
4. Generates correlation alerts
5. Sends to Java service via REST API
6. Alerts displayed in frontend
7. Users can trigger automated responses

### Incident Response Flow
1. User initiates response from frontend
2. Request sent to Java API
3. Ruby automation service receives playbook request
4. Executes playbook actions (isolate host, block IP, etc.)
5. Logs all actions in audit trail
6. Updates incident status
7. Sends notifications to integrated tools

## Security Architecture

### Authentication
- JWT-based token authentication
- Token refresh mechanism
- Secure password hashing (bcrypt)

### Authorization
- Role-Based Access Control (RBAC)
- Three roles: Admin, Analyst, Viewer
- Resource-level permissions

### Data Protection
- TLS/SSL for all communications
- Encrypted database connections
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection (content security policy)

### Logging & Audit
- All actions logged in audit_logs table
- Immutable audit trail
- Timestamps for forensics
- User attribution for all changes

## Performance Characteristics

- **Log Ingestion**: 10,000+ logs/second
- **Query Response**: <100ms (p95)
- **Correlation Latency**: <1 second
- **Frontend Update**: <500ms via WebSocket
- **Memory per Service**: ~300-500MB (typical)

## Scalability Considerations

- Horizontal scaling of Python service (multiple replicas)
- Database indexing on common query fields
- Caching layer (Redis, optional)
- Connection pooling for database
- Load balancing at Nginx

## Deployment Architecture

### Development
- Docker Compose for local development
- All services in same network
- Hot reload for code changes

### Production
- Kubernetes orchestration
- Separate namespaces for services
- Auto-scaling based on metrics
- Health checks and auto-recovery
- Distributed databases (PostgreSQL HA, MongoDB replica sets)

## Integration Points

1. **External Log Sources**
   - Firewalls, IDS/IPS, proxies
   - Endpoint agents
   - Cloud services
   - Custom applications

2. **Threat Intelligence Feeds**
   - Public feeds (AlienVault OTX, etc.)
   - Commercial feeds
   - Internal threat data

3. **Response Actions**
   - SIEM platforms (Splunk, ELK)
   - SOAR systems
   - Ticketing systems (Jira, ServiceNow)
   - Communication tools (Slack, Teams)
   - Network devices (firewalls, switches)

## Monitoring & Observability

- Application metrics via Spring Actuator
- Structured logging (ELK stack compatible)
- Performance metrics (response times, throughput)
- Error rates and exceptions
- Service health checks

---

For more details, see:
- [API Reference](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Development Setup](DEVELOPMENT.md)