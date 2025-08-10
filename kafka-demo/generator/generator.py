#!/usr/bin/env python3
"""
LLM Traffic Data Generator for Kafka Demo
Generates realistic LLM API request data matching the Shadow AI database schema
"""

import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List
import os
import logging

from kafka import KafkaProducer
from faker import Faker

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

class LLMTrafficGenerator:
    def __init__(self):
        self.kafka_broker = os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.getenv('KAFKA_TOPIC', 'llm-traffic-logs')
        self.generation_interval = int(os.getenv('GENERATION_INTERVAL', '2'))
        
        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=[self.kafka_broker],
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            key_serializer=lambda x: str(x).encode('utf-8') if x else None,
        )
        
        logger.info(f"Initialized LLM Traffic Generator")
        logger.info(f"Kafka Broker: {self.kafka_broker}")
        logger.info(f"Kafka Topic: {self.kafka_topic}")
        logger.info(f"Generation Interval: {self.generation_interval}s")

    def get_ai_providers(self) -> List[Dict]:
        """Return list of AI providers with realistic endpoints"""
        return [
            {
                "name": "openai",
                "endpoints": [
                    "https://api.openai.com/v1/chat/completions",
                    "https://api.openai.com/v1/completions",
                    "https://api.openai.com/v1/embeddings"
                ],
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "text-embedding-ada-002"]
            },
            {
                "name": "anthropic", 
                "endpoints": [
                    "https://api.anthropic.com/v1/messages",
                    "https://api.anthropic.com/v1/complete"
                ],
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1", "claude-instant-1.2"]
            },
            {
                "name": "google",
                "endpoints": [
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
                ],
                "models": ["gemini-pro", "gemini-pro-vision", "palm-2-chat-bison", "palm-2-text-bison"]
            },
            {
                "name": "cohere",
                "endpoints": [
                    "https://api.cohere.ai/v1/generate",
                    "https://api.cohere.ai/v1/embed",
                    "https://api.cohere.ai/v1/chat"
                ],
                "models": ["command", "command-light", "embed-english-v2.0", "embed-multilingual-v2.0"]
            },
            {
                "name": "mistral",
                "endpoints": [
                    "https://api.mistral.ai/v1/chat/completions",
                    "https://api.mistral.ai/v1/embeddings"
                ],
                "models": ["mistral-large-latest", "mistral-medium", "mistral-small", "mistral-embed"]
            },
            {
                "name": "huggingface",
                "endpoints": [
                    "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                    "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
                ],
                "models": ["microsoft/DialoGPT-medium", "facebook/blenderbot-400M-distill", "microsoft/DialoGPT-large"]
            },
            {
                "name": "together",
                "endpoints": [
                    "https://api.together.xyz/inference",
                    "https://api.together.xyz/v1/chat/completions"
                ],
                "models": ["meta-llama/Llama-2-70b-chat-hf", "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
            },
            {
                "name": "replicate",
                "endpoints": [
                    "https://api.replicate.com/v1/predictions",
                    "https://api.replicate.com/v1/models"
                ],
                "models": ["meta/llama-2-70b-chat", "stability-ai/sdxl", "replicate/flan-t5-xl"]
            },
            {
                "name": "perplexity",
                "endpoints": [
                    "https://api.perplexity.ai/chat/completions"
                ],
                "models": ["pplx-7b-online", "pplx-70b-online", "pplx-7b-chat", "pplx-70b-chat"]
            },
            {
                "name": "groq",
                "endpoints": [
                    "https://api.groq.com/openai/v1/chat/completions"
                ],
                "models": ["mixtral-8x7b-32768", "llama2-70b-4096", "gemma-7b-it"]
            }
        ]

    def get_realistic_prompts(self) -> List[str]:
        """Return list of realistic prompts for different use cases"""
        return [
            "Analyze the following code for security vulnerabilities",
            "Summarize the key points from the quarterly financial report",
            "Generate a professional email response to customer complaint",
            "What are the best practices for data encryption in cloud storage?",
            "Translate this technical document from English to Spanish",
            "Create a python function that validates email addresses",
            "Explain machine learning concepts in simple terms",
            "Draft a project proposal for implementing AI chatbot",
            "Review this contract and highlight potential risks",
            "Generate test cases for the user authentication system",
            "What are the GDPR compliance requirements for data processing?",
            "Create a database schema for e-commerce platform",
            "Analyze user feedback sentiment from customer reviews",
            "Generate API documentation from this code snippet",
            "Explain the differences between SQL and NoSQL databases",
            "Create a disaster recovery plan for cloud infrastructure",
            "Generate unit tests for this JavaScript function",
            "What are the security implications of using third-party APIs?",
            "Draft a technical specification for microservices architecture",
            "Analyze performance bottlenecks in this Python code"
        ]

    def get_realistic_responses(self) -> List[str]:
        """Return list of realistic AI responses"""
        return [
            "I've analyzed the code and found several potential security vulnerabilities including SQL injection risks and improper input validation. Here are the recommended fixes...",
            "Based on the quarterly report, here are the key financial highlights: Revenue increased 15% year-over-year, operating margins improved to 23%, and cash flow remains strong...",
            "Thank you for bringing this concern to our attention. We sincerely apologize for the inconvenience you experienced. Here's how we plan to resolve this issue...",
            "For cloud storage data encryption, I recommend implementing these best practices: 1) Use AES-256 encryption, 2) Implement proper key management, 3) Enable encryption in transit and at rest...",
            "Here's the Spanish translation of the technical document: [Translated content would follow with proper technical terminology and formatting]...",
            "Here's a Python function that validates email addresses using regex and additional checks for common edge cases...",
            "Machine learning is like teaching a computer to recognize patterns. Think of it as showing a child thousands of pictures of cats until they can identify cats in new photos...",
            "Project Proposal: AI Chatbot Implementation. Executive Summary: This proposal outlines the development of an intelligent chatbot system to improve customer service efficiency...",
            "I've reviewed the contract and identified these potential risks: 1) Ambiguous liability clauses, 2) Insufficient data protection provisions, 3) Unclear termination conditions...",
            "Here's a comprehensive set of test cases for the user authentication system covering positive and negative scenarios, edge cases, and security validations..."
        ]

    def generate_realistic_headers(self) -> Dict:
        """Generate realistic HTTP headers"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "curl/7.68.0",
            "python-requests/2.31.0",
            "axios/1.4.0",
            "node-fetch/3.3.1"
        ]
        
        return {
            "user-agent": random.choice(user_agents),
            "content-type": "application/json",
            "accept": "application/json",
            "authorization": f"Bearer sk-{fake.lexify('?' * 48)}",
            "x-forwarded-for": fake.ipv4(),
            "x-request-id": str(uuid.uuid4())
        }



    def generate_realistic_duration(self) -> int:
        """Generate realistic API response duration"""
        base_duration = 200  # Base 200ms
        variance = random.randint(-100, 800)  # Add realistic variance
        
        return max(50, int(base_duration + variance))

    def generate_llm_request(self) -> Dict:
        """Generate a realistic LLM request matching the database schema"""
        providers = self.get_ai_providers()
        provider_info = random.choice(providers)
        provider = provider_info["name"]
        model = random.choice(provider_info["models"])
        endpoint = random.choice(provider_info["endpoints"])
        
        prompts = self.get_realistic_prompts()
        responses = self.get_realistic_responses()
        prompt = random.choice(prompts)
        response = random.choice(responses)
        
        # Calculate realistic metrics
        duration_ms = self.generate_realistic_duration()
        
        # Generate realistic status codes (mostly 200, some errors)
        status_code = random.choices([200, 400, 401, 429, 500, 502], weights=[85, 5, 3, 4, 2, 1])[0]
        
        # Generate request data matching exact database schema
        request_data = {
            # Core identification
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": fake.ipv4(),
            
            # Provider information
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "method": "POST",
            "headers": self.generate_realistic_headers(),
            
            # Request/Response content
            "prompt": prompt,
            "response": response if status_code == 200 else None,
            
            
            "duration_ms": duration_ms,
            "status_code": status_code,
            
            # Risk analysis fields (will be populated by the ingestion system)
            "risk_score": 0,  # Will be calculated by the detection system
            "is_flagged": False,  # Will be determined by detection rules
            "flag_reason": None,
            
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return request_data

    def run(self):
        """Run the data generator continuously"""
        logger.info("Starting LLM traffic generation...")
        
        try:
            while True:
                # Generate and send request data
                request_data = self.generate_llm_request()
                
                # Use request ID as message key for partitioning
                message_key = request_data["id"]
                
                # Send to Kafka
                future = self.producer.send(
                    self.kafka_topic,
                    key=message_key,
                    value=request_data
                )
                
                # Wait for message to be sent
                future.get(timeout=10)
                
                logger.info(f"Generated LLM request: {request_data['provider']}/{request_data['model']} "
                           f"from {request_data['src_ip']} ({request_data['duration_ms']}ms)")
                
                # Wait before generating next request
                time.sleep(self.generation_interval)
                
        except KeyboardInterrupt:
            logger.info("Shutting down generator...")
        except Exception as e:
            logger.error(f"Error in generator: {e}")
        finally:
            self.producer.close()

if __name__ == "__main__":
    generator = LLMTrafficGenerator()
    generator.run()