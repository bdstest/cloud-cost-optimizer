# API Documentation

## Overview

The Cloud Cost Optimizer API provides comprehensive endpoints for cost analysis, optimization recommendations, and resource management across multi-cloud environments.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

### API Key Authentication
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8080/api/v1/costs
```

### JWT Token Authentication
```bash
curl -H "Authorization: Bearer JWT_TOKEN" \
     http://localhost:8080/api/v1/recommendations
```

## Core Endpoints

### Cost Analysis

#### Get Cost Summary
```http
GET /api/v1/costs/summary
```

**Parameters:**
- `period` (string): Time period - `day`, `week`, `month`, `quarter`, `year`
- `provider` (string): Cloud provider - `aws`, `azure`, `gcp`, `all`
- `service` (string): Service filter (optional)

**Response:**
```json
{
  "total_cost": 15420.50,
  "period": "month",
  "providers": {
    "aws": 8920.30,
    "azure": 4200.15,
    "gcp": 2300.05
  },
  "trend": {
    "percentage_change": -12.5,
    "direction": "decreasing"
  }
}
```

#### Get Detailed Cost Breakdown
```http
GET /api/v1/costs/breakdown
```

**Parameters:**
- `provider` (required): Cloud provider
- `start_date` (string): ISO date format
- `end_date` (string): ISO date format
- `group_by` (string): `service`, `region`, `resource_type`

**Response:**
```json
{
  "costs": [
    {
      "service": "EC2",
      "cost": 3420.50,
      "instances": 45,
      "usage_hours": 32400,
      "average_hourly_cost": 0.106
    },
    {
      "service": "RDS",
      "cost": 1250.30,
      "instances": 8,
      "storage_gb": 2048,
      "backup_cost": 125.50
    }
  ],
  "total": 4670.80
}
```

### Cost Optimization

#### Get Optimization Recommendations
```http
GET /api/v1/recommendations
```

**Parameters:**
- `provider` (string): Target cloud provider
- `severity` (string): `high`, `medium`, `low`
- `category` (string): `rightsizing`, `reserved_instances`, `unused_resources`

**Response:**
```json
{
  "recommendations": [
    {
      "id": "rec_001",
      "type": "rightsizing",
      "severity": "high",
      "resource_id": "i-0123456789abcdef0",
      "current_cost": 245.50,
      "optimized_cost": 122.75,
      "potential_savings": 122.75,
      "description": "Downsize EC2 instance from m5.large to m5.medium",
      "impact": "50% cost reduction with minimal performance impact",
      "implementation_effort": "low"
    }
  ],
  "total_potential_savings": 5420.30,
  "total_recommendations": 23
}
```

#### Apply Optimization
```http
POST /api/v1/recommendations/{recommendation_id}/apply
```

**Request Body:**
```json
{
  "confirm": true,
  "schedule": "2024-07-21T02:00:00Z",
  "notification_email": "admin@company.com"
}
```

**Response:**
```json
{
  "task_id": "task_001",
  "status": "scheduled",
  "estimated_completion": "2024-07-21T02:15:00Z",
  "rollback_available": true
}
```

### Resource Management

#### List Resources
```http
GET /api/v1/resources
```

**Parameters:**
- `provider` (required): Cloud provider
- `status` (string): `running`, `stopped`, `unused`
- `tag` (string): Resource tag filter

**Response:**
```json
{
  "resources": [
    {
      "id": "i-0123456789abcdef0",
      "type": "ec2_instance",
      "name": "web-server-01",
      "status": "running",
      "cost_per_hour": 0.096,
      "monthly_cost": 70.08,
      "utilization": {
        "cpu": 15.2,
        "memory": 42.8,
        "network": 5.1
      },
      "tags": {
        "Environment": "production",
        "Team": "backend"
      }
    }
  ]
}
```

#### Get Resource Details
```http
GET /api/v1/resources/{resource_id}
```

**Response:**
```json
{
  "resource": {
    "id": "i-0123456789abcdef0",
    "provider": "aws",
    "region": "us-east-1",
    "type": "ec2_instance",
    "instance_type": "m5.large",
    "state": "running",
    "launch_time": "2024-06-15T10:30:00Z",
    "cost_analytics": {
      "daily_cost": 2.30,
      "monthly_projection": 70.08,
      "yearly_projection": 840.96
    },
    "performance_metrics": {
      "cpu_utilization_avg": 15.2,
      "memory_utilization_avg": 42.8,
      "network_in_gb": 1.2,
      "network_out_gb": 0.8
    },
    "optimization_opportunities": [
      {
        "type": "rightsizing",
        "potential_savings": 35.04,
        "recommended_action": "Resize to m5.medium"
      }
    ]
  }
}
```

### Budget Management

#### Create Budget Alert
```http
POST /api/v1/budgets
```

**Request Body:**
```json
{
  "name": "Monthly AWS Budget",
  "provider": "aws",
  "limit": 10000.00,
  "period": "monthly",
  "alert_thresholds": [50, 80, 95],
  "notification_emails": ["admin@company.com"]
}
```

#### Get Budget Status
```http
GET /api/v1/budgets
```

**Response:**
```json
{
  "budgets": [
    {
      "id": "budget_001",
      "name": "Monthly AWS Budget",
      "limit": 10000.00,
      "current_spend": 6420.30,
      "percentage_used": 64.20,
      "status": "on_track",
      "forecast": {
        "end_of_period_spend": 8950.25,
        "percentage_forecast": 89.50,
        "trend": "under_budget"
      }
    }
  ]
}
```

### Analytics

#### Get Cost Trends
```http
GET /api/v1/analytics/trends
```

**Parameters:**
- `metric` (string): `cost`, `usage`, `efficiency`
- `period` (string): Time granularity
- `days` (number): Number of days to analyze

**Response:**
```json
{
  "trends": [
    {
      "date": "2024-07-01",
      "cost": 520.30,
      "usage_hours": 4320,
      "efficiency_score": 72.5
    }
  ],
  "summary": {
    "total_cost": 15420.30,
    "average_daily_cost": 497.10,
    "trend_direction": "decreasing",
    "efficiency_improvement": 12.5
  }
}
```

#### Get Anomaly Detection
```http
GET /api/v1/analytics/anomalies
```

**Response:**
```json
{
  "anomalies": [
    {
      "id": "anomaly_001",
      "detected_at": "2024-07-20T14:30:00Z",
      "resource_id": "i-0987654321fedcba0",
      "type": "cost_spike",
      "severity": "high",
      "description": "Unusual 300% cost increase detected",
      "baseline_cost": 125.50,
      "current_cost": 376.50,
      "potential_causes": [
        "Instance type changed",
        "High network usage",
        "Reserved instance expired"
      ]
    }
  ]
}
```

## Machine Learning Integration

### Cost Prediction
```http
POST /api/v1/ml/predict
```

**Request Body:**
```json
{
  "provider": "aws",
  "resource_type": "ec2",
  "forecast_days": 30,
  "parameters": {
    "instance_type": "m5.large",
    "region": "us-east-1",
    "usage_pattern": "standard"
  }
}
```

**Response:**
```json
{
  "prediction": {
    "daily_costs": [
      {"date": "2024-07-21", "cost": 2.30, "confidence": 0.95},
      {"date": "2024-07-22", "cost": 2.28, "confidence": 0.94}
    ],
    "total_forecast": 68.40,
    "savings_opportunities": [
      {
        "type": "reserved_instance",
        "potential_savings": 15.20,
        "confidence": 0.87
      }
    ]
  }
}
```

## Webhook Endpoints

### Cost Alert Webhook
```http
POST /api/v1/webhooks/cost-alert
```

Configure external systems to receive cost alerts:

**Webhook Payload:**
```json
{
  "event": "cost_threshold_exceeded",
  "timestamp": "2024-07-20T15:00:00Z",
  "budget_id": "budget_001",
  "current_spend": 8520.30,
  "threshold": 8000.00,
  "provider": "aws"
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "INVALID_PROVIDER",
    "message": "Unsupported cloud provider specified",
    "details": "Supported providers: aws, azure, gcp",
    "timestamp": "2024-07-20T15:30:00Z"
  }
}
```

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

- **Community**: 1000 requests per hour
- **Standard**: 5000 requests per hour
- **Enterprise**: 10000 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1595282400
```

## SDKs and Examples

### Python SDK
```python
from cloud_cost_optimizer import CostOptimizerClient

client = CostOptimizerClient(api_key="your_api_key")
recommendations = client.get_recommendations(provider="aws")
```

### cURL Examples
```bash
# Get cost summary
curl -H "Authorization: Bearer API_KEY" \
     "http://localhost:8080/api/v1/costs/summary?period=month"

# Apply recommendation
curl -X POST \
     -H "Authorization: Bearer API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"confirm": true}' \
     "http://localhost:8080/api/v1/recommendations/rec_001/apply"
```

