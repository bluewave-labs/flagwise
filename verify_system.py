#!/usr/bin/env python3
"""
Quick system verification script
"""
import psycopg2
import json
from datetime import datetime, timedelta

def verify_data_flow():
    """Verify that data is flowing through the system"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="shadow_ai",
            user="shadow_user",
            password="shadow_pass"
        )
        cursor = conn.cursor()
        
        # Check recent records
        cursor.execute("""
            SELECT COUNT(*) as total_count,
                   COUNT(CASE WHEN is_flagged THEN 1 END) as flagged_count,
                   AVG(risk_score) as avg_risk_score,
                   MAX(timestamp) as latest_record
            FROM llm_requests 
            WHERE timestamp >= NOW() - INTERVAL '10 minutes'
        """)
        
        result = cursor.fetchone()
        
        print("🔍 Shadow AI Detection Server - System Verification")
        print("=" * 60)
        
        if result[0] > 0:
            print(f"✅ Total requests (last 10 min): {result[0]}")
            print(f"🚨 Flagged requests: {result[1]}")
            print(f"📊 Average risk score: {result[2]:.1f}")
            print(f"⏰ Latest record: {result[3]}")
            
            # Check risk distribution
            cursor.execute("""
                SELECT risk_score, COUNT(*) as count
                FROM llm_requests 
                WHERE timestamp >= NOW() - INTERVAL '10 minutes'
                GROUP BY risk_score 
                ORDER BY risk_score DESC
                LIMIT 10
            """)
            
            risk_dist = cursor.fetchall()
            print("\n📈 Risk Score Distribution:")
            for score, count in risk_dist:
                print(f"   Score {score}: {count} requests")
            
            # Check IP sources
            cursor.execute("""
                SELECT src_ip, COUNT(*) as count
                FROM llm_requests 
                WHERE timestamp >= NOW() - INTERVAL '10 minutes'
                GROUP BY src_ip 
                ORDER BY count DESC
                LIMIT 5
            """)
            
            ip_dist = cursor.fetchall()
            print("\n🌐 Top Source IPs:")
            for ip, count in ip_dist:
                print(f"   {ip}: {count} requests")
            
            # Check personas
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN src_ip LIKE '10.0.%' THEN 'Corporate Office'
                        WHEN src_ip LIKE '192.168.%' THEN 'Remote Workers'
                        WHEN src_ip LIKE '172.16.%' THEN 'Contractors'
                        WHEN src_ip LIKE '203.0.113.%' OR src_ip LIKE '198.51.100.%' THEN 'Suspicious'
                        ELSE 'Other'
                    END as network_type,
                    COUNT(*) as count
                FROM llm_requests 
                WHERE timestamp >= NOW() - INTERVAL '10 minutes'
                GROUP BY network_type
                ORDER BY count DESC
            """)
            
            network_dist = cursor.fetchall()
            print("\n🏢 Network Distribution:")
            for network, count in network_dist:
                print(f"   {network}: {count} requests")
                
            print("\n✅ System is working correctly!")
            print("🎯 Visit http://localhost:3000 to see the dashboard")
            print("🚀 Use 'make trigger-incidents' to simulate security events")
            
        else:
            print("⚠️  No recent data found. Data generator might be starting up...")
            print("💡 Wait a few more seconds and try again")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure all services are running with 'make status'")

if __name__ == "__main__":
    verify_data_flow()