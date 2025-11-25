#!/usr/bin/env python3
"""
测试LLM增强版Orchestrator Agent
"""

import requests
import json

ORCHESTRATOR_URL = "https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer"

def test_natural_language_campaign():
    """测试自然语言活动创建"""
    print("=" * 70)
    print("🤖 测试自然语言活动创建")
    print("=" * 70)
    
    # 测试用例
    test_requests = [
        "I want to run a sales campaign targeting tech enthusiasts aged 25-45 with a budget of $5000",
        "Create a brand awareness campaign for fashion lovers with $10000 budget for 60 days",
        "Launch a conversion campaign for electronics category, budget $3000, targeting millennials"
    ]
    
    for i, user_request in enumerate(test_requests, 1):
        print(f"\n测试 {i}: {user_request}")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{ORCHESTRATOR_URL}/create_campaign_nl",
                json={"user_request": user_request},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 状态: {result['status']}")
                print(f"📋 解析的CampaignSpec:")
                print(json.dumps(result.get('campaign_spec', {}), indent=2))
                print(f"\n📊 结果:")
                print(f"  - 活动数: {len(result.get('campaigns', []))}")
                if result.get('campaigns'):
                    campaign = result['campaigns'][0]
                    print(f"  - Campaign ID: {campaign.get('campaign_id')}")
                    print(f"  - 产品数: {len(campaign.get('products', []))}")
                    print(f"  - 创意数: {len(campaign.get('creatives', []))}")
                print(f"\n💬 摘要: {result.get('summary', 'N/A')}")
            else:
                print(f"❌ 错误: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
        
        print()


def test_service_info():
    """测试服务信息"""
    print("=" * 70)
    print("ℹ️  服务信息")
    print("=" * 70)
    
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/")
        info = response.json()
        
        print(f"服务: {info.get('service')}")
        print(f"版本: {info.get('version')}")
        print(f"状态: {info.get('status')}")
        print(f"\n功能:")
        for capability in info.get('capabilities', []):
            print(f"  ✓ {capability}")
        print(f"\n端点:")
        for name, path in info.get('endpoints', {}).items():
            print(f"  • {name}: {path}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    print()


def test_services_status():
    """测试微服务状态"""
    print("=" * 70)
    print("🔍 微服务状态检查")
    print("=" * 70)
    
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/services/status")
        status = response.json()
        
        print(f"Orchestrator状态: {status.get('orchestrator_status')}")
        print(f"LLM启用: {status.get('llm_enabled')}")
        print(f"健康服务: {status.get('healthy_services')}/{status.get('total_services')}")
        print(f"\n各服务状态:")
        
        for service_name, service_info in status.get('services', {}).items():
            status_icon = "✅" if service_info['status'] == 'healthy' else "❌"
            print(f"  {status_icon} {service_name}: {service_info['status']}")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🚀 LLM增强版Orchestrator Agent - 测试套件")
    print("=" * 70)
    print()
    
    # 测试服务信息
    test_service_info()
    
    # 测试微服务状态
    test_services_status()
    
    # 测试自然语言活动创建
    test_natural_language_campaign()
    
    print("=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)
    print()
    print("📱 交互式API文档:")
    print(f"  {ORCHESTRATOR_URL}/docs")
    print()


if __name__ == "__main__":
    main()
