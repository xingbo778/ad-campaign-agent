# Ad Campaign Agent - 长期优化 Roadmap

## 目标愿景

从当前**固定 Pipeline + LLM 辅助**架构，演进为**真正的 Agent 架构**——Agent 自主决策调用哪些 tool、什么顺序、如何处理异常，而非硬编码的线性流程。

---

## Phase 1: 安全与关键 Bug 修复（立即）

### 1.1 安全问题
- [ ] **移除 API Key 日志泄露**: `app/services/creative_service/main.py:129-135` 日志打印了 `gemini_api_key_preview`（前10字符）
- [ ] **LLM 输入验证**: `app/orchestrator/llm_service.py:312` 用户请求无长度/内容校验，存在 prompt injection 和 DoS 风险
- [ ] **CORS 配置**: `app/common/middleware.py:120` 生产域名为占位符 `yourdomain.com`

### 1.2 Bug 修复
- [ ] **Pydantic API 不一致**: `llm_service.py:203` 用 `.dict()`（v1），`simple_service.py` 用 `.model_dump()`（v2），统一为 v2
- [ ] **静默异常吞没**: `product_service/scoring.py:205`、`strategy_logic.py:252,319,519` 中 `except: pass`
- [ ] **Logger 初始化不一致**: `creative_utils.py:22` 直接用 `logging.getLogger` 而非共享 `get_logger`

---

## Phase 2: 代码质量与技术债务清理（1-2周）

### 2.1 消除重复代码
- [ ] **抽取 Pipeline Runner**: `simple_service.py` 和 `llm_service.py` 的 pipeline 逻辑几乎相同，抽取为 `app/orchestrator/pipeline.py`
- [ ] **Service Client 基类**: 7 个 client 模式完全一致，抽取 `BaseMCPClient`
- [ ] **统一 HTTP 客户端**: `simple_service.py` 用同步 `requests`，`llm_service.py` 用异步 `httpx`，统一为异步

### 2.2 配置外部化
- [ ] 超时时间（6 处硬编码 `timeout=30`）→ 移入 `config.py`
- [ ] LLM 超参数（temperature、max_tokens）→ 配置化
- [ ] 评分权重 magic number（0.4/0.3/0.2/0.1）→ 提取常量
- [ ] `simple_service.py:22-28` 重复定义 URL → 统一使用 `settings`

### 2.3 大文件拆分
- [ ] `creative_utils.py`（1094行）→ `copy_generation.py`、`image_generation.py`、`video_generation.py`、`qa_validation.py`

---

## Phase 3: 可靠性与可观测性（2-4周）

### 3.1 服务容错
- [ ] **重试机制**: 为每个服务调用添加可配置重试（tenacity 已引入）
- [ ] **Circuit Breaker**: 服务连续失败 N 次后快速失败
- [ ] **Partial Success**: 部分服务失败仍返回结果
- [ ] **Checkpoint/Resume**: pipeline 执行状态持久化

### 3.2 可观测性
- [ ] **分布式追踪**: RequestID 传播到所有服务间调用（当前 middleware 生成 ID 但不传播）
- [ ] **结构化指标**: 每个服务暴露 `/metrics` 端点（Prometheus 格式）
- [ ] **OpenTelemetry**: trace/span 集成

### 3.3 限流与安全
- [ ] API 请求速率限制
- [ ] LLM API 调用 token bucket 限流
- [ ] 并发控制

---

## Phase 4: 轻量级 Agent 架构演进（4-8周）⭐ 核心变化

> **设计原则**: 不引入 ADK 等重框架，直接用 Gemini/OpenAI 原生 function calling + 自研轻量 Agent loop（~200 行核心代码）。

### 4.1 Tool 抽象层

```python
# app/agent/tool.py — 轻量 Tool 定义，不依赖任何 Agent 框架
class BaseTool(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema，直接喂给 function calling

    @abstractmethod
    async def execute(self, **kwargs) -> dict: ...

    def to_function_schema(self) -> dict:
        """生成 Gemini/OpenAI function calling schema"""
        return {"name": self.name, "description": self.description,
                "parameters": self.parameters}

# 现有 Client 直接变 Tool
class SelectProductsTool(BaseTool):
    name = "select_products"
    async def execute(self, **kwargs):
        return await self.product_client.select_products(kwargs)
```

- [ ] **定义 `BaseTool`**: ~30 行，name + description + parameters + execute
- [ ] **适配现有 Service**: 每个 `*Client` 包一层 `*Tool`（每个 ~20 行）
- [ ] **Tool Registry**: `dict[str, BaseTool]`，支持动态注册
- [ ] **Schema 生成**: `agent_config.yaml` → function calling schema 自动转换

### 4.2 轻量 Agent 执行引擎

```python
# app/agent/agent.py — 核心 ~100 行
class Agent:
    def __init__(self, llm_client, tools: list[BaseTool], system_prompt: str):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt

    async def run(self, user_request: str, max_steps: int = 10) -> AgentResult:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_request}
        ]
        steps = []

        for step in range(max_steps):
            # LLM 决定下一步：调用 tool 还是返回最终结果
            response = await self.llm.generate(
                messages=messages,
                tools=[t.to_function_schema() for t in self.tools.values()]
            )

            if not response.tool_calls:
                return AgentResult(answer=response.text, steps=steps)

            # 执行 LLM 选择的 tool
            for call in response.tool_calls:
                tool = self.tools[call.name]
                result = await tool.execute(**call.arguments)
                steps.append(AgentStep(tool=call.name, args=call.arguments, result=result))
                messages.append({"role": "tool", "name": call.name, "content": json.dumps(result)})

        raise AgentMaxStepsError(f"Agent exceeded {max_steps} steps")
```

- [ ] **ReAct Loop**: LLM 自主决定 tool 调用顺序，无硬编码 pipeline
- [ ] **Function Calling**: 直接用 Gemini `generate_content(tools=...)` / OpenAI `functions`
- [ ] **最大步数**: 默认 10 步，防止无限循环
- [ ] **Token/Cost 跟踪**: 每轮记录 input/output tokens
- [ ] **Streaming 支持**: Agent 思考过程实时返回给用户

### 4.3 LLM Provider 抽象

```python
# app/agent/llm.py — 统一 Gemini/OpenAI 接口，~80 行
class LLMProvider(ABC):
    async def generate(self, messages, tools=None) -> LLMResponse: ...

class GeminiProvider(LLMProvider): ...   # 包装 google.generativeai
class OpenAIProvider(LLMProvider): ...   # 包装 openai
```

- [ ] **统一接口**: 屏蔽 Gemini 和 OpenAI function calling 格式差异
- [ ] **自动 Fallback**: Gemini 失败 → OpenAI（已有雏形，正式化）

### 4.4 Agent 记忆
- [ ] **短期记忆**: messages 列表（tool 调用 + 结果 + LLM 推理）
- [ ] **长期记忆**: 历史 campaign 结果存 DB，Agent 可查询（"上次 electronics $5000 ROAS=3.2"）
- [ ] **Context 压缩**: tool 结果过长时 LLM 自动摘要

### 4.5 Safety Guardrails
- [ ] **Human-in-the-loop**: 高风险 tool（meta deploy）执行前需确认
- [ ] **预算上限**: Agent 不能分配超过用户指定预算
- [ ] **Dry Run**: 生成完整计划但不执行
- [ ] **Audit Log**: 每个 tool 调用记入 logs_service

### 新增文件

```
app/agent/
├── __init__.py
├── tool.py          # BaseTool 抽象 + Tool Registry (~50 行)
├── agent.py         # Agent ReAct loop (~100 行)
├── llm.py           # LLM Provider 抽象 (~80 行)
├── memory.py        # 短期/长期记忆 (~60 行)
├── guardrails.py    # 安全护栏 (~40 行)
└── tools/           # 具体 Tool 实现
    ├── product_tool.py
    ├── creative_tool.py
    ├── strategy_tool.py
    ├── meta_tool.py
    ├── logs_tool.py
    └── optimizer_tool.py
```

**总计约 500 行核心代码，零外部 Agent 框架依赖。**

---

## Phase 5: 业务功能增强（8-12周）

### 5.1 Meta Service 真实集成
- [ ] Facebook Marketing API (`facebook-business` SDK)
- [ ] OAuth 2.0 认证
- [ ] Campaign → Ad Set → Ad 完整链路
- [ ] 素材上传、状态监控 webhook

### 5.2 新 Tool 扩展（Agent 可动态调用）
- [ ] `analyze_audience` - 受众分析 tool
- [ ] `estimate_reach` - 到达率预估 tool
- [ ] `check_compliance` - 广告合规检查 tool
- [ ] `compare_campaigns` - 历史 campaign 对比 tool
- [ ] `adjust_budget` - 运行中 campaign 预算调整 tool

### 5.3 Creative Service 增强
- [ ] Meta Ads Policy 合规验证
- [ ] CDN 图片托管（S3 + CloudFront）
- [ ] 视频持久化存储
- [ ] 更多 A/B 变体策略

### 5.4 Optimizer Service 真实实现
- [ ] 接入真实 Analytics 数据
- [ ] ROAS/CPA/CTR 计算
- [ ] 异常检测
- [ ] 自动优化建议（Agent 可主动触发）

---

## Phase 6: 多 Agent 协作与 ML 集成（12周+）

### 6.1 Multi-Agent 协作（复用 Phase 4 的轻量 Agent）
```
┌──────────────────────────────────────────────┐
│         Supervisor Agent (Agent 实例)         │
│    tools = [delegate_to_creative_agent,       │
│             delegate_to_strategy_agent, ...]  │
├──────────┬──────────┬──────────┬─────────────┤
│ Campaign │ Creative │ Strategy │ Performance  │
│  Agent   │  Agent   │  Agent   │   Agent      │
│ (Agent)  │ (Agent)  │ (Agent)  │  (Agent)     │
│ tools=   │ tools=   │ tools=   │ tools=       │
│ [select, │ [gen_    │ [gen_    │ [summarize,  │
│  deploy] │  copy,   │  budget, │  analyze]    │
│          │  image]  │  target] │              │
└──────────┴──────────┴──────────┴─────────────┘
```
- [ ] 每个子 Agent 是 Phase 4 的 `Agent` 实例，配不同 tools + prompt
- [ ] Supervisor 的 "tools" 是调用子 Agent（Agent-as-Tool 模式）
- [ ] 共享 memory 层，Agent 间结果传递

### 6.2 ML 集成
- [ ] 产品评分 ML 模型（基于历史 CTR/转化学习权重）
- [ ] 预算分配 Multi-Armed Bandit
- [ ] Creative 表现预测模型
- [ ] Agent 自动触发 A/B 测试

### 6.3 多平台扩展
- [ ] TikTok Ads API tool
- [ ] Google Ads API tool
- [ ] Agent 自主选择最优平台组合

### 6.4 基础设施
- [ ] Kubernetes 部署（Helm Charts）
- [ ] CI/CD Pipeline（GitHub Actions）
- [ ] 数据库迁移（Alembic）
- [ ] Secret 管理（Vault / AWS SM）
- [ ] API 版本化（v1/v2）

---

## 架构演进路线总览

```
Phase 1-2: 修复 + 清理
  ┌──────────────────────┐
  │  Fixed Pipeline      │  ← 当前
  │  LLM = parsing only  │
  └──────────────────────┘
           ↓
Phase 3: 可靠性
  ┌──────────────────────┐
  │  Robust Pipeline     │
  │  + Circuit Breaker   │
  │  + Observability     │
  └──────────────────────┘
           ↓
Phase 4: Agent 化 ⭐
  ┌──────────────────────┐
  │  Single Agent        │
  │  + Tool Registry     │
  │  + ReAct Loop        │
  │  + Function Calling  │
  └──────────────────────┘
           ↓
Phase 5: 业务扩展
  ┌──────────────────────┐
  │  Agent + Real APIs   │
  │  + More Tools        │
  │  + Memory            │
  └──────────────────────┘
           ↓
Phase 6: Multi-Agent
  ┌──────────────────────┐
  │  Supervisor Agent    │
  │  + Specialist Agents │
  │  + ML Models         │
  │  + Multi-Platform    │
  └──────────────────────┘
```

## 每阶段验证标准

| 阶段 | 验收条件 |
|------|---------|
| Phase 1 | 无安全告警、所有 Bug 修复、`make test` 通过 |
| Phase 2 | 代码重复率下降 50%+、`make lint` 零警告 |
| Phase 3 | 单服务故障不影响整体、P99 延迟可监控 |
| Phase 4 | Agent 能自主完成标准 campaign 创建、支持自然对话 |
| Phase 5 | Meta 真实投放成功、新 tool 可热插拔 |
| Phase 6 | 多 Agent 协作完成跨平台 campaign、ML 模型可在线更新 |
