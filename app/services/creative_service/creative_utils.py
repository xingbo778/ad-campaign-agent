"""
Utility functions for creative generation.
"""

import os
import yaml
import logging
import json
import google.generativeai as genai
from openai import OpenAI
import replicate
from typing import Dict, Optional, Tuple, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from app.common.config import settings

logger = logging.getLogger(__name__)

# Initialize LLM clients
# Try OpenAI first, then Gemini as fallback
openai_client = None
openai_image_client = None  # Separate client for DALL-E (uses native OpenAI API)
gemini_model = None
gemini_image_model = None
replicate_client = None  # For video generation

# Get API keys from environment
openai_api_key = os.getenv("OPENAI_API_KEY", None)
openai_real_key = os.getenv("OPENAI_REAL_KEY", None)  # For DALL-E 3

if openai_api_key:
    try:
        # Client for text generation (uses Manus proxy)
        openai_client = OpenAI()
        logger.info("OpenAI client initialized successfully (text generation)")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI text client: {e}")
        openai_client = None

if openai_real_key:
    try:
        # Separate client for image generation (uses native OpenAI API)
        openai_image_client = OpenAI(
            api_key=openai_real_key,
            base_url="https://api.openai.com/v1"  # Use native OpenAI API
        )
        logger.info("OpenAI image client initialized successfully (DALL-E 3)")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI image client: {e}")
        openai_image_client = None

if not openai_client:
    # Fallback to Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    gemini_image_api_key = os.getenv("GEMINI_IMAGE_API_KEY", None)
    
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
        gemini_image_model = genai.GenerativeModel(settings.GEMINI_IMAGE_MODEL) if hasattr(settings, 'GEMINI_IMAGE_MODEL') else gemini_model
    else:
        logger.warning("Neither OPENAI_API_KEY nor GEMINI_API_KEY set. LLM features will use fallback templates.")

# Initialize Replicate client for video generation
replicate_api_token = os.getenv("REPLICATE_API_TOKEN", settings.REPLICATE_API_TOKEN)
if replicate_api_token:
    try:
        os.environ["REPLICATE_API_TOKEN"] = replicate_api_token
        replicate_client = replicate.Client(api_token=replicate_api_token)
        logger.info("Replicate client initialized successfully (video generation)")
    except Exception as e:
        logger.warning(f"Failed to initialize Replicate client: {e}")
        replicate_client = None
else:
    logger.warning("REPLICATE_API_TOKEN not set. Video generation will be disabled.")


def load_creative_policy() -> Dict:
    """
    Load creative policy from YAML file or return default policy.
    
    Returns:
        Dictionary containing policy rules by category
    """
    policy_path = os.path.join(
        os.path.dirname(__file__),
        "creative_policy.yaml"
    )
    
    default_policy = {
        "default": {
            "copy_style": "direct_response",
            "visual_style": "clean_product_focus",
            "tone": "professional",
            "headline_style": "benefit_focused",
            "primary_text_length": "medium"
        }
    }
    
    try:
        if os.path.exists(policy_path):
            with open(policy_path, 'r') as f:
                policy = yaml.safe_load(f)
                return policy if policy else default_policy
        else:
            logger.warning(f"Policy file not found at {policy_path}, using default policy")
            return default_policy
    except Exception as e:
        logger.error(f"Error loading policy file: {e}, using default policy")
        return default_policy


def get_policy_for_category(category: str, policy: Dict) -> Dict:
    """
    Get policy rules for a specific category, falling back to default.
    
    Args:
        category: Product category
        policy: Full policy dictionary
        
    Returns:
        Policy rules for the category
    """
    category_lower = category.lower() if category else ""
    
    # Try exact match first
    if category_lower in policy:
        return policy[category_lower]
    
    # Try partial match (e.g., "electronics" matches "electronics")
    for key in policy.keys():
        if key != "default" and key in category_lower:
            return policy[key]
    
    # Fall back to default
    return policy.get("default", {
        "copy_style": "direct_response",
        "visual_style": "clean_product_focus",
        "tone": "professional",
        "headline_style": "benefit_focused",
        "primary_text_length": "medium"
    })


def build_copy_prompt(product, campaign_spec, policy: Dict, variant: str) -> str:
    """
    Build prompt for generating ad copy (headline + primary text).
    
    Args:
        product: Product object
        campaign_spec: CampaignSpec object
        policy: Policy rules for the category
        variant: Variant ID ("A" or "B")
        
    Returns:
        Prompt string for LLM
    """
    category_policy = get_policy_for_category(product.category, policy)
    
    variant_instructions = {
        "A": "Use a direct, benefit-focused approach. Emphasize clear value proposition.",
        "B": "Use a more emotional or storytelling approach. Create connection with the audience."
    }
    
    variant_instruction = variant_instructions.get(variant, variant_instructions["A"])
    
    prompt = f"""Generate advertising copy for a {campaign_spec.platform} ad campaign.

Product Information:
- Title: {product.title}
- Description: {product.description}
- Price: ${product.price}
- Category: {product.category}

Campaign Details:
- Objective: {campaign_spec.objective}
- Platform: {campaign_spec.platform}

Style Guidelines:
- Copy Style: {category_policy.get('copy_style', 'direct_response')}
- Tone: {category_policy.get('tone', 'professional')}
- Headline Style: {category_policy.get('headline_style', 'benefit_focused')}
- Primary Text Length: {category_policy.get('primary_text_length', 'medium')}
- Variant Approach: {variant_instruction}

Platform Requirements:
- Meta: Headline max 40 chars, Primary text max 125 chars
- TikTok: Headline max 80 chars, Primary text max 220 chars
- Google: Headline max 30 chars, Primary text max 90 chars

Generate ONLY a JSON object with this exact structure:
{{
  "headline": "the headline text",
  "primary_text": "the primary text content"
}}

Do not include any markdown formatting, explanations, or additional text. Return only the JSON object."""
    
    return prompt


def build_image_prompt(product, campaign_spec, policy: Dict, variant: str) -> str:
    """
    Build prompt for generating image description/prompt.
    
    Args:
        product: Product object
        campaign_spec: CampaignSpec object
        policy: Policy rules for the category
        variant: Variant ID ("A", "B", "C", etc.)
        
    Returns:
        Prompt string for image generation
    """
    category_policy = get_policy_for_category(product.category, policy)
    
    variant_styles = {
        "A": "product-focused, clean background, professional studio lighting, minimalist composition",
        "B": "lifestyle context, natural setting, emotional connection, people using the product",
        "C": "dynamic action shot, vibrant colors, energetic atmosphere, product in use",
        "D": "comparison or before/after style, problem-solving visual, clear benefits shown",
        "E": "aspirational lifestyle, premium aesthetic, sophisticated composition, luxury feel"
    }
    
    variant_style = variant_styles.get(variant, variant_styles["A"])
    visual_style = category_policy.get('visual_style', 'clean_product_focus')
    
    prompt = f"""You are a professional advertising photographer creating an image brief for a {campaign_spec.platform} ad campaign.

Product: {product.title}
Product Description: {product.description}
Category: {product.category}
Price: ${product.price:.2f}

Campaign Context:
- Platform: {campaign_spec.platform}
- Objective: {campaign_spec.objective}
- Visual Style: {visual_style}
- Variant Style: {variant_style}

Requirements:
1. Create a detailed image description (2-3 sentences) suitable for professional product photography or AI image generation
2. Focus on: composition, lighting, mood, colors, background, and key visual elements
3. Match the visual style: {visual_style}
4. Match the variant approach: {variant_style}
5. Platform-appropriate: {campaign_spec.platform} ads typically use {visual_style} style
6. Do NOT include product name, text overlays, or written content in the description
7. Focus on visual elements that will make the ad compelling and conversion-focused

Generate a concise, professional image description that can be used for image generation or photography direction.

Return ONLY the image description text, no JSON, no markdown, no explanations, just the description."""
    
    return prompt


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def _call_openai_api_internal(prompt: str, json_mode: bool = False) -> Optional[str]:
    """
    Internal function to call OpenAI API with retry logic.
    
    Args:
        prompt: Prompt string
        json_mode: Whether to request JSON output
        
    Returns:
        Generated text or None if error
    """
    if not openai_client:
        return None
    
    messages = [{"role": "user", "content": prompt}]
    
    kwargs = {
        "model": "gpt-4.1-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    
    response = openai_client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip() if response.choices else None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
def _call_gemini_api_internal(prompt: str, response_schema: Optional[Dict] = None) -> Optional[str]:
    """
    Internal function to call Gemini API with retry logic and optional JSON Mode.
    
    Args:
        prompt: Prompt string
        response_schema: Optional JSON schema for structured output (JSON Mode)
        
    Returns:
        Generated text or None if error
    """
    if not gemini_model:
        return None
    
    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=500
    )
    
    # Use JSON Mode if schema provided
    if response_schema:
        generation_config.response_schema = response_schema
        generation_config.response_mime_type = "application/json"
    
    response = gemini_model.generate_content(
        prompt,
        generation_config=generation_config
    )
    return response.text.strip() if response and response.text else None


def call_gemini_text(prompt: str, response_schema: Optional[Dict] = None) -> Optional[str]:
    """
    Call LLM API (OpenAI or Gemini) for text generation with exponential backoff retry.
    
    This function implements retry logic to handle:
    - Rate limiting (429 errors)
    - Timeout errors
    - Transient network errors
    
    Args:
        prompt: Prompt string
        response_schema: Optional JSON schema for structured output (JSON Mode)
                       When provided, forces JSON output matching the schema
        
    Returns:
        Generated text or None if error after retries
        If response_schema is provided, returns valid JSON string
    """
    logger.debug(f"call_gemini_text called with prompt length: {len(prompt)}")
    
    # Try OpenAI first
    if openai_client:
        logger.debug(f"Calling OpenAI API with model: gpt-4.1-mini, JSON Mode: {response_schema is not None}")
        try:
            result = _call_openai_api_internal(prompt, json_mode=(response_schema is not None))
            if result:
                logger.debug(f"OpenAI API call successful, response length: {len(result)}")
                return result
        except RetryError as e:
            logger.error(f"OpenAI API call failed after retries: {e.last_attempt.exception()}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
    
    # Fallback to Gemini
    if gemini_model:
        logger.debug(f"Calling Gemini API with model: {settings.GEMINI_MODEL}, JSON Mode: {response_schema is not None}")
        try:
            result = _call_gemini_api_internal(prompt, response_schema=response_schema)
            logger.debug(f"Gemini API call successful, response length: {len(result) if result else 0}")
            return result
        except RetryError as e:
            logger.error(f"Gemini API call failed after retries: {e.last_attempt.exception()}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
    
    logger.warning("No LLM available, using fallback")
    return None


def call_openai_image(image_prompt: str) -> Optional[str]:
    """
    Call OpenAI DALL-E 3 for image generation using native OpenAI API.
    
    Args:
        image_prompt: Image description prompt
        
    Returns:
        Image URL or None if error
    """
    if not openai_image_client:
        logger.debug("OpenAI image client not available, skipping image generation")
        return None
    
    try:
        logger.info("Calling OpenAI DALL-E 3 for image generation (native API)")
        
        # DALL-E 3 has a 4000 character limit for prompts
        if len(image_prompt) > 4000:
            image_prompt = image_prompt[:3997] + "..."
            logger.warning(f"Image prompt truncated to 4000 characters")
        
        response = openai_image_client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        logger.info(f"✅ DALL-E 3 image generated successfully!")
        logger.info(f"Image URL: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"❌ Error calling DALL-E 3: {e}")
        return None


def call_gemini_image(image_prompt: str) -> Optional[str]:
    """
    Call Gemini Image API for image generation using gemini-2.5-flash-preview-image model.
    
    Args:
        image_prompt: Image description prompt
        
    Returns:
        Image URL or None if not available/error
    """
    if not gemini_image_model:
        logger.debug("Gemini image model not available, skipping image generation")
        return None
    
    if not gemini_api_key:
        logger.debug("GEMINI_API_KEY not set, skipping image generation")
        return None
    
    try:
        logger.debug(f"Calling Gemini Image API with model: {settings.GEMINI_IMAGE_MODEL}")
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500
        )
        
        response = gemini_image_model.generate_content(
            image_prompt,
            generation_config=generation_config
        )
        
        # Note: Gemini image model may return image data or URL
        # Adjust based on actual API response format
        if response and response.text:
            # If response contains image URL, return it
            # Otherwise, may need to extract from response.candidates[0].content.parts
            logger.debug("Gemini Image API call successful")
            # For now, return a placeholder - adjust based on actual API response
            return response.text.strip() if response.text else None
        else:
            logger.warning("Gemini Image API returned empty response")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Gemini Image API: {e}", exc_info=True)
        return None


def parse_copy_response(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse LLM response to extract headline and primary_text.
    
    With JSON Mode enabled, the response should already be valid JSON.
    This function handles both JSON Mode responses and legacy markdown-wrapped responses.
    
    Args:
        llm_response: Raw LLM response text (should be JSON with JSON Mode)
        
    Returns:
        Tuple of (headline, primary_text) or (None, None) if parsing fails
    """
    if not llm_response:
        return None, None
    
    try:
        import json
        # With JSON Mode, response is already valid JSON
        text = llm_response.strip()
        
        # Try direct JSON parse first (JSON Mode)
        try:
            data = json.loads(text)
            headline = data.get("headline", "").strip()
            primary_text = data.get("primary_text", "").strip()
            if headline and primary_text:
                return headline, primary_text
        except json.JSONDecodeError:
            # Fallback: Remove markdown code blocks if present (legacy format)
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Try parsing again after removing markdown
            data = json.loads(text)
            headline = data.get("headline", "").strip()
            primary_text = data.get("primary_text", "").strip()
            if headline and primary_text:
                return headline, primary_text
                
    except Exception as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
    
    # Final fallback: try to extract from plain text
    lines = [line.strip() for line in llm_response.split("\n") if line.strip()]
    if len(lines) >= 2:
        return lines[0], " ".join(lines[1:])
    
    return None, None


def run_creative_qa(creative) -> Tuple[bool, List[str]]:
    """
    Run QA checks on a creative.
    
    Args:
        creative: Creative object to check
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check text length
    if creative.headline:
        if len(creative.headline) > 100:
            issues.append(f"Headline too long: {len(creative.headline)} chars")
    
    if len(creative.primary_text) < 10:
        issues.append(f"Primary text too short: {len(creative.primary_text)} chars")
    elif len(creative.primary_text) > 500:
        issues.append(f"Primary text too long: {len(creative.primary_text)} chars")
    
    # Check for banned words (simple example)
    banned_words = ["spam", "free money", "guaranteed", "click here"]
    text_lower = creative.primary_text.lower()
    if creative.headline:
        text_lower += " " + creative.headline.lower()
    
    for word in banned_words:
        if word in text_lower:
            issues.append(f"Banned word detected: {word}")
    
    # Check for empty fields
    if not creative.primary_text or not creative.primary_text.strip():
        issues.append("Primary text is empty")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def fallback_text_generation(product, campaign_spec, variant: str) -> Tuple[str, str]:
    """
    Generate fallback text when LLM fails.
    
    Uses safe, generic templates that comply with advertising policies.
    
    Args:
        product: Product object
        campaign_spec: CampaignSpec object
        variant: Variant ID
        
    Returns:
        Tuple of (headline, primary_text)
    """
    # Get locale for language-specific fallbacks
    locale = campaign_spec.metadata.get("locale", "en_US") if campaign_spec.metadata else "en_US"
    is_chinese = locale.startswith("zh")
    
    if is_chinese:
        # Chinese fallback templates
        if variant == "A":
            headline = f"{product.title} 限时优惠"
            primary_text = f"高性价比的{product.title}，现在下单享受优惠。{product.description[:80]}..."
        elif variant == "B":
            headline = f"发现 {product.title}"
            primary_text = f"体验{product.title}带来的改变。{product.description[:80]}... 立即购买，仅需${product.price:.2f}。"
        else:
            headline = f"{product.title} 热销中"
            primary_text = f"{product.description[:100]}... 现在购买，享受特价${product.price:.2f}。"
    else:
        # English fallback templates
        if variant == "A":
            headline = f"Discover {product.title}"
            primary_text = f"{product.description[:100]}... Get yours today for ${product.price:.2f}!"
        elif variant == "B":
            headline = f"Transform Your Life with {product.title}"
            primary_text = f"Experience the difference. {product.description[:80]}... Limited time offer at ${product.price:.2f}."
        else:
            headline = f"{product.title} - Special Offer"
            primary_text = f"{product.description[:100]}... Shop now and save! Only ${product.price:.2f}."
    
    # Ensure length constraints (platform-specific)
    platform_max = {
        "meta": {"headline": 40, "primary": 125},
        "tiktok": {"headline": 80, "primary": 220},
        "google": {"headline": 30, "primary": 90}
    }
    limits = platform_max.get(campaign_spec.platform, platform_max["meta"])
    
    if len(headline) > limits["headline"]:
        headline = headline[:limits["headline"]-3] + "..."
    if len(primary_text) > limits["primary"]:
        primary_text = primary_text[:limits["primary"]-3] + "..."
    
    return headline, primary_text


def fallback_image_url(product) -> str:
    """
    Generate fallback image URL.
    
    Uses deterministic placeholder URLs based on product ID for consistency.
    
    Args:
        product: Product object
        
    Returns:
        Placeholder image URL
    """
    # Use product image if available
    if product.image_url and product.image_url.startswith(("http://", "https://")):
        return product.image_url
    
    # Use deterministic placeholder based on product ID
    # This ensures the same product always gets the same placeholder image
    import hashlib
    product_hash = hashlib.md5(product.product_id.encode()).hexdigest()[:8]
    
    # Use picsum.photos with seed for deterministic images
    return f"https://picsum.photos/seed/{product_hash}/1200/630"


def generate_video_description(product, campaign_spec, variant: str = "A") -> str:
    """
    Generate AI-powered video description/prompt for video generation.
    
    Args:
        product: Product object with details
        campaign_spec: Campaign specification
        variant: Creative variant (A or B)
        
    Returns:
        Video description/prompt string
    """
    # Build prompt for video description
    prompt = f"""Generate a detailed video description for an advertising video based on this product:

Product: {product.title}
Description: {product.description}
Price: ${product.price:.2f}
Category: {product.category}
Platform: {campaign_spec.platform}

The video should:
- Be 5 seconds long
- Show the product in an appealing way
- Match the advertising platform style ({campaign_spec.platform})
- Variant {variant}: {"Focus on product features and benefits" if variant == "A" else "Create emotional connection and lifestyle appeal"}

Describe the video motion, camera movement, and visual effects in detail. Keep it under 200 characters."""

    # Try OpenAI first
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional video director creating advertising videos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            description = response.choices[0].message.content.strip()
            logger.info(f"Generated video description using OpenAI for variant {variant}")
            return description
        except Exception as e:
            logger.warning(f"OpenAI video description generation failed: {e}, falling back to template")
    
    # Fallback to template
    if variant == "A":
        description = f"Smooth 360-degree rotation of {product.title} on a clean white background, highlighting key features and premium quality"
    else:
        description = f"Dynamic lifestyle shot of {product.title} in use, with smooth camera movement and warm lighting creating aspirational mood"
    
    logger.info(f"Using template video description for variant {variant}")
    return description


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception)
)
def call_replicate_video(image_url: str, video_description: str) -> Optional[str]:
    """
    Generate video from image using Replicate Wan 2.5 model.
    
    Args:
        image_url: URL of the input image (from DALL-E 3)
        video_description: Text description/prompt for video generation
        
    Returns:
        Video URL or None if generation fails
    """
    if not replicate_client:
        logger.warning("Replicate client not initialized, video generation disabled")
        return None
    
    try:
        logger.info(f"Generating video with Replicate Wan 2.5...")
        logger.info(f"Image URL: {image_url[:100]}...")
        logger.info(f"Video description: {video_description}")
        
        # Run the model
        output = replicate_client.run(
            settings.REPLICATE_VIDEO_MODEL,
            input={
                "image": image_url,
                "prompt": video_description,
                "duration": 5,  # 5 seconds
                "num_frames": 125,  # 25 fps * 5 seconds
            }
        )
        
        # The output is typically a FileOutput object or URL
        if output:
            video_url = str(output) if not isinstance(output, str) else output
            logger.info(f"Video generated successfully: {video_url[:100]}...")
            return video_url
        else:
            logger.error("Replicate returned empty output")
            return None
            
    except Exception as e:
        logger.error(f"Replicate video generation failed: {e}")
        raise


def fallback_video_url(product) -> Optional[str]:
    """
    Generate fallback video URL (placeholder or None).
    
    Args:
        product: Product object
        
    Returns:
        Placeholder video URL or None
    """
    # For now, return None as we don't have a good placeholder video service
    # In production, you might want to use a default product video
    logger.warning(f"Using fallback (no video) for product {product.product_id}")
    return None


def generate_storyline(
    product_title: str,
    product_description: str,
    category: str,
    platform: str,
    objective: str,
    num_segments: int = 3,
    request_id: str = ""
) -> Optional[Dict]:
    """
    Generate a storyline for multi-segment video generation.
    
    Args:
        product_title: Product name
        product_description: Product description
        category: Product category
        platform: Target platform (meta, tiktok, google)
        objective: Campaign objective
        num_segments: Number of video segments (default: 3)
        request_id: Request ID for logging
        
    Returns:
        Storyline dict with theme, style, and segments
    """
    logger.info(f"[{request_id}] - Generating {num_segments}-segment storyline for {product_title}")
    
    prompt = f"""Create a {num_segments}-segment video storyline for {product_title}.

Product: {product_description}
Category: {category}
Platform: {platform}

Create {num_segments} segments (5 seconds each):
- Segment 1: Product close-up
- Segment 2: Person using product
- Segment 3: Benefits and CTA

Return valid JSON only (no markdown, no explanations):
{{
  "theme": "string",
  "style": "minimalist_modern",
  "total_duration": {num_segments * 5},
  "num_segments": {num_segments},
  "segments": [
    {{
      "segment_id": 1,
      "duration": 5,
      "scene_description": "string",
      "camera_movement": "slow_zoom_in",
      "focus": "product_detail",
      "text_overlay": "string",
      "video_prompt": "string"
    }}
  ]
}}"""

    try:
        # Use call_gemini_text with JSON Mode enabled
        response_schema = {
            "type": "object",
            "properties": {
                "theme": {"type": "string"},
                "style": {"type": "string"},
                "total_duration": {"type": "integer"},
                "num_segments": {"type": "integer"},
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "segment_id": {"type": "integer"},
                            "duration": {"type": "integer"},
                            "scene_description": {"type": "string"},
                            "camera_movement": {"type": "string"},
                            "focus": {"type": "string"},
                            "text_overlay": {"type": "string"},
                            "video_prompt": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        response = call_gemini_text(prompt, response_schema=response_schema)
        if response:
            storyline = json.loads(response)
            logger.info(f"[{request_id}] - Storyline generated successfully")
            return storyline
        
        logger.error(f"[{request_id}] - No LLM available for storyline generation")
        return None
        
    except json.JSONDecodeError as e:
        logger.error(f"[{request_id}] - Failed to parse storyline JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"[{request_id}] - Error generating storyline: {e}")
        return None


def generate_lifestyle_product_image_prompt(
    product_title: str,
    product_description: str,
    category: str,
    storyline_style: str,
    request_id: str = ""
) -> str:
    """
    Generate DALL-E prompt for lifestyle product image (with person using product).
    
    Args:
        product_title: Product name
        product_description: Product description
        category: Product category
        storyline_style: Visual style from storyline
        request_id: Request ID for logging
        
    Returns:
        DALL-E prompt string
    """
    # Determine usage scenario based on category
    usage_scenarios = {
        "electronics": "modern workspace or home office",
        "fashion": "urban street or cafe setting",
        "health": "gym or outdoor fitness setting",
        "home": "cozy living room or bedroom",
        "toys": "playful indoor setting with natural light"
    }
    
    scenario = usage_scenarios.get(category, "modern lifestyle setting")
    
    prompt = f"""Professional lifestyle product photography featuring {product_title}.

Scene: A person using/wearing the product in a {scenario}.

Product Details:
{product_description}

Requirements:
- Product clearly visible and in focus
- Person appears natural, relatable, and engaged with the product
- Clean, professional composition
- {storyline_style} visual style
- Soft, natural lighting
- High detail on both product and person
- Suitable for video animation (stable, clear image)
- No text, logos, or overlays
- Product should maintain consistent appearance for video generation

Mood: Professional, aspirational, authentic
Lighting: Soft natural light, slightly diffused
Composition: Medium shot showing person and product clearly"""

    logger.info(f"[{request_id}] - Generated lifestyle product image prompt")
    return prompt


def download_video(url: str, output_path: str) -> bool:
    """
    Download video from URL to local file.
    
    Args:
        url: Video URL
        output_path: Local file path to save video
        
    Returns:
        True if successful, False otherwise
    """
    import requests
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded video to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download video from {url}: {e}")
        return False


def concatenate_videos(video_urls: List[str], output_path: str, request_id: str = "") -> Optional[str]:
    """
    Concatenate multiple videos into one using FFmpeg.
    
    Args:
        video_urls: List of video URLs to concatenate
        output_path: Output file path
        request_id: Request ID for logging
        
    Returns:
        Output file path if successful, None otherwise
    """
    import subprocess
    import tempfile
    import os
    
    logger.info(f"[{request_id}] - Concatenating {len(video_urls)} video segments")
    
    try:
        # Create temporary directory for downloaded videos
        temp_dir = tempfile.mkdtemp()
        video_files = []
        
        # Download all videos
        for i, url in enumerate(video_urls):
            video_file = os.path.join(temp_dir, f"segment_{i}.mp4")
            if download_video(url, video_file):
                video_files.append(video_file)
            else:
                logger.error(f"[{request_id}] - Failed to download segment {i}")
                return None
        
        if len(video_files) != len(video_urls):
            logger.error(f"[{request_id}] - Not all videos downloaded successfully")
            return None
        
        # Create concat file for FFmpeg
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w") as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")
        
        # Run FFmpeg to concatenate videos
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-y",  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.error(f"[{request_id}] - FFmpeg error: {result.stderr}")
            return None
        
        logger.info(f"[{request_id}] - Videos concatenated successfully: {output_path}")
        
        # Clean up temporary files
        for video_file in video_files:
            try:
                os.remove(video_file)
            except:
                pass
        try:
            os.remove(concat_file)
            os.rmdir(temp_dir)
        except:
            pass
        
        return output_path
        
    except Exception as e:
        logger.error(f"[{request_id}] - Error concatenating videos: {e}")
        return None


def generate_video_segments(
    image_url: str,
    storyline: Dict,
    request_id: str = ""
) -> List[Optional[str]]:
    """
    Generate multiple video segments based on storyline.
    
    Args:
        image_url: Product image URL (with person using it)
        storyline: Storyline dict with segments
        request_id: Request ID for logging
        
    Returns:
        List of video URLs (one per segment)
    """
    logger.info(f"[{request_id}] - Generating {len(storyline['segments'])} video segments")
    
    video_urls = []
    
    for segment in storyline['segments']:
        segment_id = segment['segment_id']
        video_prompt = segment['video_prompt']
        
        logger.info(f"[{request_id}] - Generating segment {segment_id}")
        logger.info(f"[{request_id}] - Video prompt: {video_prompt}")
        
        try:
            video_url = call_replicate_video(image_url, video_prompt)
            video_urls.append(video_url)
            
            if video_url:
                logger.info(f"[{request_id}] - Segment {segment_id} generated successfully")
            else:
                logger.error(f"[{request_id}] - Segment {segment_id} generation failed")
                
        except Exception as e:
            logger.error(f"[{request_id}] - Error generating segment {segment_id}: {e}")
            video_urls.append(None)
    
    # Check if all segments were generated successfully
    successful_count = sum(1 for url in video_urls if url is not None)
    logger.info(f"[{request_id}] - Generated {successful_count}/{len(video_urls)} segments successfully")
    
    return video_urls
