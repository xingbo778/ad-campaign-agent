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
from typing import Union, Dict, Optional, List
from datetime import datetime
import uuid
from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware_class, get_logger
from app.common.config import settings
from app.common.exceptions import register_exception_handlers

from .schemas import GenerateCreativesRequest, GenerateCreativesResponse, ABConfig
from app.common.schemas import Creative, ErrorResponse
from .creative_utils import (
    load_creative_policy,
    build_copy_prompt,
    build_image_prompt,
    call_gemini_text,
    call_openai_image,
    call_gemini_image,
    parse_copy_response,
    run_creative_qa,
    fallback_text_generation,
    fallback_image_url,
    get_policy_for_category,
    generate_video_description,
    call_replicate_video,
    fallback_video_url
)

# Configure unified logging
setup_logging(level=settings.LOG_LEVEL, service_name="creative_service")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Creative Service",
    description="MCP microservice for generating ad creatives",
    version="2.0.0"
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
cors_middleware = get_cors_middleware_class(settings.ENVIRONMENT)
cors_middleware(app)

# Register exception handlers
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "creative_service"}


@app.post("/generate_creatives", response_model=Union[GenerateCreativesResponse, ErrorResponse])
async def generate_creatives(request: GenerateCreativesRequest) -> Union[GenerateCreativesResponse, ErrorResponse]:
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
        
        # Step 2: Parse ab_config (with defaults)
        ab_config = request.ab_config or ABConfig()
        variants_per_product = ab_config.variants_per_product
        max_creatives = ab_config.max_creatives
        enable_image_generation = ab_config.enable_image_generation
        
        logger.info(f"A/B config: {variants_per_product} variants/product, max {max_creatives} creatives, "
                   f"image_gen={enable_image_generation}")
        
        # Step 3: Load policy
        policy = load_creative_policy()
        logger.debug(f"Loaded policy with categories: {list(policy.keys())}")
        
        # Step 4: Initialize debug info
        # Check LLM configuration status
        import os
        from app.common.config import settings
        from app.services.creative_service.creative_utils import gemini_model, gemini_image_model
        gemini_api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        gemini_model_name = settings.GEMINI_MODEL if gemini_api_key else None
        gemini_image_model_name = getattr(settings, 'GEMINI_IMAGE_MODEL', None) if gemini_api_key else None
        gemini_model_initialized = gemini_model is not None
        gemini_image_model_initialized = gemini_image_model is not None
        
        debug_info = {
            "llm_config": {
                "gemini_api_key_set": gemini_api_key is not None and len(gemini_api_key) > 0,
                "gemini_api_key_length": len(gemini_api_key) if gemini_api_key else 0,
                "gemini_api_key_preview": f"{gemini_api_key[:10]}..." if gemini_api_key and len(gemini_api_key) > 10 else "not_set",
                "gemini_model": gemini_model_name,
                "gemini_model_initialized": gemini_model_initialized,
                "gemini_image_model": gemini_image_model_name,
                "gemini_image_model_initialized": gemini_image_model_initialized,
                "gemini_image_api_key_set": os.getenv("GEMINI_IMAGE_API_KEY") is not None,
                "environment_variables": {
                    "GEMINI_API_KEY_from_env": os.getenv("GEMINI_API_KEY") is not None,
                    "GEMINI_API_KEY_from_settings": settings.GEMINI_API_KEY is not None if hasattr(settings, 'GEMINI_API_KEY') else False
                }
            },
            "request_info": {
                "num_products": len(request.products),
                "platform": request.campaign_spec.platform,
                "objective": request.campaign_spec.objective,
                "category": request.campaign_spec.category,
                "budget": request.campaign_spec.budget
            },
            "policy_loaded": {
                "categories": list(policy.keys()) if policy else [],
                "default_policy": policy.get("default", {}) if policy else {}
            },
            "copy_prompts": [],
            "image_prompts": [],
            "raw_llm_responses": [],
            "image_generation": [],
            "qa_results": [],
            "execution_steps": []
        }
        
        all_creatives: List[Creative] = []
        
        # Step 5: Generate creatives for each product
        variant_labels = ["A", "B", "C", "D", "E"][:variants_per_product]
        
        for product in request.products:
            # Check if we've reached max_creatives limit
            if len(all_creatives) >= max_creatives:
                logger.info(f"Reached max_creatives limit ({max_creatives}), stopping generation")
                break
            
            logger.info(f"Processing product: {product.product_id} - {product.title}")
            
            # Generate variants for this product
            variants = variant_labels[:variants_per_product]
            
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
                    
                    # Step 4b: Call LLM for copy with JSON Mode for structured output
                    logger.debug(f"Calling LLM for copy generation (variant {variant})")
                    debug_info["execution_steps"].append({
                        "step": "call_llm_copy",
                        "product_id": product.product_id,
                        "variant": variant,
                        "prompt_length": len(copy_prompt),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Define JSON schema for copy response (JSON Mode)
                    copy_schema = {
                        "type": "object",
                        "properties": {
                            "headline": {"type": "string"},
                            "primary_text": {"type": "string"}
                        },
                        "required": ["headline", "primary_text"]
                    }
                    copy_response = call_gemini_text(copy_prompt, response_schema=copy_schema)
                    copy_llm_success = copy_response is not None and len(copy_response) > 0
                    
                    debug_info["raw_llm_responses"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "type": "copy",
                        "llm_call_success": copy_llm_success,
                        "response": copy_response,
                        "response_length": len(copy_response) if copy_response else 0,
                        "error": None if copy_llm_success else "LLM returned None or empty response"
                    })
                    
                    # Parse copy response
                    logger.debug(f"Parsing copy response for variant {variant}")
                    headline, primary_text = parse_copy_response(copy_response)
                    parse_success = headline is not None and primary_text is not None
                    
                    debug_info["execution_steps"].append({
                        "step": "parse_copy_response",
                        "product_id": product.product_id,
                        "variant": variant,
                        "parse_success": parse_success,
                        "headline": headline,
                        "primary_text": primary_text[:50] + "..." if primary_text and len(primary_text) > 50 else primary_text,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Fallback if LLM failed
                    if not headline or not primary_text:
                        logger.warning(f"LLM copy generation failed for variant {variant}, using fallback")
                        debug_info["execution_steps"].append({
                            "step": "fallback_copy",
                            "product_id": product.product_id,
                            "variant": variant,
                            "reason": "LLM response parsing failed or empty",
                            "timestamp": datetime.now().isoformat()
                        })
                        headline, primary_text = fallback_text_generation(
                            product,
                            request.campaign_spec,
                            variant
                        )
                    
                    # Step 4c: Call LLM for image prompt
                    logger.debug(f"Calling LLM for image prompt generation (variant {variant})")
                    debug_info["execution_steps"].append({
                        "step": "call_llm_image_prompt",
                        "product_id": product.product_id,
                        "variant": variant,
                        "prompt_length": len(image_prompt_prompt),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    image_description = call_gemini_text(image_prompt_prompt)
                    image_description_success = image_description is not None and len(image_description) > 0
                    
                    debug_info["raw_llm_responses"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "type": "image_prompt",
                        "llm_call_success": image_description_success,
                        "response": image_description,
                        "response_length": len(image_description) if image_description else 0,
                        "error": None if image_description_success else "LLM returned None or empty response"
                    })
                    
                    if not image_description:
                        logger.warning(f"LLM image prompt generation failed for variant {variant}, using fallback")
                        debug_info["execution_steps"].append({
                            "step": "fallback_image_prompt",
                            "product_id": product.product_id,
                            "variant": variant,
                            "reason": "LLM returned None or empty response",
                            "timestamp": datetime.now().isoformat()
                        })
                        image_description = f"Professional product photography of {product.title}, {get_policy_for_category(product.category, policy).get('visual_style', 'clean')} style"
                    
                    # Step 4d: Optionally call image generator
                    if enable_image_generation:
                        logger.debug(f"Calling image generator for variant {variant}")
                        
                        # Try OpenAI DALL-E 3 first
                        image_url = call_openai_image(image_description)
                        
                        # Fallback to Gemini if DALL-E fails
                        if not image_url:
                            logger.debug(f"DALL-E 3 failed, trying Gemini")
                            image_url = call_gemini_image(image_description)
                        
                        image_generator_success = image_url is not None and len(image_url) > 0
                        
                        if not image_url:
                            logger.debug(f"All image generators failed for variant {variant}, using fallback")
                            image_url = fallback_image_url(product)
                    else:
                        logger.debug(f"Image generation disabled, using fallback")
                        image_url = fallback_image_url(product)
                        image_generator_success = False
                    
                    # Record image generation debug info
                    debug_info["image_generation"].append({
                        "product_id": product.product_id,
                        "variant": variant,
                        "image_prompt_llm_success": image_description_success,
                        "image_description": image_description,
                        "image_generator_success": image_generator_success,
                        "final_image_url": image_url,
                        "used_fallback": not image_generator_success
                    })
                    
                    # Step 4d-2: Optionally generate video from image
                    video_url = None
                    enable_video_generation = ab_config.enable_video_generation
                    
                    if enable_video_generation and image_url and image_generator_success:
                        logger.debug(f"Generating video for variant {variant}")
                        
                        # Generate video description
                        video_description = generate_video_description(product, request.campaign_spec, variant)
                        
                        # Generate video from image
                        try:
                            video_url = call_replicate_video(image_url, video_description)
                            video_generator_success = video_url is not None
                        except Exception as e:
                            logger.error(f"Video generation failed: {e}")
                            video_url = fallback_video_url(product)
                            video_generator_success = False
                        
                        debug_info["video_generation"] = debug_info.get("video_generation", [])
                        debug_info["video_generation"].append({
                            "product_id": product.product_id,
                            "variant": variant,
                            "video_description": video_description,
                            "video_generator_success": video_generator_success,
                            "final_video_url": video_url,
                            "used_fallback": not video_generator_success
                        })
                    
                    # Step 4e: Assemble Creative object
                    creative = Creative(
                        creative_id=str(uuid.uuid4()),
                        product_id=product.product_id,
                        platform=request.campaign_spec.platform,
                        variant_id=variant,
                        primary_text=primary_text,
                        headline=headline,
                        image_url=image_url,
                        video_url=video_url,
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
                    
                    # Check if we've reached max_creatives limit
                    if len(all_creatives) >= max_creatives:
                        logger.info(f"Reached max_creatives limit ({max_creatives})")
                        break
                    
                except Exception as e:
                    logger.error(f"Error generating creative for variant {variant}: {e}", exc_info=True)
                    # Continue with next variant
                    continue
            
            # Break outer loop if we've reached max_creatives
            if len(all_creatives) >= max_creatives:
                break
        
        # Step 6: Check if we have any creatives
        if not all_creatives:
            logger.error("No creatives generated")
            return ErrorResponse(
                status="error",
                error_code="CREATIVE_GENERATION_FAILED",
                message="Failed to generate any creatives",
                details={"products_processed": len(request.products)}
            )
        
        # Step 7: Build response
        logger.info(f"Successfully generated {len(all_creatives)} creatives")
        
        # Add summary to debug info
        debug_info["summary"] = {
            "total_creatives_generated": len(all_creatives),
            "total_products_processed": len(request.products),
            "variants_per_product": variants_per_product,
            "max_creatives_limit": max_creatives,
            "image_generation_enabled": enable_image_generation,
            "llm_available": gemini_api_key is not None and len(gemini_api_key) > 0,
            "execution_completed": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Count LLM call statistics
        llm_calls = [r for r in debug_info["raw_llm_responses"] if r.get("type") in ["copy", "image_prompt"]]
        successful_llm_calls = [r for r in llm_calls if r.get("llm_call_success", False)]
        debug_info["summary"]["llm_call_stats"] = {
            "total_llm_calls": len(llm_calls),
            "successful_llm_calls": len(successful_llm_calls),
            "failed_llm_calls": len(llm_calls) - len(successful_llm_calls),
            "success_rate": len(successful_llm_calls) / len(llm_calls) if llm_calls else 0
        }
        
        # Add policy information to debug
        debug_info["policy_used"] = {
            "categories_available": list(policy.keys()),
            "default_policy": policy.get("default", {}),
            "products_processed": [
                {
                    "product_id": p.product_id,
                    "category": p.category,
                    "policy_applied": get_policy_for_category(p.category, policy)
                }
                for p in request.products
            ]
        }
        
        # Convert Creative objects to dicts for Pydantic v2 compatibility
        creatives_dict = [creative.model_dump() for creative in all_creatives]
        
        return GenerateCreativesResponse(
            status="success",
            creatives=creatives_dict,
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
