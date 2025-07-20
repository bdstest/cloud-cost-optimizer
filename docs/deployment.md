# Deployment Guide

## Overview

This guide covers production deployment of Cloud Cost Optimizer across enterprise environments.

## Prerequisites

### System Requirements
- **CPU**: 8+ cores (16+ recommended)
- **RAM**: 16 GB minimum (32+ GB recommended)
- **Storage**: 100 GB SSD (500+ GB for large deployments)
- **Network**: 1 Gbps connectivity

### Software Dependencies
- Docker 24+ or Kubernetes 1.25+
- PostgreSQL 14+ with TimescaleDB
- Redis 6+
- Node.js 18+ (for frontend)
- Python 3.9+ (for ML models)

## Deployment Options

### Option 1: Docker Compose (Development/Small Production)

```bash
# Clone repository
git clone https://github.com/bdstest/cloud-cost-optimizer
cd cloud-cost-optimizer

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy with Docker Compose
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:3000/health
```

### Option 2: Kubernetes (Enterprise Production)

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-optimizer-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cost-optimizer-api
  template:
    metadata:
      labels:
        app: cost-optimizer-api
    spec:
      containers:
      - name: api
        image: cost-optimizer:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cost-optimizer-secrets
              key: database-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Option 3: Cloud-Native Deployment

#### AWS ECS with Fargate
```json
{
  "family": "cost-optimizer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "cost-optimizer-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/cost-optimizer:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ]
    }
  ]
}
```

## Configuration

### Environment Variables
```bash
# Application Settings
APP_PORT=8080
NODE_ENV=production
LOG_LEVEL=info

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/cost_optimizer
REDIS_URL=redis://localhost:6379

# Cloud Provider Credentials
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_secret
GCP_SERVICE_ACCOUNT_KEY=path/to/service-account.json

# Machine Learning Settings
ML_MODEL_PATH=/app/models
ML_INFERENCE_BATCH_SIZE=100
ML_PREDICTION_CACHE_TTL=3600

# Security Settings
JWT_SECRET=your_jwt_secret
API_RATE_LIMIT=1000
CORS_ORIGIN=https://your-domain.com
```

### Database Setup

#### PostgreSQL with TimescaleDB
```sql
-- Create database
CREATE DATABASE cost_optimizer;

-- Install TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create hypertables for time-series data
SELECT create_hypertable('cost_data', 'timestamp');
SELECT create_hypertable('usage_metrics', 'timestamp');

-- Create indexes for performance
CREATE INDEX idx_cost_data_provider ON cost_data(provider, timestamp);
CREATE INDEX idx_usage_metrics_resource ON usage_metrics(resource_id, timestamp);
```

## Security Configuration

### SSL/TLS Setup
```bash
# Generate certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key -out ssl/certificate.crt

# Configure nginx
server {
    listen 443 ssl http2;
    server_name cost-optimizer.company.com;
    
    ssl_certificate /etc/ssl/certificate.crt;
    ssl_certificate_key /etc/ssl/private.key;
    
    location / {
        proxy_pass http://cost-optimizer-api:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Authentication Setup
```javascript
// Configure JWT authentication
const jwtConfig = {
  secret: process.env.JWT_SECRET,
  expiresIn: '24h',
  issuer: 'cost-optimizer',
  audience: 'cost-optimizer-users'
};

// Configure OAuth providers
const oauthConfig = {
  google: {
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: '/auth/google/callback'
  },
  microsoft: {
    clientID: process.env.MICROSOFT_CLIENT_ID,
    clientSecret: process.env.MICROSOFT_CLIENT_SECRET,
    callbackURL: '/auth/microsoft/callback'
  }
};
```

## Monitoring and Observability

### Prometheus Metrics
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cost-optimizer'
    static_configs:
      - targets: ['cost-optimizer-api:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Health Checks
```javascript
// Health check endpoint
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    checks: {
      database: await checkDatabase(),
      redis: await checkRedis(),
      cloudProviders: await checkCloudConnections(),
      mlModels: await checkMLModels()
    }
  };
  
  const isHealthy = Object.values(health.checks).every(check => check.status === 'ok');
  res.status(isHealthy ? 200 : 503).json(health);
});
```

### Logging Configuration
```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});
```

## Scaling and Performance

### Horizontal Scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cost-optimizer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cost-optimizer-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Optimization
```sql
-- Optimize PostgreSQL for time-series workload
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '64MB';
SELECT pg_reload_conf();

-- Set up compression for old data
SELECT add_compression_policy('cost_data', INTERVAL '7 days');
SELECT add_retention_policy('cost_data', INTERVAL '2 years');
```

### Caching Strategy
```javascript
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

// Cache frequently accessed data
const cacheConfig = {
  costSummary: { ttl: 3600 }, // 1 hour
  recommendations: { ttl: 1800 }, // 30 minutes
  resourceList: { ttl: 600 }, // 10 minutes
  mlPredictions: { ttl: 7200 } // 2 hours
};

async function getCachedData(key, fetchFunction, ttl) {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);
  
  const data = await fetchFunction();
  await redis.setex(key, ttl, JSON.stringify(data));
  return data;
}
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup-database.sh
BACKUP_DIR="/backups/cost-optimizer"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump $DATABASE_URL | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" s3://your-backup-bucket/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Disaster Recovery
```bash
#!/bin/bash
# restore-database.sh
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

# Stop application
kubectl scale deployment cost-optimizer-api --replicas=0

# Restore database
gunzip -c "$BACKUP_FILE" | psql $DATABASE_URL

# Restart application
kubectl scale deployment cost-optimizer-api --replicas=3
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage by component
docker stats cost-optimizer-api
kubectl top pods

# Optimize ML model memory usage
export ML_INFERENCE_BATCH_SIZE=50
export ML_MODEL_CACHE_SIZE=100MB
```

#### Database Performance
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_cost_data_composite 
ON cost_data(provider, service, timestamp);
```

#### API Rate Limiting
```javascript
// Configure rate limiting
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // requests per window
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/api/', limiter);
```

## Production Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database schema migrated
- [ ] Cloud provider credentials validated
- [ ] ML models trained and deployed
- [ ] Monitoring dashboards configured
- [ ] Backup procedures tested

### Post-deployment
- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Cost data ingestion verified
- [ ] User authentication functional
- [ ] ML predictions generating
- [ ] Alerts configured
- [ ] Documentation updated

### Security Checklist
- [ ] API endpoints secured
- [ ] Database access restricted
- [ ] Secrets management implemented
- [ ] Network policies configured
- [ ] Audit logging enabled
- [ ] Vulnerability scanning completed