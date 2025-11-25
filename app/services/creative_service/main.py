"""
Creative Service - MCP microservice for generating ad creatives.

This service generates creative content (text, images) for ad campaigns using:
- Rule-based orchestration
- LLM (Gemini) for copy and image prompt generation
- Optional image generation API
- QA validation
- A/B variant generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
from typing import List, Dict
import uuid
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .schemas import GenerateCreativesRequest, GenerateCreativesResponse
from common.schemas import Creative, ErrorResponse
from .creative_utils import (
    load_creative_policy,
    build_copy_prompt,
    build_image_prompt,
    call_gemini_text,
    call_gemini_image,
    parse_copy_response,
    run_creative_qa,
    fallback_text_generation,
    fallback_image_url,
    get_policy_for_category
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Creative Service",
    description="MCP microservice for generating ad creatives",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "creative_service"}


@app.post("/generate_creatives", response_model=None)
async def generate_creatives(request: GenerateCreativesRequest):
    """
    Generate creative content for ad campaigns.
    
    Args:
        request: Request containing campaign_spec and products
        
    Returns:
        Generated creatives with debug information, or ErrorResponse on failure
    """
    try:
        logger.info(f"Generating creatives for {len(request.products)} products, "
                   f"platform={request.campaign_spec.platform}, "
                   f"objective={request.campaign_spec.objective}")
        
        # Step 1: Validate payload
        if not request.products:
            return ErrorResponse(
                status="error",
                error_code="VALIDATION_ERROR",
                message="No products provided",
                details={}
            )
        
        if not request.campaign_spec:
            return ErrorResponse(
                status="error",
                error_code="VALIDATION_ERROR",
                message="No campaign_spec provided",
                details={}
            )
        
        # Step 2: Load policy
        policy = load_creative_policy()
        logger.debug(f"Loaded policy with categories: {list(policy.keys())}")
        
        # Step 3: Initialize debug info
        debug_info = {
            "copy_prompts": [],
            "image_prompts": [],
            "raw_llm_responses": [],
            "qa_results": []
        }
        
        all_creatives: List[Creative] = []
        
        # Step 4: Generate creatives for each product
        for product in request.products:
            logger.info(f"Processing product: {product.product_id} - {product.title}")
            
            # Generate at least 2 variants (A and B)
            variants = ["A", "B"]
            
            for variant in variants:
                try:
                    # Step 4a: Build prompts
                    copy_prompt = build_copy_prompt(
                        product,
                        request.campaign_spec,
                        policy,
                        variant
                    )
                    image_prompt_prompt = build_image_prompt(
                        product,
                        request.campaign_spec,
                        policy,
                        variant
                    )
                    
                    debug_info["copy_prompts"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "prompt": copy_prompt
                    })
                    debug_info["image_prompts"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "prompt": image_prompt_prompt
                    })
                    
                    # Step 4b: Call LLM for copy
                    logger.debug(f"Calling LLM for copy generation (variant {variant})")
                    copy_response = call_gemini_text(copy_prompt)
                    debug_info["raw_llm_responses"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "type": "copy",
                        "response": copy_response
                    })
                    
                    # Parse copy response
                    headline, primary_text = parse_copy_response(copy_response)
                    
                    # Fallback if LLM failed
                    if not headline or not primary_text:
                        logger.warning(f"LLM copy generation failed for variant {variant}, using fallback")
                        headline, primary_text = fallback_text_generation(
                            product,
                            request.campaign_spec,
                            variant
                        )
                    
                    # Step 4c: Call LLM for image prompt
                    logger.debug(f"Calling LLM for image prompt generation (variant {variant})")
                    image_description = call_gemini_text(image_prompt_prompt)
                    
                    if not image_description:
                        image_description = f"Professional product photography of {product.title}, {get_policy_for_category(product.category, policy).get('visual_style', 'clean')} style"
                    
                    # Step 4d: Optionally call image generator
                    image_url = call_gemini_image(image_description)
                    if not image_url:
                        image_url = fallback_image_url(product)
                    
                    # Step 4e: Assemble Creative object
                    creative = Creative(
                        creative_id=str(uuid.uuid4()),
                        product_id=product.product_id,
                        platform=request.campaign_spec.platform,
                        variant_id=variant,
                        primary_text=primary_text,
                        headline=headline,
                        image_url=image_url,
                        style_profile=get_policy_for_category(product.category, policy),
                        ab_group="control" if variant == "A" else "variant"
                    )
                    
                    # Step 4f: QA checks
                    is_valid, issues = run_creative_qa(creative)
                    debug_info["qa_results"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "is_valid": is_valid,
                        "issues": issues
                    })
                    
                    if not is_valid:
                        logger.warning(f"QA issues for variant {variant}: {issues}")
                        # Continue anyway, but log the issues
                    
                    all_creatives.append(creative)
                    logger.info(f"Generated creative {creative.creative_id} for variant {variant}")
                    
                except Exception as e:
                    logger.error(f"Error generating creative for variant {variant}: {e}")
                    # Continue with next variant
                    continue
        
        # Step 5: Check if we have any creatives
        if not all_creatives:
            logger.error("No creatives generated")
            return ErrorResponse(
                status="error",
                error_code="CREATIVE_GENERATION_FAILED",
                message="Failed to generate any creatives",
                details={"products_processed": len(request.products)}
            )
        
        # Step 6: Build response
        logger.info(f"Successfully generated {len(all_creatives)} creatives")
        
        return GenerateCreativesResponse(
            status="success",
            creatives=all_creatives,
            debug=debug_info
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_creatives: {e}", exc_info=True)
        return ErrorResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            details={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
