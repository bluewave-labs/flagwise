#!/usr/bin/env python3
"""
Test script for the detection engine
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from uuid import uuid4
from models import DatabaseRecord
from detection_engine import DetectionEngine

def create_test_record(prompt: str, provider: str = "openai", model: str = "gpt-4") -> DatabaseRecord:
    """Create a test database record"""
    return DatabaseRecord(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        src_ip="192.168.1.100",
        provider=provider,
        model=model,
        prompt=prompt,
    )

def test_detection_engine():
    """Test the detection engine with various prompts"""
    print("Testing Detection Engine...")
    
    # Initialize detection engine
    engine = DetectionEngine()
    
    # Test cases
    test_cases = [
        # Normal prompts (should not be flagged)
        ("What is the capital of France?", "Normal query"),
        ("Explain quantum computing", "Technical query"),
        
        # Keyword rule triggers
        ("My password is secret123", "Contains password keyword"),
        ("The API_KEY for this service is xyz", "Contains API key keyword"),
        ("This is confidential information", "Contains confidential keyword"),
        
        # Regex rule triggers (emails, credit cards, etc.)
        ("Please send the report to john.doe@company.com", "Contains email address"),
        ("My credit card number is 4532-1234-5678-9012", "Contains credit card number"),
        ("The server IP is 192.168.1.100", "Contains IP address"),
        ("Call me at 555-123-4567", "Contains phone number"),
        
        # Model restriction (if configured)
        ("Test with restricted model", "Test restricted model", "gpt-4"),
        
        # Multiple rule triggers
        ("My password is secret123 and email is user@company.com with CC 4532-1234-5678-9012", 
         "Multiple triggers"),
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        if len(test_case) == 2:
            prompt, description = test_case
            record = create_test_record(prompt)
        elif len(test_case) == 4:
            prompt, description, provider, model = test_case
            record = create_test_record(prompt, provider, model)
        
        # Process single record
        processed_records = engine.process_batch([record])
        processed_record = processed_records[0]
        
        results.append({
            'test_id': i + 1,
            'description': description,
            'prompt': prompt[:100] + "..." if len(prompt) > 100 else prompt,
            'risk_score': processed_record.risk_score,
            'is_flagged': processed_record.is_flagged,
            'flag_reason': processed_record.flag_reason or "None"
        })
        
        print(f"\nTest {i+1}: {description}")
        print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"Risk Score: {processed_record.risk_score}")
        print(f"Flagged: {processed_record.is_flagged}")
        print(f"Reasons: {processed_record.flag_reason or 'None'}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("DETECTION ENGINE TEST SUMMARY")
    print(f"{'='*60}")
    
    flagged_count = sum(1 for r in results if r['is_flagged'])
    total_count = len(results)
    
    print(f"Total tests: {total_count}")
    print(f"Flagged: {flagged_count}")
    print(f"Clean: {total_count - flagged_count}")
    print(f"Flag rate: {flagged_count/total_count*100:.1f}%")
    
    # Print detection statistics
    print(f"\n{'='*60}")
    print("DETECTION ENGINE STATISTICS")
    print(f"{'='*60}")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return results

if __name__ == "__main__":
    try:
        test_detection_engine()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()