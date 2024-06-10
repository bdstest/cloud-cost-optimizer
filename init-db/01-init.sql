-- Initialize TimescaleDB for Hybrid Cloud Cost Optimizer
-- Creates tables and hypertables for time-series cost data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create cost_data table for time-series cost metrics
CREATE TABLE IF NOT EXISTS cost_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    provider VARCHAR(50) NOT NULL,
    service VARCHAR(100) NOT NULL,
    resource_id VARCHAR(200),
    cost DECIMAL(12,2) NOT NULL,
    usage_hours INTEGER,
    resource_count INTEGER,
    region VARCHAR(50),
    department VARCHAR(100),
    tags JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('cost_data', 'timestamp', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cost_data_provider_service ON cost_data (provider, service);
CREATE INDEX IF NOT EXISTS idx_cost_data_resource_id ON cost_data (resource_id);
CREATE INDEX IF NOT EXISTS idx_cost_data_department ON cost_data (department);
CREATE INDEX IF NOT EXISTS idx_cost_data_region ON cost_data (region);

-- Create resource_utilization table
CREATE TABLE IF NOT EXISTS resource_utilization (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    resource_id VARCHAR(200) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    cpu_utilization DECIMAL(5,2),
    memory_utilization DECIMAL(5,2),
    network_io_mbps DECIMAL(10,2),
    disk_io_iops INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create hypertable for utilization metrics
SELECT create_hypertable('resource_utilization', 'timestamp', if_not_exists => TRUE);

-- Create optimization_recommendations table
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_id VARCHAR(50) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    service VARCHAR(100) NOT NULL,
    resource_id VARCHAR(200),
    recommendation_type VARCHAR(50) NOT NULL,
    current_config JSONB,
    recommended_config JSONB,
    current_cost DECIMAL(10,2) NOT NULL,
    projected_cost DECIMAL(10,2) NOT NULL,
    monthly_savings DECIMAL(10,2) NOT NULL,
    confidence DECIMAL(4,3) NOT NULL,
    description TEXT,
    reasoning TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    applied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON optimization_recommendations (status);
CREATE INDEX IF NOT EXISTS idx_recommendations_provider ON optimization_recommendations (provider);

-- Create budget_alerts table
CREATE TABLE IF NOT EXISTS budget_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100),
    provider VARCHAR(50),
    service VARCHAR(100),
    budget_amount DECIMAL(12,2) NOT NULL,
    current_spend DECIMAL(12,2) NOT NULL,
    threshold_percentage INTEGER NOT NULL,
    alert_level VARCHAR(20) NOT NULL, -- 'warning', 'critical'
    message TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create forecast_data table for ML predictions
CREATE TABLE IF NOT EXISTS forecast_data (
    id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    provider VARCHAR(50),
    service VARCHAR(100),
    predicted_cost DECIMAL(12,2) NOT NULL,
    confidence_lower DECIMAL(12,2) NOT NULL,
    confidence_upper DECIMAL(12,2) NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for forecasts
CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_data (forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_provider ON forecast_data (provider);

-- Create continuous aggregates for daily cost summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_cost_summary
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS day,
    provider,
    service,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost,
    COUNT(*) as record_count
FROM cost_data
GROUP BY day, provider, service
WITH NO DATA;

-- Create policy to refresh the continuous aggregate
SELECT add_continuous_aggregate_policy('daily_cost_summary',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Create data retention policies
SELECT add_retention_policy('cost_data', INTERVAL '2 years', if_not_exists => TRUE);
SELECT add_retention_policy('resource_utilization', INTERVAL '1 year', if_not_exists => TRUE);

-- Create compression policy for older data
SELECT add_compression_policy('cost_data', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_compression_policy('resource_utilization', INTERVAL '7 days', if_not_exists => TRUE);

-- Insert initial demo data
INSERT INTO cost_data (timestamp, provider, service, resource_id, cost, usage_hours, resource_count, region, department) VALUES
('2024-06-01 00:00:00+00', 'aws', 'ec2', 'i-0123456789abcdef0', 4200.50, 720, 25, 'us-east-1', 'Engineering'),
('2024-06-01 00:00:00+00', 'aws', 'rds', 'db-prod-mysql-01', 2800.25, 720, 5, 'us-east-1', 'Engineering'),
('2024-06-01 00:00:00+00', 'aws', 's3', 'bucket-analytics-logs', 450.75, 720, 1, 'us-east-1', 'Data Science'),
('2024-06-01 00:00:00+00', 'azure', 'compute', 'vm-standard-d4s-v4', 3200.40, 720, 20, 'eastus', 'Marketing'),
('2024-06-01 00:00:00+00', 'azure', 'storage', 'stg-backups-prod', 380.90, 720, 1, 'eastus', 'Marketing'),
('2024-06-01 00:00:00+00', 'onpremises', 'vmware', 'esx-cluster-01', 2500.00, 720, 15, 'datacenter-1', 'Operations');

-- Insert sample optimization recommendations
INSERT INTO optimization_recommendations (
    recommendation_id, provider, service, resource_id, recommendation_type,
    current_config, recommended_config, current_cost, projected_cost, monthly_savings,
    confidence, description, reasoning
) VALUES
('rec-001', 'aws', 'ec2', 'i-0123456789abcdef0', 'rightsizing',
 '{"instance_type": "m5.4xlarge", "cpu": 16, "memory": 64}',
 '{"instance_type": "m5.large", "cpu": 2, "memory": 8}',
 560.16, 70.02, 490.14, 0.92,
 'Instance is severely under-utilized with 25% CPU usage',
 'Right-sizing from m5.4xlarge to m5.large based on utilization analysis'),
('rec-002', 'azure', 'compute', 'vm-standard-d4s-v4', 'reserved_instance',
 '{"pricing": "pay_as_you_go", "commitment": "none"}',
 '{"pricing": "reserved", "commitment": "3_year"}',
 175.20, 89.50, 85.70, 0.87,
 'Consistent usage pattern suitable for reserved instance',
 '3-year reserved instance commitment for predictable workload'),
('rec-003', 'aws', 's3', 'bucket-analytics-logs', 'storage_optimization',
 '{"storage_class": "standard", "access_pattern": "infrequent"}',
 '{"storage_class": "intelligent_tiering", "access_pattern": "infrequent"}',
 245.80, 147.48, 98.32, 0.78,
 'Objects accessed less than once per month',
 'Intelligent Tiering for infrequently accessed objects');

-- Create functions for cost analysis
CREATE OR REPLACE FUNCTION get_monthly_cost_summary(target_month DATE)
RETURNS TABLE (
    provider VARCHAR(50),
    service VARCHAR(100),
    total_cost DECIMAL(12,2),
    resource_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cd.provider,
        cd.service,
        SUM(cd.cost)::DECIMAL(12,2) as total_cost,
        COUNT(DISTINCT cd.resource_id) as resource_count
    FROM cost_data cd
    WHERE DATE_TRUNC('month', cd.timestamp) = DATE_TRUNC('month', target_month)
    GROUP BY cd.provider, cd.service
    ORDER BY total_cost DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function for cost trend analysis
CREATE OR REPLACE FUNCTION get_cost_trend(days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    date DATE,
    total_cost DECIMAL(12,2),
    provider_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cd.timestamp::DATE as date,
        SUM(cd.cost)::DECIMAL(12,2) as total_cost,
        jsonb_object_agg(cd.provider, provider_cost) as provider_breakdown
    FROM (
        SELECT 
            timestamp::DATE,
            provider,
            SUM(cost) as provider_cost
        FROM cost_data
        WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back
        GROUP BY timestamp::DATE, provider
    ) cd
    GROUP BY cd.timestamp::DATE
    ORDER BY date DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to demo user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO demouser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO demouser;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO demouser;

COMMIT;