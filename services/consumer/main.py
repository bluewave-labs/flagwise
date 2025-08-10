#!/usr/bin/env python3
import logging
import signal
import sys
import time
from typing import Optional

from kafka_consumer import LLMTrafficConsumer
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/consumer.log') if '/app' in sys.path[0] else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global consumer instance for signal handling
consumer: Optional[LLMTrafficConsumer] = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}")
    if consumer:
        consumer.stop_consuming()
    sys.exit(0)

def wait_for_dependencies():
    """Wait for dependencies (Kafka, PostgreSQL) to be ready"""
    from database import DatabaseManager
    
    max_retries = 30
    retry_delay = 2
    
    logger.info("Waiting for dependencies...")
    
    # Test database connection
    db_manager = DatabaseManager()
    for attempt in range(max_retries):
        if db_manager.test_connection():
            logger.info("Database connection established")
            break
        else:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error("Database connection failed after maximum retries")
                sys.exit(1)
    
    # Test Kafka connection (basic check)
    try:
        from confluent_kafka import Consumer
        test_consumer = Consumer({
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'group.id': 'test-connection',
            'auto.offset.reset': 'latest'
        })
        
        # Get metadata to test connection
        metadata = test_consumer.list_topics(timeout=5)
        test_consumer.close()
        logger.info("Kafka connection established")
        
    except Exception as e:
        logger.error(f"Kafka connection failed: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    global consumer
    
    logger.info("Starting Shadow AI Detection Consumer")
    logger.info(f"Configuration: {settings.dict()}")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Wait for dependencies
        wait_for_dependencies()
        
        # Create and start consumer
        consumer = LLMTrafficConsumer()
        
        logger.info("Consumer starting...")
        consumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Consumer failed: {e}")
        sys.exit(1)
    finally:
        if consumer:
            stats = consumer.get_stats()
            logger.info(f"Final stats: {stats}")

if __name__ == "__main__":
    main()