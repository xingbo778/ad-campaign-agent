"""
Tests for product scoring logic.
"""

import pytest
from app.common.schemas import Product, CampaignSpec
from app.services.product_service.scoring import (
    compute_product_score,
    score_products,
    _compute_category_score,
    _compute_price_score,
    _compute_description_score
)


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    return Product(
        product_id="PROD-001",
        title="Wireless Headphones",
        description="Premium noise-canceling wireless headphones with excellent sound quality",
        price=199.99,
        category="electronics",
        image_url="https://example.com/image.jpg",
        metadata={"brand": "AudioTech"}
    )


@pytest.fixture
def sample_campaign_spec():
    """Sample campaign specification."""
    return CampaignSpec(
        user_query="Create a campaign for electronics",
        platform="meta",
        budget=2000.0,
        objective="conversions",
        category="electronics",
        metadata={}
    )


class TestCategoryScore:
    """Test category scoring."""
    
    def test_exact_category_match(self):
        """Test exact category match gets highest score."""
        score = _compute_category_score("electronics", "electronics")
        assert score == 0.4
    
    def test_similar_category_match(self):
        """Test similar category gets partial score."""
        score = _compute_category_score("electronics", "electronic")
        assert score >= 0.2
    
    def test_no_category_match(self):
        """Test no match gets zero score."""
        score = _compute_category_score("electronics", "fashion")
        assert score == 0.0
    
    def test_empty_campaign_category(self):
        """Test empty campaign category gets neutral score."""
        score = _compute_category_score("electronics", "")
        assert score == 0.2


class TestPriceScore:
    """Test price scoring."""
    
    def test_low_budget_cheap_product(self):
        """Test cheap products score well for low budgets."""
        score = _compute_price_score(50.0, 1000.0)  # budget/20
        assert score > 0.1
    
    def test_high_budget_mid_range_product(self):
        """Test mid-range products score well for high budgets."""
        score = _compute_price_score(100.0, 5000.0)  # budget/50
        assert score > 0.2
    
    def test_expensive_product_low_score(self):
        """Test very expensive products get lower score."""
        score = _compute_price_score(500.0, 1000.0)  # budget/2
        assert score < 0.2


class TestDescriptionScore:
    """Test description scoring."""
    
    def test_long_description_scores_higher(self):
        """Test longer descriptions score better."""
        long_desc = "A" * 300
        short_desc = "A" * 50
        
        long_score = _compute_description_score(long_desc, CampaignSpec(
            user_query="test", platform="meta", budget=1000, objective="conversions", category="test"
        ))
        short_score = _compute_description_score(short_desc, CampaignSpec(
            user_query="test", platform="meta", budget=1000, objective="conversions", category="test"
        ))
        
        assert long_score > short_score
    
    def test_keyword_match_boosts_score(self):
        """Test keyword matches boost description score."""
        desc_with_keyword = "Premium electronics product with great features"
        desc_no_keyword = "A generic product"
        
        campaign = CampaignSpec(
            user_query="electronics campaign",
            platform="meta",
            budget=1000,
            objective="conversions",
            category="electronics"
        )
        
        with_keyword_score = _compute_description_score(desc_with_keyword, campaign)
        no_keyword_score = _compute_description_score(desc_no_keyword, campaign)
        
        assert with_keyword_score > no_keyword_score


class TestComputeProductScore:
    """Test complete product scoring."""
    
    def test_compute_score_returns_valid_range(self, sample_product, sample_campaign_spec):
        """Test score is in valid range [0, 1]."""
        score, debug = compute_product_score(sample_product, sample_campaign_spec)
        
        assert 0.0 <= score <= 1.0
        assert "total_score" in debug
        assert debug["total_score"] == score
    
    def test_compute_score_breakdown(self, sample_product, sample_campaign_spec):
        """Test score breakdown includes all components."""
        score, debug = compute_product_score(sample_product, sample_campaign_spec)
        
        assert "category_score" in debug
        assert "price_score" in debug
        assert "description_score" in debug
        assert "metadata_score" in debug
        assert "total_score" in debug
    
    def test_exact_match_high_score(self, sample_campaign_spec):
        """Test product with exact match gets high score."""
        perfect_product = Product(
            product_id="PERFECT",
            title="Electronics Product",
            description="Premium electronics product for conversions campaign",
            price=100.0,  # Good price for budget
            category="electronics",  # Exact match
            metadata={"popularity": 0.9}
        )
        
        score, _ = compute_product_score(perfect_product, sample_campaign_spec)
        assert score >= 0.7  # Should be high score
    
    def test_poor_match_low_score(self, sample_campaign_spec):
        """Test product with poor match gets low score."""
        poor_product = Product(
            product_id="POOR",
            title="Fashion Item",
            description="Short",
            price=5000.0,  # Too expensive
            category="fashion",  # Wrong category
            metadata={}
        )
        
        score, _ = compute_product_score(poor_product, sample_campaign_spec)
        assert score < 0.5  # Should be low score


class TestScoreProducts:
    """Test scoring multiple products."""
    
    def test_score_products_sorts_by_score(self, sample_campaign_spec):
        """Test scored products are sorted by score descending."""
        products = [
            Product(product_id="P1", title="Product 1", description="Good match", price=100, category="electronics"),
            Product(product_id="P2", title="Product 2", description="Poor match", price=5000, category="fashion"),
            Product(product_id="P3", title="Product 3", description="Medium match", price=200, category="electronics"),
        ]
        
        scored = score_products(products, sample_campaign_spec)
        
        # Should be sorted descending
        scores = [score for _, score, _ in scored]
        assert scores == sorted(scores, reverse=True)
        
        # First product should have highest score
        assert scored[0][1] >= scored[-1][1]
    
    def test_score_products_returns_all_products(self, sample_campaign_spec):
        """Test all products are scored."""
        products = [
            Product(product_id=f"P{i}", title=f"Product {i}", description="Test", price=100, category="electronics")
            for i in range(5)
        ]
        
        scored = score_products(products, sample_campaign_spec)
        
        assert len(scored) == len(products)
        assert all(len(item) == 3 for item in scored)  # (product, score, debug_info)

