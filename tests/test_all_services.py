#!/usr/bin/env python3.11
"""Final test script with correct endpoint paths"""
import requests
import json
from datetime import datetime

SERVICES = {
    "Product Service": "http://localhost:8001",
    "Creative Service": "http://localhost:8002",
    "Strategy Service": "http://localhost:8003",
    "Meta Service": "http://localhost:8004",
    "Logs Service": "http://localhost:8005",
    "Schema Validator": "http://localhost:8006",
    "Optimizer Service": "http://localhost:8007",
}

def test_health_checks():
    """Test all health check endpoints"""
    print("\n📊 Health Check Status:")
    print("-" * 70)
    healthy = 0
    for name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {data.get('status', 'healthy')}")
                healthy += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    return healthy

def test_product_service():
    """Test Product Service"""
    print("\n📦 Product Service - /select_products")
    try:
        payload = {
            "campaign_objective": "sales",
            "target_audience": "young professionals aged 25-40",
            "budget": 10000,
            "product_categories": ["electronics", "accessories"]
        }
        response = requests.post("http://localhost:8001/select_products", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Selected {len(data['products'])} products")
            if data['products']:
                print(f"  📌 Sample product: {data['products'][0]['name']}")
                print(f"     Price: ${data['products'][0]['price']}")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_creative_service():
    """Test Creative Service"""
    print("\n🎨 Creative Service - /generate_creatives")
    try:
        payload = {
            "product_name": "Premium Wireless Headphones",
            "product_description": "High-quality audio with noise cancellation",
            "target_audience": "music lovers and audiophiles",
            "platform": "facebook",
            "tone": "exciting"
        }
        response = requests.post("http://localhost:8002/generate_creatives", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Generated {len(data['creatives'])} creatives")
            if data['creatives']:
                creative = data['creatives'][0]
                print(f"  📌 Creative ID: {creative['creative_id']}")
                print(f"     Headline: {creative['headline'][:60]}...")
                print(f"     Body: {creative['body'][:60]}...")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_strategy_service():
    """Test Strategy Service"""
    print("\n🎯 Strategy Service - /generate_strategy")
    try:
        payload = {
            "campaign_goal": "awareness",
            "total_budget": 10000,
            "duration_days": 30,
            "target_audience": {
                "age_range": "25-45",
                "interests": ["technology", "business"],
                "locations": ["US", "UK", "CA"]
            },
            "platforms": ["facebook", "instagram", "google"]
        }
        response = requests.post("http://localhost:8003/generate_strategy", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Strategy ID: {data['strategy_id']}")
            print(f"  📌 Budget allocation:")
            for alloc in data['budget_allocation']:
                print(f"     {alloc['platform']}: ${alloc['amount']} ({alloc['percentage']:.1f}%)")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_meta_service():
    """Test Meta Service"""
    print("\n📱 Meta Service - /create_campaign")
    try:
        payload = {
            "campaign_name": "Test Campaign Q4 2025",
            "objective": "REACH",
            "daily_budget": 100,
            "targeting": {
                "age_min": 25,
                "age_max": 45,
                "interests": ["technology", "business"]
            },
            "creatives": [
                {
                    "headline": "Discover Innovation",
                    "body": "Experience the future today",
                    "image_url": "https://example.com/image.jpg"
                }
            ],
            "start_date": "2025-12-01",
            "end_date": "2025-12-31"
        }
        response = requests.post("http://localhost:8004/create_campaign", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Campaign ID: {data['campaign_id']}")
            print(f"  📌 Status: {data['status']}")
            print(f"     Ad Set ID: {data['ad_set_id']}")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_logs_service():
    """Test Logs Service"""
    print("\n📝 Logs Service - /append_event")
    try:
        payload = {
            "event_type": "test_event",
            "severity": "info",
            "data": {
                "test_id": "test_001",
                "message": "Testing logs service",
                "timestamp": datetime.now().isoformat()
            }
        }
        response = requests.post("http://localhost:8005/append_event", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Event ID: {data['event_id']}")
            print(f"  📌 Status: {data['status']}")
            print(f"     Timestamp: {data['timestamp']}")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_validator_service():
    """Test Schema Validator Service"""
    print("\n✔️  Schema Validator Service - /validate")
    try:
        payload = {
            "schema_type": "campaign",
            "data": {
                "name": "Test Campaign",
                "budget": 5000,
                "duration_days": 30,
                "objective": "awareness"
            }
        }
        response = requests.post("http://localhost:8006/validate", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Valid: {data['valid']}")
            if not data['valid']:
                print(f"  ⚠️  Errors: {data.get('errors', [])}")
            else:
                print(f"  📌 Schema validation passed")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def test_optimizer_service():
    """Test Optimizer Service"""
    print("\n⚡ Optimizer Service - /summarize_recent_runs")
    try:
        payload = {
            "campaign_ids": ["camp_001", "camp_002"],
            "time_period_days": 7
        }
        response = requests.post("http://localhost:8007/summarize_recent_runs", json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success! Summary generated")
            print(f"  📌 Period: {data['time_period']}")
            print(f"     Campaigns analyzed: {len(data['campaigns'])}")
            if data['campaigns']:
                camp = data['campaigns'][0]
                print(f"     Sample - {camp['campaign_id']}: {camp['total_spend']} spent, {camp['conversions']} conversions")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

def main():
    print("=" * 70)
    print("🚀 Ad Campaign Agent - Complete Service Testing")
    print("=" * 70)
    
    # Health checks
    healthy = test_health_checks()
    print(f"\n✅ {healthy}/{len(SERVICES)} services are healthy\n")
    
    if healthy < len(SERVICES):
        print("⚠️  Warning: Some services are not responding\n")
    
    # Detailed tests
    print("=" * 70)
    print("🧪 Detailed Endpoint Tests")
    print("=" * 70)
    
    test_product_service()
    test_creative_service()
    test_strategy_service()
    test_meta_service()
    test_logs_service()
    test_validator_service()
    test_optimizer_service()
    
    print("\n" + "=" * 70)
    print("✅ All Tests Complete!")
    print("=" * 70)
    print("\n💡 Tip: Visit http://localhost:800X/docs for interactive API documentation")
    print("   (Replace X with service port number 1-7)")

if __name__ == "__main__":
    main()
