# Security Architecture

## Overview

The Cloud Cost Optimizer implements enterprise-grade security measures to protect sensitive financial and infrastructure data across multi-cloud environments.

## Security Principles

### Defense in Depth
Multiple layers of security controls:
- Network security (firewalls, VPCs)
- Application security (authentication, authorization)
- Data security (encryption, access controls)
- Infrastructure security (container security, secrets management)

### Zero Trust Architecture
- No implicit trust based on network location
- Verify every request and user
- Principle of least privilege access
- Continuous monitoring and validation

## Authentication and Authorization

### Multi-Factor Authentication (MFA)
```javascript
// MFA implementation with TOTP
const speakeasy = require('speakeasy');
const qrcode = require('qrcode');

class MFAService {
  generateSecret(user) {
    const secret = speakeasy.generateSecret({
      name: `CostOptimizer (${user.email})`,
      issuer: 'Cloud Cost Optimizer'
    });
    
    return {
      secret: secret.base32,
      qrCode: qrcode.toDataURL(secret.otpauth_url)
    };
  }
  
  verifyToken(secret, token) {
    return speakeasy.totp.verify({
      secret: secret,
      encoding: 'base32',
      token: token,
      window: 1
    });
  }
}
```

### Role-Based Access Control (RBAC)
```json
{
  "roles": {
    "admin": {
      "permissions": [
        "costs:read",
        "costs:write",
        "recommendations:read",
        "recommendations:apply",
        "users:manage",
        "settings:manage"
      ]
    },
    "manager": {
      "permissions": [
        "costs:read",
        "recommendations:read",
        "recommendations:apply",
        "budgets:manage"
      ]
    },
    "analyst": {
      "permissions": [
        "costs:read",
        "recommendations:read",
        "reports:generate"
      ]
    },
    "viewer": {
      "permissions": [
        "costs:read",
        "dashboards:view"
      ]
    }
  }
}
```

### JWT Token Security
```javascript
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

class JWTService {
  constructor() {
    this.secret = process.env.JWT_SECRET;
    this.algorithm = 'HS256';
    this.expiresIn = '24h';
  }
  
  generateToken(user) {
    const payload = {
      userId: user.id,
      email: user.email,
      roles: user.roles,
      permissions: this.getPermissions(user.roles),
      iat: Math.floor(Date.now() / 1000),
      jti: crypto.randomUUID() // Unique token ID for revocation
    };
    
    return jwt.sign(payload, this.secret, {
      algorithm: this.algorithm,
      expiresIn: this.expiresIn,
      issuer: 'cost-optimizer',
      audience: 'cost-optimizer-api'
    });
  }
  
  verifyToken(token) {
    try {
      const decoded = jwt.verify(token, this.secret, {
        algorithms: [this.algorithm],
        issuer: 'cost-optimizer',
        audience: 'cost-optimizer-api'
      });
      
      // Check if token is revoked
      if (this.isTokenRevoked(decoded.jti)) {
        throw new Error('Token has been revoked');
      }
      
      return decoded;
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
}
```

## Data Protection

### Encryption at Rest
```javascript
const crypto = require('crypto');

class EncryptionService {
  constructor() {
    this.algorithm = 'aes-256-gcm';
    this.keyLength = 32;
    this.ivLength = 16;
    this.tagLength = 16;
  }
  
  encrypt(text, key) {
    const iv = crypto.randomBytes(this.ivLength);
    const cipher = crypto.createCipher(this.algorithm, key, iv);
    
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const tag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('hex'),
      tag: tag.toString('hex')
    };
  }
  
  decrypt(encryptedData, key) {
    const decipher = crypto.createDecipher(
      this.algorithm,
      key,
      Buffer.from(encryptedData.iv, 'hex')
    );
    
    decipher.setAuthTag(Buffer.from(encryptedData.tag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }
}

// Database column encryption
class ColumnEncryption {
  static encryptSensitiveFields(data) {
    const sensitiveFields = ['api_keys', 'secrets', 'credentials'];
    const encrypted = { ...data };
    
    sensitiveFields.forEach(field => {
      if (encrypted[field]) {
        encrypted[field] = this.encrypt(encrypted[field]);
      }
    });
    
    return encrypted;
  }
}
```

### Encryption in Transit
```nginx
# nginx.conf - TLS configuration
server {
    listen 443 ssl http2;
    server_name cost-optimizer.company.com;
    
    # SSL/TLS configuration
    ssl_certificate /etc/ssl/certs/cost-optimizer.crt;
    ssl_certificate_key /etc/ssl/private/cost-optimizer.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'";
    
    location / {
        proxy_pass http://cost-optimizer-backend;
        proxy_ssl_verify on;
        proxy_ssl_trusted_certificate /etc/ssl/certs/ca-bundle.crt;
    }
}
```

## Secrets Management

### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cost-optimizer-secrets
type: Opaque
data:
  database-url: <base64-encoded-url>
  jwt-secret: <base64-encoded-secret>
  aws-access-key: <base64-encoded-key>
  aws-secret-key: <base64-encoded-secret>
```

### HashiCorp Vault Integration
```javascript
const vault = require('node-vault');

class VaultService {
  constructor() {
    this.client = vault({
      apiVersion: 'v1',
      endpoint: process.env.VAULT_ENDPOINT,
      token: process.env.VAULT_TOKEN
    });
  }
  
  async getSecret(path) {
    try {
      const result = await this.client.read(path);
      return result.data;
    } catch (error) {
      throw new Error(`Failed to retrieve secret: ${error.message}`);
    }
  }
  
  async storeSecret(path, data) {
    try {
      await this.client.write(path, data);
      return true;
    } catch (error) {
      throw new Error(`Failed to store secret: ${error.message}`);
    }
  }
}

// Usage in application
const vaultService = new VaultService();
const dbCredentials = await vaultService.getSecret('secret/database');
```

## API Security

### Rate Limiting
```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const Redis = require('ioredis');

// Redis client for distributed rate limiting
const redisClient = new Redis(process.env.REDIS_URL);

// Different rate limits for different endpoints
const createRateLimiter = (windowMs, max, message) => {
  return rateLimit({
    store: new RedisStore({
      sendCommand: (...args) => redisClient.call(...args)
    }),
    windowMs,
    max,
    message,
    standardHeaders: true,
    legacyHeaders: false,
    keyGenerator: (req) => {
      // Use user ID if authenticated, otherwise IP
      return req.user?.id || req.ip;
    }
  });
};

// Apply different limits
const strictLimiter = createRateLimiter(15 * 60 * 1000, 100, 'Too many requests');
const normalLimiter = createRateLimiter(15 * 60 * 1000, 1000, 'Rate limit exceeded');

app.use('/api/admin', strictLimiter);
app.use('/api/', normalLimiter);
```

### Input Validation and Sanitization
```javascript
const Joi = require('joi');
const xss = require('xss');

class ValidationService {
  static schemas = {
    costQuery: Joi.object({
      provider: Joi.string().valid('aws', 'azure', 'gcp').required(),
      startDate: Joi.date().iso().required(),
      endDate: Joi.date().iso().min(Joi.ref('startDate')).required(),
      granularity: Joi.string().valid('daily', 'weekly', 'monthly').default('daily')
    }),
    
    recommendation: Joi.object({
      resourceId: Joi.string().alphanum().max(100).required(),
      action: Joi.string().valid('resize', 'terminate', 'reserve').required(),
      confirm: Joi.boolean().required()
    })
  };
  
  static validate(schema, data) {
    const { error, value } = schema.validate(data, {
      abortEarly: false,
      stripUnknown: true
    });
    
    if (error) {
      throw new Error(`Validation error: ${error.details.map(d => d.message).join(', ')}`);
    }
    
    return value;
  }
  
  static sanitize(input) {
    if (typeof input === 'string') {
      return xss(input);
    }
    
    if (typeof input === 'object' && input !== null) {
      const sanitized = {};
      Object.keys(input).forEach(key => {
        sanitized[key] = this.sanitize(input[key]);
      });
      return sanitized;
    }
    
    return input;
  }
}

// Middleware usage
const validateAndSanitize = (schema) => {
  return (req, res, next) => {
    try {
      req.body = ValidationService.sanitize(req.body);
      req.body = ValidationService.validate(schema, req.body);
      next();
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  };
};
```

## Network Security

### Firewall Rules
```bash
# iptables rules for application server
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # HTTP (redirect to HTTPS)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # SSH (restrict to admin IPs)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -j DROP  # Drop all other traffic

# Cloud provider security groups
# AWS Security Group rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 22 \
  --cidr 10.0.0.0/8  # Restrict SSH to internal network
```

### VPC Configuration
```yaml
# AWS VPC setup with Terraform
resource "aws_vpc" "cost_optimizer_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "cost-optimizer-vpc"
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.cost_optimizer_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-west-2a"
  
  tags = {
    Name = "cost-optimizer-private"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.cost_optimizer_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "cost-optimizer-public"
  }
}
```

## Monitoring and Auditing

### Security Event Logging
```javascript
const winston = require('winston');

class SecurityLogger {
  constructor() {
    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.File({ 
          filename: 'logs/security.log',
          level: 'warn'
        }),
        new winston.transports.Console()
      ]
    });
  }
  
  logAuthEvent(event, user, request) {
    this.logger.info('Authentication Event', {
      event: event,
      userId: user?.id,
      email: user?.email,
      ip: request.ip,
      userAgent: request.get('User-Agent'),
      timestamp: new Date().toISOString()
    });
  }
  
  logSecurityAlert(alert, details) {
    this.logger.warn('Security Alert', {
      alert: alert,
      details: details,
      timestamp: new Date().toISOString()
    });
  }
  
  logDataAccess(user, resource, action) {
    this.logger.info('Data Access', {
      userId: user.id,
      resource: resource,
      action: action,
      timestamp: new Date().toISOString()
    });
  }
}
```

### Intrusion Detection
```javascript
class IntrusionDetection {
  constructor() {
    this.suspiciousPatterns = [
      /union.*select/i,  // SQL injection
      /<script.*>/i,     // XSS
      /\.\.\//,          // Path traversal
      /eval\(.*\)/i      // Code injection
    ];
    
    this.rateLimits = new Map();
  }
  
  detectSuspiciousActivity(request) {
    const alerts = [];
    
    // Check for malicious patterns
    const requestData = JSON.stringify(request.body) + request.url;
    this.suspiciousPatterns.forEach(pattern => {
      if (pattern.test(requestData)) {
        alerts.push({
          type: 'malicious_pattern',
          pattern: pattern.toString(),
          data: requestData
        });
      }
    });
    
    // Check for unusual access patterns
    const userKey = request.user?.id || request.ip;
    const now = Date.now();
    const window = 60000; // 1 minute
    
    if (!this.rateLimits.has(userKey)) {
      this.rateLimits.set(userKey, []);
    }
    
    const userRequests = this.rateLimits.get(userKey);
    userRequests.push(now);
    
    // Clean old requests
    const recentRequests = userRequests.filter(time => now - time < window);
    this.rateLimits.set(userKey, recentRequests);
    
    // Alert if too many requests
    if (recentRequests.length > 100) {
      alerts.push({
        type: 'rate_limit_exceeded',
        count: recentRequests.length,
        window: window
      });
    }
    
    return alerts;
  }
}
```

## Compliance and Governance

### SOC 2 Compliance
```javascript
class ComplianceService {
  static generateAuditTrail(action, user, resource, details) {
    return {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      action: action,
      user: {
        id: user.id,
        email: user.email,
        roles: user.roles
      },
      resource: resource,
      details: details,
      ip: details.ip,
      userAgent: details.userAgent
    };
  }
  
  static async logAuditEvent(auditTrail) {
    // Store in immutable audit log
    await database.auditLog.create(auditTrail);
    
    // Also send to external SIEM if configured
    if (process.env.SIEM_ENDPOINT) {
      await this.sendToSIEM(auditTrail);
    }
  }
}
```

### GDPR Compliance
```javascript
class GDPRService {
  static async handleDataRequest(type, userId) {
    switch (type) {
      case 'export':
        return await this.exportUserData(userId);
      case 'delete':
        return await this.deleteUserData(userId);
      case 'rectify':
        return await this.rectifyUserData(userId);
    }
  }
  
  static async exportUserData(userId) {
    const userData = await database.users.findById(userId);
    const costData = await database.costs.findByUser(userId);
    const auditLogs = await database.auditLog.findByUser(userId);
    
    return {
      personal_data: userData,
      cost_data: costData,
      audit_trail: auditLogs,
      export_date: new Date().toISOString()
    };
  }
  
  static async deleteUserData(userId) {
    // Anonymize rather than delete for audit trail integrity
    await database.users.anonymize(userId);
    await database.costs.anonymize(userId);
    
    // Keep audit logs but remove PII
    await database.auditLog.anonymizePII(userId);
    
    return { status: 'completed', date: new Date().toISOString() };
  }
}
```

## Incident Response

### Security Incident Playbook
```javascript
class IncidentResponse {
  static async handleSecurityIncident(incident) {
    const severity = this.assessSeverity(incident);
    
    // Immediate response
    if (severity === 'critical') {
      await this.emergencyResponse(incident);
    }
    
    // Create incident record
    const incidentRecord = await this.createIncidentRecord(incident, severity);
    
    // Notify security team
    await this.notifySecurityTeam(incidentRecord);
    
    // Begin investigation
    await this.startInvestigation(incidentRecord);
    
    return incidentRecord;
  }
  
  static async emergencyResponse(incident) {
    // Block malicious IP
    if (incident.type === 'brute_force' || incident.type === 'injection_attempt') {
      await this.blockIP(incident.source_ip);
    }
    
    // Revoke compromised tokens
    if (incident.type === 'token_compromise') {
      await this.revokeTokens(incident.user_id);
    }
    
    // Scale down if DDoS
    if (incident.type === 'ddos') {
      await this.enableDDoSProtection();
    }
  }
}
```

## Security Testing

### Automated Security Scanning
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run SAST
        uses: github/super-linter@v4
        env:
          VALIDATE_JAVASCRIPT_ES: true
          VALIDATE_TYPESCRIPT_ES: true
          
      - name: Run Dependency Check
        run: npm audit --audit-level moderate
        
      - name: Run Container Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: cost-optimizer:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
```

### Penetration Testing
```bash
# Automated penetration testing with OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:3000 \
  -J zap-report.json \
  -r zap-report.html
```