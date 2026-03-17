"""
Mock data generators for meta_service.
"""
import uuid
from app.services.meta_service.schemas import CreateCampaignResponse, CreateCampaignRequest


def create_mock_response(request: CreateCampaignRequest) -> CreateCampaignResponse:
    """
    Create a mock response for campaign creation.
    
    Args:
        request: CreateCampaignRequest with campaign details
        
    Returns:
        CreateCampaignResponse with mock campaign_id and ad_ids
    """
    # Generate mock IDs
    campaign_id = f"campaign_{uuid.uuid4().hex[:12]}"
    ad_ids = [f"ad_{uuid.uuid4().hex[:8]}" for _ in range(len(request.creatives))]
    
    return CreateCampaignResponse(
        campaign_id=campaign_id,
        ad_ids=ad_ids,
        status="active"
    )




