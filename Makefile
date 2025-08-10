.PHONY: help build up down logs clean restart

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all services
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs from all services
	docker-compose logs -f

logs-consumer: ## Show consumer service logs
	docker-compose logs -f consumer

logs-api: ## Show API service logs
	docker-compose logs -f api

logs-web: ## Show web service logs
	docker-compose logs -f web

clean: ## Remove all containers and volumes
	docker-compose down -v
	docker system prune -f

restart: ## Restart all services
	docker-compose restart

restart-consumer: ## Restart consumer service
	docker-compose restart consumer

restart-api: ## Restart API service
	docker-compose restart api

restart-web: ## Restart web service
	docker-compose restart web

dev-consumer: ## Run consumer in development mode
	cd services/consumer && python -m pip install -r requirements.txt && python main.py

dev-api: ## Run API in development mode
	cd services/api && python -m pip install -r requirements.txt && uvicorn main:app --reload --port 8000

dev-web: ## Run web in development mode
	cd services/web && npm install && npm start

setup: ## Initial setup - copy env file and build
	cp .env.example .env
	docker-compose build

kafka-topics: ## List Kafka topics
	docker exec shadow-ai-kafka kafka-topics --bootstrap-server localhost:9092 --list

kafka-create-topic: ## Create llm-traffic-logs topic
	docker exec shadow-ai-kafka kafka-topics --bootstrap-server localhost:9092 --create --topic llm-traffic-logs --partitions 3 --replication-factor 1

db-shell: ## Connect to PostgreSQL shell
	docker exec -it shadow-ai-postgres psql -U shadow_user -d shadow_ai

# Data Generation Commands
start-generator: ## Start the test data generator
	docker-compose --profile generator up -d data-generator

stop-generator: ## Stop the test data generator
	docker-compose stop data-generator

logs-generator: ## Show data generator logs
	docker-compose logs -f data-generator

restart-generator: ## Restart data generator
	docker-compose restart data-generator

trigger-incidents: ## Run interactive incident simulator
	cd data-generator && python incident_trigger.py

demo: ## Start full system with data generation
	docker-compose --profile generator up -d
	@echo "🚀 Shadow AI Detection Server is starting..."
	@echo "📊 Dashboard: http://localhost:3000"
	@echo "🔧 API: http://localhost:8000"
	@echo "📈 Data generator is running in background"
	@echo "🎯 Run 'make trigger-incidents' to simulate security incidents"

full-demo: demo ## Alias for demo

status: ## Show status of all services
	docker-compose ps

dev-generator: ## Run data generator in development mode
	cd data-generator && python -m pip install -r requirements.txt && python data_generator.py