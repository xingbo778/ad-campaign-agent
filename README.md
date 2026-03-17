# Ad Campaign AI Agent System

A production-ready scaffold for an ad-campaign AI agent system using Google ADK / Gemini 3 Pro as the orchestrator and multiple MCP-style microservices implemented as FastAPI apps.

Supports **dual-channel campaigns**: traditional human channels (Meta/Facebook/Instagram) and the **Agent Marketing Platform (AMP)** for reaching AI agents.

## Architecture

- **Orchestrator Agent**: Built with Google ADK / Gemini 3 Pro, coordinates all MCP services
- **MCP Microservices**: FastAPI-based services for different campaign functions
  - `product_service`: Product selection and grouping
  - `creative_service`: Ad creative generation (human + agent creatives)
  - `strategy_service`: Campaign strategy development (dual-channel: human + agent)
  - `meta_service`: Meta platform campaign creation (human channel)
  - `amp_service`: Agent Marketing Platform publishing (agent channel)
  - `logs_service`: Event logging and audit trails
  - `schema_validator_service`: Data validation
  - `optimizer_service`: Campaign optimization analysis (human + agent metrics)

### Dual-Channel Concept

```
                    creative_service
                    ├── /generate_creatives        → Human creatives (text/image/video)
                    └── /generate_agent_creatives   → Agent creatives (structured schemas)
                              │
                    strategy_service (include_agent_channel=true)
                    ├── Human channels: 75% budget  → Facebook/Instagram/Meta
                    └── Agent channel: 25% budget   → AMP marketplace
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
        meta_service                   amp_service
        (Meta Ads)                     (AMP marketplace)
               │                             │
               ▼                             ▼
          Human users                   AI Agents → Users
```

## Project Structure

```
ad-campaign-agent/
├── app/
│   ├── common/
│   │   ├── config.py          # Configuration management
│   │   └── http_client.py     # HTTP client utilities
│   ├── orchestrator/
│   │   ├── agent_prompt.md    # Orchestrator agent prompt
│   │   ├── agent_config.yaml  # ADK agent configuration (9 tools)
│   │   └── clients/           # MCP service clients
│   └── services/
│       ├── product_service/
│       ├── creative_service/   # Extended: +agent creative generation
│       ├── strategy_service/   # Extended: +agent channel strategy
│       ├── meta_service/
│       ├── amp_service/        # NEW: Agent Marketing Platform
│       ├── logs_service/
│       ├── schema_validator_service/
│       └── optimizer_service/  # Extended: +agent channel metrics
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

## Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd ad-campaign-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Running Services

### Option 1: Docker Compose (Recommended)

Start all services:
```bash
docker-compose up -d
```

Stop all services:
```bash
docker-compose down
```

### Option 2: Individual Services

Run each service individually:

```bash
# Product Service
uvicorn app.services.product_service.main:app --host 0.0.0.0 --port 8001

# Creative Service
uvicorn app.services.creative_service.main:app --host 0.0.0.0 --port 8002

# Strategy Service
uvicorn app.services.strategy_service.main:app --host 0.0.0.0 --port 8003

# Meta Service
uvicorn app.services.meta_service.main:app --host 0.0.0.0 --port 8004

# Logs Service
uvicorn app.services.logs_service.main:app --host 0.0.0.0 --port 8005

# Schema Validator Service
uvicorn app.services.schema_validator_service.main:app --host 0.0.0.0 --port 8006

# Optimizer Service
uvicorn app.services.optimizer_service.main:app --host 0.0.0.0 --port 8007

# AMP Service (Agent Marketing Platform)
uvicorn app.services.amp_service.main:app --host 0.0.0.0 --port 8008
```

## Service Endpoints

All services expose:
- Main endpoint: `POST /{service_endpoint}`
- Health check: `GET /health`
- API docs: `GET /docs` (FastAPI auto-generated)

### Example API Calls

**Product Service:**
```bash
curl -X POST http://localhost:8001/select_products \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_objective": "conversions",
    "target_audience": {
      "demographics": {"age": [25, 45]},
      "interests": ["technology", "gadgets"]
    }
  }'
```

**Creative Service (Human):**
```bash
curl -X POST http://localhost:8002/generate_creatives \
  -H "Content-Type: application/json" \
  -d '{
    "products": [{"product_id": "prod_001", "name": "Widget", "category": "Electronics", "price": 99.99}],
    "campaign_objective": "awareness",
    "platform": "facebook"
  }'
```

**Creative Service (Agent):**
```bash
curl -X POST http://localhost:8002/generate_agent_creatives \
  -H "Content-Type: application/json" \
  -d '{
    "products": [{"product_id": "prod_001", "name": "Widget", "category": "Electronics", "price": 99.99}],
    "campaign_objective": "conversions",
    "target_agent_categories": ["shopping_assistant", "price_comparison"]
  }'
```

**AMP Service:**
```bash
curl -X POST http://localhost:8008/publish_to_amp \
  -H "Content-Type: application/json" \
  -d '{
    "agent_creatives": [{"creative_id": "ac_1", "product_id": "prod_001", "product_schema": {"name": "Widget", "category": "Electronics", "price": {"amount": 99.99, "currency": "USD"}}, "tags": ["electronics"]}],
    "budget": 2500.0,
    "bidding_strategy": "cost_per_recommendation"
  }'
```

## Current Status

⚠️ **All services currently return MOCK data.** 

Each service includes TODO comments indicating where real implementations should be added:
- Database connections
- External API integrations
- ML model inference
- Business logic

## Next Steps

1. **Replace Mock Implementations**:
   - Add database connections (PostgreSQL, MongoDB, etc.)
   - Integrate with Meta Marketing API
   - Add Gemini API calls for creative generation
   - Implement real validation logic
   - **Build AMP marketplace API integration**
   - **Implement real product schema generation from raw product data**
   - **Integrate third-party verification APIs (Vanta, UptimeRobot, G2)**

2. **Orchestrator Integration**:
   - Configure Google ADK with `agent_config.yaml`
   - Wire up orchestrator to use MCP clients
   - Test end-to-end dual-channel campaign creation flow

3. **AMP Channel Development**:
   - Build real AMP marketplace backend
   - Implement product schema validation against AMP standards
   - Build sandbox API provisioning system
   - Implement agent bidding engine (CPR/CPQ/CPA)
   - Build agent query and recommendation tracking

4. **Production Readiness**:
   - Add authentication/authorization
   - Implement rate limiting
   - Add monitoring and observability
   - Set up CI/CD pipelines

## Development

### Code Structure

Each service follows the same pattern:
- `main.py`: FastAPI application with endpoints
- `schemas.py`: Pydantic models for request/response
- `mock_data.py`: Mock data generators

### Adding New Services

1. Create service directory under `app/services/`
2. Add `main.py`, `schemas.py`, `mock_data.py`
3. Add service client in `app/orchestrator/clients/`
4. Update `docker-compose.yml` and `.env.example`
5. Add service URL to `app/common/config.py`

## License

[Add your license here]




