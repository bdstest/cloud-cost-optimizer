#!/usr/bin/env python3
"""
Initialize sample cost data for the Hybrid Cloud Cost Optimizer demo.
Creates realistic enterprise-scale cost data across AWS, Azure, and on-premises.
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os

def wait_for_db(max_retries=30):
    """Wait for database to be ready"""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host="timescaledb",
                database="cost_optimizer", 
                user="demouser",
                password="demopass123"
            )
            conn.close()
            print("✅ Database is ready!")
            return True
        except psycopg2.OperationalError:
            print(f"⏳ Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    
    print("❌ Database connection timeout")
    return False

def create_tables():
    """Create necessary tables"""
    conn = psycopg2.connect(
        host="timescaledb",
        database="cost_optimizer",
        user="demouser", 
        password="demopass123"
    )
    
    cursor = conn.cursor()
    
    # Create cost_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cost_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            provider VARCHAR(50) NOT NULL,
            service VARCHAR(100) NOT NULL,
            resource_id VARCHAR(200),
            cost DECIMAL(10,2) NOT NULL,
            usage_hours INTEGER,
            resource_count INTEGER,
            region VARCHAR(50),
            department VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    
    # Create hypertable for time-series data
    cursor.execute("""
        SELECT create_hypertable('cost_data', 'timestamp', if_not_exists => TRUE);
    """)
    
    # Create optimization_recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS optimization_recommendations (
            id SERIAL PRIMARY KEY,
            recommendation_id VARCHAR(50) UNIQUE NOT NULL,
            provider VARCHAR(50) NOT NULL,
            service VARCHAR(100) NOT NULL,
            resource_id VARCHAR(200),
            recommendation_type VARCHAR(50) NOT NULL,
            current_cost DECIMAL(10,2) NOT NULL,
            projected_cost DECIMAL(10,2) NOT NULL,
            monthly_savings DECIMAL(10,2) NOT NULL,
            confidence DECIMAL(4,3) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tables created successfully")

def generate_sample_data():
    """Generate 90 days of realistic sample cost data"""
    
    # Date range: 90 days of historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    data = []
    
    # AWS services configuration
    aws_services = {
        'ec2': {'base_cost': 12000, 'volatility': 0.15, 'trend': 0.001},
        'rds': {'base_cost': 8000, 'volatility': 0.10, 'trend': 0.0005},
        's3': {'base_cost': 3000, 'volatility': 0.20, 'trend': 0.002},
        'lambda': {'base_cost': 500, 'volatility': 0.30, 'trend': 0.003},
        'cloudfront': {'base_cost': 1200, 'volatility': 0.25, 'trend': 0.001}
    }
    
    # Azure services configuration
    azure_services = {
        'compute': {'base_cost': 10000, 'volatility': 0.12, 'trend': 0.0008},
        'storage': {'base_cost': 2500, 'volatility': 0.18, 'trend': 0.001},
        'sql-database': {'base_cost': 6000, 'volatility': 0.08, 'trend': 0.0003},
        'app-service': {'base_cost': 1800, 'volatility': 0.22, 'trend': 0.002}
    }
    
    # On-premises services configuration
    onprem_services = {
        'vmware': {'base_cost': 8000, 'volatility': 0.05, 'trend': -0.0002},
        'kubernetes': {'base_cost': 4000, 'volatility': 0.15, 'trend': 0.001},
        'storage': {'base_cost': 3000, 'volatility': 0.08, 'trend': 0.0001}
    }
    
    departments = ['Engineering', 'Marketing', 'Sales', 'Operations', 'Data Science']
    regions = {
        'aws': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'azure': ['eastus', 'westus2', 'northeurope'],
        'onpremises': ['datacenter-1', 'datacenter-2']
    }
    
    # Generate daily data
    current_date = start_date
    while current_date <= end_date:
        day_of_year = current_date.timetuple().tm_yday
        
        # AWS data
        for service, config in aws_services.items():
            base = config['base_cost']
            volatility = config['volatility']
            trend = config['trend']
            
            # Add trend, seasonality, and random variation
            days_from_start = (current_date - start_date).days
            trend_factor = 1 + (trend * days_from_start)
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * day_of_year / 365)
            random_factor = 1 + np.random.normal(0, volatility)
            
            daily_cost = base * trend_factor * seasonal_factor * random_factor
            
            # Multiple entries per service (different regions/departments)
            for i in range(np.random.randint(2, 5)):
                data.append({
                    'timestamp': current_date,
                    'provider': 'aws',
                    'service': service,
                    'resource_id': f'aws-{service}-{i+1:03d}',
                    'cost': round(daily_cost / 3, 2),
                    'usage_hours': np.random.randint(16, 25),
                    'resource_count': np.random.randint(5, 50),
                    'region': np.random.choice(regions['aws']),
                    'department': np.random.choice(departments)
                })
        
        # Azure data
        for service, config in azure_services.items():
            base = config['base_cost']
            volatility = config['volatility']
            trend = config['trend']
            
            days_from_start = (current_date - start_date).days
            trend_factor = 1 + (trend * days_from_start)
            seasonal_factor = 1 + 0.08 * np.sin(2 * np.pi * day_of_year / 365)
            random_factor = 1 + np.random.normal(0, volatility)
            
            daily_cost = base * trend_factor * seasonal_factor * random_factor
            
            for i in range(np.random.randint(2, 4)):
                data.append({
                    'timestamp': current_date,
                    'provider': 'azure',
                    'service': service,
                    'resource_id': f'azure-{service}-{i+1:03d}',
                    'cost': round(daily_cost / 2, 2),
                    'usage_hours': np.random.randint(18, 25),
                    'resource_count': np.random.randint(3, 30),
                    'region': np.random.choice(regions['azure']),
                    'department': np.random.choice(departments)
                })
        
        # On-premises data
        for service, config in onprem_services.items():
            base = config['base_cost']
            volatility = config['volatility']
            trend = config['trend']
            
            days_from_start = (current_date - start_date).days
            trend_factor = 1 + (trend * days_from_start)
            seasonal_factor = 1 + 0.05 * np.sin(2 * np.pi * day_of_year / 365)
            random_factor = 1 + np.random.normal(0, volatility)
            
            daily_cost = base * trend_factor * seasonal_factor * random_factor
            
            for i in range(np.random.randint(1, 3)):
                data.append({
                    'timestamp': current_date,
                    'provider': 'onpremises',
                    'service': service,
                    'resource_id': f'onprem-{service}-{i+1:03d}',
                    'cost': round(daily_cost / 1, 2),
                    'usage_hours': 24,  # On-premises runs 24/7
                    'resource_count': np.random.randint(5, 25),
                    'region': np.random.choice(regions['onpremises']),
                    'department': np.random.choice(departments)
                })
        
        current_date += timedelta(days=1)
    
    return data

def insert_cost_data(data):
    """Insert cost data into database"""
    conn = psycopg2.connect(
        host="timescaledb",
        database="cost_optimizer",
        user="demouser",
        password="demopass123"
    )
    
    cursor = conn.cursor()
    
    # Insert cost data
    insert_query = """
        INSERT INTO cost_data (timestamp, provider, service, resource_id, cost, 
                             usage_hours, resource_count, region, department)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for record in data:
        cursor.execute(insert_query, (
            record['timestamp'],
            record['provider'],
            record['service'],
            record['resource_id'],
            record['cost'],
            record['usage_hours'],
            record['resource_count'],
            record['region'],
            record['department']
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {len(data)} cost records")

def insert_recommendations():
    """Insert sample optimization recommendations"""
    conn = psycopg2.connect(
        host="timescaledb",
        database="cost_optimizer",
        user="demouser",
        password="demopass123"
    )
    
    cursor = conn.cursor()
    
    recommendations = [
        {
            'recommendation_id': 'rec-001',
            'provider': 'aws',
            'service': 'ec2',
            'resource_id': 'i-0123456789abcdef0',
            'recommendation_type': 'rightsizing',
            'current_cost': 560.16,
            'projected_cost': 70.02,
            'monthly_savings': 490.14,
            'confidence': 0.92,
            'description': 'Instance is severely under-utilized with 25% CPU usage. Recommend downsizing from m5.4xlarge to m5.large.'
        },
        {
            'recommendation_id': 'rec-002',
            'provider': 'azure',
            'service': 'compute',
            'resource_id': 'vm-standard-d4s-v4',
            'recommendation_type': 'reserved_instance',
            'current_cost': 175.20,
            'projected_cost': 89.50,
            'monthly_savings': 85.70,
            'confidence': 0.87,
            'description': 'Consistent usage pattern suitable for 3-year reserved instance commitment.'
        },
        {
            'recommendation_id': 'rec-003',
            'provider': 'aws',
            'service': 's3',
            'resource_id': 'bucket-analytics-logs',
            'recommendation_type': 'storage_optimization',
            'current_cost': 245.80,
            'projected_cost': 147.48,
            'monthly_savings': 98.32,
            'confidence': 0.78,
            'description': 'Objects accessed less than once per month. Recommend Intelligent Tiering storage class.'
        },
        {
            'recommendation_id': 'rec-004',
            'provider': 'aws',
            'service': 'rds',
            'resource_id': 'db-prod-mysql-01',
            'recommendation_type': 'rightsizing',
            'current_cost': 892.35,
            'projected_cost': 446.18,
            'monthly_savings': 446.17,
            'confidence': 0.89,
            'description': 'Database instance showing 35% CPU utilization. Recommend downsizing from db.r5.2xlarge to db.r5.xlarge.'
        },
        {
            'recommendation_id': 'rec-005',
            'provider': 'azure',
            'service': 'storage',
            'resource_id': 'stg-backups-prod',
            'recommendation_type': 'storage_optimization',
            'current_cost': 156.90,
            'projected_cost': 78.45,
            'monthly_savings': 78.45,
            'confidence': 0.91,
            'description': 'Backup data older than 30 days. Recommend moving to Archive storage tier.'
        }
    ]
    
    insert_query = """
        INSERT INTO optimization_recommendations 
        (recommendation_id, provider, service, resource_id, recommendation_type,
         current_cost, projected_cost, monthly_savings, confidence, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (recommendation_id) DO NOTHING
    """
    
    for rec in recommendations:
        cursor.execute(insert_query, (
            rec['recommendation_id'],
            rec['provider'],
            rec['service'],
            rec['resource_id'],
            rec['recommendation_type'],
            rec['current_cost'],
            rec['projected_cost'],
            rec['monthly_savings'],
            rec['confidence'],
            rec['description']
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {len(recommendations)} optimization recommendations")

def main():
    """Main initialization function"""
    print("🚀 Starting Hybrid Cloud Cost Optimizer data initialization...")
    
    # Wait for database
    if not wait_for_db():
        exit(1)
    
    # Create tables
    create_tables()
    
    # Generate and insert sample data
    print("📊 Generating 90 days of sample cost data...")
    cost_data = generate_sample_data()
    insert_cost_data(cost_data)
    
    # Insert optimization recommendations
    print("🤖 Creating optimization recommendations...")
    insert_recommendations()
    
    print("✅ Data initialization completed successfully!")
    print(f"📈 Total cost records: {len(cost_data)}")
    print("🎯 Ready for cost optimization analysis!")

if __name__ == "__main__":
    main()