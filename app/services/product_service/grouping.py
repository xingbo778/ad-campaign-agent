"""
Product grouping logic based on scores.

Groups products into high, medium, and low priority groups.
"""

from typing import List, Tuple
from app.common.schemas import Product, ProductGroup
from app.common.middleware import get_logger

logger = get_logger(__name__)

# Grouping thresholds
HIGH_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 0.45


def group_products(scored_products: List[Tuple[Product, float, dict]]) -> List[ProductGroup]:
    """
    Group products by score into high, medium, and low priority groups.
    
    Thresholds:
    - high: score >= 0.75
    - medium: 0.45 <= score < 0.75
    - low: score < 0.45
    
    Args:
        scored_products: List of tuples (product, score, debug_info)
        
    Returns:
        List of ProductGroup objects
    """
    high_products = []
    medium_products = []
    low_products = []
    
    high_scores = []
    medium_scores = []
    low_scores = []
    
    for product, score, debug_info in scored_products:
        if score >= HIGH_THRESHOLD:
            high_products.append(product)
            high_scores.append(score)
        elif score >= MEDIUM_THRESHOLD:
            medium_products.append(product)
            medium_scores.append(score)
        else:
            low_products.append(product)
            low_scores.append(score)
    
    groups = []
    
    # High priority group
    if high_products:
        groups.append(ProductGroup(
            group="high",
            products=high_products,
            score_range=(min(high_scores), max(high_scores)) if high_scores else None,
            reasoning=f"High-scoring products (score >= {HIGH_THRESHOLD}) with strong campaign alignment"
        ))
    
    # Medium priority group
    if medium_products:
        groups.append(ProductGroup(
            group="medium",
            products=medium_products,
            score_range=(min(medium_scores), max(medium_scores)) if medium_scores else None,
            reasoning=f"Medium-scoring products ({MEDIUM_THRESHOLD} <= score < {HIGH_THRESHOLD}) with moderate campaign alignment"
        ))
    
    # Low priority group
    if low_products:
        groups.append(ProductGroup(
            group="low",
            products=low_products,
            score_range=(min(low_scores), max(low_scores)) if low_scores else None,
            reasoning=f"Low-scoring products (score < {MEDIUM_THRESHOLD}) with weak campaign alignment"
        ))
    
    logger.info(
        f"Grouped products: {len(high_products)} high, {len(medium_products)} medium, {len(low_products)} low"
    )
    
    return groups

