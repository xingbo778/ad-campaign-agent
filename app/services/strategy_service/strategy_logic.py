"""
Strategy generation logic for campaign optimization.

This module contains the core business logic for:
- Budget allocation across product groups and creatives
- Audience targeting for Meta platform
- Strategy optimization (bidding, adset structure)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.common.schemas import (
    CampaignSpec,
    ProductGroup,
    Creative,
    AbstractStrategy,
    PlatformStrategy
)
from app.common.middleware import get_logger

logger = get_logger(__name__)


# Budget allocation rules
BUDGET_ALLOCATION_RULES = {
    "high": 0.65,    # 65% for high priority products
    "medium": 0.25,  # 25% for medium priority products
    "low": 0.10      # 10% for low priority products (optional)
}


def allocate_budget_by_groups(
    total_budget: float,
    product_groups: List[ProductGroup],
    creatives: List[Creative]
) -> Dict:
    """
    Allocate budget across product groups and creatives.
    
    Args:
        total_budget: Total campaign budget
        product_groups: List of product groups with priority levels
        creatives: List of creatives to allocate budget to
        
    Returns:
        Dictionary with budget allocation details
    """
    # Step 1: Allocate budget by group priority
    group_allocation = {}
    group_weights = {}
    
    # Calculate group weights based on priority
    for group in product_groups:
        priority = group.group.lower()
        if priority in BUDGET_ALLOCATION_RULES:
            group_weights[priority] = BUDGET_ALLOCATION_RULES[priority]
        else:
            # Default weight for unknown priorities
            group_weights[priority] = 0.1
    
    # Normalize weights to ensure they sum to 1.0
    total_weight = sum(group_weights.values())
    if total_weight > 0:
        group_weights = {k: v / total_weight for k, v in group_weights.items()}
    
    # Allocate budget to groups
    for group in product_groups:
        priority = group.group.lower()
        group_budget = total_budget * group_weights.get(priority, 0.1)
        group_allocation[priority] = group_budget
    
    # Step 2: Allocate budget to creatives within each group
    creative_allocation = {}
    
    # Map creatives to their product groups
    product_to_group = {}
    for group in product_groups:
        for product in group.products:
            product_to_group[product.product_id] = group.group.lower()
    
    # Group creatives by product group
    creatives_by_group: Dict[str, List[Creative]] = {}
    for creative in creatives:
        product_id = creative.product_id
        group_priority = product_to_group.get(product_id, "low")
        if group_priority not in creatives_by_group:
            creatives_by_group[group_priority] = []
        creatives_by_group[group_priority].append(creative)
    
    # Allocate budget to creatives proportionally within each group
    for group_priority, group_creatives in creatives_by_group.items():
        group_budget = group_allocation.get(group_priority, 0.0)
        
        if not group_creatives:
            continue
        
        # Calculate creative scores (simple: variant A gets more, B gets less)
        creative_scores = {}
        for creative in group_creatives:
            # Base score from group priority
            base_score = {"high": 3.0, "medium": 2.0, "low": 1.0}.get(group_priority, 1.0)
            
            # Variant adjustment (A gets 60%, B gets 40%)
            variant_multiplier = 1.0 if creative.variant_id == "A" else 0.67
            
            # Optional: use creative metadata score if available
            creative_score = base_score * variant_multiplier
            if creative.style_profile and "score" in creative.style_profile:
                creative_score *= creative.style_profile.get("score", 1.0)
            
            creative_scores[creative.creative_id] = creative_score
        
        # Normalize scores
        total_score = sum(creative_scores.values())
        if total_score > 0:
            for creative in group_creatives:
                creative_id = creative.creative_id
                score_ratio = creative_scores[creative_id] / total_score
                creative_allocation[creative_id] = group_budget * score_ratio
        else:
            # Equal allocation if no scores
            budget_per_creative = group_budget / len(group_creatives)
            for creative in group_creatives:
                creative_allocation[creative.creative_id] = budget_per_creative
    
    return {
        "total_budget": total_budget,
        "group_allocation": group_allocation,
        "creative_allocation": creative_allocation,
        "group_weights": group_weights
    }


def build_meta_targeting(
    campaign_spec: CampaignSpec,
    product_groups: List[ProductGroup],
    creatives: List[Creative]
) -> Dict:
    """
    Build Meta platform targeting criteria based on campaign and products.
    
    Args:
        campaign_spec: Campaign specification
        product_groups: Product groups
        creatives: Generated creatives
        
    Returns:
        Targeting dictionary for Meta platform
    """
    targeting = {
        "age_min": 25,
        "age_max": 45,
        "genders": [1, 2],  # Both male and female
        "interests": [],
        "locations": ["US"]  # Default to US
    }
    
    # Extract category from campaign spec
    category = campaign_spec.category.lower() if campaign_spec.category else "general"
    
    # Category-based targeting rules
    category_targeting = {
        "toys": {
            "age_min": 25,
            "age_max": 45,
            "interests": ["parenting", "children", "education", "family"]
        },
        "fashion": {
            "age_min": 18,
            "age_max": 55,
            "interests": ["fashion", "shopping", "style", "clothing"]
        },
        "electronics": {
            "age_min": 25,
            "age_max": 50,
            "interests": ["technology", "gadgets", "electronics", "innovation"]
        },
        "beauty": {
            "age_min": 18,
            "age_max": 45,
            "interests": ["beauty", "cosmetics", "skincare", "makeup"]
        },
        "sports": {
            "age_min": 18,
            "age_max": 50,
            "interests": ["sports", "fitness", "health", "outdoor"]
        },
        "food": {
            "age_min": 25,
            "age_max": 55,
            "interests": ["food", "cooking", "restaurants", "recipes"]
        }
    }
    
    # Apply category-specific targeting
    if category in category_targeting:
        cat_targeting = category_targeting[category]
        targeting.update(cat_targeting)
    
    # Adjust age range based on product prices (if available)
    if product_groups:
        # Get average price from high priority products
        high_priority_products = []
        for group in product_groups:
            if group.group.lower() == "high":
                high_priority_products.extend(group.products)
        
        if high_priority_products:
            avg_price = sum(p.price for p in high_priority_products) / len(high_priority_products)
            
            # Adjust targeting based on price
            if avg_price < 50:
                # Budget products: younger audience
                targeting["age_min"] = max(18, targeting["age_min"] - 5)
                targeting["age_max"] = min(45, targeting["age_max"] - 5)
            elif avg_price > 200:
                # Premium products: older, more affluent audience
                targeting["age_min"] = min(30, targeting["age_min"] + 5)
                targeting["age_max"] = min(65, targeting["age_max"] + 10)
    
    # Extract location from metadata
    if campaign_spec.metadata:
        if "locale" in campaign_spec.metadata:
            locale = campaign_spec.metadata["locale"]
            # Map locale to country codes
            locale_to_country = {
                "zh_CN": ["CN"],
                "en_US": ["US"],
                "en_GB": ["GB"],
                "ja_JP": ["JP"],
                "ko_KR": ["KR"]
            }
            if locale in locale_to_country:
                targeting["locations"] = locale_to_country[locale]
        
        if "country" in campaign_spec.metadata:
            targeting["locations"] = [campaign_spec.metadata["country"]]
    
    # Extract age hints from product metadata
    if product_groups:
        age_ranges = []
        for group in product_groups:
            for product in group.products:
                if product.metadata and "age_range" in product.metadata:
                    age_range = product.metadata["age_range"]
                    # Parse age range like "3-8" or "25-45"
                    if isinstance(age_range, str) and "-" in age_range:
                        try:
                            parts = age_range.split("-")
                            age_ranges.append((int(parts[0]), int(parts[1])))
                        except (ValueError, IndexError):
                            pass
        
        if age_ranges:
            # Use the most common age range
            avg_min = sum(r[0] for r in age_ranges) / len(age_ranges)
            avg_max = sum(r[1] for r in age_ranges) / len(age_ranges)
            # Adjust targeting to include product age range (add 10 years for parents)
            targeting["age_min"] = max(18, int(avg_min) + 10)
            targeting["age_max"] = min(65, int(avg_max) + 20)
    
    return targeting


def choose_bidding_strategy(campaign_spec: CampaignSpec) -> str:
    """
    Choose appropriate bidding strategy based on campaign objective.
    
    Args:
        campaign_spec: Campaign specification
        
    Returns:
        Bidding strategy string
    """
    objective = campaign_spec.objective.lower()
    
    bidding_strategies = {
        "conversions": "LOWEST_COST_WITH_CAP",
        "sales": "LOWEST_COST_WITH_CAP",
        "traffic": "LOWEST_COST",
        "leads": "LOWEST_COST_WITH_CAP",
        "awareness": "LOWEST_COST",
        "engagement": "LOWEST_COST"
    }
    
    return bidding_strategies.get(objective, "LOWEST_COST")


def design_adset_structure(
    campaign_spec: CampaignSpec,
    product_groups: List[ProductGroup],
    budget_plan: Dict
) -> Dict:
    """
    Design adset structure based on budget and product groups.
    
    Args:
        campaign_spec: Campaign specification
        product_groups: Product groups
        budget_plan: Budget allocation plan
        
    Returns:
        Campaign structure dictionary
    """
    total_budget = campaign_spec.budget
    
    # Calculate duration days from time_range
    duration_days = 30  # Default
    if campaign_spec.time_range:
        if isinstance(campaign_spec.time_range, dict):
            start = campaign_spec.time_range.get("start")
            end = campaign_spec.time_range.get("end")
            if start and end:
                try:
                    start_date = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_date = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    duration_days = max(1, (end_date - start_date).days)
                except (ValueError, AttributeError):
                    pass
    
    daily_budget = total_budget / duration_days
    
    structure = {
        "campaign_name": f"{campaign_spec.category}_{campaign_spec.objective}_campaign",
        "campaign_objective": campaign_spec.objective,
        "daily_budget": daily_budget,
        "adsets": []
    }
    
    # Strategy based on budget size
    if total_budget < 1000:
        # Single adset conservative strategy
        structure["adsets"] = [{
            "adset_name": "Single Adset - All Products",
            "daily_budget": daily_budget,
            "targeting": {},
            "product_groups": ["high", "medium", "low"]
        }]
    elif total_budget < 5000:
        # 2-3 adsets: one for high, one mixed
        high_budget = daily_budget * 0.7
        mixed_budget = daily_budget * 0.3
        
        structure["adsets"] = [
            {
                "adset_name": "High Priority Products",
                "daily_budget": high_budget,
                "targeting": {},
                "product_groups": ["high"]
            },
            {
                "adset_name": "Mixed Priority Products",
                "daily_budget": mixed_budget,
                "targeting": {},
                "product_groups": ["high", "medium"]
            }
        ]
    else:
        # Large budget: separate adsets for each priority
        high_budget = daily_budget * 0.6
        medium_budget = daily_budget * 0.3
        low_budget = daily_budget * 0.1
        
        structure["adsets"] = [
            {
                "adset_name": "High Priority Products",
                "daily_budget": high_budget,
                "targeting": {},
                "product_groups": ["high"]
            },
            {
                "adset_name": "Medium Priority Products",
                "daily_budget": medium_budget,
                "targeting": {},
                "product_groups": ["medium"]
            },
            {
                "adset_name": "Low Priority Products",
                "daily_budget": low_budget,
                "targeting": {},
                "product_groups": ["low"]
            }
        ]
    
    return structure


def estimate_reach_and_conversions(
    campaign_spec: CampaignSpec,
    budget_plan: Dict,
    targeting: Dict
) -> Tuple[int, int]:
    """
    Estimate reach and conversions based on budget and targeting.
    
    Args:
        campaign_spec: Campaign specification
        budget_plan: Budget allocation plan
        targeting: Targeting criteria
        
    Returns:
        Tuple of (estimated_reach, estimated_conversions)
    """
    total_budget = campaign_spec.budget
    objective = campaign_spec.objective.lower()
    
    # Base estimates (per $1000 budget)
    base_reach_per_1k = 50000  # 50k reach per $1000
    base_conversions_per_1k = {
        "conversions": 25,
        "sales": 20,
        "traffic": 100,
        "leads": 30,
        "awareness": 0,  # Awareness campaigns don't track conversions
        "engagement": 50
    }
    
    # Calculate base estimates
    estimated_reach = int((total_budget / 1000) * base_reach_per_1k)
    base_conversions = base_conversions_per_1k.get(objective, 20)
    estimated_conversions = int((total_budget / 1000) * base_conversions)
    
    # Adjust based on targeting (narrower targeting = lower reach, higher conversion rate)
    age_min = targeting.get("age_min", 25)
    age_max = targeting.get("age_max", 45)
    age_range = age_max - age_min
    
    if age_range < 15:
        # Narrow targeting: lower reach, higher conversion rate
        estimated_reach = int(estimated_reach * 0.7)
        estimated_conversions = int(estimated_conversions * 1.2)
    elif age_range > 30:
        # Broad targeting: higher reach, lower conversion rate
        estimated_reach = int(estimated_reach * 1.3)
        estimated_conversions = int(estimated_conversions * 0.9)
    
    # Adjust based on budget (larger budgets have better efficiency)
    if total_budget > 5000:
        estimated_conversions = int(estimated_conversions * 1.1)
    elif total_budget < 1000:
        estimated_conversions = int(estimated_conversions * 0.9)
    
    return estimated_reach, estimated_conversions


def generate_abstract_strategy(
    campaign_spec: CampaignSpec,
    budget_plan: Dict,
    bidding_strategy: str
) -> AbstractStrategy:
    """
    Generate abstract strategy from campaign spec and budget plan.
    
    Args:
        campaign_spec: Campaign specification
        budget_plan: Budget allocation plan
        bidding_strategy: Chosen bidding strategy
        
    Returns:
        AbstractStrategy object
    """
    # Create budget split by variant (A, B, C)
    budget_split = {}
    creative_allocation = budget_plan.get("creative_allocation", {})
    
    # Group by variant
    variant_budgets = {}
    for creative_id, budget in creative_allocation.items():
        # Extract variant from creative (we need to pass creatives to this function)
        # For now, use a simple split
        pass
    
    # Simple split: 60% A, 40% B (if we had creatives, we'd calculate this)
    # Default split
    budget_split = {"A": 0.6, "B": 0.4}
    
    return AbstractStrategy(
        objective=campaign_spec.objective,
        budget_split=budget_split,
        bidding_strategy=bidding_strategy,
        constraints={
            "platform": campaign_spec.platform,
            "category": campaign_spec.category,
            "budget_limit": campaign_spec.budget
        },
        metadata={
            "total_budget": campaign_spec.budget,
            "platform": campaign_spec.platform
        }
    )


def generate_platform_strategy(
    campaign_spec: CampaignSpec,
    budget_plan: Dict,
    targeting: Dict,
    adset_structure: Dict,
    bidding_strategy: str
) -> PlatformStrategy:
    """
    Generate platform-specific strategy for Meta.
    
    Args:
        campaign_spec: Campaign specification
        budget_plan: Budget allocation plan
        targeting: Targeting criteria
        adset_structure: Adset structure
        bidding_strategy: Bidding strategy
        
    Returns:
        PlatformStrategy object
    """
    total_budget = campaign_spec.budget
    
    # Calculate duration days from time_range
    duration_days = 30  # Default
    if campaign_spec.time_range:
        if isinstance(campaign_spec.time_range, dict):
            start = campaign_spec.time_range.get("start")
            end = campaign_spec.time_range.get("end")
            if start and end:
                try:
                    start_date = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    end_date = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    duration_days = max(1, (end_date - start_date).days)
                except (ValueError, AttributeError):
                    pass
    
    daily_budget = total_budget / duration_days
    
    return PlatformStrategy(
        platform=campaign_spec.platform,
        campaign_structure=adset_structure,
        optimization_goal=campaign_spec.objective.upper(),
        targeting=targeting,
        placements=["facebook_feed", "instagram_feed", "instagram_stories"],
        metadata={
            "daily_budget": daily_budget,
            "total_budget": total_budget,
            "bidding_strategy": bidding_strategy,
            "duration_days": duration_days
        }
    )

