#!/usr/bin/env python3
"""
Test script for Slack alerting functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from uuid import uuid4
from models import DatabaseRecord
from alert_service import SlackAlertService
from config import settings

def create_test_record(prompt: str, risk_score: int = 75, flag_reason: str = "Test Alert") -> DatabaseRecord:
    """Create a test database record for alerting"""
    return DatabaseRecord(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        src_ip="192.168.1.100",
        provider="openai",
        model="gpt-4",
        prompt=prompt,
        risk_score=risk_score,
        is_flagged=True,
        flag_reason=flag_reason,
    )

def test_slack_alerts():
    """Test Slack alert functionality"""
    print("Testing Slack Alert Service...")
    print(f"Webhook URL configured: {bool(settings.slack_webhook_url and settings.slack_webhook_url != 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK')}")
    
    # Initialize alert service
    alert_service = SlackAlertService()
    
    # Test different alert scenarios
    test_cases = [
        {
            "name": "High Risk Alert",
            "prompt": "My password is secret123 and my email is user@company.com. Please help me hack into the system.",
            "risk_score": 85,
            "flag_reason": "Critical Keywords, Email Pattern"
        },
        {
            "name": "Medium Risk Alert",
            "prompt": "Can you help me with API_KEY authentication? My key is abc-123-def-456.",
            "risk_score": 65,
            "flag_reason": "API Key Pattern"
        },
        {
            "name": "Low Risk Alert (Should Not Send)",
            "prompt": "What is the capital of France?",
            "risk_score": 25,
            "flag_reason": "None"
        },
        {
            "name": "Credit Card Alert",
            "prompt": "My credit card number is 4532-1234-5678-9012. Can you help me process a payment?",
            "risk_score": 90,
            "flag_reason": "Credit Card Pattern, Financial Keywords"
        }
    ]
    
    print(f"\nTesting {len(test_cases)} alert scenarios:")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {case['name']} ---")
        
        # Create test record
        record = create_test_record(
            prompt=case['prompt'],
            risk_score=case['risk_score'],
            flag_reason=case['flag_reason']
        )
        
        print(f"Record ID: {record.id}")
        print(f"Risk Score: {record.risk_score}")
        print(f"Prompt: {record.prompt[:100]}{'...' if len(record.prompt) > 100 else ''}")
        
        # Test if alert should be sent
        should_send = alert_service.should_send_alert(record)
        print(f"Should send alert: {should_send}")
        
        if should_send:
            # Try to send alert
            try:
                result = alert_service.send_alert(record)
                print(f"Alert sent: {result}")
                
                if not result:
                    print("Alert was not sent (likely due to configuration or rate limiting)")
                    
            except Exception as e:
                print(f"Alert failed with error: {e}")
        else:
            print("Alert skipped (below threshold or not configured)")
        
        print("-" * 50)
    
    # Test rate limiting
    print("\n=== Rate Limiting Test ===")
    print("Sending multiple alerts to test rate limiting...")
    
    for i in range(8):  # Try to send 8 alerts (should hit 5/minute limit)
        record = create_test_record(
            prompt=f"Test rate limit alert #{i+1}",
            risk_score=75,
            flag_reason="Rate Limit Test"
        )
        
        result = alert_service.send_alert(record)
        print(f"Alert {i+1}: {'✓' if result else '✗'}")
    
    # Get alert statistics
    print("\n=== Alert Statistics ===")
    stats = alert_service.get_alert_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    try:
        test_slack_alerts()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()