#!/usr/bin/env python3
"""
Test script for the Shadow AI Detection API
"""
import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
    return response.status_code == 200

def test_authentication():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication ===")
    
    # Test login with admin user
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", params=login_data)
    
    print(f"Login Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        print(f"Token received: {token_data['access_token'][:50]}...")
        return token_data['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_requests_endpoint(token):
    """Test requests endpoints"""
    print("\n=== Testing Requests Endpoints ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get requests with pagination
    response = requests.get(
        f"{BASE_URL}/requests",
        headers=headers,
        params={"page": 1, "page_size": 10}
    )
    
    print(f"Get Requests Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total requests: {data.get('total_count', 0)}")
        print(f"Items in page: {len(data.get('items', []))}")
        
        # Test with filters
        response = requests.get(
            f"{BASE_URL}/requests",
            headers=headers,
            params={"flagged": True, "page_size": 5}
        )
        
        if response.status_code == 200:
            flagged_data = response.json()
            print(f"Flagged requests: {flagged_data.get('total_count', 0)}")
    else:
        print(f"Get requests failed: {response.text}")

def test_stats_endpoint(token):
    """Test statistics endpoint"""
    print("\n=== Testing Statistics Endpoint ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/stats/totals", headers=headers)
    
    print(f"Stats Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Total requests: {stats.get('total_requests', 0)}")
        print(f"Flagged requests: {stats.get('flagged_requests', 0)}")
        print(f"Flagged rate: {stats.get('flagged_rate', 0)}%")
        print(f"Top providers: {stats.get('top_providers', [])}")
    else:
        print(f"Stats failed: {response.text}")

def test_rules_endpoint(token):
    """Test detection rules endpoints (Admin only)"""
    print("\n=== Testing Detection Rules Endpoints ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all rules
    response = requests.get(f"{BASE_URL}/rules", headers=headers)
    print(f"Get Rules Status: {response.status_code}")
    
    if response.status_code == 200:
        rules = response.json()
        print(f"Number of rules: {len(rules)}")
        
        # Create a new test rule
        new_rule = {
            "name": "Test API Rule",
            "description": "Test rule created via API",
            "rule_type": "keyword",
            "pattern": "test,api",
            "severity": "low",
            "points": 5,
            "is_active": True
        }
        
        create_response = requests.post(
            f"{BASE_URL}/rules",
            headers=headers,
            json=new_rule
        )
        
        print(f"Create Rule Status: {create_response.status_code}")
        if create_response.status_code == 200:
            created_rule = create_response.json()
            rule_id = created_rule['id']
            print(f"Created rule ID: {rule_id}")
            
            # Update the rule
            update_data = {"points": 10, "description": "Updated test rule"}
            update_response = requests.put(
                f"{BASE_URL}/rules/{rule_id}",
                headers=headers,
                json=update_data
            )
            print(f"Update Rule Status: {update_response.status_code}")
            
            # Delete the rule
            delete_response = requests.delete(
                f"{BASE_URL}/rules/{rule_id}",
                headers=headers
            )
            print(f"Delete Rule Status: {delete_response.status_code}")
    else:
        print(f"Get rules failed: {response.text}")

def test_unauthorized_access():
    """Test unauthorized access"""
    print("\n=== Testing Unauthorized Access ===")
    
    # Test without token
    response = requests.get(f"{BASE_URL}/requests")
    print(f"No token status: {response.status_code}")
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/requests", headers=headers)
    print(f"Invalid token status: {response.status_code}")
    
    # Test read-only user trying admin endpoint
    login_data = {"username": "viewer", "password": "viewer123"}
    response = requests.post(f"{BASE_URL}/auth/login", params=login_data)
    
    if response.status_code == 200:
        viewer_token = response.json()['access_token']
        headers = {"Authorization": f"Bearer {viewer_token}"}
        
        # Try to access admin-only endpoint
        response = requests.get(f"{BASE_URL}/rules", headers=headers)
        print(f"Read-only user admin access status: {response.status_code}")

def main():
    """Main test function"""
    print("Shadow AI Detection API Test Suite")
    print("=" * 50)
    
    # Test health endpoint first
    if not test_health():
        print("Health check failed. Make sure the API is running.")
        return
    
    # Test authentication
    admin_token = test_authentication()
    if not admin_token:
        print("Authentication failed. Cannot continue with other tests.")
        return
    
    # Test other endpoints
    test_requests_endpoint(admin_token)
    test_stats_endpoint(admin_token)
    test_rules_endpoint(admin_token)
    test_unauthorized_access()
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()