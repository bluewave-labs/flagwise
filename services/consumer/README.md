# Shadow AI Consumer Service

Kafka consumer service that ingests LLM traffic messages, processes them through a rule-based detection engine, and sends real-time Slack alerts for high-risk requests.

## Components

### Main Consumer (`kafka_consumer.py`)
- Consumes from `llm-traffic-logs` topic
- Consumer group: `shadow-ai-detection`
- Processes messages in micro-batches (100 records)
- Integrates with detection engine and alert service

### Detection Engine (`detection_engine.py`)
- **Rule Types Supported:**
  - `keyword`: Case-insensitive substring matching
  - `regex`: Regular expression patterns
  - `model_restriction`: Blocked model names

- **Scoring System:**
  - Each rule adds points (0-100)
  - Total score capped at 100 maximum
  - Records flagged if score > 0

- **Rule Cache:**
  - In-memory rule caching
  - Refreshes every 60 seconds from database
  - Thread-safe with RLock

### Slack Alert Service (`alert_service.py`)
- **Real-time alerting** for flagged requests during ingestion
- **Rich Slack blocks** with risk score, source IP, prompt preview, and dashboard links
- **Rate limiting** - Maximum 5 alerts per minute globally
- **Risk threshold** - Only sends alerts for requests ≥50 risk score (configurable)
- **Alert logging** - Tracks all alert attempts in database

### Database Manager (`database.py`)
- PostgreSQL connection management
- Bulk insert operations for performance
- Handles up to 500 records per batch

## Default Detection Rules

| Rule Name | Type | Pattern | Points | Description |
|-----------|------|---------|--------|-------------|
| Critical Keywords | keyword | password,secret,api_key,private_key,confidential,classified,internal | 50 | High-risk keywords |
| Email Pattern | regex | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | 30 | Email addresses |
| Credit Card Pattern | regex | `\b(?:\d{4}[-\s]?){3}\d{4}\b` | 60 | Credit card numbers |
| IP Address Pattern | regex | `\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b` | 20 | IP addresses |
| Phone Number Pattern | regex | `\b\d{3}[-.]?\d{3}[-.]?\d{4}\b` | 15 | Phone numbers |
| Restricted Models | model_restriction | gpt-4,claude-3-opus | 20 | Disallowed models |

## Usage

### Running the Consumer
```bash
# Via Docker Compose
docker-compose up consumer

# Development mode
cd services/consumer
python main.py
```

### Testing
```bash
# Test detection engine
python test_detection.py

# Send test messages to Kafka
python test_consumer.py
```

### Configuration
Environment variables (see `.env.example`):
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address
- `KAFKA_TOPIC`: Topic to consume from (`llm-traffic-logs`)
- `POSTGRES_*`: Database connection settings

## Performance

- **Throughput**: Handles 2000+ messages/second
- **Latency**: <500ms from Kafka receipt to DB write
- **Batch Processing**: Optimized bulk operations
- **Memory**: Rule caching reduces database queries

## Monitoring

Consumer exposes statistics via `get_stats()`:
- Messages processed/failed
- Processing rate per second
- Detection engine hit rates
- Rule trigger counts
- Database record counts