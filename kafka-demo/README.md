# Demo Kafka Environment for Shadow AI

This directory contains a complete Kafka setup that generates realistic LLM traffic data for testing Shadow AI's monitoring capabilities.

## Overview

- **Kafka + Zookeeper**: Latest stable versions with simple authentication
- **Topic**: `llm-traffic-logs` (matches Shadow AI configuration)
- **Data Generator**: Produces realistic LLM request data every 2 seconds
- **AI Providers**: 10+ providers including OpenAI, Anthropic, Google, etc.
- **Schema**: Matches exact Shadow AI database structure

## Quick Start

1. **Start the Kafka environment:**
   ```bash
   cd kafka-demo
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f llm-traffic-generator
   ```

3. **Stop the environment:**
   ```bash
   docker-compose down
   ```

## Generated Data Features

### AI Providers (10+)
- OpenAI (GPT-4, GPT-3.5-turbo, etc.)
- Anthropic (Claude-3, Claude-2)
- Google (Gemini Pro, Palm-2)
- Cohere (Command, Embed)
- Mistral (Large, Medium, Small)
- HuggingFace (DialoGPT, BlenderBot)
- Together AI (Llama-2, Mixtral)
- Replicate (Meta models)
- Perplexity (Online models)
- Groq (Mixtral, Llama2)

### Realistic Data Points
- **Prompts**: Security analysis, code review, translations, etc.
- **Responses**: Contextually appropriate AI responses
- **IP Addresses**: Varied source IPs for user simulation
- **Tokens**: Calculated based on content length with realistic variance
- **Costs**: Provider-specific pricing (2024 rates)
- **Timing**: Realistic API response durations
- **Status Codes**: Mostly 200s with some errors (401, 429, 500, etc.)

### Schema Compatibility
Perfect match with Shadow AI's `llm_requests` table:
- `id`, `timestamp`, `src_ip`, `provider`, `model`, `endpoint`
- `prompt`, `response`, `tokens_*`, `cost_usd`, `duration_ms`
- `headers` (JSONB), `status_code`, `method`
- Risk fields: `risk_score`, `is_flagged`, `flag_reason`

## Kafka Configuration

- **Broker**: localhost:9092
- **Topic**: llm-traffic-logs
- **Partitions**: 3
- **Replication**: 1
- **Retention**: 7 days

## Shadow AI Integration

The system is pre-configured to work with Shadow AI:

1. **Topic Name**: `llm-traffic-logs` (matches database config)
2. **Schema**: Exact match with `llm_requests` table structure
3. **Connection**: localhost:9092 (standard Kafka port)
4. **Authentication**: None (simple setup)

## Environment Variables

Generator can be customized via environment variables:
- `KAFKA_BROKER`: Kafka broker address (default: kafka:29092)
- `KAFKA_TOPIC`: Topic name (default: llm-traffic-logs)  
- `GENERATION_INTERVAL`: Seconds between messages (default: 2)

## Monitoring

Monitor the topic:
```bash
# View messages
docker exec -it demo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic llm-traffic-logs \
  --from-beginning

# Topic information
docker exec -it demo-kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic llm-traffic-logs
```

## Testing with Shadow AI

1. Start this Kafka demo environment
2. Configure Shadow AI to connect to localhost:9092
3. Enable Kafka ingestion in Shadow AI settings
4. Watch real-time LLM traffic appear in the dashboard

The generated data will trigger Shadow AI's detection rules and populate all dashboard metrics with realistic data patterns.