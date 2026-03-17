"""
Mock data generators for product_service.
"""
from typing import Dict, List
from app.services.product_service.schemas import Product, ProductGroupsResponse


def generate_mock_products() -> Dict[str, List[Product]]:
    """
    Generate mock product groups.
    
    Returns:
        Dictionary with high, medium, low priority product groups
    """
    return {
        "high": [
            Product(
                product_id="prod_001",
                name="Premium Widget Pro",
                category="Electronics",
                price=299.99,
                description="High-end widget with advanced features",
                tags=["premium", "featured", "best-seller"]
            ),
            Product(
                product_id="prod_002",
                name="Smart Home Hub",
                category="Smart Home",
                price=199.99,
                description="Central control for your smart home",
                tags=["smart", "popular", "trending"]
            ),
        ],
        "medium": [
            Product(
                product_id="prod_003",
                name="Standard Widget",
                category="Electronics",
                price=149.99,
                description="Reliable widget for everyday use",
                tags=["standard", "reliable"]
            ),
            Product(
                product_id="prod_004",
                name="Basic Home Assistant",
                category="Smart Home",
                price=99.99,
                description="Entry-level home automation",
                tags=["basic", "affordable"]
            ),
        ],
        "low": [
            Product(
                product_id="prod_005",
                name="Budget Widget",
                category="Electronics",
                price=49.99,
                description="Economical widget option",
                tags=["budget", "economy"]
            ),
        ]
    }


def create_mock_response() -> ProductGroupsResponse:
    """
    Create a mock response for product selection.
    
    Returns:
        ProductGroupsResponse with mock product groups
    """
    product_groups = generate_mock_products()
    return ProductGroupsResponse(product_groups=product_groups)




