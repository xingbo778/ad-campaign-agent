"""
Tests for product grouping logic.
"""

import pytest
from app.common.schemas import Product
from app.services.product_service.grouping import group_products


@pytest.fixture
def high_score_products():
    """Products with high scores."""
    return [
        (Product(product_id="H1", title="High 1", description="Test", price=100, category="electronics"), 0.85, {}),
        (Product(product_id="H2", title="High 2", description="Test", price=150, category="electronics"), 0.80, {}),
        (Product(product_id="H3", title="High 3", description="Test", price=200, category="electronics"), 0.75, {}),
    ]


@pytest.fixture
def medium_score_products():
    """Products with medium scores."""
    return [
        (Product(product_id="M1", title="Medium 1", description="Test", price=100, category="electronics"), 0.60, {}),
        (Product(product_id="M2", title="Medium 2", description="Test", price=150, category="electronics"), 0.50, {}),
        (Product(product_id="M3", title="Medium 3", description="Test", price=200, category="electronics"), 0.45, {}),
    ]


@pytest.fixture
def low_score_products():
    """Products with low scores."""
    return [
        (Product(product_id="L1", title="Low 1", description="Test", price=100, category="electronics"), 0.40, {}),
        (Product(product_id="L2", title="Low 2", description="Test", price=150, category="electronics"), 0.30, {}),
        (Product(product_id="L3", title="Low 3", description="Test", price=200, category="electronics"), 0.20, {}),
    ]


class TestGroupProducts:
    """Test product grouping."""
    
    def test_group_high_priority(self, high_score_products):
        """Test high priority grouping."""
        groups = group_products(high_score_products)
        
        assert len(groups) == 1
        assert groups[0].group == "high"
        assert len(groups[0].products) == 3
        assert groups[0].score_range is not None
        assert groups[0].score_range[0] >= 0.75
    
    def test_group_medium_priority(self, medium_score_products):
        """Test medium priority grouping."""
        groups = group_products(medium_score_products)
        
        assert len(groups) == 1
        assert groups[0].group == "medium"
        assert len(groups[0].products) == 3
        assert 0.45 <= groups[0].score_range[0] < 0.75
    
    def test_group_low_priority(self, low_score_products):
        """Test low priority grouping."""
        groups = group_products(low_score_products)
        
        assert len(groups) == 1
        assert groups[0].group == "low"
        assert len(groups[0].products) == 3
        assert groups[0].score_range[0] < 0.45
    
    def test_group_all_priorities(self, high_score_products, medium_score_products, low_score_products):
        """Test grouping products from all priority levels."""
        all_products = high_score_products + medium_score_products + low_score_products
        groups = group_products(all_products)
        
        assert len(groups) == 3
        
        # Check groups are in correct order
        group_names = [g.group for g in groups]
        assert "high" in group_names
        assert "medium" in group_names
        assert "low" in group_names
        
        # Verify product counts
        high_group = next(g for g in groups if g.group == "high")
        medium_group = next(g for g in groups if g.group == "medium")
        low_group = next(g for g in groups if g.group == "low")
        
        assert len(high_group.products) == 3
        assert len(medium_group.products) == 3
        assert len(low_group.products) == 3
    
    def test_group_empty_list(self):
        """Test grouping empty list returns empty list."""
        groups = group_products([])
        assert groups == []
    
    def test_group_boundary_scores(self):
        """Test grouping with boundary scores."""
        boundary_products = [
            (Product(product_id="B1", title="Boundary 1", description="Test", price=100, category="electronics"), 0.75, {}),  # Exactly high threshold
            (Product(product_id="B2", title="Boundary 2", description="Test", price=100, category="electronics"), 0.45, {}),  # Exactly medium threshold
            (Product(product_id="B3", title="Boundary 3", description="Test", price=100, category="electronics"), 0.44, {}),  # Just below medium
        ]
        
        groups = group_products(boundary_products)
        
        assert len(groups) == 3
        high_group = next(g for g in groups if g.group == "high")
        medium_group = next(g for g in groups if g.group == "medium")
        low_group = next(g for g in groups if g.group == "low")
        
        assert len(high_group.products) == 1
        assert len(medium_group.products) == 1
        assert len(low_group.products) == 1
    
    def test_group_score_ranges(self, high_score_products, medium_score_products, low_score_products):
        """Test score ranges are correctly calculated."""
        all_products = high_score_products + medium_score_products + low_score_products
        groups = group_products(all_products)
        
        for group in groups:
            assert group.score_range is not None
            min_score, max_score = group.score_range
            assert min_score <= max_score
            
            # Verify all products in group are within range
            for product in group.products:
                # Find the score for this product
                for p, score, _ in all_products:
                    if p.product_id == product.product_id:
                        assert min_score <= score <= max_score
                        break

