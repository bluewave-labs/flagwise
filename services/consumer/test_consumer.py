#!/usr/bin/env python3
"""
Test script to simulate LLM traffic messages for the Kafka consumer
"""
import json
import time
from datetime import datetime
from confluent_kafka import Producer
from uuid import uuid4

def create_test_message(provider: str = "openai", model: str = "gpt-4") -> dict:
    """Create a test LLM request message"""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "src_ip": f"192.168.1.{100 + (int(time.time()) % 50)}",  # Random IP in range
        "provider": provider,
        "model": model,
        "endpoint": f"https://api.{provider}.com/v1/chat/completions",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer sk-***",
            "Content-Type": "application/json",
            "User-Agent": "company-app/1.0"
        },
        "prompt": f"Test prompt {uuid4().hex[:8]} - What is the capital of France?",
        "status_code": 200,
        "duration_ms": int(300 + (time.time() % 200)),  # 300-500ms
    }

def send_test_messages():
    """Send test messages to Kafka topic"""
    producer_config = {
        'bootstrap.servers': 'localhost:9092',  # External port
    }
    
    producer = Producer(producer_config)
    topic = 'llm-traffic-logs'
    
    providers_models = [
        ("openai", "gpt-4"),
        ("openai", "gpt-3.5-turbo"),
        ("anthropic", "claude-3-sonnet"),
        ("anthropic", "claude-3-haiku"),
        ("google", "gemini-pro"),
    ]
    
    print(f"Sending test messages to topic: {topic}")
    
    try:
        for i in range(10):  # Send 10 test messages
            provider, model = providers_models[i % len(providers_models)]
            message = create_test_message(provider, model)
            
            # Add some sensitive data occasionally for testing detection
            if i % 3 == 0:
                message["prompt"] = "My password is secret123 and my email is user@company.com"
            elif i % 4 == 0:
                message["prompt"] = "Please send the report to john.doe@company.com with API_KEY abc123"
            
            message_json = json.dumps(message)
            
            # Send message
            producer.produce(
                topic,
                key=str(uuid4()),
                value=message_json,
                callback=lambda err, msg: print(f"Message sent: {msg.topic()}[{msg.partition()}] @ {msg.offset()}" if not err else f"Error: {err}")
            )
            
            print(f"Sent message {i+1}: {provider}/{model} from {message['src_ip']}")
            time.sleep(1)  # Send one message per second
        
        # Wait for all messages to be delivered
        producer.flush()
        print("All test messages sent successfully!")
        
    except Exception as e:
        print(f"Error sending messages: {e}")
    finally:
        producer.flush()

if __name__ == "__main__":
    send_test_messages()