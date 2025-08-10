import json
import logging
from typing import List, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
import time

from config import settings
from models import LLMRequest, DatabaseRecord
from database import DatabaseManager
from detection_engine import DetectionEngine
from alert_service import slack_alert_service

logger = logging.getLogger(__name__)

class LLMTrafficConsumer:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.detection_engine = DetectionEngine()
        
        # Kafka consumer configuration
        self.consumer_config = {
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'group.id': settings.kafka_group_id,
            'auto.offset.reset': settings.kafka_auto_offset_reset,
            'session.timeout.ms': settings.session_timeout_ms,
            'heartbeat.interval.ms': settings.heartbeat_interval_ms,
            'max.poll.interval.ms': 300000,  # 5 minutes
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,  # Commit every 5 seconds
        }
        
        self.consumer = Consumer(self.consumer_config)
        self.running = False
        
        # Metrics
        self.messages_processed = 0
        self.messages_failed = 0
        self.start_time = time.time()
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        try:
            # Test database connection first
            if not self.db_manager.test_connection():
                raise Exception("Database connection failed")
            
            # Subscribe to topic
            self.consumer.subscribe([settings.kafka_topic])
            logger.info(f"Started consuming from topic: {settings.kafka_topic}")
            logger.info(f"Consumer group: {settings.kafka_group_id}")
            
            self.running = True
            self._consume_loop()
            
        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
            raise
        finally:
            self.cleanup()
    
    def stop_consuming(self):
        """Gracefully stop the consumer"""
        logger.info("Stopping consumer...")
        self.running = False
    
    def _consume_loop(self):
        """Main consumption loop"""
        batch_records = []
        batch_size = min(settings.max_poll_records, 100)  # Process in smaller batches
        
        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    # No message within timeout, process any pending batch
                    if batch_records:
                        self._process_batch(batch_records)
                        batch_records = []
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"End of partition reached: {msg.topic()}[{msg.partition()}]")
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        continue
                
                # Process message
                try:
                    record = self._parse_message(msg)
                    if record:
                        batch_records.append(record)
                        
                        # Process batch when it reaches target size
                        if len(batch_records) >= batch_size:
                            self._process_batch(batch_records)
                            batch_records = []
                            
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    self.messages_failed += 1
                    self._send_to_dlq(msg, str(e))
                    continue
                
        except KafkaException as e:
            logger.error(f"Kafka exception: {e}")
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            # Process any remaining records
            if batch_records:
                self._process_batch(batch_records)
    
    def _parse_message(self, msg) -> Optional[DatabaseRecord]:
        """Parse Kafka message into LLMRequest and convert to DatabaseRecord"""
        try:
            # Decode message value
            message_data = json.loads(msg.value().decode('utf-8'))
            
            # Create LLMRequest from message data
            llm_request = LLMRequest(**message_data)
            
            # Convert to DatabaseRecord
            db_record = DatabaseRecord.from_llm_request(llm_request)
            
            logger.debug(f"Parsed message for {db_record.provider}/{db_record.model} from {db_record.src_ip}")
            return db_record
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            raise
    
    def _process_batch(self, records: List[DatabaseRecord]):
        """Process a batch of records"""
        if not records:
            return
            
        try:
            # Run detection engine on batch
            processed_records = self.detection_engine.process_batch(records)
            
            # Send alerts for flagged records
            self._send_alerts(processed_records)
            
            # Bulk insert to database
            successful_inserts = self.db_manager.bulk_insert_llm_requests(processed_records)
            
            self.messages_processed += successful_inserts
            
            if successful_inserts < len(records):
                self.messages_failed += len(records) - successful_inserts
                logger.warning(f"Only {successful_inserts}/{len(records)} records inserted successfully")
            else:
                logger.debug(f"Successfully processed batch of {len(records)} records")
                
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            self.messages_failed += len(records)
    
    def _send_alerts(self, records: List[DatabaseRecord]):
        """Send alerts for flagged records"""
        flagged_count = 0
        alerts_sent = 0
        
        for record in records:
            if record.is_flagged:
                flagged_count += 1
                try:
                    if slack_alert_service.send_alert(record):
                        alerts_sent += 1
                except Exception as e:
                    logger.error(f"Failed to send alert for record {record.id}: {e}")
        
        if flagged_count > 0:
            logger.info(f"Processed {flagged_count} flagged records, sent {alerts_sent} alerts")
    
    def _send_to_dlq(self, msg, error_reason: str):
        """Send failed message to dead letter queue"""
        # For now, just log the failed message
        # In production, you might want to send to a DLQ topic
        logger.error(f"Message sent to DLQ. Reason: {error_reason}")
        logger.debug(f"Failed message: {msg.value().decode('utf-8', errors='replace')}")
    
    def get_stats(self) -> dict:
        """Get consumer statistics"""
        uptime = time.time() - self.start_time
        rate = self.messages_processed / uptime if uptime > 0 else 0
        
        # Get detection engine stats
        detection_stats = self.detection_engine.get_statistics()
        
        # Get alert stats
        alert_stats = slack_alert_service.get_alert_stats()
        
        return {
            'messages_processed': self.messages_processed,
            'messages_failed': self.messages_failed,
            'uptime_seconds': uptime,
            'processing_rate_per_second': rate,
            'total_db_records': self.db_manager.get_record_count(),
            'detection_stats': detection_stats,
            'alert_stats': alert_stats
        }
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'consumer'):
            logger.info("Closing Kafka consumer...")
            self.consumer.close()
        
        stats = self.get_stats()
        logger.info(f"Consumer stats: {stats}")
        logger.info("Consumer cleanup complete")