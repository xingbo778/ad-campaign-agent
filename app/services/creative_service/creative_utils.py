"""
Utility functions for creative generation.
"""

import os
import yaml
import logging
import google.generativeai as genai
from typing import Dict, Optional, Tuple, List
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini client
gemini_api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
gemini_image_api_key = os.getenv("GEMINI_IMAGE_API_KEY", None)

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
else:
    gemini_model = None
    logger.warning("GEMINI_API_KEY not set. LLM features will use fallback templates.")


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
        variant: Variant ID ("A" or "B")
        
    Returns:
        Prompt string for image generation
    """
    category_policy = get_policy_for_category(product.category, policy)
    
    variant_styles = {
        "A": "product-focused, clean background, professional lighting",
        "B": "lifestyle context, natural setting, emotional connection"
    }
    
    variant_style = variant_styles.get(variant, variant_styles["A"])
    
    prompt = f"""Generate a detailed image prompt for advertising photography.

Product: {product.title}
Category: {product.category}
Visual Style: {category_policy.get('visual_style', 'clean_product_focus')}
Variant Style: {variant_style}
Platform: {campaign_spec.platform}

Generate a concise image description (2-3 sentences) suitable for image generation.
Focus on: composition, lighting, mood, colors, and key visual elements.
Do not include product name or text overlays in the description.

Return ONLY the image description text, no JSON, no markdown, just the description."""
    
    return prompt


def call_gemini_text(prompt: str) -> Optional[str]:
    """
    Call Gemini API for text generation.
    
    Args:
        prompt: Prompt string
        
    Returns:
        Generated text or None if error
    """
    logger.debug(f"call_gemini_text called with prompt length: {len(prompt)}")
    
    if not gemini_model:
        logger.warning("Gemini model not available, using fallback")
        logger.debug(f"gemini_model is None. gemini_api_key exists: {gemini_api_key is not None and len(gemini_api_key) > 0}")
        return None
    
    logger.debug(f"Calling Gemini API with model: {settings.GEMINI_MODEL}")
    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500
            )
        )
        result = response.text.strip() if response and response.text else None
        logger.debug(f"Gemini API call successful, response length: {len(result) if result else 0}")
        return result
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        logger.debug(f"Exception type: {type(e).__name__}, Exception message: {str(e)}")
        return None


def call_gemini_image(image_prompt: str) -> Optional[str]:
    """
    Call Gemini Image API for image generation (if available).
    
    Args:
        image_prompt: Image description prompt
        
    Returns:
        Image URL or None if not available/error
    """
    if not gemini_image_api_key:
        logger.debug("GEMINI_IMAGE_API_KEY not set, skipping image generation")
        return None
    
    # Note: Gemini doesn't have a direct image generation API like DALL-E
    # This is a placeholder for future integration or alternative services
    # For now, return None to use fallback image URLs
    logger.debug("Image generation API not yet implemented")
    return None


def parse_copy_response(llm_response: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse LLM response to extract headline and primary_text.
    
    Args:
        llm_response: Raw LLM response text
        
    Returns:
        Tuple of (headline, primary_text) or (None, None) if parsing fails
    """
    if not llm_response:
        return None, None
    
    try:
        # Remove markdown code blocks if present
        text = llm_response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Try to parse as JSON
        import json
        data = json.loads(text)
        headline = data.get("headline", "").strip()
        primary_text = data.get("primary_text", "").strip()
        
        if headline and primary_text:
            return headline, primary_text
    except Exception as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
    
    # Fallback: try to extract from plain text
    lines = [line.strip() for line in text.split("\n") if line.strip()]
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
    
    Args:
        product: Product object
        campaign_spec: CampaignSpec object
        variant: Variant ID
        
    Returns:
        Tuple of (headline, primary_text)
    """
    if variant == "A":
        headline = f"Discover {product.title}"
        primary_text = f"{product.description[:100]}... Get yours today for ${product.price}!"
    else:
        headline = f"Transform Your Life with {product.title}"
        primary_text = f"Experience the difference. {product.description[:80]}... Limited time offer at ${product.price}."
    
    return headline, primary_text


def fallback_image_url(product) -> str:
    """
    Generate fallback image URL.
    
    Args:
        product: Product object
        
    Returns:
        Placeholder image URL
    """
    # Use product image if available
    if product.image_url:
        return product.image_url
    
    # Return placeholder service URL
    return f"https://via.placeholder.com/1200x630?text={product.title.replace(' ', '+')}"

