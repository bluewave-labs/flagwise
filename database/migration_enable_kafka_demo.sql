-- Migration: Enable Kafka demo configuration
-- Updates Kafka settings to work with demo environment and complete message schema

-- Enable Kafka consumer by default for demo
UPDATE system_settings 
SET value = 'true' 
WHERE key = 'kafka_enabled';

-- Update Kafka message schema to match complete database structure
UPDATE system_settings 
SET value = '{
  "id": "string",
  "timestamp": "string", 
  "src_ip": "string",
  "provider": "string",
  "model": "string",
  "endpoint": "string",
  "method": "string",
  "headers": "object",
  "prompt": "string",
  "response": "string",
  "tokens_prompt": "integer",
  "tokens_response": "integer", 
  "tokens_total": "integer",
  "cost_usd": "number",
  "duration_ms": "integer",
  "status_code": "integer",
  "risk_score": "integer",
  "is_flagged": "boolean",
  "flag_reason": "string",
  "created_at": "string",
  "updated_at": "string"
}' 
WHERE key = 'kafka_message_schema';

-- Add demo-specific settings
INSERT INTO system_settings (key, value, description, category) VALUES
('kafka_demo_mode', 'true', 'Enable demo Kafka environment integration', 'data_sources'),
('kafka_demo_auto_connect', 'true', 'Automatically connect to demo Kafka on startup', 'data_sources')
ON CONFLICT (key) DO UPDATE SET
  value = EXCLUDED.value,
  description = EXCLUDED.description,
  updated_at = NOW();