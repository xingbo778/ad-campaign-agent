"""
Orchestrator Agent Web Service (Simplified)
提供RESTful API来调用orchestrator agent
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import requests

app = FastAPI(
    title="Ad Campaign Orchestrator Agent",
    description="AI-powered orchestrator for managing ad campaign creation workflow",
    version="1.0.0"
)

# 服务URL配置 - 优先使用环境变量，否则使用本地默认值
from app.common.config import settings

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", settings.PRODUCT_SERVICE_URL)
CREATIVE_SERVICE_URL = os.getenv("CREATIVE_SERVICE_URL", settings.CREATIVE_SERVICE_URL)
STRATEGY_SERVICE_URL = os.getenv("STRATEGY_SERVICE_URL", settings.STRATEGY_SERVICE_URL)
META_SERVICE_URL = os.getenv("META_SERVICE_URL", settings.META_SERVICE_URL)
LOGS_SERVICE_URL = os.getenv("LOGS_SERVICE_URL", settings.LOGS_SERVICE_URL)
# VALIDATOR_SERVICE_URL removed - validation now uses local Pydantic models
OPTIMIZER_SERVICE_URL = os.getenv("OPTIMIZER_SERVICE_URL", settings.OPTIMIZER_SERVICE_URL)


# Request/Response Models
class CampaignRequest(BaseModel):
    """创建广告活动的请求"""
    campaign_objective: str = Field(..., description="Campaign objective (e.g., sales, brand_awareness)")
    target_audience: str = Field(..., description="Target audience description")
    budget: float = Field(..., description="Total budget in USD", gt=0)
    duration_days: int = Field(30, description="Campaign duration in days", gt=0)
    product_category: Optional[str] = Field(None, description="Product category filter")
    platforms: List[str] = Field(["facebook", "instagram"], description="Ad platforms")


class CampaignResponse(BaseModel):
    """创建广告活动的响应"""
    status: str
    campaign_id: Optional[str] = None
    message: str
    workflow_steps: List[Dict[str, Any]]
    selected_products: Optional[List[Dict[str, Any]]] = None
    strategy: Optional[Dict[str, Any]] = None
    creatives: Optional[List[Dict[str, Any]]] = None
    meta_campaign: Optional[Dict[str, Any]] = None


class OptimizationRequest(BaseModel):
    """优化请求"""
    campaign_id: str
    performance_data: Dict[str, Any]


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Ad Campaign Orchestrator Agent",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered orchestrator for ad campaign management",
        "endpoints": {
            "health": "/health",
            "create_campaign": "/create_campaign",
            "optimize_campaign": "/optimize_campaign",
            "services_status": "/services/status",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "orchestrator_agent",
        "connected_services": {
            "product_service": PRODUCT_SERVICE_URL,
            "creative_service": CREATIVE_SERVICE_URL,
            "strategy_service": STRATEGY_SERVICE_URL,
            "meta_service": META_SERVICE_URL,
            "logs_service": LOGS_SERVICE_URL,
            "optimizer_service": OPTIMIZER_SERVICE_URL
        }
    }


@app.post("/create_campaign", response_model=CampaignResponse)
async def create_campaign(request: CampaignRequest):
    """
    创建完整的广告活动
    
    这个端点会协调所有微服务来完成完整的广告活动创建流程：
    1. 选择产品
    2. 生成策略
    3. 生成创意
    4. 创建Meta广告活动
    5. 记录日志
    """
    workflow_steps = []
    
    try:
        # Step 1: 选择产品
        workflow_steps.append({"step": 1, "action": "Selecting products", "status": "in_progress"})
        
        product_request = {
            "campaign_objective": request.campaign_objective,
            "target_audience": request.target_audience,
            "budget": request.budget,
            "product_filters": {"category": request.product_category} if request.product_category else {}
        }
        
        response = requests.post(
            f"{PRODUCT_SERVICE_URL}/select_products",
            json=product_request,
            timeout=30
        )
        response.raise_for_status()
        products_response = response.json()
        selected_products = products_response.get("products", [])
        
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["result"] = f"Selected {len(selected_products)} products"
        
        # Step 2: 生成策略
        workflow_steps.append({"step": 2, "action": "Generating strategy", "status": "in_progress"})
        
        strategy_request = {
            "campaign_objective": request.campaign_objective,
            "total_budget": request.budget,
            "duration_days": request.duration_days,
            "target_audience": request.target_audience,
            "platforms": request.platforms
        }
        
        response = requests.post(
            f"{STRATEGY_SERVICE_URL}/generate_strategy",
            json=strategy_request,
            timeout=30
        )
        response.raise_for_status()
        strategy_response = response.json()
        
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["result"] = f"Strategy generated with {len(strategy_response.get('platform_strategies', []))} platform strategies"
        
        # Step 3: 生成创意
        workflow_steps.append({"step": 3, "action": "Generating creatives", "status": "in_progress"})
        
        product_ids = [p["product_id"] for p in selected_products[:3]]  # 取前3个产品
        
        creative_request = {
            "product_ids": product_ids,
            "campaign_objective": request.campaign_objective,
            "target_audience": request.target_audience,
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
        
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["result"] = f"Generated {len(creatives)} creative variants"
        
        # Step 4: 创建Meta广告活动
        workflow_steps.append({"step": 4, "action": "Creating Meta campaign", "status": "in_progress"})
        
        meta_request = {
            "campaign_name": f"{request.campaign_objective}_campaign",
            "objective": request.campaign_objective,
            "budget": request.budget,
            "target_audience": request.target_audience,
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
        
        workflow_steps[-1]["status"] = "completed"
        workflow_steps[-1]["result"] = f"Meta campaign created: {campaign_id}"
        
        # Step 5: 记录完成
        workflow_steps.append({"step": 5, "action": "Workflow completed", "status": "completed"})
        
        return CampaignResponse(
            status="success",
            campaign_id=campaign_id,
            message="Campaign created successfully through orchestrator",
            workflow_steps=workflow_steps,
            selected_products=selected_products,
            strategy=strategy_response,
            creatives=creatives,
            meta_campaign=meta_response
        )
        
    except requests.exceptions.RequestException as e:
        # 网络或HTTP错误
        workflow_steps.append({
            "step": len(workflow_steps) + 1,
            "action": "Error handling",
            "status": "failed",
            "error": f"Service communication error: {str(e)}"
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Campaign creation failed: {str(e)}",
                "workflow_steps": workflow_steps
            }
        )
    except Exception as e:
        # 其他错误
        workflow_steps.append({
            "step": len(workflow_steps) + 1,
            "action": "Error handling",
            "status": "failed",
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Campaign creation failed: {str(e)}",
                "workflow_steps": workflow_steps
            }
        )


@app.post("/optimize_campaign")
async def optimize_campaign(request: OptimizationRequest):
    """
    优化现有广告活动
    """
    try:
        optimization_request = {
            "campaign_id": request.campaign_id,
            "performance_metrics": request.performance_data
        }
        
        response = requests.post(
            f"{OPTIMIZER_SERVICE_URL}/optimize_campaign",
            json=optimization_request,
            timeout=30
        )
        response.raise_for_status()
        optimization_response = response.json()
        
        return {
            "status": "success",
            "campaign_id": request.campaign_id,
            "recommendations": optimization_response.get("recommendations", []),
            "estimated_improvement": optimization_response.get("estimated_improvement", {})
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


@app.get("/services/status")
async def check_services_status():
    """
    检查所有微服务的状态
    """
    services_status = {}
    
    services = {
        "product_service": PRODUCT_SERVICE_URL,
        "creative_service": CREATIVE_SERVICE_URL,
        "strategy_service": STRATEGY_SERVICE_URL,
        "meta_service": META_SERVICE_URL,
        "logs_service": LOGS_SERVICE_URL,
        "validator_service": VALIDATOR_SERVICE_URL,
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
        "services": services_status,
        "total_services": len(services),
        "healthy_services": sum(1 for s in services_status.values() if s["status"] == "healthy")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
