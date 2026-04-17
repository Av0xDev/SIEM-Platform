# Security Best Practices

## Overview

This document outlines security practices for the SIEM Platform.

## Authentication & Authorization

### JWT Token Security

- Tokens expire after 24 hours
- Use secure random secret key (minimum 32 characters)
- Store secret in environment variable, not in code
- Rotate secrets regularly

```python
# Good
SECRET_KEY = os.getenv('JWT_SECRET')

# Bad
SECRET_KEY = 'hardcoded-secret'
```

### Password Security

- Minimum 12 characters
- Require uppercase, lowercase, numbers, special characters
- Hash with bcrypt (minimum 12 rounds)
- Never log passwords

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
hashed = generate_password_hash(password, method='pbkdf2:sha256')

# Verify password
if check_password_hash(hashed, password):
    # Password correct
```

### RBAC Implementation

Three roles with specific permissions:

- **Admin**: Full access, user management
- **Analyst**: View/manage alerts and incidents
- **Viewer**: Read-only access

```java
@PreAuthorize("hasRole('ADMIN')")
@PostMapping("/users")
public ResponseEntity createUser(@RequestBody UserRequest request) {
    // Only admins can create users
}
```

## Data Protection

### Database Security

- Use strong passwords (minimum 20 characters)
- Enable SSL/TLS for database connections
- Restrict database access by IP
- Regular backups with encryption
- Encrypt sensitive fields in database

```python
DATABASE_URL = 'postgresql://user:password@host:5432/db?sslmode=require'
```

### Encryption

- TLS 1.2+ for all communications
- Encrypt sensitive data at rest
- Use secure cipher suites
- Certificate pinning for APIs

### API Security

- HTTPS only (force redirect from HTTP)
- HSTS header with max-age=31536000
- Content Security Policy headers
- CORS restricted to known origins

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
```

## Input Validation

### SQL Injection Prevention

Use parameterized queries:

```python
# Good
cursor.execute("SELECT * FROM logs WHERE source = %s", (source,))

# Bad
cursor.execute(f"SELECT * FROM logs WHERE source = '{source}'")
```

### XSS Prevention

- Validate and sanitize all user input
- Use templating engine that auto-escapes
- Content Security Policy

```html
<!-- Good: Variables escaped -->
<p>{{ user_input }}</p>

<!-- Bad: Raw HTML -->
<p>{{ user_input | safe }}</p>
```

### Command Injection Prevention

```python
# Good: Use subprocess with list of args
import subprocess
subprocess.run(['ping', '-c', '1', hostname])

# Bad: Shell=True allows injection
os.system(f'ping -c 1 {hostname}')
```

## Logging & Monitoring

### What to Log

- Authentication attempts (success/failure)
- Authorization failures
- Data access and modifications
- Configuration changes
- System errors

### What NOT to Log

- Passwords or API keys
- Sensitive personal data
- Health records
- Credit card numbers
- Authentication tokens

```python
# Good: Log without sensitive data
logger.info(f"User {username} logged in from {ip_address}")

# Bad: Logging password
logger.info(f"User {username} logged in with password {password}")
```

### Audit Trail

All user actions logged with:
- User ID and username
- Action performed
- Resource affected
- Timestamp
- Result (success/failure)

```python
audit_log = {
    'user_id': user.id,
    'action': 'alert_resolved',
    'resource': alert_id,
    'timestamp': datetime.utcnow(),
    'details': {...}
}
db.audit_logs.insert_one(audit_log)
```

## Infrastructure Security

### Network Security

- Firewall rules restrict access
- Network segmentation (VPC)
- Security groups for containers
- No services exposed to internet except Nginx

```bash
# Firewall rule example (AWS)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

### Container Security

- Use minimal base images (Alpine Linux)
- Don't run containers as root
- Regular vulnerability scanning (Trivy, Clair)
- Image signing with Notary

```dockerfile
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
USER appuser
```

### Kubernetes Security

- Network policies restrict pod-to-pod communication
- RBAC for service accounts
- Pod security policies
- Secret management (HashiCorp Vault)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: siem-network-policy
spec:
  podSelector:
    matchLabels:
      app: python
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx
```

## Secrets Management

### Environment Variables

```bash
# Never commit secrets
echo '.env' >> .gitignore

# Use secure storage
export JWT_SECRET=$(openssl rand -base64 32)
export DB_PASSWORD=$(openssl rand -base64 16)
```

### HashiCorp Vault

```bash
# Integrate with Vault
vault kv get secret/siem/db-password
vault kv get secret/siem/jwt-secret
```

### Kubernetes Secrets

```bash
kubectl create secret generic siem-secrets \
  --from-literal=db-password=<password>

kubectl get secret siem-secrets -o yaml
```

## Vulnerability Management

### Dependency Scanning

```bash
# Python
pip install safety
safety check

# Java
mvn dependency-check:check

# Node.js
npm audit
```

### SAST (Static Analysis)

```bash
# Python
pip install bandit
bandit -r .

# Java
mvn sonar:sonar
```

### DAST (Dynamic Analysis)

```bash
# OWASP ZAP
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t http://localhost
```

## Incident Response

### Breach Detection

- Monitor failed authentication attempts
- Alert on privilege escalation
- Track data access patterns
- Monitor for indicators of compromise

### Incident Handling

1. **Detect**: Automated alerts trigger
2. **Respond**: Execute playbooks automatically
3. **Contain**: Isolate affected systems
4. **Investigate**: Gather logs and evidence
5. **Recover**: Restore from backups
6. **Review**: Post-incident analysis

## Compliance

### Standards Supported

- NIST Cybersecurity Framework
- CIS Controls
- PCI-DSS (for payment data)
- HIPAA (for health data)
- GDPR (for personal data)

### Data Retention

- Logs: 90 days (configurable)
- Alerts: 365 days
- Incidents: Indefinite (for forensics)
- Audit logs: 3 years (compliance)

```python
# Delete old logs
db.logs.delete_many({
    'timestamp': {'$lt': datetime.utcnow() - timedelta(days=90)}
})
```

## Security Checklist

- [ ] All passwords meet complexity requirements
- [ ] SSH keys generated and secured
- [ ] TLS certificates installed and valid
- [ ] Firewall rules configured
- [ ] CORS restricted to known origins
- [ ] Secrets in environment variables
- [ ] Database encryption enabled
- [ ] Backup strategy implemented
- [ ] Vulnerability scans passing
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] HTTPS enforced
- [ ] Security headers set
- [ ] Regular security updates scheduled
- [ ] Incident response plan documented

---

For security issues, please email security@example.com (do not create public GitHub issues).
