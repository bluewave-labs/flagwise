-- Shadow AI Detection Server Database Schema
-- PostgreSQL initialization script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create database user if not exists (for development)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'shadow_user') THEN
        CREATE ROLE shadow_user WITH LOGIN PASSWORD 'shadow_pass';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE shadow_ai TO shadow_user;
GRANT ALL ON SCHEMA public TO shadow_user;

-- Main table for storing LLM requests
CREATE TABLE IF NOT EXISTS llm_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    src_ip TEXT NOT NULL,
    provider TEXT NOT NULL, -- openai, anthropic, etc.
    model TEXT NOT NULL, -- gpt-4, claude-3, etc.
    endpoint TEXT, -- API endpoint called
    method TEXT DEFAULT 'POST',
    headers JSONB,
    prompt TEXT, -- Will be encrypted
    response TEXT, -- Will be encrypted, optional
    duration_ms INTEGER,
    status_code INTEGER,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_llm_requests_timestamp ON llm_requests (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_llm_requests_src_ip ON llm_requests (src_ip);
CREATE INDEX IF NOT EXISTS idx_llm_requests_provider ON llm_requests (provider);
CREATE INDEX IF NOT EXISTS idx_llm_requests_model ON llm_requests (model);
CREATE INDEX IF NOT EXISTS idx_llm_requests_is_flagged ON llm_requests (is_flagged) WHERE is_flagged = TRUE;
CREATE INDEX IF NOT EXISTS idx_llm_requests_risk_score ON llm_requests (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_llm_requests_created_at ON llm_requests (created_at DESC);

-- Table for detection rules
CREATE TABLE IF NOT EXISTS detection_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    category TEXT DEFAULT 'security',
    rule_type TEXT NOT NULL CHECK (rule_type IN ('keyword', 'regex', 'model_restriction')),
    pattern TEXT NOT NULL, -- The actual pattern/value to match
    severity TEXT NOT NULL DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    points INTEGER NOT NULL DEFAULT 10 CHECK (points >= 0 AND points <= 100),
    priority INTEGER DEFAULT 1,
    stop_on_match BOOLEAN DEFAULT FALSE,
    combination_logic TEXT DEFAULT 'and',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default detection rules
INSERT INTO detection_rules (name, description, rule_type, pattern, severity, points) VALUES
    ('Critical Keywords', 'High-risk keywords in prompts', 'keyword', 'password,secret,api_key,private_key,confidential,classified,internal', 'critical', 50),
    ('Email Pattern', 'Email addresses in prompts', 'regex', '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'high', 30),
    ('Credit Card Pattern', 'Credit card numbers', 'regex', '\b(?:\d{4}[-\s]?){3}\d{4}\b', 'critical', 60),
    ('IP Address Pattern', 'IP addresses in content', 'regex', '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'medium', 20),
    ('Phone Number Pattern', 'Phone numbers', 'regex', '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'medium', 15),
    ('Restricted Models', 'Disallowed model usage', 'model_restriction', 'gpt-4,claude-3-opus', 'medium', 20)
ON CONFLICT (name) DO NOTHING;

-- Table for alerts
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id UUID NOT NULL REFERENCES llm_requests(id),
    alert_type TEXT NOT NULL CHECK (alert_type IN ('slack', 'email')),
    recipient TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_request_id ON alerts (request_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts (created_at DESC);

-- Table for user sessions (grouping requests by IP and time window)
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    src_ip TEXT NOT NULL,
    session_start TIMESTAMPTZ NOT NULL,
    session_end TIMESTAMPTZ NOT NULL,
    request_count INTEGER DEFAULT 0,
    flagged_requests INTEGER DEFAULT 0,
    max_risk_score INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_src_ip ON user_sessions (src_ip);
CREATE INDEX IF NOT EXISTS idx_user_sessions_start ON user_sessions (session_start DESC);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Analytics aggregation tables for pre-computed metrics
CREATE TABLE IF NOT EXISTS analytics_hourly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time_bucket TIMESTAMPTZ NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,
    threat_detection_rate DECIMAL(5,2) DEFAULT 0, -- percentage
    avg_risk_score DECIMAL(5,2) DEFAULT 0,
    max_risk_score INTEGER DEFAULT 0,
    avg_duration_ms DECIMAL(8,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(time_bucket, provider, model)
);

CREATE TABLE IF NOT EXISTS analytics_daily (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date_bucket DATE NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,
    threat_detection_rate DECIMAL(5,2) DEFAULT 0,
    avg_risk_score DECIMAL(5,2) DEFAULT 0,
    max_risk_score INTEGER DEFAULT 0,
    avg_duration_ms DECIMAL(8,2) DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date_bucket, provider, model)
);

CREATE TABLE IF NOT EXISTS analytics_weekly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    week_bucket DATE NOT NULL, -- Monday of the week
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,
    threat_detection_rate DECIMAL(5,2) DEFAULT 0,
    avg_risk_score DECIMAL(5,2) DEFAULT 0,
    max_risk_score INTEGER DEFAULT 0,
    avg_duration_ms DECIMAL(8,2) DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(week_bucket, provider, model)
);

CREATE TABLE IF NOT EXISTS analytics_monthly (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    month_bucket DATE NOT NULL, -- First day of the month
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    flagged_count INTEGER DEFAULT 0,
    threat_detection_rate DECIMAL(5,2) DEFAULT 0,
    avg_risk_score DECIMAL(5,2) DEFAULT 0,
    max_risk_score INTEGER DEFAULT 0,
    avg_duration_ms DECIMAL(8,2) DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(month_bucket, provider, model)
);

-- Analytics indexes for performance
CREATE INDEX IF NOT EXISTS idx_analytics_hourly_time ON analytics_hourly (time_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_hourly_provider ON analytics_hourly (provider);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_date ON analytics_daily (date_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_provider ON analytics_daily (provider);
CREATE INDEX IF NOT EXISTS idx_analytics_weekly_week ON analytics_weekly (week_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_weekly_provider ON analytics_weekly (provider);
CREATE INDEX IF NOT EXISTS idx_analytics_monthly_month ON analytics_monthly (month_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_monthly_provider ON analytics_monthly (provider);

-- Function to aggregate analytics data
CREATE OR REPLACE FUNCTION refresh_analytics_aggregates()
RETURNS void AS $$
BEGIN
    -- Refresh hourly aggregates for the last 7 days
    INSERT INTO analytics_hourly (time_bucket, provider, model, request_count, 
                                  flagged_count, threat_detection_rate, avg_risk_score, max_risk_score, 
                                  avg_duration_ms)
    SELECT 
        date_trunc('hour', timestamp) as time_bucket,
        provider,
        model,
        COUNT(*) as request_count,
        COUNT(*) FILTER (WHERE is_flagged = true) as flagged_count,
        CASE WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(*) FILTER (WHERE is_flagged = true) * 100.0 / COUNT(*))::numeric, 2)
        ELSE 0 END as threat_detection_rate,
        COALESCE(AVG(risk_score), 0) as avg_risk_score,
        COALESCE(MAX(risk_score), 0) as max_risk_score,
        COALESCE(AVG(duration_ms), 0) as avg_duration_ms
    FROM llm_requests
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY date_trunc('hour', timestamp), provider, model
    ON CONFLICT (time_bucket, provider, model) DO UPDATE SET
        request_count = EXCLUDED.request_count,
        flagged_count = EXCLUDED.flagged_count,
        threat_detection_rate = EXCLUDED.threat_detection_rate,
        avg_risk_score = EXCLUDED.avg_risk_score,
        max_risk_score = EXCLUDED.max_risk_score,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        created_at = NOW();

    -- Refresh daily aggregates for the last 90 days
    INSERT INTO analytics_daily (date_bucket, provider, model, request_count, 
                                 flagged_count, threat_detection_rate, avg_risk_score, max_risk_score, 
                                 total_cost_usd, avg_duration_ms, unique_ips)
    SELECT 
        DATE(timestamp) as date_bucket,
        provider,
        model,
        COUNT(*) as request_count,
        COUNT(*) FILTER (WHERE is_flagged = true) as flagged_count,
        CASE WHEN COUNT(*) > 0 THEN 
            ROUND((COUNT(*) FILTER (WHERE is_flagged = true) * 100.0 / COUNT(*))::numeric, 2)
        ELSE 0 END as threat_detection_rate,
        COALESCE(AVG(risk_score), 0) as avg_risk_score,
        COALESCE(MAX(risk_score), 0) as max_risk_score,
        COALESCE(AVG(duration_ms), 0) as avg_duration_ms,
        COUNT(DISTINCT src_ip) as unique_ips
    FROM llm_requests
    WHERE timestamp >= NOW() - INTERVAL '90 days'
    GROUP BY DATE(timestamp), provider, model
    ON CONFLICT (date_bucket, provider, model) DO UPDATE SET
        request_count = EXCLUDED.request_count,
        flagged_count = EXCLUDED.flagged_count,
        threat_detection_rate = EXCLUDED.threat_detection_rate,
        avg_risk_score = EXCLUDED.avg_risk_score,
        max_risk_score = EXCLUDED.max_risk_score,
        avg_duration_ms = EXCLUDED.avg_duration_ms,
        unique_ips = EXCLUDED.unique_ips,
        created_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Triggers to automatically update updated_at
CREATE TRIGGER update_llm_requests_updated_at BEFORE UPDATE ON llm_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_detection_rules_updated_at BEFORE UPDATE ON detection_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- System settings table for configuration
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create trigger for system_settings after table creation
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default settings
INSERT INTO system_settings (key, value, description, category) VALUES
('data_retention_days', '180', 'Number of days to retain data before automatic deletion', 'data_storage'),
('cleanup_enabled', 'true', 'Enable automatic data cleanup', 'data_storage'),
('max_export_records', '100000', 'Maximum number of records allowed in a single export', 'data_storage'),

-- Kafka Data Sources Configuration
('kafka_enabled', 'false', 'Enable Kafka consumer for real data ingestion', 'data_sources'),
('kafka_brokers', 'localhost:9092', 'Comma-separated list of Kafka broker URLs', 'data_sources'),
('kafka_topic', 'llm-traffic-logs', 'Kafka topic to consume LLM traffic from', 'data_sources'),
('kafka_group_id', 'flagwise-consumer', 'Consumer group ID for Kafka consumption', 'data_sources'),
('kafka_auth_type', 'none', 'Authentication type: none, sasl_plain, sasl_ssl, ssl', 'data_sources'),
('kafka_username', '', 'Username for SASL authentication', 'data_sources'),
('kafka_password', '', 'Password for SASL authentication (encrypted)', 'data_sources'),
('kafka_ssl_cert', '', 'SSL certificate content for SSL authentication', 'data_sources'),
('kafka_ssl_key', '', 'SSL private key content for SSL authentication', 'data_sources'),
('kafka_ssl_ca', '', 'SSL CA certificate content for SSL authentication', 'data_sources'),
('kafka_timeout_ms', '30000', 'Connection timeout in milliseconds', 'data_sources'),
('kafka_retry_backoff_ms', '1000', 'Retry backoff time in milliseconds', 'data_sources'),
('kafka_message_schema', '{
  "timestamp": "string",
  "request_id": "string",
  "src_ip": "string",
  "provider": "string",
  "model": "string",
  "prompt": "string",
  "response": "string",
  "prompt_tokens": "integer",
  "completion_tokens": "integer",
  "total_tokens": "integer"
}', 'Expected JSON schema for Kafka messages', 'data_sources'),
('demo_data_enabled', 'true', 'Enable demo data generation for testing', 'data_sources')
ON CONFLICT (key) DO NOTHING;

-- Users table for authentication and authorization
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'read_only' CHECK (role IN ('admin', 'read_only')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);

-- Create default admin user (password: admin123)
INSERT INTO users (username, password_hash, role) VALUES 
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Add trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for configurable data retention
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
DECLARE
    retention_days INTEGER;
    cleanup_enabled BOOLEAN;
BEGIN
    -- Get retention settings
    SELECT value::INTEGER INTO retention_days 
    FROM system_settings 
    WHERE key = 'data_retention_days';
    
    SELECT value::BOOLEAN INTO cleanup_enabled 
    FROM system_settings 
    WHERE key = 'cleanup_enabled';
    
    -- Default to 180 days if setting not found
    IF retention_days IS NULL THEN
        retention_days := 180;
    END IF;
    
    -- Default to enabled if setting not found
    IF cleanup_enabled IS NULL THEN
        cleanup_enabled := true;
    END IF;
    
    -- Only cleanup if enabled
    IF cleanup_enabled THEN
        DELETE FROM llm_requests WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
        DELETE FROM alerts WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;
        DELETE FROM user_sessions WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;
        
        -- Log cleanup activity
        RAISE NOTICE 'Cleanup completed: deleted records older than % days', retention_days;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to shadow_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO shadow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO shadow_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO shadow_user;