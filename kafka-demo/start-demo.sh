#!/bin/bash

echo "🚀 Starting Shadow AI Kafka Demo Environment..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start the services
echo "📦 Starting Kafka, Zookeeper, and Data Generator..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "🔥 Demo environment is ready!"
echo ""
echo "📋 Connection Details:"
echo "   Kafka Broker: localhost:9092"
echo "   Topic: llm-traffic-logs"
echo "   Data Generation: Every 2 seconds"
echo ""
echo "🔧 Useful Commands:"
echo "   View generator logs: docker-compose logs -f llm-traffic-generator"
echo "   Stop environment: docker-compose down"
echo "   View all logs: docker-compose logs -f"
echo ""
echo "📈 Next Steps:"
echo "1. Configure Shadow AI to connect to localhost:9092"
echo "2. Enable Kafka ingestion in Shadow AI settings"
echo "3. Watch real-time LLM traffic in the dashboard!"
echo ""