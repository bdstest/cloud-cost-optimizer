from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import asyncio
import json
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid Cloud Cost Optimizer",
    description="Enterprise-grade multi-cloud cost optimization platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
COST_SAVINGS_TOTAL = Counter('cost_savings_total_usd', 'Total cost savings in USD')

# Security
security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "demo-key-sk-cloudcost123456")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Sample data generation
def generate_sample_cost_data():
    """Generate realistic sample cost data for demo purposes"""
    current_date = datetime.now()
    data = []
    
    # AWS sample data
    for i in range(90):  # 90 days of data
        date = current_date - timedelta(days=i)
        aws_cost = 15000 + (i * 50) + (i % 7) * 2000  # Trend with weekly patterns
        azure_cost = 12000 + (i * 40) + (i % 5) * 1500
        onprem_cost = 8000 + (i * 20) + (i % 10) * 500
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "provider": "aws",
            "service": "ec2",
            "cost": aws_cost * 0.4,
            "usage_hours": 24 * 100,
            "resource_count": 100
        })
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "provider": "aws", 
            "service": "rds",
            "cost": aws_cost * 0.3,
            "usage_hours": 24 * 20,
            "resource_count": 20
        })
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "provider": "azure",
            "service": "compute",
            "cost": azure_cost * 0.5,
            "usage_hours": 24 * 80,
            "resource_count": 80
        })
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "provider": "onpremises",
            "service": "vmware",
            "cost": onprem_cost,
            "usage_hours": 24 * 50,
            "resource_count": 50
        })
    
    return data

# Global sample data
SAMPLE_DATA = generate_sample_cost_data()

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "up",
            "redis": "up", 
            "ml_models": "up"
        },
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/costs/summary")
async def get_cost_summary(api_key: str = Depends(verify_api_key)):
    """Get cost summary across all providers"""
    df = pd.DataFrame(SAMPLE_DATA)
    
    # Calculate current month costs
    current_month = datetime.now().strftime("%Y-%m")
    current_month_data = df[df['date'].str.startswith(current_month)]
    
    # Previous month for comparison
    prev_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m")
    prev_month_data = df[df['date'].str.startswith(prev_month)]
    
    current_total = current_month_data['cost'].sum()
    prev_total = prev_month_data['cost'].sum()
    
    savings_pct = ((prev_total - current_total) / prev_total * 100) if prev_total > 0 else 0
    
    # Update savings counter
    if savings_pct > 0:
        COST_SAVINGS_TOTAL.inc(prev_total - current_total)
    
    return {
        "current_month_cost": round(current_total, 2),
        "previous_month_cost": round(prev_total, 2),
        "savings_percentage": round(savings_pct, 1),
        "savings_amount": round(prev_total - current_total, 2),
        "providers": {
            "aws": round(current_month_data[current_month_data['provider'] == 'aws']['cost'].sum(), 2),
            "azure": round(current_month_data[current_month_data['provider'] == 'azure']['cost'].sum(), 2),
            "onpremises": round(current_month_data[current_month_data['provider'] == 'onpremises']['cost'].sum(), 2)
        },
        "top_services": [
            {"service": "ec2", "cost": round(current_month_data[current_month_data['service'] == 'ec2']['cost'].sum(), 2)},
            {"service": "compute", "cost": round(current_month_data[current_month_data['service'] == 'compute']['cost'].sum(), 2)},
            {"service": "rds", "cost": round(current_month_data[current_month_data['service'] == 'rds']['cost'].sum(), 2)},
            {"service": "vmware", "cost": round(current_month_data[current_month_data['service'] == 'vmware']['cost'].sum(), 2)}
        ]
    }

@app.get("/api/costs/trend")
async def get_cost_trend(days: int = 30, api_key: str = Depends(verify_api_key)):
    """Get cost trend data for specified number of days"""
    df = pd.DataFrame(SAMPLE_DATA)
    
    # Filter to requested days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    filtered_data = df[
        (pd.to_datetime(df['date']) >= start_date) & 
        (pd.to_datetime(df['date']) <= end_date)
    ]
    
    # Group by date and sum costs
    daily_costs = filtered_data.groupby('date')['cost'].sum().reset_index()
    
    return {
        "trend_data": [
            {
                "date": row['date'],
                "total_cost": round(row['cost'], 2)
            }
            for _, row in daily_costs.iterrows()
        ],
        "average_daily_cost": round(daily_costs['cost'].mean(), 2),
        "total_period_cost": round(daily_costs['cost'].sum(), 2)
    }

@app.get("/api/optimization/recommendations")
async def get_recommendations(api_key: str = Depends(verify_api_key)):
    """Get cost optimization recommendations"""
    
    # Simulate ML-generated recommendations
    recommendations = [
        {
            "id": "rec-001",
            "type": "rightsizing",
            "provider": "aws",
            "service": "ec2",
            "resource_id": "i-0123456789abcdef0",
            "current_instance": "m5.4xlarge",
            "recommended_instance": "m5.large",
            "current_cost": 560.16,
            "projected_cost": 70.02,
            "monthly_savings": 490.14,
            "utilization": 25,
            "confidence": 0.92,
            "description": "Instance is severely under-utilized with 25% CPU usage",
            "impact": "high"
        },
        {
            "id": "rec-002", 
            "type": "reserved_instance",
            "provider": "azure",
            "service": "compute",
            "resource_id": "vm-standard-d4s-v4",
            "current_pricing": "pay_as_you_go",
            "recommended_pricing": "3_year_reserved",
            "current_cost": 175.20,
            "projected_cost": 89.50,
            "monthly_savings": 85.70,
            "commitment_years": 3,
            "confidence": 0.87,
            "description": "Consistent usage pattern suitable for reserved instance",
            "impact": "medium"
        },
        {
            "id": "rec-003",
            "type": "storage_optimization", 
            "provider": "aws",
            "service": "s3",
            "resource_id": "bucket-analytics-logs",
            "current_storage_class": "standard",
            "recommended_storage_class": "intelligent_tiering",
            "current_cost": 245.80,
            "projected_cost": 147.48,
            "monthly_savings": 98.32,
            "access_pattern": "infrequent",
            "confidence": 0.78,
            "description": "Objects accessed less than once per month",
            "impact": "medium"
        }
    ]
    
    total_savings = sum(rec['monthly_savings'] for rec in recommendations)
    
    return {
        "recommendations": recommendations,
        "total_monthly_savings": round(total_savings, 2),
        "total_annual_savings": round(total_savings * 12, 2),
        "high_impact_count": len([r for r in recommendations if r['impact'] == 'high']),
        "medium_impact_count": len([r for r in recommendations if r['impact'] == 'medium']),
        "low_impact_count": len([r for r in recommendations if r['impact'] == 'low'])
    }

@app.get("/api/forecasting/predict")
async def get_cost_forecast(days: int = 30, api_key: str = Depends(verify_api_key)):
    """Get cost forecast using Prophet model"""
    
    # Simulate Prophet forecasting results
    base_cost = 35000  # Current monthly average
    growth_rate = 0.02  # 2% monthly growth
    
    forecast_data = []
    for i in range(1, days + 1):
        date = datetime.now() + timedelta(days=i)
        
        # Add trend, seasonality, and some noise
        trend_factor = 1 + (growth_rate * i / 30)
        seasonal_factor = 1 + 0.1 * (i % 7) / 7  # Weekly seasonality
        noise_factor = 1 + 0.05 * ((i % 3) - 1) / 3  # Random variation
        
        predicted_cost = base_cost * trend_factor * seasonal_factor * noise_factor
        confidence_lower = predicted_cost * 0.85
        confidence_upper = predicted_cost * 1.15
        
        forecast_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "predicted_cost": round(predicted_cost, 2),
            "confidence_lower": round(confidence_lower, 2),
            "confidence_upper": round(confidence_upper, 2)
        })
    
    total_forecast = sum(day['predicted_cost'] for day in forecast_data)
    
    return {
        "forecast": forecast_data,
        "total_predicted_cost": round(total_forecast, 2),
        "confidence_interval": "85%",
        "model_accuracy": 0.89,
        "last_trained": "2024-09-15T10:30:00Z"
    }

@app.get("/api/utilization/overview")
async def get_utilization_overview(api_key: str = Depends(verify_api_key)):
    """Get resource utilization overview"""
    
    utilization_data = {
        "aws": {
            "ec2": {
                "total_instances": 100,
                "avg_cpu_utilization": 45.2,
                "avg_memory_utilization": 52.8,
                "underutilized_count": 34,
                "overutilized_count": 8,
                "optimal_count": 58
            },
            "rds": {
                "total_instances": 20,
                "avg_cpu_utilization": 68.5,
                "avg_memory_utilization": 71.2,
                "underutilized_count": 5,
                "overutilized_count": 2,
                "optimal_count": 13
            }
        },
        "azure": {
            "compute": {
                "total_instances": 80,
                "avg_cpu_utilization": 58.7,
                "avg_memory_utilization": 63.1,
                "underutilized_count": 22,
                "overutilized_count": 6,
                "optimal_count": 52
            }
        },
        "onpremises": {
            "vmware": {
                "total_instances": 50,
                "avg_cpu_utilization": 72.3,
                "avg_memory_utilization": 68.9,
                "underutilized_count": 8,
                "overutilized_count": 12,
                "optimal_count": 30
            }
        }
    }
    
    # Calculate overall metrics
    total_instances = sum(
        sum(service.get('total_instances', 0) for service in provider.values())
        for provider in utilization_data.values()
    )
    
    total_underutilized = sum(
        sum(service.get('underutilized_count', 0) for service in provider.values())
        for provider in utilization_data.values()
    )
    
    return {
        "utilization_data": utilization_data,
        "summary": {
            "total_resources": total_instances,
            "underutilized_percentage": round((total_underutilized / total_instances) * 100, 1),
            "potential_cost_reduction": "35%",
            "optimization_opportunities": total_underutilized
        }
    }

@app.post("/api/optimization/apply")
async def apply_optimization(
    recommendation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Apply an optimization recommendation"""
    
    # Simulate applying optimization
    await asyncio.sleep(2)  # Simulate processing time
    
    return {
        "success": True,
        "recommendation_id": recommendation_id,
        "status": "applied",
        "estimated_savings": 490.14,
        "applied_at": datetime.now().isoformat(),
        "message": "Optimization applied successfully. Changes will be reflected in 5-10 minutes."
    }

@app.get("/api/dashboard/overview")
async def get_dashboard_overview(api_key: str = Depends(verify_api_key)):
    """Get comprehensive dashboard overview"""
    
    # Current costs
    current_month_cost = 315250.45
    previous_month_cost = 485000.22
    savings_amount = previous_month_cost - current_month_cost
    savings_percentage = (savings_amount / previous_month_cost) * 100
    
    return {
        "cost_summary": {
            "current_month": current_month_cost,
            "previous_month": previous_month_cost,
            "savings_amount": savings_amount,
            "savings_percentage": round(savings_percentage, 1)
        },
        "utilization_summary": {
            "average_utilization": 67.8,
            "improvement_from_last_month": 22.8,
            "optimization_opportunities": 69
        },
        "top_cost_drivers": [
            {"service": "AWS EC2", "cost": 125400.20, "percentage": 39.8},
            {"service": "Azure Compute", "cost": 89650.15, "percentage": 28.4},
            {"service": "AWS RDS", "cost": 45300.80, "percentage": 14.4},
            {"service": "On-Premises VMware", "cost": 32200.50, "percentage": 10.2},
            {"service": "AWS S3", "cost": 22698.80, "percentage": 7.2}
        ],
        "alerts": [
            {
                "type": "warning",
                "message": "34 EC2 instances are underutilized (< 30% CPU)",
                "potential_savings": 16420.50
            },
            {
                "type": "info", 
                "message": "5 Azure VMs eligible for reserved instance pricing",
                "potential_savings": 8540.30
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )