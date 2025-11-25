"""
Example usage of the orchestrator clients to create an ad campaign.

This demonstrates how to use the client libraries to interact with
all MCP services in a coordinated workflow.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.orchestrator.clients import (
    ProductClient,
    CreativeClient,
    StrategyClient,
    MetaClient,
    LogsClient,
    ValidatorClient,
    OptimizerClient
)


def create_campaign_example():
    """
    Example workflow for creating a complete ad campaign.
    
    This demonstrates the typical orchestration flow:
    1. Select products
    2. Generate strategy
    3. Create creatives
    4. Validate data
    5. Deploy to Meta
    6. Log events
    """
    
    print("=" * 60)
    print("Ad Campaign Creation Example")
    print("=" * 60)
    
    # Initialize clients
    product_client = ProductClient()
    creative_client = CreativeClient()
    strategy_client = StrategyClient()
    meta_client = MetaClient()
    logs_client = LogsClient()
    validator_client = ValidatorClient()
    optimizer_client = OptimizerClient()
    
    try:
        # Step 1: Select products
        print("\n[1/7] Selecting products...")
        products_response = product_client.select_products(
            campaign_objective="increase sales",
            target_audience="tech enthusiasts aged 25-45",
            budget=10000.0,
            max_products=5
        )
        print(f"✓ Selected {products_response['total_products']} products")
        
        # Extract product IDs
        product_ids = []
        for group in products_response['product_groups']:
            for product in group['products']:
                product_ids.append(product['product_id'])
        
        # Step 2: Generate strategy
        print("\n[2/7] Generating campaign strategy...")
        strategy_response = strategy_client.generate_strategy(
            campaign_objective="increase sales",
            total_budget=10000.0,
            duration_days=30,
            target_audience="tech enthusiasts aged 25-45",
            platforms=["facebook", "instagram"]
        )
        print(f"✓ Strategy created with {len(strategy_response['platform_strategies'])} platforms")
        print(f"  Estimated reach: {strategy_response['estimated_reach']:,}")
        print(f"  Estimated conversions: {strategy_response['estimated_conversions']:,}")
        
        # Step 3: Generate creatives
        print("\n[3/7] Generating ad creatives...")
        creatives_response = creative_client.generate_creatives(
            product_ids=product_ids[:3],  # Use top 3 products
            campaign_objective="increase sales",
            target_audience="tech enthusiasts aged 25-45",
            brand_voice="professional"
        )
        print(f"✓ Generated {creatives_response['total_creatives']} creatives")
        
        # Step 4: Validate campaign data
        print("\n[4/7] Validating campaign data...")
        validation_response = validator_client.validate(
            schema_name="campaign",
            data={
                "products": products_response,
                "strategy": strategy_response,
                "creatives": creatives_response
            }
        )
        print(f"✓ Validation {'passed' if validation_response['valid'] else 'failed'}")
        
        # Step 5: Deploy to Meta
        print("\n[5/7] Deploying campaign to Meta platforms...")
        
        # Prepare creatives for Meta
        meta_creatives = []
        for creative in creatives_response['creatives'][:5]:  # Use first 5 creatives
            meta_creatives.append({
                "creative_id": creative['creative_id'],
                "headline": creative['headline'],
                "body_text": creative['body_text'],
                "call_to_action": creative['call_to_action'],
                "image_url": creative.get('asset_url')
            })
        
        # Calculate daily budget from strategy
        daily_budget = strategy_response['platform_strategies'][0]['daily_budget']
        
        # Create campaign
        start_date = datetime.now().isoformat()
        end_date = (datetime.now() + timedelta(days=30)).isoformat()
        
        campaign_response = meta_client.create_campaign(
            campaign_name="Tech Products Q4 Campaign",
            objective="CONVERSIONS",
            daily_budget=daily_budget,
            targeting={
                "age_range": "25-45",
                "interests": "technology, electronics, gadgets",
                "location": "United States"
            },
            creatives=meta_creatives,
            start_date=start_date,
            end_date=end_date
        )
        print(f"✓ Campaign created: {campaign_response['campaign_id']}")
        print(f"  Status: {campaign_response['status']}")
        print(f"  Ads created: {len(campaign_response['ad_ids'])}")
        
        # Step 6: Log campaign creation
        print("\n[6/7] Logging campaign creation event...")
        log_response = logs_client.append_event(
            event_type="campaign_created",
            message=f"Campaign {campaign_response['campaign_id']} created successfully",
            metadata={
                "campaign_id": campaign_response['campaign_id'],
                "total_products": products_response['total_products'],
                "total_creatives": creatives_response['total_creatives'],
                "budget": 10000.0
            },
            campaign_id=campaign_response['campaign_id']
        )
        print(f"✓ Event logged: {log_response['event_id']}")
        
        # Step 7: Get optimization suggestions
        print("\n[7/7] Getting optimization suggestions...")
        optimization_response = optimizer_client.summarize_recent_runs(days=7)
        print(f"✓ Retrieved {len(optimization_response['suggestions'])} optimization suggestions")
        print(f"\nTop suggestion:")
        if optimization_response['suggestions']:
            top_suggestion = optimization_response['suggestions'][0]
            print(f"  Category: {top_suggestion['category']}")
            print(f"  Suggestion: {top_suggestion['suggestion']}")
            print(f"  Expected impact: {top_suggestion['expected_impact']}")
        
        print("\n" + "=" * 60)
        print("Campaign creation completed successfully!")
        print("=" * 60)
        
        return campaign_response['campaign_id']
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
    
    finally:
        # Clean up clients
        product_client.close()
        creative_client.close()
        strategy_client.close()
        meta_client.close()
        logs_client.close()
        validator_client.close()
        optimizer_client.close()


if __name__ == "__main__":
    print("\nMake sure all services are running before executing this script!")
    print("Run: ./start_services.sh\n")
    
    try:
        campaign_id = create_campaign_example()
        print(f"\nCampaign ID: {campaign_id}")
    except Exception as e:
        print(f"\nFailed to create campaign: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure all services are running (./start_services.sh)")
        print("2. Check service logs in the logs/ directory")
        print("3. Verify .env configuration")
        sys.exit(1)
