# Deployment Guide

## Local Deployment (Docker Compose)

The simplest way to deploy SIEM Platform locally:

```bash
cd SIEM-Platform
docker-compose up -d
```

This starts:
- PostgreSQL database
- MongoDB database
- Python log processing service
- Java API gateway
- PHP webhook service
- Ruby automation service
- React frontend
- Nginx reverse proxy

Access the platform at `http://localhost:80`

## Docker Compose Configuration

The `docker-compose.yml` includes:

```yaml
- PostgreSQL 15 (port 5432)
- MongoDB 6 (port 27017)
- Python Flask (port 5000)
- Java Spring Boot (port 8080)
- PHP Apache (port 8000)
- Ruby Sinatra (port 3000)
- React Frontend (port 3001)
- Nginx Reverse Proxy (port 80/443)
```

## Production Deployment

### AWS ECS + RDS

#### Prerequisites
- AWS account
- AWS CLI configured
- Docker image built and pushed to ECR

#### Steps

1. **Create ECR Repository**

```bash
aws ecr create-repository --repository-name siem-platform
```

2. **Build and Push Images**

```bash
# Build images
docker-compose build

# Tag and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

docker tag siem-platform:python <account>.dkr.ecr.<region>.amazonaws.com/siem-platform:python
docker push <account>.dkr.ecr.<region>.amazonaws.com/siem-platform:python
# Repeat for other services
```

3. **Create RDS Instances**

```bash
# PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier siem-postgres \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username siem_user \
  --master-user-password <secure-password> \
  --allocated-storage 100

# MongoDB (DocumentDB)
aws docdb create-db-cluster \
  --db-cluster-identifier siem-mongodb \
  --engine docdb \
  --master-username siem_user \
  --master-user-password <secure-password>
```

4. **Create ECS Cluster**

```bash
aws ecs create-cluster --cluster-name siem-platform
```

5. **Create Task Definitions**

Create task definition JSON for each service and register:

```bash
aws ecs register-task-definition --cli-input-json file://python-task-def.json
```

6. **Create Services**

```bash
aws ecs create-service \
  --cluster siem-platform \
  --service-name python-service \
  --task-definition siem-python:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (EKS, GKE, AKS)
- kubectl configured
- Helm (optional but recommended)

#### Create Namespace

```bash
kubectl create namespace siem
kubectl config set-context --current --namespace=siem
```

#### Create ConfigMaps

```bash
kubectl create configmap siem-config \
  --from-literal=PYTHON_SERVICE_URL=http://python:5000 \
  --from-literal=JAVA_SERVICE_URL=http://java:8080
```

#### Create Secrets

```bash
kubectl create secret generic siem-secrets \
  --from-literal=DB_PASSWORD=<secure-password> \
  --from-literal=JWT_SECRET=<jwt-secret>
```

#### Deploy Services

```yaml
# python-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: python
  template:
    metadata:
      labels:
        app: python
    spec:
      containers:
      - name: python
        image: <registry>/siem-platform:python
        ports:
        - containerPort: 5000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: siem-secrets
              key: mongodb-url
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

Apply all manifests:

```bash
kubectl apply -f k8s/
```

### Azure Kubernetes Service (AKS)

```bash
# Create resource group
az group create --name siem-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group siem-rg \
  --name siem-cluster \
  --node-count 3 \
  --enable-managed-identity \
  --network-plugin azure

# Get credentials
az aks get-credentials \
  --resource-group siem-rg \
  --name siem-cluster

# Deploy using kubectl
kubectl apply -f k8s/
```

## SSL/TLS Configuration

### Using Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem

# Update nginx.conf to use SSL
```

### Nginx SSL Configuration

In `nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
}
```

## Database Backup & Recovery

### PostgreSQL Backup

```bash
# Full backup
docker-compose exec postgres pg_dump -U siem_user siem_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U siem_user siem_db < backup.sql
```

### MongoDB Backup

```bash
# Full backup
docker-compose exec mongodb mongodump --username siem_user --authenticationDatabase admin --out /backup

# Restore
docker-compose exec mongodb mongorestore --username siem_user --authenticationDatabase admin /backup
```

## Monitoring & Logging

### Prometheus Metrics

Java service exposes metrics at `/actuator/prometheus`

```bash
# Add to prometheus.yml
scrape_configs:
  - job_name: 'siem-java'
    static_configs:
      - targets: ['localhost:8080']
```

### ELK Stack Integration

```bash
# Elasticsearch
docker run -d \
  --name elasticsearch \
  -e discovery.type=single-node \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Kibana
docker run -d \
  --name kibana \
  -p 5601:5601 \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  docker.elastic.co/kibana/kibana:8.0.0
```

Configure log shipping in services.

## Performance Tuning

### PostgreSQL

```sql
-- Increase work_mem for queries
ALTER SYSTEM SET work_mem = '256MB';

-- Enable parallel queries
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

SELECT pg_reload_conf();
```

### MongoDB

```javascript
// Create indexes
db.logs.createIndex({ timestamp: -1 });
db.logs.createIndex({ source: 1 });
db.logs.createIndex({ level: 1 });

// Enable compression
db.adminCommand({ setParameter: 1, wiredTigerEngineRuntimeConfig: 
  "cache_size=50GB,eviction_dirty_target=80" });
```

### Java

```bash
# Set heap size in docker-compose.yml
environment:
  - JAVA_OPTS=-Xms1g -Xmx2g -XX:+UseG1GC
```

## Health Checks

All services include health check endpoints:

```bash
# Frontend
http://localhost:3001

# Java API
http://localhost:8080/actuator/health

# Python API
http://localhost:5000/health

# PHP Service
http://localhost:8000/health.php

# Ruby Service
http://localhost:3000/health
```

## Rollback Procedures

### Docker Compose Rollback

```bash
# Check previous image
docker images | grep siem-platform

# Revert docker-compose.yml to previous version
git checkout HEAD~1 docker-compose.yml

# Restart services
docker-compose down
docker-compose up -d
```

### Kubernetes Rollback

```bash
# View deployment history
kubectl rollout history deployment/python-service

# Rollback to previous version
kubectl rollout undo deployment/python-service

# Rollback to specific revision
kubectl rollout undo deployment/python-service --to-revision=2
```

---

For more information, see the [Architecture Documentation](ARCHITECTURE.md).
