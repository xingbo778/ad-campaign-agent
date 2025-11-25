"""
Pytest configuration and shared fixtures for all tests.

This module provides:
- TestClient fixtures for each service
- Sample data fixtures (CampaignSpec, Products, Creatives, etc.)
- Mock configurations for external dependencies
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.common.schemas import (
    CampaignSpec,
    Product,
    ProductGroup,
    Creative,
    AbstractStrategy,
    PlatformStrategy
)
from tests.testdata import (
    VALID_CAMPAIGN_SPEC_META_TOYS,
    VALID_CAMPAIGN_SPEC_META_ELECTRONICS,
    SAMPLE_PRODUCTS_TOYS,
    SAMPLE_PRODUCTS_ELECTRONICS,
    SAMPLE_PRODUCT_GROUPS_TOYS,
    SAMPLE_PRODUCT_GROUPS_ELECTRONICS,
    SAMPLE_CREATIVES_TOYS,
    SAMPLE_CREATIVES_ELECTRONICS
)


# ============================================================================
# Service TestClient Fixtures (Session scope for performance)
# ============================================================================

@pytest.fixture(scope="session")
def product_client():
    """TestClient for product_service (session scope for performance)."""
    from app.services.product_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def creative_client():
    """TestClient for creative_service (session scope for performance)."""
    from app.services.creative_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def strategy_client():
    """TestClient for strategy_service (session scope for performance)."""
    from app.services.strategy_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def meta_client():
    """TestClient for meta_service (session scope for performance)."""
    from app.services.meta_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def logs_client():
    """TestClient for logs_service (session scope for performance)."""
    from app.services.logs_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def optimizer_client():
    """TestClient for optimizer_service (session scope for performance)."""
    from app.services.optimizer_service.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def orchestrator_client():
    """TestClient for orchestrator (simple_service) (session scope for performance)."""
    from app.orchestrator.simple_service import app
    return TestClient(app)


@pytest.fixture(scope="session")
def llm_orchestrator_client():
    """TestClient for LLM orchestrator (session scope for performance)."""
    from app.orchestrator.llm_service import app
    return TestClient(app)


# ============================================================================
# Campaign Specification Fixtures
# ============================================================================

@pytest.fixture
def campaign_spec_valid():
    """Valid CampaignSpec fixture for electronics."""
    return VALID_CAMPAIGN_SPEC_META_ELECTRONICS


@pytest.fixture
def campaign_spec_toys():
    """CampaignSpec for toys category."""
    return VALID_CAMPAIGN_SPEC_META_TOYS


@pytest.fixture
def campaign_spec_fashion():
    """CampaignSpec for fashion category."""
    return CampaignSpec(
        user_query="Create a fashion campaign",
        platform="meta",
        budget=3000.0,
        objective="traffic",
        category="fashion",
        time_range={"start": "2025-01-01", "end": "2025-01-31"},
        metadata={"locale": "en_US"}
    )


@pytest.fixture
def campaign_spec_small_budget():
    """CampaignSpec with small budget for edge case testing."""
    return CampaignSpec(
        user_query="Create a campaign with small budget",
        platform="meta",
        budget=50.0,
        objective="conversions",
        category="electronics",
        time_range={"start": "2025-01-01", "end": "2025-01-31"},
        metadata={}
    )


@pytest.fixture
def campaign_spec_large_budget():
    """CampaignSpec with large budget for edge case testing."""
    return CampaignSpec(
        user_query="Create a campaign with large budget",
        platform="meta",
        budget=10000.0,
        objective="conversions",
        category="electronics",
        time_range={"start": "2025-01-01", "end": "2025-01-31"},
        metadata={}
    )


# ============================================================================
# Product Fixtures
# ============================================================================

@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return SAMPLE_PRODUCTS_ELECTRONICS


@pytest.fixture
def sample_products_toys():
    """Sample toy products for testing."""
    return SAMPLE_PRODUCTS_TOYS


@pytest.fixture
def sample_product():
    """Single product fixture."""
    return SAMPLE_PRODUCTS_ELECTRONICS[0]


@pytest.fixture
def product_group_high():
    """High priority ProductGroup fixture."""
    return SAMPLE_PRODUCT_GROUPS_ELECTRONICS[0]


@pytest.fixture
def product_group_medium():
    """Medium priority ProductGroup fixture."""
    return ProductGroup(
        group="medium",
        products=[
            Product(
                product_id="PROD-002",
                title="Bluetooth Speaker",
                description="Portable wireless speaker",
                price=79.99,
                category="electronics",
                image_url="https://example.com/speaker.jpg",
                metadata={}
            )
        ],
        score_range=(0.5, 0.8),
        reasoning="Medium conversion potential"
    )


@pytest.fixture
def product_group_low():
    """Low priority ProductGroup fixture."""
    return ProductGroup(
        group="low",
        products=[
            Product(
                product_id="PROD-003",
                title="USB Cable",
                description="Standard USB charging cable",
                price=9.99,
                category="electronics",
                image_url="https://example.com/cable.jpg",
                metadata={}
            )
        ],
        score_range=(0.0, 0.5),
        reasoning="Low conversion potential"
    )


# ============================================================================
# Creative Fixtures
# ============================================================================

@pytest.fixture
def creatives_ab():
    """Creatives with A and B variants fixture."""
    return SAMPLE_CREATIVES_ELECTRONICS


@pytest.fixture
def creatives_toys():
    """Creatives for toys category."""
    return SAMPLE_CREATIVES_TOYS


@pytest.fixture
def sample_creatives():
    """Sample creatives for testing."""
    return SAMPLE_CREATIVES_ELECTRONICS


@pytest.fixture
def creatives_multiple_products():
    """Creatives for multiple products fixture."""
    return [
        Creative(
            creative_id="CREATIVE-001-A",
            product_id="PROD-001",
            platform="meta",
            variant_id="A",
            primary_text="Premium headphones",
            headline="Amazing Headphones",
            image_url="https://example.com/creative1a.jpg"
        ),
        Creative(
            creative_id="CREATIVE-001-B",
            product_id="PROD-001",
            platform="meta",
            variant_id="B",
            primary_text="Wireless headphones",
            headline="Premium Audio",
            image_url="https://example.com/creative1b.jpg"
        ),
        Creative(
            creative_id="CREATIVE-002-A",
            product_id="PROD-002",
            platform="meta",
            variant_id="A",
            primary_text="Portable speaker",
            headline="Bluetooth Speaker",
            image_url="https://example.com/creative2a.jpg"
        ),
        Creative(
            creative_id="CREATIVE-002-B",
            product_id="PROD-002",
            platform="meta",
            variant_id="B",
            primary_text="Wireless speaker",
            headline="Portable Audio",
            image_url="https://example.com/creative2b.jpg"
        )
    ]


# ============================================================================
# Request Payload Fixtures
# ============================================================================

@pytest.fixture
def minimal_valid_request(campaign_spec_valid, product_group_high, creatives_ab):
    """Minimal valid request payload fixture."""
    return {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }


@pytest.fixture
def generate_creatives_request(campaign_spec_valid, sample_products):
    """Request payload for generate_creatives endpoint."""
    return {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "products": [p.model_dump() for p in sample_products],
        "ab_config": {
            "variants_per_product": 2,
            "max_creatives": 10,
            "enable_image_generation": True
        }
    }


@pytest.fixture
def select_products_request(campaign_spec_valid):
    """Request payload for select_products endpoint."""
    return {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "limit": 10
    }


@pytest.fixture
def generate_strategy_request(campaign_spec_valid, product_group_high, creatives_ab):
    """Request payload for generate_strategy endpoint."""
    return {
        "campaign_spec": campaign_spec_valid.model_dump(),
        "product_groups": [product_group_high.model_dump()],
        "creatives": [c.model_dump() for c in creatives_ab]
    }


@pytest.fixture
def create_campaign_request(creatives_ab):
    """Request payload for meta_service create_campaign endpoint."""
    from app.services.meta_service.schemas import AdCreative
    return {
        "campaign_name": "Test Campaign",
        "objective": "CONVERSIONS",
        "daily_budget": 100.0,
        "targeting": {
            "age_min": 25,
            "age_max": 45,
            "genders": [1, 2],
            "locations": ["US"]
        },
        "creatives": [
            {
                "creative_id": c.creative_id,
                "headline": c.headline or "",
                "body_text": c.primary_text,
                "call_to_action": "SHOP_NOW",
                "image_url": c.image_url
            }
            for c in creatives_ab
        ],
        "start_date": "2025-01-01T00:00:00Z"
    }


# ============================================================================
# Mock Fixtures for External Dependencies (Optimized for Performance)
# ============================================================================

@pytest.fixture
def mock_gemini_text():
    """Mock Gemini text generation API - bypasses retry logic for fast tests."""
    # Mock the internal function to avoid retry delays
    with patch('app.services.creative_service.creative_utils._call_gemini_api_internal') as mock_internal, \
         patch('app.services.creative_service.creative_utils.call_gemini_text') as mock:
        # Mock internal function to return immediately (bypasses retry)
        mock_internal.return_value = '{"headline": "Test Headline", "primary_text": "Test primary text content for the ad."}'
        # Also mock the public function for direct calls
        mock.return_value = '{"headline": "Test Headline", "primary_text": "Test primary text content for the ad."}'
        yield mock


@pytest.fixture
def mock_gemini_image():
    """Mock Gemini image generation API - bypasses retry logic for fast tests."""
    with patch('app.services.creative_service.creative_utils.call_gemini_image') as mock:
        # Return immediately, no retry delays
        mock.return_value = "https://example.com/generated-image.jpg"
        yield mock


@pytest.fixture
def mock_gemini_failure():
    """Mock Gemini API failure - bypasses retry logic for fast tests."""
    # Mock internal function to avoid retry delays
    with patch('app.services.creative_service.creative_utils._call_gemini_api_internal') as mock_internal, \
         patch('app.services.creative_service.creative_utils.call_gemini_text') as mock_text, \
         patch('app.services.creative_service.creative_utils.call_gemini_image') as mock_image:
        # Return None immediately, no retry delays
        mock_internal.return_value = None
        mock_text.return_value = None
        mock_image.return_value = None
        yield mock_text, mock_image


@pytest.fixture
def mock_meta_api():
    """Mock Meta Marketing API."""
    with patch('app.services.meta_service.main.get_mock_campaign_response') as mock:
        from app.services.meta_service.schemas import CreateCampaignResponse, AdResult
        mock.return_value = CreateCampaignResponse(
            campaign_id="CAMP-MOCK-123",
            ad_set_id="ADSET-MOCK-456",
            ad_ids=[
                AdResult(ad_id="AD-MOCK-789-A", creative_id="CREATIVE-001-A", status="PENDING_REVIEW"),
                AdResult(ad_id="AD-MOCK-789-B", creative_id="CREATIVE-001-B", status="PENDING_REVIEW")
            ],
            status="ACTIVE"
        )
        yield mock


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for orchestrator service calls."""
    from unittest.mock import MagicMock
    with patch('httpx.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm_generate():
    """Mock LLM generation for orchestrator."""
    with patch('app.orchestrator.llm_service.gemini_model') as mock_model:
        mock_response = MagicMock()
        mock_response.text = '{"platform": "meta", "budget": 5000, "objective": "conversions", "category": "electronics"}'
        mock_model.generate_content.return_value = mock_response
        yield mock_model


# ============================================================================
# Database Fixtures (if needed)
# ============================================================================

@pytest.fixture
def test_db_session(monkeypatch):
    """Mock database session for tests."""
    # Set test database URL
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    yield


@pytest.fixture(autouse=True)
def disable_external_apis(monkeypatch):
    """Automatically disable external API calls in tests."""
    # Disable Gemini API key
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_IMAGE_API_KEY", "")
    # Disable Meta API key
    monkeypatch.setenv("META_ACCESS_TOKEN", "")
    yield
