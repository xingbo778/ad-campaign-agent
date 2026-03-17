"""
Mock data generators for amp_service.
"""
import uuid
from app.services.amp_service.schemas import (
    PublishToAMPRequest,
    PublishToAMPResponse,
    AMPListing,
)


def create_mock_response(request: PublishToAMPRequest) -> PublishToAMPResponse:
    """
    Create a mock response for AMP publishing.

    Args:
        request: PublishToAMPRequest with agent creatives and budget

    Returns:
        PublishToAMPResponse with mock campaign_id and listings
    """
    campaign_id = f"amp_campaign_{uuid.uuid4().hex[:12]}"
    listings = [
        AMPListing(
            listing_id=f"amp_listing_{uuid.uuid4().hex[:8]}",
            product_id=creative.product_id,
            status="active",
            marketplace_url=f"https://amp-marketplace.example.com/listings/{creative.product_id}",
        )
        for creative in request.agent_creatives
    ]

    return PublishToAMPResponse(
        campaign_id=campaign_id,
        listings=listings,
        status="active",
    )
