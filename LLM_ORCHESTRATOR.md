# 🤖 LLM-Enhanced Orchestrator Agent

## 概述

基于提供的Agent Prompt设计模式，实现了一个**LLM增强的Orchestrator Agent**，它清晰地区分了LLM应该和不应该参与的决策环节。

---

## 🎯 设计原则

### LLM **应该**使用推理的地方

1. **意图解析 (Intent Parsing)**
   - 将自然语言用户请求 → 结构化的`CampaignSpec`
   - 提取关键信息：目标、受众、预算、时长等

2. **错误解释 (Error Explanation)**
   - 将技术错误消息转换为用户友好的解释
   - 生成澄清问题，帮助用户提供缺失信息

3. **最终摘要 (Final Summary)**
   - 将技术执行结果转换为人类可读的摘要
   - 解释做了什么以及为什么这样做

### LLM **不应该**使用推理的地方

1. **工具调用顺序** - 管道是固定的
2. **JSON结构决策** - Schema由服务定义
3. **业务逻辑** - 评分、策略等委托给MCP服务

---

## 🏗️ 架构

```
用户自然语言请求
        ↓
   [LLM: 意图解析]
        ↓
   CampaignSpec (结构化)
        ↓
   固定管道执行:
   1. product_service.select_products
   2. creative_service.generate_creatives
   3. strategy_service.generate_strategy
   4. meta_service.create_campaign
   5. logs_service.append_event
        ↓
   [LLM: 生成摘要]
        ↓
   人类可读的结果
```

---

## 📡 API端点

### 1. 自然语言接口（推荐）

**POST /create_campaign_nl**

接受自然语言描述，自动解析并执行完整管道。

**请求示例：**

```json
{
  "user_request": "I want to run a sales campaign targeting tech enthusiasts aged 25-45 with a budget of $5000"
}
```

**响应示例：**

```json
{
  "status": "success",
  "campaign_spec": {
    "campaign_objective": "sales",
    "target_audience": "tech enthusiasts aged 25-45",
    "budget": 5000.0,
    "duration_days": 30,
    "platforms": ["facebook", "instagram"]
  },
  "campaigns": [
    {
      "platform": "meta",
      "campaign_id": "camp_abc123",
      "products": [...],
      "creatives": [...],
      "strategy": {...},
      "summary": "Created campaign with 5 products and 6 creative variants"
    }
  ],
  "errors": [],
  "summary": "Successfully created a sales-focused ad campaign targeting tech enthusiasts with a $5000 budget. The campaign includes 5 carefully selected products and 6 creative variants optimized for Facebook and Instagram platforms."
}
```

### 2. 结构化接口

**POST /create_campaign**

接受预定义的`CampaignSpec`，跳过意图解析。

**请求示例：**

```json
{
  "campaign_objective": "sales",
  "target_audience": "tech enthusiasts aged 25-45",
  "budget": 5000.0,
  "duration_days": 30,
  "product_category": "electronics",
  "platforms": ["facebook", "instagram"]
}
```

### 3. 服务状态

**GET /services/status**

检查orchestrator和所有微服务的健康状态。

**GET /health**

Orchestrator自身的健康检查。

---

## 🚀 使用示例

### Python示例

```python
import requests

# 自然语言创建活动
url = "https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/create_campaign_nl"

response = requests.post(url, json={
    "user_request": "Create a brand awareness campaign for fashion lovers with $10000 budget"
})

result = response.json()

print(f"Status: {result['status']}")
print(f"Campaign ID: {result['campaigns'][0]['campaign_id']}")
print(f"Summary: {result['summary']}")
```

### cURL示例

```bash
curl -X POST https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/create_campaign_nl \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Launch a conversion campaign for electronics, budget $3000, targeting millennials"
  }'
```

### JavaScript示例

```javascript
const response = await fetch(
  'https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/create_campaign_nl',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_request: 'I need a sales campaign for tech products with $5000 budget'
    })
  }
);

const result = await response.json();
console.log('Campaign ID:', result.campaigns[0].campaign_id);
console.log('Summary:', result.summary);
```

---

## 🔄 工作流程详解

### Step 1: LLM意图解析

用户输入：
```
"I want to run a sales campaign targeting tech enthusiasts aged 25-45 with a budget of $5000"
```

LLM解析为`CampaignSpec`：
```json
{
  "campaign_objective": "sales",
  "target_audience": "tech enthusiasts aged 25-45",
  "budget": 5000.0,
  "duration_days": 30,
  "product_category": null,
  "platforms": ["facebook", "instagram"]
}
```

### Step 2-5: 固定管道执行

**无需LLM参与**，按固定顺序调用：

1. **Product Service** - 选择最佳产品
2. **Strategy Service** - 生成跨平台策略
3. **Creative Service** - 生成广告创意
4. **Meta Service** - 创建Meta广告活动
5. **Logs Service** - 记录关键事件

### Step 6: LLM生成摘要

将技术结果转换为人类可读的摘要：

```
"Successfully created a sales-focused ad campaign targeting tech enthusiasts 
aged 25-45 with a $5000 budget. The campaign includes 5 carefully selected 
products and 6 creative variants optimized for Facebook and Instagram platforms. 
Expected to reach 50,000+ users over the 30-day campaign period."
```

---

## 🎨 Agent Prompt

系统使用的完整Agent Prompt：

```
You are the main orchestrator agent of an ad campaign automation system.

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

When parsing user input, extract these fields and return ONLY valid JSON.
```

---

## 🛠️ 技术栈

- **FastAPI** - Web框架
- **OpenAI Python SDK** - LLM集成（支持Gemini）
- **Pydantic** - 数据验证
- **Requests** - HTTP客户端
- **Uvicorn** - ASGI服务器

---

## 🌐 部署信息

### 公网访问

**Orchestrator URL:**  
https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer

**交互式API文档:**  
https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/docs

### 连接的微服务

- Product Service: 8001
- Creative Service: 8002
- Strategy Service: 8003
- Meta Service: 8004
- Logs Service: 8005
- Schema Validator: 8006
- Optimizer Service: 8007

---

## 📊 输出格式

### 成功响应

```json
{
  "status": "success",
  "campaigns": [
    {
      "platform": "meta",
      "campaign_id": "camp_abc123",
      "products": [
        {
          "product_id": "prod_001",
          "name": "Smart Watch Pro",
          "priority_score": 0.95
        }
      ],
      "creatives": [
        {
          "creative_id": "creative_001",
          "type": "image",
          "headline": "Discover the Future"
        }
      ],
      "strategy": {
        "strategy_id": "strat_001",
        "platform_strategies": [...]
      },
      "summary": "short explanation for this campaign"
    }
  ],
  "errors": [],
  "summary": "overall natural language summary for the user",
  "campaign_spec": {...}
}
```

### 错误响应

```json
{
  "status": "error",
  "campaigns": [],
  "errors": [
    "The budget you specified ($100) is below the minimum required for a Meta campaign ($500). Please increase your budget to at least $500 to proceed."
  ],
  "summary": "Campaign creation failed due to insufficient budget. Please provide a budget of at least $500.",
  "campaign_spec": {...}
}
```

---

## 🔐 安全和限制

### 当前限制

⚠️ **临时部署** - 基于沙箱环境  
⚠️ **无认证** - 公开访问  
⚠️ **Mock数据** - 微服务返回模拟数据  
⚠️ **无速率限制** - 可能被滥用

### 生产建议

✅ 添加API认证（JWT/API Key）  
✅ 实现速率限制  
✅ 添加请求验证和清理  
✅ 使用真实的数据库和API  
✅ 部署到专业云平台  
✅ 配置监控和告警  
✅ 添加缓存层  
✅ 实现重试和超时策略

---

## 🧪 测试

### 运行测试套件

```bash
cd /home/ubuntu/ad-campaign-agent
python3 test_llm_orchestrator.py
```

### 手动测试

```bash
# 测试健康检查
curl https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/health

# 测试自然语言接口
curl -X POST https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/create_campaign_nl \
  -H "Content-Type: application/json" \
  -d '{"user_request": "Create a sales campaign with $5000 budget"}'

# 测试服务状态
curl https://8000-iwz58hex7zmgmb594dps4-ef747173.manus-asia.computer/services/status
```

---

## 📚 相关文档

- **Agent Prompt设计** - 本文档
- **Orchestrator部署** - `ORCHESTRATOR_DEPLOYMENT.md`
- **微服务部署** - `ONLINE_DEPLOYMENT.md`
- **快速开始** - `QUICKSTART.md`
- **GitHub仓库** - https://github.com/xingbo778/ad-campaign-agent

---

## 🎯 优势

### 1. 清晰的责任分离

- **LLM** - 处理自然语言理解和生成
- **固定管道** - 确保一致的执行流程
- **MCP服务** - 处理业务逻辑和数据

### 2. 可预测性

- 工具调用顺序固定
- Schema由服务定义
- 易于测试和调试

### 3. 可扩展性

- 添加新服务只需更新管道
- LLM部分独立于业务逻辑
- 易于替换LLM提供商

### 4. 用户友好

- 接受自然语言输入
- 智能错误解释
- 人类可读的摘要

---

## 🔮 未来增强

1. **多语言支持** - 支持中文、西班牙语等
2. **上下文记忆** - 记住用户偏好
3. **A/B测试** - 自动测试不同策略
4. **实时优化** - 基于性能数据自动调整
5. **批量操作** - 一次创建多个活动
6. **模板系统** - 保存和重用活动模板

---

**部署时间:** 2025-11-24  
**版本:** 2.0.0 (LLM-Enhanced)  
**状态:** ✅ 在线运行  
**LLM模型:** Gemini 2.5 Flash
