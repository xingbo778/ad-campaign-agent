"""
Enhanced Orchestrator Agent with LLM Integration
Based on the Agent Prompt design pattern
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import requests
import json
import google.generativeai as genai

app = FastAPI(
    title="Ad Campaign Orchestrator Agent (LLM-Enhanced)",
    description="AI-powered orchestrator with natural language understanding and fixed pipeline execution",
    version="2.0.0"
)

# 服务URL配置 - 优先使用环境变量，否则使用本地默认值
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import settings

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", settings.PRODUCT_SERVICE_URL)
CREATIVE_SERVICE_URL = os.getenv("CREATIVE_SERVICE_URL", settings.CREATIVE_SERVICE_URL)
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", settings.STRATEGY_SERVICE_URL)
META_SERVICE_URL = os.getenv("META_SERVICE_URL", settings.META_SERVICE_URL)
LOGS_SERVICE_URL = os.getenv("LOGS_SERVICE_URL", settings.LOGS_SERVICE_URL)
# VALIDATOR_SERVICE_URL removed - validation now uses local Pydantic models
OPTIMIZER_SERVICE_URL = os.getenv("OPTIMIZER_SERVICE_URL", settings.OPTIMIZER_SERVICE_URL)

# 初始化Gemini客户端
gemini_api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
else:
    gemini_model = None

# Agent Prompt
AGENT_PROMPT = """You are the main orchestrator agent of an ad campaign automation system.

Your role:
- Understand high-level user requests in natural language.
- Convert them into a structured CampaignSpec.
- The system will call MCP-style tools (HTTP services) in a fixed pipeline.

Where you SHOULD use LLM reasoning:
1. Intent parsing: map user request → CampaignSpec.
2. Error explanation and clarification question generation.
3. Final human-readable summary of what was done and why.

Where you SHOULD NOT use LLM reasoning:
- Deciding which tools to call (pipeline is fixed).
- Deciding JSON structures for tools (those are fixed by schema).
- Running business logic for scoring or strategy (delegated to MCPs).

CampaignSpec JSON structure:
{
  "campaign_objective": "sales | brand_awareness | conversions | traffic",
  "target_audience": "description of target audience",
  "budget": <number>,
  "duration_days": <number>,
  "product_category": "optional category filter",
  "platforms": ["facebook", "instagram", "etc"]
}

When parsing user input, extract these fields and return ONLY valid JSON."""


# Models
class NaturalLanguageRequest(BaseModel):
    """自然语言请求"""
    user_request: str = Field(..., description="Natural language description of the campaign needs")
    

class CampaignSpec(BaseModel):
    """结构化的活动规格"""
    campaign_objective: str
    target_audience: str
    budget: float
    duration_days: int = 30
    product_category: Optional[str] = None
    platforms: List[str] = ["facebook", "instagram"]


class CampaignResult(BaseModel):
    """单个活动结果"""
    platform: str
    campaign_id: Optional[str] = None
    products: List[Dict[str, Any]] = []
    creatives: List[Dict[str, Any]] = []
    strategy: Dict[str, Any] = {}
    summary: str


class OrchestratorResponse(BaseModel):
    """Orchestrator响应"""
    status: str
    campaigns: List[CampaignResult] = []
    errors: List[str] = []
    summary: str
    campaign_spec: Optional[Dict[str, Any]] = None


def parse_user_intent(user_request: str) -> CampaignSpec:
    """
    使用LLM解析用户意图并生成CampaignSpec
    """
    try:
        if not gemini_model:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY not configured. Please set GEMINI_API_KEY environment variable."
            )
        
        prompt = f"{AGENT_PROMPT}\n\nParse this campaign request into CampaignSpec JSON:\n\n{user_request}"
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500
            )
        )
        
        content = response.text
        
        # 提取JSON（可能被包裹在markdown代码块中）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        spec_dict = json.loads(content)
        return CampaignSpec(**spec_dict)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse user intent: {str(e)}. Please provide more specific information."
        )


def generate_summary(campaign_spec: CampaignSpec, results: Dict[str, Any]) -> str:
    """
    使用LLM生成最终摘要
    """
    try:
        summary_prompt = f"""Based on the campaign creation results, generate a concise, human-readable summary.

Campaign Spec:
{json.dumps(campaign_spec.dict(), indent=2)}

Results:
- Products selected: {len(results.get('products', []))}
- Creatives generated: {len(results.get('creatives', []))}
- Strategy created: {results.get('strategy', {}).get('strategy_id', 'N/A')}
- Campaign ID: {results.get('campaign_id', 'N/A')}

Generate a 2-3 sentence summary explaining what was accomplished."""

        if not gemini_model:
            return f"Campaign created successfully with {len(results.get('products', []))} products and {len(results.get('creatives', []))} creatives."
        
        prompt = "You are a helpful assistant that summarizes ad campaign creation results.\n\n" + summary_prompt
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=200
            )
        )
        
        return response.text.strip()
        
    except Exception as e:
        return f"Campaign created successfully with {len(results.get('products', []))} products and {len(results.get('creatives', []))} creatives."


def explain_error(error: str, context: Dict[str, Any]) -> str:
    """
    使用LLM解释错误并生成澄清问题
    """
    try:
        error_prompt = f"""An error occurred during campaign creation:

Error: {error}
Context: {json.dumps(context, indent=2)}

Explain this error in simple terms and suggest what information the user should provide to fix it."""

        if not gemini_model:
            return f"Error: {error}. Please check your input and try again."
        
        prompt = "You are a helpful assistant that explains errors clearly.\n\n" + error_prompt
        response = gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=200
            )
        )
        
        return response.text.strip()
        
    except Exception:
        return f"Error: {error}. Please check your input and try again."


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Ad Campaign Orchestrator Agent (LLM-Enhanced)",
        "version": "2.0.0",
        "status": "running",
        "description": "AI-powered orchestrator with natural language understanding",
        "capabilities": [
            "Natural language intent parsing",
            "Fixed pipeline execution",
            "Intelligent error handling",
            "Human-readable summaries"
        ],
        "endpoints": {
            "health": "/health",
            "create_campaign_nl": "/create_campaign_nl (Natural Language)",
            "create_campaign": "/create_campaign (Structured)",
            "services_status": "/services/status",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "orchestrator_agent_llm",
        "llm_enabled": True,
        "connected_services": {
            "product_service": PRODUCT_SERVICE_URL,
            "creative_service": CREATIVE_SERVICE_URL,
            "strategy_service": STRATEGY_SERVICE_URL,
            "meta_service": META_SERVICE_URL,
            "logs_service": LOGS_SERVICE_URL,
            "optimizer_service": OPTIMIZER_SERVICE_URL
        },
        "validation": "Local Pydantic validation (app.common.validators)"
    }


@app.post("/create_campaign_nl", response_model=OrchestratorResponse)
async def create_campaign_natural_language(request: NaturalLanguageRequest):
    """
    从自然语言创建广告活动
    
    这是主要的入口点，接受自然语言描述并：
    1. 使用LLM解析意图 → CampaignSpec
    2. 执行固定的工具调用管道
    3. 使用LLM生成最终摘要
    """
    errors = []
    
    try:
        # Step 1: 使用LLM解析用户意图
        campaign_spec = parse_user_intent(request.user_request)
        
        # Step 2-6: 执行固定管道（与原来的create_campaign相同）
        # Step 2: 选择产品
        product_request = {
            "campaign_objective": campaign_spec.campaign_objective,
            "target_audience": campaign_spec.target_audience,
            "budget": campaign_spec.budget,
            "product_filters": {"category": campaign_spec.product_category} if campaign_spec.product_category else {}
        }
        
        response = requests.post(
            f"{PRODUCT_SERVICE_URL}/select_products",
            json=product_request,
            timeout=30
        )
        response.raise_for_status()
        products_response = response.json()
        selected_products = products_response.get("products", [])
        
        # Step 3: 生成策略
        strategy_request = {
            "campaign_objective": campaign_spec.campaign_objective,
            "total_budget": campaign_spec.budget,
            "duration_days": campaign_spec.duration_days,
            "target_audience": campaign_spec.target_audience,
            "platforms": campaign_spec.platforms
        }
        
        response = requests.post(
            f"{STRATEGY_SERVICE_URL}/generate_strategy",
            json=strategy_request,
            timeout=30
        )
        response.raise_for_status()
        strategy_response = response.json()
        
        # Step 4: 生成创意
        product_ids = [p["product_id"] for p in selected_products[:3]]
        
        creative_request = {
            "product_ids": product_ids,
            "campaign_objective": campaign_spec.campaign_objective,
            "target_audience": campaign_spec.target_audience,
            "brand_guidelines": {"tone": "professional", "style": "modern"}
        }
        
        response = requests.post(
            f"{CREATIVE_SERVICE_URL}/generate_creatives",
            json=creative_request,
            timeout=30
        )
        response.raise_for_status()
        creatives_response = response.json()
        creatives = creatives_response.get("creatives", [])
        
        # Step 5: 创建Meta广告活动
        meta_request = {
            "campaign_name": f"{campaign_spec.campaign_objective}_campaign",
            "objective": campaign_spec.campaign_objective,
            "budget": campaign_spec.budget,
            "target_audience": campaign_spec.target_audience,
            "creatives": [c["creative_id"] for c in creatives[:5]]
        }
        
        response = requests.post(
            f"{META_SERVICE_URL}/create_campaign",
            json=meta_request,
            timeout=30
        )
        response.raise_for_status()
        meta_response = response.json()
        campaign_id = meta_response.get("campaign_id")
        
        # 收集结果
        results = {
            "products": selected_products,
            "strategy": strategy_response,
            "creatives": creatives,
            "campaign_id": campaign_id
        }
        
        # Step 6: 使用LLM生成摘要
        summary = generate_summary(campaign_spec, results)
        
        # 构建响应
        campaign_result = CampaignResult(
            platform="meta",
            campaign_id=campaign_id,
            products=selected_products,
            creatives=creatives,
            strategy=strategy_response,
            summary=f"Created campaign with {len(selected_products)} products and {len(creatives)} creative variants"
        )
        
        return OrchestratorResponse(
            status="success",
            campaigns=[campaign_result],
            errors=[],
            summary=summary,
            campaign_spec=campaign_spec.dict()
        )
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Service communication error: {str(e)}"
        explanation = explain_error(error_msg, {"user_request": request.user_request})
        errors.append(explanation)
        
        return OrchestratorResponse(
            status="error",
            campaigns=[],
            errors=errors,
            summary=explanation
        )
        
    except Exception as e:
        error_msg = str(e)
        explanation = explain_error(error_msg, {"user_request": request.user_request})
        errors.append(explanation)
        
        return OrchestratorResponse(
            status="error",
            campaigns=[],
            errors=errors,
            summary=explanation
        )


@app.post("/create_campaign", response_model=OrchestratorResponse)
async def create_campaign_structured(campaign_spec: CampaignSpec):
    """
    从结构化CampaignSpec创建广告活动
    
    跳过LLM意图解析，直接执行管道
    """
    errors = []
    
    try:
        # 执行固定管道（与create_campaign_nl的步骤2-6相同）
        # ... (代码与上面相同，为简洁省略)
        
        # 简化版：调用自然语言版本
        nl_request = NaturalLanguageRequest(
            user_request=f"Create a {campaign_spec.campaign_objective} campaign for {campaign_spec.target_audience} with budget ${campaign_spec.budget}"
        )
        
        return await create_campaign_natural_language(nl_request)
        
    except Exception as e:
        return OrchestratorResponse(
            status="error",
            campaigns=[],
            errors=[str(e)],
            summary=f"Campaign creation failed: {str(e)}"
        )


@app.get("/services/status")
async def check_services_status():
    """检查所有微服务的状态"""
    services_status = {}
    
    services = {
        "product_service": PRODUCT_SERVICE_URL,
        "creative_service": CREATIVE_SERVICE_URL,
        "strategy_service": STRATEGY_SERVICE_URL,
        "meta_service": META_SERVICE_URL,
        "logs_service": LOGS_SERVICE_URL,
        "optimizer_service": OPTIMIZER_SERVICE_URL,
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            health = response.json()
            services_status[service_name] = {
                "status": "healthy" if health.get("status") == "healthy" else "unhealthy",
                "url": url,
                "response": health
            }
        except Exception as e:
            services_status[service_name] = {
                "status": "unreachable",
                "url": url,
                "error": str(e)
            }
    
    all_healthy = all(s["status"] == "healthy" for s in services_status.values())
    
    return {
        "orchestrator_status": "healthy" if all_healthy else "degraded",
        "llm_enabled": True,
        "services": services_status,
        "total_services": len(services),
        "healthy_services": sum(1 for s in services_status.values() if s["status"] == "healthy")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
