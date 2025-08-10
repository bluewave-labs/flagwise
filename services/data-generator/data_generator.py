#!/usr/bin/env python3

import json
import time
import random
import logging
from datetime import datetime, timezone
from confluent_kafka import Producer
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LLM Providers and Models
PROVIDERS = {
    "openai": [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "text-embedding-ada-002",
        "dall-e-3"
    ],
    "anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307",
        "claude-instant-v1"
    ],
    "google": [
        "palm-2-chat-bison",
        "palm-2-text-bison",
        "gemini-pro",
        "gemini-pro-vision"
    ],
    "cohere": [
        "embed-multilingual-v2.0",
        "embed-english-v2.0",
        "command-nightly",
        "command"
    ],
    "huggingface": [
        "microsoft/DialoGPT-medium",
        "gpt2",
        "facebook/blenderbot-400M-distill"
    ]
}

# Sample prompts and responses
SAMPLE_DATA = [
    {
        "prompt": "What is machine learning?",
        "response": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task.",
        "risk_level": "low"
    },
    {
        "prompt": "How do I hack into a database?",
        "response": "I can't provide information about unauthorized access to databases. However, I can help you learn about database security, ethical hacking certifications, or legitimate penetration testing.",
        "risk_level": "high"
    },
    {
        "prompt": "Explain quantum computing",
        "response": "Quantum computing uses quantum mechanical phenomena like superposition and entanglement to process information in ways that classical computers cannot.",
        "risk_level": "low"
    },
    {
        "prompt": "Generate fake credit card numbers",
        "response": "I cannot generate real credit card numbers as that would be illegal. For testing purposes, you should use officially provided test card numbers from payment processors.",
        "risk_level": "high"
    },
    {
        "prompt": "What is the weather like today?",
        "response": "I don't have access to real-time weather data. You can check current weather conditions using weather apps or websites like Weather.com or AccuWeather.",
        "risk_level": "low"
    },
    {
        "prompt": "How to build a bomb?",
        "response": "I cannot and will not provide information about creating explosive devices or weapons. This type of information could be used to harm others.",
        "risk_level": "critical"
    },
    {
        "prompt": "Summarize this document for me",
        "response": "I'd be happy to help summarize a document. Please share the document or its content, and I'll provide a concise summary highlighting the key points.",
        "risk_level": "low"
    },
    {
        "prompt": "What is my social security number?",
        "response": "I don't have access to your personal information like social security numbers. Please keep such sensitive information private and secure.",
        "risk_level": "medium"
    }
]

# IP address ranges for realistic simulation
IP_RANGES = [
    "192.168.1",
    "10.0.0", 
    "172.16.0",
    "203.0.113",
    "198.51.100",
    "203.113.0"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "FlagWise-Client/1.0",
    "Python-requests/2.28.1",
    "curl/7.68.0",
    "PostmanRuntime/7.29.2"
]

class LLMDataGenerator:
    def __init__(self):
        self.kafka_config = {
            'bootstrap.servers': 'kafka:29092',
            'client.id': 'flagwise-data-generator'
        }
        self.producer = Producer(self.kafka_config)
        self.topic = 'llm-traffic-logs'
        
    def generate_request_id(self):
        """Generate a unique request ID"""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    def generate_ip_address(self):
        """Generate a realistic IP address"""
        base = random.choice(IP_RANGES)
        return f"{base}.{random.randint(1, 254)}"
    
    def generate_user_id(self):
        """Generate a user ID"""
        return f"user_{random.randint(1000, 9999)}"
    
    def calculate_risk_score(self, sample_data):
        """Calculate risk score based on content"""
        risk_mapping = {
            "low": random.randint(0, 25),
            "medium": random.randint(26, 50),
            "high": random.randint(51, 85),
            "critical": random.randint(86, 100)
        }
        return risk_mapping.get(sample_data["risk_level"], 10)
    
    def get_flagged_rules(self, risk_score):
        """Generate flagged rules based on risk score"""
        if risk_score > 75:
            return ["High Risk Content", "Policy Violation"]
        elif risk_score > 50:
            return ["Restricted Models", "Unusual Activity"]
        elif risk_score > 25:
            return ["Rate Limit Warning"]
        return []
    
    def generate_llm_request(self):
        """Generate a realistic LLM request"""
        # Select random provider and model
        provider = random.choice(list(PROVIDERS.keys()))
        model = random.choice(PROVIDERS[provider])
        
        # Select sample data
        sample_data = random.choice(SAMPLE_DATA)
        
        # Generate token counts
        prompt_tokens = random.randint(20, 200)
        completion_tokens = random.randint(10, 300)
        total_tokens = prompt_tokens + completion_tokens
        
        # Calculate risk score
        risk_score = self.calculate_risk_score(sample_data)
        flagged_rules = self.get_flagged_rules(risk_score)
        
        # Generate request data
        request_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": self.generate_request_id(),
            "src_ip": self.generate_ip_address(),
            "user_id": self.generate_user_id(),
            "provider": provider,
            "model": model,
            "prompt": sample_data["prompt"],
            "response": sample_data["response"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "risk_score": risk_score,
            "is_flagged": risk_score > 50,
            "flagged_rules": flagged_rules,
            "metadata": {
                "user_agent": random.choice(USER_AGENTS),
                "cost_usd": round(total_tokens * 0.00001, 4),  # Rough cost estimate
                "response_time_ms": random.randint(200, 2000),
                "session_id": f"sess_{random.randint(1000, 9999)}"
            }
        }
        
        return request_data
    
    def delivery_report(self, err, msg):
        """Kafka message delivery callback"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')
    
    def send_request(self, request_data):
        """Send request to Kafka"""
        try:
            message = json.dumps(request_data)
            self.producer.produce(
                self.topic,
                key=request_data["request_id"],
                value=message,
                callback=self.delivery_report
            )
            self.producer.poll(0)  # Trigger delivery callbacks
            
            logger.info(f"Generated LLM request: {request_data['provider']}/{request_data['model']} "
                       f"from {request_data['src_ip']} ({request_data['total_tokens']} tokens, "
                       f"risk: {request_data['risk_score']})")
                       
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
    
    def run(self, interval=3):
        """Run the data generator"""
        logger.info("Starting FlagWise LLM Data Generator")
        logger.info(f"Kafka servers: {self.kafka_config['bootstrap.servers']}")
        logger.info(f"Topic: {self.topic}")
        logger.info(f"Generation interval: {interval} seconds")
        
        try:
            while True:
                request_data = self.generate_llm_request()
                self.send_request(request_data)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Shutting down data generator...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.producer.flush()
            logger.info("Data generator stopped")

if __name__ == "__main__":
    generator = LLMDataGenerator()
    
    # Generate data every 3 seconds by default
    interval = 3
    generator.run(interval)