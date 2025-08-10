# Shadow AI Kafka Demo - Quick Setup Guide

## 🎯 Purpose
This demo environment provides realistic LLM traffic data to test Shadow AI's monitoring capabilities with real Kafka ingestion instead of test data.

## 🚀 Quick Start (5 minutes)

### 1. Start Demo Environment
```bash
cd kafka-demo
./start-demo.sh
```

### 2. Apply Database Migration (Optional)
To enable Kafka by default in Shadow AI:
```bash
# Run this in your Shadow AI PostgreSQL database:
psql -h localhost -U shadow_user -d shadow_ai -f migration_enable_kafka_demo.sql
```

### 3. Configure Shadow AI Dashboard
1. Go to **Administration > System Settings**
2. Find **Kafka Connection Status**
3. Connection should show: `localhost:9092` (already configured)
4. Topic: `llm-traffic-logs` (already configured) 
5. Click **Test Connection** - should succeed
6. Enable Kafka ingestion if not already enabled

### 4. Watch Data Flow
- Real-time LLM traffic will appear in all dashboard sections
- Data generates every 2 seconds with realistic patterns
- 10+ AI providers (OpenAI, Anthropic, Google, etc.)
- Realistic prompts, responses, costs, and timing

## 📊 What You'll See

### Dashboard Metrics
- **Total Requests**: Increasing every 2 seconds
- **Flagged Requests**: Based on detection rules
- **Provider Distribution**: 10+ different AI providers
- **Cost Tracking**: Realistic pricing per provider/model

### LLM Requests Page
- Real API calls with proper headers
- Authentic prompts and responses
- Token counts and costs
- Various status codes (200, 401, 429, 500)

### Sessions & Analytics
- IP-based user sessions
- Request patterns and timing
- Cost analysis per provider
- Geographic distribution simulation

## 🔧 Verification Commands

```bash
# Check if services are running
docker-compose ps

# View real-time data generation
docker-compose logs -f llm-traffic-generator

# Monitor Kafka topic
docker exec -it demo-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic llm-traffic-logs --from-beginning

# Stop everything
docker-compose down
```

## ⚙️ Configuration Details

- **Kafka Broker**: localhost:9092
- **Topic**: llm-traffic-logs  
- **Partitions**: 3
- **Retention**: 7 days
- **Authentication**: None (simple setup)
- **Data Rate**: 1 message every 2 seconds
- **Schema**: Exact match with Shadow AI database

## 🎨 Generated Data Features

### AI Providers (10+)
- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic (Claude-3 variants)
- Google (Gemini Pro, Palm-2)
- Cohere, Mistral, HuggingFace
- Together AI, Replicate, Perplexity, Groq

### Realistic Patterns
- Security analysis prompts
- Code review requests  
- Translation tasks
- Business communications
- Technical documentation
- Error scenarios (401, 429, 500)
- Varied response times and costs

## 🔍 Troubleshooting

### Kafka Connection Issues
```bash
# Check if Kafka is accessible
docker exec -it demo-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Data Not Appearing
1. Verify Kafka is enabled in Shadow AI settings
2. Check database migration was applied
3. Ensure no firewall blocking port 9092
4. Check Shadow AI logs for ingestion errors

### Performance
- Default: 1 message/2 seconds = 1,800 messages/hour
- Modify `GENERATION_INTERVAL` in docker-compose.yml if needed

## 📋 Next Steps

1. ✅ **Start Demo**: `./start-demo.sh`
2. ✅ **Configure Dashboard**: Point to localhost:9092
3. ✅ **Enable Ingestion**: Turn on Kafka in settings
4. ✅ **Watch Data**: Monitor dashboard for real-time updates
5. ✅ **Test Detection**: Watch flagged requests appear
6. ✅ **Remove Old Test Data**: Discuss removing old test containers

The demo provides continuous, realistic LLM traffic that will populate all Shadow AI features with authentic data patterns for comprehensive testing!