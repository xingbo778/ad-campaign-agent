# 项目优化建议

基于对 `ad-campaign-agent` 项目的全面分析，以下是 5 个最重要的优化建议。

---

## 1. 统一日志配置和中间件管理

### 问题分析

**当前状态：**
- 每个服务都重复配置 `logging.basicConfig(level=logging.INFO)`
- CORS 配置在每个服务中重复（`allow_origins=["*"]`）
- 日志格式不统一，难以追踪跨服务请求
- 缺少请求 ID 追踪机制

**影响：**
- 代码重复，维护成本高
- 日志格式不一致，难以分析
- 无法追踪完整的请求链路

### 优化方案

创建统一的中间件和日志配置模块：

```python
# app/common/middleware.py
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware

# 统一日志配置
def setup_logging(level: str = "INFO"):
    """统一配置日志格式"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# 请求 ID 中间件
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # 添加到日志上下文
        logger = logging.getLogger(__name__)
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        logging.setLogRecordFactory(record_factory)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# CORS 配置工厂
def get_cors_middleware():
    """统一的 CORS 配置"""
    from app.common.config import settings
    
    allowed_origins = ["*"] if settings.ENVIRONMENT == "development" else [
        "https://yourdomain.com"
    ]
    
    return CORSMiddleware(
        app=None,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**使用方式：**
```python
# app/services/product_service/main.py
from app.common.middleware import setup_logging, RequestIDMiddleware, get_cors_middleware

setup_logging(settings.LOG_LEVEL)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(get_cors_middleware())
```

**预期收益：**
- ✅ 减少代码重复（每个服务减少 ~15 行）
- ✅ 统一日志格式，便于日志聚合和分析
- ✅ 支持请求链路追踪
- ✅ 生产环境 CORS 安全配置

---

## 2. 清理 Docker Compose 配置

### 问题分析

**当前状态：**
- `docker-compose.yml` 中仍包含已删除的 `schema_validator_service`（Port 8006）
- 该服务已在代码中移除，但 Docker 配置未更新

**影响：**
- 配置不一致，可能导致部署错误
- 浪费资源（尝试启动不存在的服务）

### 优化方案

```yaml
# docker-compose.yml
# 移除 schema_validator_service 配置（第 80-93 行）

services:
  # ... 其他服务保持不变
  
  # 删除以下服务配置：
  # schema_validator_service:
  #   build: ...
  #   ports:
  #     - "8006:8006"
  #   ...
  
  optimizer_service:
    # ... 保持不变
```

**同时更新：**
- 更新 `docs/CONFIGURATION.md` 中的服务列表
- 确保所有文档反映当前架构

**预期收益：**
- ✅ 配置与代码一致
- ✅ 避免部署错误
- ✅ 减少资源浪费

---

## 3. 增强健康检查端点

### 问题分析

**当前状态：**
- 所有服务只有基本的 `/health` 端点
- 只返回 `{"status": "healthy", "service": "service_name"}`
- 缺少依赖检查（数据库、外部 API、其他服务）
- 缺少资源使用情况（内存、CPU）
- 无法判断服务是否真正可用

**影响：**
- 无法准确判断服务健康状态
- 故障排查困难
- 无法实现自动故障转移

### 优化方案

创建增强的健康检查端点：

```python
# app/common/health.py
from fastapi import APIRouter, status
from typing import Dict, Any, Optional
from datetime import datetime
import psutil
import httpx

router = APIRouter()

class HealthCheck:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.dependencies = []
    
    def add_dependency(self, name: str, check_func):
        """添加依赖检查"""
        self.dependencies.append({"name": name, "check": check_func})
    
    async def check(self) -> Dict[str, Any]:
        """执行健康检查"""
        health_status = {
            "status": "healthy",
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {}
        }
        
        # 系统资源检查
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # 依赖检查
        all_healthy = True
        for dep in self.dependencies:
            try:
                result = await dep["check"]() if callable(dep["check"]) else dep["check"]
                health_status["checks"][dep["name"]] = {
                    "status": "healthy" if result else "unhealthy",
                    "checked_at": datetime.utcnow().isoformat()
                }
                if not result:
                    all_healthy = False
            except Exception as e:
                health_status["checks"][dep["name"]] = {
                    "status": "error",
                    "error": str(e)
                }
                all_healthy = False
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        return health_status

# 使用示例
health_checker = HealthCheck("creative_service")
health_checker.add_dependency("gemini_api", lambda: check_gemini_api())
health_checker.add_dependency("policy_file", lambda: check_policy_file())

@router.get("/health")
async def health():
    return await health_checker.check()

@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    health = await health_checker.check()
    if health["status"] in ["healthy", "degraded"]:
        return health
    return Response(status_code=503, content=health)

@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
```

**预期收益：**
- ✅ 更准确的健康状态判断
- ✅ 支持 Kubernetes 探针
- ✅ 便于故障排查
- ✅ 支持自动故障转移

---

## 4. 统一错误处理中间件

### 问题分析

**当前状态：**
- 每个服务独立处理错误
- 错误响应格式不统一
- 缺少全局异常处理
- 错误日志记录不一致

**影响：**
- 错误处理代码重复
- 客户端难以统一处理错误
- 错误追踪困难

### 优化方案

创建统一的错误处理中间件：

```python
# app/common/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.common.schemas import ErrorResponse
import logging

logger = logging.getLogger(__name__)

class ServiceException(Exception):
    """服务异常基类"""
    def __init__(self, error_code: str, message: str, status_code: int = 500, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

# 全局异常处理器
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    if isinstance(exc, ServiceException):
        logger.warning(f"[{request_id}] Service error: {exc.error_code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status="error",
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details
            ).model_dump()
        )
    
    elif isinstance(exc, RequestValidationError):
        logger.warning(f"[{request_id}] Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                status="error",
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": exc.errors()}
            ).model_dump()
        )
    
    else:
        logger.error(f"[{request_id}] Unexpected error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                status="error",
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details={"request_id": request_id}
            ).model_dump()
        )

# 在 FastAPI app 中注册
# app.add_exception_handler(Exception, global_exception_handler)
```

**使用方式：**
```python
# 在服务中抛出标准异常
from app.common.exceptions import ServiceException

if not product:
    raise ServiceException(
        error_code="PRODUCT_NOT_FOUND",
        message="Product not found",
        status_code=404,
        details={"product_id": product_id}
    )
```

**预期收益：**
- ✅ 统一的错误响应格式
- ✅ 减少错误处理代码重复
- ✅ 更好的错误追踪
- ✅ 客户端统一处理

---

## 5. 完善测试覆盖率

### 问题分析

**当前状态：**
- 只有 `creative_service` 有完整的测试套件（`test_creative_service.py`）
- 其他 5 个服务（product, strategy, meta, logs, optimizer）缺少测试
- 集成测试不完整
- 缺少性能测试和负载测试

**影响：**
- 代码质量无法保证
- 重构风险高
- 难以发现回归问题

### 优化方案

**5.1 为每个服务创建测试文件**

```python
# tests/test_product_service.py
import pytest
from fastapi.testclient import TestClient
from app.services.product_service.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_select_products():
    payload = {
        "campaign_objective": "sales",
        "target_audience": "young professionals",
        "budget": 10000
    }
    response = client.post("/select_products", json=payload)
    assert response.status_code == 200
    assert "products" in response.json()
```

**5.2 创建测试工具模块**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def product_service_client():
    from app.services.product_service.main import app
    return TestClient(app)

@pytest.fixture
def creative_service_client():
    from app.services.creative_service.main import app
    return TestClient(app)

# ... 其他服务的 fixtures
```

**5.3 添加集成测试**

```python
# tests/test_integration.py
def test_full_campaign_flow():
    """测试完整的广告活动创建流程"""
    # 1. 选择产品
    products = product_service.select_products(...)
    
    # 2. 生成创意
    creatives = creative_service.generate_creatives(...)
    
    # 3. 生成策略
    strategy = strategy_service.generate_strategy(...)
    
    # 4. 创建活动
    campaign = meta_service.create_campaign(...)
    
    assert campaign.status == "success"
```

**5.4 添加性能测试**

```python
# tests/test_performance.py
import time
import concurrent.futures

def test_concurrent_requests():
    """测试并发请求性能"""
    def make_request():
        return client.post("/select_products", json=payload)
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    duration = time.time() - start
    assert duration < 5.0  # 100 个请求应在 5 秒内完成
    assert all(r.status_code == 200 for r in results)
```

**预期收益：**
- ✅ 提高代码质量
- ✅ 减少回归问题
- ✅ 支持安全重构
- ✅ 发现性能瓶颈

---

## 实施优先级

| 优先级 | 优化项 | 工作量 | 影响 |
|--------|--------|--------|------|
| 🔴 高 | 1. 统一日志配置 | 2-3 天 | 高 |
| 🔴 高 | 2. 清理 Docker 配置 | 0.5 天 | 中 |
| 🟡 中 | 3. 增强健康检查 | 3-4 天 | 中 |
| 🟡 中 | 4. 统一错误处理 | 2-3 天 | 中 |
| 🟢 低 | 5. 完善测试覆盖 | 5-7 天 | 高 |

---

## 总结

这 5 个优化建议将显著提升项目的：
- **可维护性** - 减少代码重复，统一配置
- **可观测性** - 更好的日志和健康检查
- **可靠性** - 统一错误处理和测试覆盖
- **生产就绪度** - 符合生产环境最佳实践

建议按优先级逐步实施，每个优化都可以独立完成并带来立竿见影的效果。

