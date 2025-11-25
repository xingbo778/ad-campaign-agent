"""
Product scoring logic for campaign matching.

Implements rule-based scoring that can be extended with ML in the future.
"""

from typing import Dict, Tuple
from app.common.schemas import Product, CampaignSpec
from app.common.middleware import get_logger

logger = get_logger(__name__)


def compute_product_score(product: Product, campaign_spec: CampaignSpec) -> Tuple[float, Dict]:
    """
    Compute product score based on campaign specification.
    
    Scoring factors:
    - Category alignment: +0.4 (exact match), +0.2 (similar prefix)
    - Price fit: Based on budget level (cheap for low budget, expensive for high budget)
    - Description quality: Based on length and keyword match
    - Metadata features: Additional scoring from metadata
    
    Args:
        product: Product to score
        campaign_spec: Campaign specification
        
    Returns:
        Tuple of (score, debug_info) where:
        - score: float in [0, 1]
        - debug_info: Dictionary with scoring breakdown
    """
    debug_info = {
        "category_score": 0.0,
        "price_score": 0.0,
        "description_score": 0.0,
        "metadata_score": 0.0,
        "total_score": 0.0
    }
    
    total_score = 0.0
    
    # 1. Category alignment (max 0.4)
    category_score = _compute_category_score(product.category, campaign_spec.category)
    debug_info["category_score"] = category_score
    total_score += category_score
    
    # 2. Price fit (max 0.3)
    price_score = _compute_price_score(product.price, campaign_spec.budget)
    debug_info["price_score"] = price_score
    total_score += price_score
    
    # 3. Description quality (max 0.2)
    description_score = _compute_description_score(product.description, campaign_spec)
    debug_info["description_score"] = description_score
    total_score += description_score
    
    # 4. Metadata features (max 0.1)
    metadata_score = _compute_metadata_score(product.metadata, campaign_spec)
    debug_info["metadata_score"] = metadata_score
    total_score += metadata_score
    
    # Clip to [0, 1]
    total_score = max(0.0, min(1.0, total_score))
    debug_info["total_score"] = total_score
    
    return total_score, debug_info


def _compute_category_score(product_category: str, campaign_category: str) -> float:
    """
    Compute category alignment score.
    
    - Exact match: 0.4
    - Similar prefix (first word matches): 0.2
    - No match: 0.0
    """
    if not campaign_category:
        return 0.2  # Neutral score if no category specified
    
    product_cat_lower = product_category.lower().strip()
    campaign_cat_lower = campaign_category.lower().strip()
    
    # Exact match
    if product_cat_lower == campaign_cat_lower:
        return 0.4
    
    # Check if product category contains campaign category or vice versa
    if campaign_cat_lower in product_cat_lower or product_cat_lower in campaign_cat_lower:
        return 0.3
    
    # Check first word match
    product_first = product_cat_lower.split()[0] if product_cat_lower.split() else ""
    campaign_first = campaign_cat_lower.split()[0] if campaign_cat_lower.split() else ""
    
    if product_first and campaign_first and product_first == campaign_first:
        return 0.2
    
    # Partial word match
    if product_first and campaign_first:
        if product_first.startswith(campaign_first) or campaign_first.startswith(product_first):
            return 0.15
    
    return 0.0


def _compute_price_score(product_price: float, campaign_budget: float) -> float:
    """
    Compute price fit score based on budget.
    
    Rules:
    - If budget < 1000: Prefer products < budget/40 (cheap products)
    - If budget >= 1000: Prefer products in [budget/40, budget/20] (mid-range)
    - Very expensive products (> budget/10) get lower score
    """
    if campaign_budget <= 0:
        return 0.1  # Neutral score
    
    budget_ratio = product_price / campaign_budget
    
    if campaign_budget < 1000:
        # Low budget: prefer cheap products
        if budget_ratio < 0.025:  # < budget/40
            return 0.3
        elif budget_ratio < 0.05:  # < budget/20
            return 0.2
        elif budget_ratio < 0.1:  # < budget/10
            return 0.1
        else:
            return 0.05
    else:
        # Higher budget: prefer mid-range products
        if 0.025 <= budget_ratio < 0.05:  # budget/40 to budget/20
            return 0.3
        elif 0.01 <= budget_ratio < 0.025:  # budget/100 to budget/40
            return 0.25
        elif 0.05 <= budget_ratio < 0.1:  # budget/20 to budget/10
            return 0.2
        elif budget_ratio < 0.01:  # Very cheap
            return 0.1
        else:  # > budget/10
            return 0.05


def _compute_description_score(description: str, campaign_spec: CampaignSpec) -> float:
    """
    Compute description quality score.
    
    Factors:
    - Length: Longer descriptions are better (capped at 300 chars)
    - Keyword match: Match with campaign category/objective
    """
    if not description:
        return 0.0
    
    score = 0.0
    
    # Length score (max 0.1)
    desc_length = len(description)
    length_score = min(0.1, desc_length / 300.0 * 0.1)
    score += length_score
    
    # Keyword match score (max 0.1)
    desc_lower = description.lower()
    keywords = []
    
    if campaign_spec.category:
        keywords.append(campaign_spec.category.lower())
    
    if campaign_spec.objective:
        keywords.append(campaign_spec.objective.lower())
    
    if campaign_spec.user_query:
        # Extract key words from user query
        query_words = campaign_spec.user_query.lower().split()
        keywords.extend([w for w in query_words if len(w) > 3])
    
    keyword_matches = sum(1 for keyword in keywords if keyword in desc_lower)
    keyword_score = min(0.1, keyword_matches * 0.03)
    score += keyword_score
    
    return min(0.2, score)


def _compute_metadata_score(metadata: Dict, campaign_spec: CampaignSpec) -> float:
    """
    Compute score from product metadata.
    
    Considers:
    - Popularity indicators
    - Brand alignment
    - Feature matches
    """
    if not metadata:
        return 0.0
    
    score = 0.0
    
    # Popularity boost (if available)
    if "popularity" in metadata:
        try:
            popularity = float(metadata["popularity"])
            score += min(0.05, popularity * 0.05)
        except (ValueError, TypeError):
            pass
    
    # Brand alignment (if campaign specifies brand)
    if campaign_spec.metadata and "brand" in campaign_spec.metadata:
        campaign_brand = campaign_spec.metadata.get("brand", "").lower()
        product_brand = metadata.get("brand", "").lower()
        if product_brand and campaign_brand in product_brand:
            score += 0.03
    
    # Feature matches
    if "features" in metadata and isinstance(metadata["features"], list):
        # More features = slightly better
        feature_count = len(metadata["features"])
        score += min(0.02, feature_count * 0.005)
    
    return min(0.1, score)


def score_products(products: list, campaign_spec: CampaignSpec) -> list:
    """
    Score a list of products and return sorted by score (descending).
    
    Args:
        products: List of Product objects
        campaign_spec: Campaign specification
        
    Returns:
        List of tuples (product, score, debug_info) sorted by score descending
    """
    scored_products = []
    
    for product in products:
        score, debug_info = compute_product_score(product, campaign_spec)
        scored_products.append((product, score, debug_info))
    
    # Sort by score descending
    scored_products.sort(key=lambda x: x[1], reverse=True)
    
    return scored_products

