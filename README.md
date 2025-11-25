# Ad Campaign AI Agent System

A production-ready scaffold for an AI-powered ad campaign orchestration system built with Google ADK/Gemini and MCP-style microservices.

## Architecture Overview

This system uses a **microservices architecture** with an orchestrator agent that coordinates multiple specialized services:

- **Orchestrator Agent**: Built with Google Gemini, coordinates all services using LLM for intent parsing and natural language understanding
- **MCP Microservices**: Independent FastAPI services handling specific domains with real business logic

### Business Flow

The system follows a **fixed pipeline workflow** for campaign creation:

```
User Request (Natural Language)
        ↓
[Orchestrator: LLM Intent Parsing]
        ↓
CampaignSpec (Structured)
        ↓
┌─────────────────────────────────────┐
│  Fixed Pipeline Execution           │
│  1. Product Service                 │
│     → Select & Score Products       │
│  2. Strategy Service                │
│     → Allocate Budget & Targeting   │
│  3. Creative Service                │
│     → Generate Ad Copy & Images     │
│  4. Meta Service                    │
│     → Deploy Campaign to Meta       │
│  5. Logs Service                    │
│     → Record Events                 │
└─────────────────────────────────────┘
        ↓
[Orchestrator: LLM Summary Generation]
        ↓
Human-Readable Campaign Result
```

### Key Design Principles

1. **LLM for Understanding, Not Execution**: LLM is used only for:
   - Parsing natural language user requests into structured `CampaignSpec`
   - Generating human-readable summaries
   - Explaining errors in user-friendly terms

2. **Deterministic Business Logic**: All business decisions (scoring, budget allocation, targeting) are handled by rule-based services, ensuring:
   - Reproducible results
   - Explainable decisions
   - No LLM hallucinations in critical paths

3. **Service Independence**: Each microservice can operate independently:
   - Own data source (database/CSV)
   - Own business logic
   - Own error handling
   - Can be tested and deployed separately

### Services

| Service | Port | Status | Description | Business Logic |
|---------|------|--------|-------------|----------------|
| **product_service** | 8001 | ✅ **Implemented** | Selects optimal products for campaigns | **Real**: Database/CSV loading, rule-based scoring (category, price, description), priority grouping (high/medium/low) |
| **strategy_service** | 8003 | ✅ **Implemented** | Creates campaign strategies and budget allocation | **Real**: Budget allocation algorithm, Meta audience targeting, bidding strategy selection, adset structure design |
| **creative_service** | 8002 | 🟡 **Partial** | Generates ad creatives (text, images) | **Real**: LLM-powered copy generation (Gemini), image prompt generation, QA validation. **Mock**: Image generation API (fallback) |
| **meta_service** | 8004 | 🚧 **Mock** | Deploys campaigns to Meta platforms | **Mock**: Returns mock campaign IDs. **TODO**: Integrate Facebook Marketing API |
| **logs_service** | 8005 | 🚧 **Mock** | Logs events for auditing and monitoring | **Mock**: In-memory event storage. **TODO**: Database persistence |
| **optimizer_service** | 8007 | 🚧 **Mock** | Analyzes performance and suggests optimizations | **Mock**: Returns mock optimization suggestions. **TODO**: Real analytics integration |
| **orchestrator_agent** | 8000 | ✅ **Implemented** | Coordinates all services (LLM-enhanced) | **Real**: LLM intent parsing, fixed pipeline orchestration, error handling, summary generation |

**Legend:**
- ✅ **Implemented**: Real business logic, no mock data
- 🟡 **Partial**: Core logic implemented, some features still mock
- 🚧 **Mock**: Using mock data, real implementation pending

## Project Structure

```
ad-campaign-agent/
├── app/                        # Application code
│   ├── orchestrator/           # Orchestrator agent
│   │   ├── agent_prompt.md    # Agent system prompt
│   │   ├── agent_config.yaml  # ADK tool definitions
│   │   └── clients/           # HTTP clients for MCP services
│   ├── services/               # MCP microservices
│   │   ├── product_service/
│   │   ├── creative_service/
│   │   ├── strategy_service/
│   │   ├── meta_service/
│   │   ├── logs_service/
│   │   └── optimizer_service/
│   └── common/                 # Shared utilities
│       ├── config.py          # Configuration management
│       ├── http_client.py     # HTTP client (sync & async)
│       ├── schemas.py         # Unified data models
│       └── validators.py      # Local validation utilities
├── docs/                       # Documentation
│   ├── API_DOCUMENTATION.md    # Complete API reference
│   ├── CONFIGURATION.md        # Configuration guide
│   ├── DEPLOYMENT_GUIDE.md     # Deployment instructions
│   ├── DEPLOYMENT_REPORT.md    # Deployment report
│   ├── DOCKER_COMPOSE_GUIDE.md # Docker Compose usage
│   ├── LLM_ORCHESTRATOR.md     # LLM orchestrator guide
│   ├── MAKEFILE_USAGE.md       # Makefile commands
│   ├── OPTIMIZATION_RECOMMENDATIONS.md # Optimization suggestions
│   ├── PROJECT_SUMMARY.md      # Project overview
│   ├── QUICKSTART.md           # Quick start guide
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
├── scripts/                     # Shell scripts (backup to Makefile)
│   ├── start_services.sh
│   ├── stop_services.sh
│   ├── start_orchestrator.sh
│   ├── start_orchestrator_llm.sh
│   └── stop_orchestrator.sh
├── tests/                       # Test suite
├── examples/                    # Example usage
├── logs/                        # Service logs
├── Makefile                     # Unified command management
├── pyproject.toml              # Poetry configuration
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn/Gunicorn** - ASGI server
- **Pydantic** - Data validation using Python type annotations
- **google-generativeai** - Google Gemini API client
- **httpx** - Async HTTP client
- **Docker** - Containerization (optional)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip
- (Optional) Docker and Docker Compose
- (Optional) Google Gemini API Key (for LLM-enhanced orchestrator)

### Installation

1. **Clone the repository**:
   ```bash
   cd ad-campaign-agent
   ```

2. **Create a virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   ```bash
   # Create .env file for production deployment or LLM features
   # For local development, defaults are used (localhost)
   # See CONFIGURATION.md for details
   ```

## Quick Start - Complete System

### Startup Flow Overview

```
┌─────────────────────────────────────────────────────────┐
│  Step 1: Start 6 MCP Services (Ports 8001-8005, 8007)  │
│  make start-services                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 2: Start Orchestrator Agent (Port 8000)           │
│  Choose one:                                            │
│  • make start-orchestrator (Simple Mode)                │
│  • make start-orchestrator (LLM Mode)                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Step 3: Verify & Test                                   │
│  curl http://localhost:8000/health                      │
│  python example_usage.py                                │
└─────────────────────────────────────────────────────────┘
```

### Step 1: Start All MCP Services

Start all 6 microservices using the startup script:

```bash
make start-services
```

This will start all 6 microservices in the background:
- Product Service (port 8001)
- Creative Service (port 8002)
- Strategy Service (port 8003)
- Meta Service (port 8004)
- Logs Service (port 8005)
- Optimizer Service (port 8007)

**Verify services are running:**
```bash
# Check all services
make health-check

# Or manually
for port in 8001 8002 8003 8004 8005 8007; do
  echo "Port $port: $(curl -s http://localhost:$port/health | grep -o '"service":"[^"]*"')"
done
```

### Step 2: Start Orchestrator Agent

Choose one of two modes:

#### Option A: Simple Mode (Recommended for beginners)

```bash
make start-orchestrator
```

- Uses structured API calls
- No LLM required
- Fast and reliable

#### Option B: LLM-Enhanced Mode (Natural Language Processing)

```bash
make start-orchestrator
```

- Accepts natural language input
- Intelligent error handling
- Human-readable summaries
- Requires `GEMINI_API_KEY` (optional, will warn if not set)

**Verify orchestrator is running:**
```bash
curl http://localhost:8000/health
```

### Step 3: Test the System

```bash
# Test with example workflow
python example_usage.py

# Or test with demo workflow
python demo_workflow.py
```

### Complete Startup Sequence

```bash
# 1. Start all MCP services
make start-services

# 2. Wait a few seconds for services to initialize
sleep 3

# 3. Start orchestrator (choose one)
make start-orchestrator          # Simple mode
# OR
make start-orchestrator      # LLM mode

# 4. Verify everything is running
curl http://localhost:8000/health
curl http://localhost:8000/services/status
```

### Stopping Services

```bash
# Stop orchestrator
make stop-orchestrator

# Stop all MCP services
make stop-services
```

## Alternative Startup Methods

### Manual Startup (for debugging)

Start each service in a separate terminal:

```bash
# Terminal 1-6: Start MCP services
python -m app.services.product_service.main      # Port 8001
python -m app.services.creative_service.main    # Port 8002
python -m app.services.strategy_service.main    # Port 8003
python -m app.services.meta_service.main        # Port 8004
python -m app.services.logs_service.main        # Port 8005
python -m app.services.optimizer_service.main   # Port 8007

# Terminal 8: Start orchestrator
python -m app.orchestrator.simple_service       # Port 8000 (Simple)
# OR
python -m app.orchestrator.llm_service          # Port 8000 (LLM)
```

### Docker Compose

```bash
docker-compose up --build
```

This will start all services in containers.

## Service Status & Health Checks

### Check Individual Services

Each service exposes a health check endpoint:

```bash
# MCP Services
curl http://localhost:8001/health  # Product Service
curl http://localhost:8002/health  # Creative Service
curl http://localhost:8003/health  # Strategy Service
curl http://localhost:8004/health  # Meta Service
curl http://localhost:8005/health  # Logs Service
curl http://localhost:8007/health  # Optimizer Service

# Orchestrator Agent
curl http://localhost:8000/health
```

### Check All Services Status

```bash
# Via orchestrator (if running)
curl http://localhost:8000/services/status | python -m json.tool

# Or manually check all
for port in 8001 8002 8003 8004 8005 8007 8000; do
  service=$(curl -s http://localhost:$port/health 2>/dev/null | grep -o '"service":"[^"]*"' | cut -d'"' -f4 || echo "not running")
  printf "Port %d: %s\n" $port "$service"
done
```

### Using the Orchestrator Clients

Example usage of the client libraries:

```python
from app.orchestrator.clients import ProductClient, CreativeClient

# Select products
product_client = ProductClient()
products = product_client.select_products(
    campaign_objective="increase sales",
    target_audience="tech enthusiasts",
    budget=10000.0
)
print(products)

# Generate creatives
creative_client = CreativeClient()
creatives = creative_client.generate_creatives(
    product_ids=["PROD-001", "PROD-002"],
    campaign_objective="increase sales",
    target_audience="tech enthusiasts"
)
print(creatives)
```

## Business Logic & Implementation Details

### Product Service (✅ Fully Implemented)

**Business Logic:**
1. **Data Loading**: Supports PostgreSQL (preferred) or CSV fallback
   - Automatically detects `DATABASE_URL` environment variable
   - Falls back to CSV file if database unavailable
   - Provides default sample products if no data source

2. **Product Scoring Algorithm** (Rule-based, deterministic):
   - **Category Alignment** (0-0.4 points):
     - Exact match: +0.4
     - Similar category: +0.2-0.3
     - No match: 0
   - **Price Fit** (0-0.3 points):
     - Low budget campaigns: Prefer cheaper products (< budget/40)
     - High budget campaigns: Prefer mid-range products (budget/40 to budget/20)
     - Very expensive products (> budget/10) get lower scores
   - **Description Quality** (0-0.2 points):
     - Length score: Longer descriptions score better (capped at 300 chars)
     - Keyword match: Matches with campaign category/objective boost score
   - **Metadata Features** (0-0.1 points):
     - Popularity indicators
     - Brand alignment
     - Feature richness
   - **Final Score**: Sum of all factors, clipped to [0, 1]

3. **Product Grouping**:
   - **High Priority**: score ≥ 0.75
   - **Medium Priority**: 0.45 ≤ score < 0.75
   - **Low Priority**: score < 0.45

4. **Selection Process**:
   - Filter by category (if specified)
   - Score all products
   - Sort by score (descending)
   - Select top N products
   - Group by priority

**API Endpoints:**
- `POST /select_products`: Accepts `CampaignSpec` + `limit`, returns scored and grouped products with debug info

### Strategy Service (✅ Fully Implemented)

**Business Logic:**
1. **Budget Allocation Algorithm**:
   - Allocates budget across product groups based on priority:
     - High priority: 60-70% of budget
     - Medium priority: 20-30% of budget
     - Low priority: 0-20% of budget
   - Distributes budget among creatives within each group
   - Supports variant-level budget split (A/B testing)

2. **Audience Targeting** (Meta Platform):
   - Derives targeting from `CampaignSpec.category`, `Product.metadata`, and `CampaignSpec.metadata`
   - Age range: Based on product category and campaign metadata
   - Interests: Extracted from product category and description
   - Locations: From campaign metadata or defaults

3. **Bidding Strategy Selection**:
   - `LOWEST_COST_WITH_CAP`: For large budgets and conversion objectives
   - `LOWEST_COST`: For traffic/awareness objectives
   - `TARGET_COST`: For specific CPA targets (if provided)

4. **Adset Structure Design**:
   - Small budgets (< $1000): Single adset
   - Large budgets: Multiple adsets per product group
   - Daily budget calculation: Total budget / duration days / number of adsets

5. **Reach & Conversion Estimation**:
   - Basic estimates based on budget, targeting, and historical benchmarks
   - Provides expected reach and conversion counts

**API Endpoints:**
- `POST /generate_strategy`: Accepts `CampaignSpec` + `ProductGroup[]` + `Creative[]`, returns `AbstractStrategy` and `PlatformStrategy[]`

### Creative Service (🟡 Partially Implemented)

**Business Logic:**
1. **Copy Generation** (✅ Real):
   - Uses Google Gemini API to generate ad copy
   - Creates primary text and headline
   - Supports A/B variants (at least 2 per product)
   - Uses category-based style policies

2. **Image Prompt Generation** (✅ Real):
   - Generates image prompts using Gemini
   - Platform-specific visual styles
   - Variant-specific prompts

3. **QA Validation** (✅ Real):
   - Text length validation (primary_text ≤ 200, headline ≤ 60)
   - Banned words filtering
   - Platform-specific rules (Meta disallows superlatives, second-person targeting)
   - Image URL validation

4. **Image Generation** (🚧 Fallback):
   - Currently uses placeholder URLs
   - TODO: Integrate Gemini Image API or other image generation service

**API Endpoints:**
- `POST /generate_creatives`: Accepts `CampaignSpec` + `Product[]`, returns `Creative[]` with A/B variants

### Orchestrator Agent (✅ Fully Implemented)

**Business Logic:**
1. **Intent Parsing** (LLM):
   - Accepts natural language user requests
   - Extracts: objective, budget, target audience, category, platform, duration
   - Outputs structured `CampaignSpec`

2. **Fixed Pipeline Execution**:
   - Calls services in strict order:
     1. Product Service → Get products
     2. Strategy Service → Generate strategy
     3. Creative Service → Generate creatives
     4. Meta Service → Deploy campaign
     5. Logs Service → Record events
   - No LLM decision-making in pipeline (deterministic)

3. **Error Handling**:
   - Catches service errors
   - Uses LLM to explain errors in user-friendly terms
   - Provides actionable error messages

4. **Summary Generation** (LLM):
   - Converts technical results to human-readable summary
   - Explains what was done and why

**API Endpoints:**
- `POST /create_campaign_nl`: Natural language input → Full campaign creation
- `POST /create_campaign`: Structured `CampaignSpec` input → Full campaign creation

## Current Implementation Status

### ✅ Fully Implemented Services

1. **Product Service**:
   - ✅ Database/CSV data loading
   - ✅ Rule-based product scoring
   - ✅ Priority-based grouping
   - ✅ Category filtering
   - ✅ Comprehensive test suite (32 tests)

2. **Strategy Service**:
   - ✅ Budget allocation algorithm
   - ✅ Meta audience targeting
   - ✅ Bidding strategy selection
   - ✅ Adset structure design
   - ✅ Comprehensive test suite (27 tests)

3. **Creative Service**:
   - ✅ LLM-powered copy generation (Gemini)
   - ✅ Image prompt generation
   - ✅ QA validation module
   - ✅ A/B variant generation
   - ✅ Fallback mechanisms

4. **Orchestrator Agent**:
   - ✅ LLM intent parsing
   - ✅ Fixed pipeline orchestration
   - ✅ Error handling and explanation
   - ✅ Summary generation

### 🟡 Partially Implemented Services

1. **Creative Service**:
   - 🚧 Image generation API integration (currently uses fallback URLs)

### 🚧 Mock Services (TODO)

1. **Meta Service**:
   - 🚧 Integrate Facebook Marketing API
   - 🚧 Handle authentication and permissions
   - 🚧 Add campaign status monitoring

2. **Logs Service**:
   - 🚧 Connect to database (PostgreSQL, MongoDB)
   - 🚧 Integrate with logging platforms (ELK, Datadog)
   - 🚧 Add search and filtering

3. **Optimizer Service**:
   - 🚧 Query analytics database
   - 🚧 Implement ML-based optimization models
   - 🚧 Add performance benchmarking

## API Documentation

### Interactive API Docs

Each service provides interactive Swagger/OpenAPI documentation:

- **Orchestrator Agent**: http://localhost:8000/docs
- **Product Service**: http://localhost:8001/docs
- **Creative Service**: http://localhost:8002/docs
- **Strategy Service**: http://localhost:8003/docs
- **Meta Service**: http://localhost:8004/docs
- **Logs Service**: http://localhost:8005/docs
- **Optimizer Service**: http://localhost:8007/docs

### Complete API Reference

For detailed API documentation, see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

**Key Endpoints:**

- **Orchestrator** (`http://localhost:8000`)
  - `POST /create_campaign_nl` - Create campaign from natural language
  - `POST /create_campaign` - Create campaign with structured input
  - `GET /services/status` - Check all service statuses
  - `GET /health` - Health check

- **Product Service** (`http://localhost:8001`)
  - `POST /select_products` - Select products for campaign
    - **Input**: `CampaignSpec` + `limit` (or legacy format)
    - **Output**: Scored products grouped by priority (high/medium/low) with debug info
    - **Business Logic**: Rule-based scoring, category filtering, top-N selection

- **Strategy Service** (`http://localhost:8003`)
  - `POST /generate_strategy` - Generate campaign strategy
    - **Input**: `CampaignSpec` + `ProductGroup[]` + `Creative[]` (or legacy format)
    - **Output**: `AbstractStrategy` (budget allocation) + `PlatformStrategy[]` (platform-specific configs)
    - **Business Logic**: Budget allocation, audience targeting, bidding strategy, adset structure

- **Creative Service** (`http://localhost:8002`)
  - `POST /generate_creatives` - Generate ad creatives
    - **Input**: `CampaignSpec` + `Product[]`
    - **Output**: `Creative[]` with A/B variants (at least 2 per product)
    - **Business Logic**: LLM copy generation, image prompt generation, QA validation

- **Meta Service** (`http://localhost:8004`)
  - `POST /create_campaign` - Deploy campaign to Meta
    - **Input**: Campaign name, objective, budget, targeting, creatives
    - **Output**: Campaign ID, Ad Set ID, Ad IDs
    - **Status**: 🚧 Mock implementation (returns mock IDs)

- **Logs Service** (`http://localhost:8005`)
  - `POST /append_event` - Log events
    - **Input**: Event type, message, metadata
    - **Output**: Event ID
    - **Status**: 🚧 Mock implementation (in-memory storage)

- **Optimizer Service** (`http://localhost:8007`)
  - `POST /summarize_recent_runs` - Get optimization suggestions
    - **Input**: Campaign IDs, time range
    - **Output**: Summary, suggestions, metrics
    - **Status**: 🚧 Mock implementation (returns mock suggestions)

## Data Flow & Service Interactions

### Complete Campaign Creation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Request (Natural Language)                         │
│    "Create a $5000 campaign for electronics targeting      │
│     tech enthusiasts aged 25-45"                           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Orchestrator: LLM Intent Parsing                        │
│    Input: Natural language string                          │
│    Output: CampaignSpec {                                  │
│      user_query: "...",                                     │
│      platform: "meta",                                      │
│      budget: 5000.0,                                       │
│      objective: "conversions",                             │
│      category: "electronics",                              │
│      time_range: {...},                                     │
│      metadata: {...}                                        │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Product Service: Product Selection                       │
│    Input: CampaignSpec { category: "electronics", ... }    │
│    Process:                                                  │
│      - Load products from DB/CSV (filter by category)      │
│      - Score each product (category, price, description)    │
│      - Sort by score                                        │
│      - Select top N products                               │
│      - Group into high/medium/low priority                 │
│    Output: ProductGroup[] with scored products            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Strategy Service: Strategy Generation                    │
│    Input: CampaignSpec + ProductGroup[] + Creative[]        │
│    Process:                                                  │
│      - Allocate budget across groups (high: 60-70%, etc.)   │
│      - Build Meta targeting (age, interests, locations)     │
│      - Choose bidding strategy (LOWEST_COST_WITH_CAP, etc.)│
│      - Design adset structure (single vs multi-adset)     │
│      - Estimate reach and conversions                     │
│    Output: AbstractStrategy + PlatformStrategy[]           │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Creative Service: Creative Generation                   │
│    Input: CampaignSpec + Product[]                         │
│    Process:                                                  │
│      - For each product, generate 2+ variants (A, B)       │
│      - Use Gemini to generate copy (headline + text)       │
│      - Generate image prompts                              │
│      - Run QA validation (length, banned words, etc.)      │
│      - Apply fallback if QA fails                          │
│    Output: Creative[] with A/B variants                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Meta Service: Campaign Deployment                       │
│    Input: Campaign name, objective, budget, targeting,       │
│           creatives                                         │
│    Process:                                                  │
│      - Create Meta campaign                                 │
│      - Create ad sets with targeting                        │
│      - Create ads with creatives                           │
│    Output: Campaign ID, Ad Set ID, Ad IDs                 │
│    Status: 🚧 Currently returns mock IDs                   │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Logs Service: Event Logging                             │
│    Input: Event type, message, metadata                     │
│    Process:                                                  │
│      - Store event with timestamp                          │
│      - Generate event ID                                   │
│    Output: Event ID                                         │
│    Status: 🚧 Currently in-memory storage                 │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Orchestrator: LLM Summary Generation                     │
│    Input: All service results                               │
│    Process:                                                  │
│      - Use LLM to generate human-readable summary         │
│      - Explain what was done and why                        │
│    Output: Natural language summary                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. Final Response to User                                   │
│    {                                                         │
│      status: "success",                                     │
│      campaigns: [{                                          │
│        campaign_id: "CAMP-123",                            │
│        products: [...],                                    │
│        creatives: [...],                                   │
│        strategy: {...}                                     │
│      }],                                                    │
│      summary: "Successfully created campaign..."            │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
```

### Service Data Contracts

All services use shared schemas from `app/common/schemas.py`:

- **CampaignSpec**: Campaign requirements (platform, budget, objective, category, etc.)
- **Product**: Product information (ID, title, description, price, category, metadata)
- **ProductGroup**: Grouped products with priority (high/medium/low) and score ranges
- **Creative**: Ad creative (product_id, platform, variant_id, primary_text, headline, image_url)
- **AbstractStrategy**: High-level strategy (objective, budget_split, bidding_strategy)
- **PlatformStrategy**: Platform-specific strategy (targeting, adset structure, optimization_goal)
- **ErrorResponse**: Standardized error format (status, error_code, message, details)

## Development Guidelines

### Adding New Services

1. Create a new directory under `app/services/`
2. Add `schemas.py` for Pydantic models (import from `app.common.schemas` for shared models)
3. Add `main.py` with FastAPI app
4. Implement real business logic (avoid mock data for production)
5. Add comprehensive tests in `tests/services/<service_name>/`
6. Create a client in `app/orchestrator/clients/`
7. Update orchestrator pipeline to include new service

### Code Style

- Use **type hints** for all function parameters and return values
- Add **docstrings** to all classes and functions
- Follow **PEP 8** style guidelines
- Use **Pydantic models** for request/response validation

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app tests/
```

## Configuration

### Environment Variables

The system supports two deployment modes:

#### Local Development (Default)
- Uses `localhost` URLs automatically
- No configuration needed
- All services run on localhost:8001-8007

#### Production Deployment
Set environment variables to override defaults:

```bash
# Service URLs (for production)
export PRODUCT_SERVICE_URL=https://product-service.yourdomain.com
export CREATIVE_SERVICE_URL=https://creative-service.yourdomain.com
export STRATEGY_SERVICE_URL=https://strategy-service.yourdomain.com
export META_SERVICE_URL=https://meta-service.yourdomain.com
export LOGS_SERVICE_URL=https://logs-service.yourdomain.com
export OPTIMIZER_SERVICE_URL=https://optimizer-service.yourdomain.com

# LLM Configuration (optional, for LLM mode)
export GEMINI_API_KEY=your_gemini_api_key_here
export GEMINI_MODEL=gemini-2.0-flash-exp
```

**See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed configuration guide.**

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCT_SERVICE_URL` | `http://localhost:8001` | Product service URL |
| `CREATIVE_SERVICE_URL` | `http://localhost:8002` | Creative service URL |
| `STRATEGY_SERVICE_URL` | `http://localhost:8003` | Strategy service URL |
| `META_SERVICE_URL` | `http://localhost:8004` | Meta service URL |
| `LOGS_SERVICE_URL` | `http://localhost:8005` | Logs service URL |
| `OPTIMIZER_SERVICE_URL` | `http://localhost:8007` | Optimizer service URL |
| `GEMINI_API_KEY` | `None` | Google Gemini API key (for LLM mode) |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` | Gemini model name |
| `ENVIRONMENT` | `development` | Environment identifier |

## Deployment

### Production Considerations

- Use **Gunicorn** with multiple workers for production
- Set up **reverse proxy** (nginx) for load balancing
- Implement **authentication and authorization**
- Add **rate limiting** and **request throttling**
- Set up **monitoring and alerting** (Prometheus, Grafana)
- Use **secrets management** (AWS Secrets Manager, HashiCorp Vault)
- Implement **circuit breakers** for service resilience

## License

This is a scaffold/template project. Add your own license as needed.

## Contributing

This is a starting scaffold. Customize it for your specific needs:

1. Replace mock data with real implementations
2. Add authentication and security
3. Implement error handling and retries
4. Add comprehensive testing
5. Set up CI/CD pipelines
6. Add monitoring and observability

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process on a port
lsof -ti:8000 | xargs kill

# Or use the stop scripts
make stop-orchestrator
make stop-services
```

### Services Not Responding

```bash
# Check logs
tail -f logs/*.log

# Check specific service log
tail -f logs/product_service.log
tail -f logs/orchestrator.log
tail -f logs/orchestrator_llm.log
```

### Import Errors

Make sure you're in the project root and have activated the virtual environment:

```bash
cd ad-campaign-agent
source venv/bin/activate
```

### LLM Mode Not Working

If using LLM mode, ensure `GEMINI_API_KEY` is set:

```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Set it in .env file
echo "GEMINI_API_KEY=your_key_here" >> .env
```

## Common Commands Reference

```bash
# Start all services
make start-services              # Start 6 MCP services
make start-orchestrator          # Start orchestrator (simple mode)
make start-orchestrator     # Start orchestrator (LLM mode)

# Stop services
make stop-services               # Stop all MCP services
make stop-orchestrator           # Stop orchestrator

# Check status
curl http://localhost:8000/health
curl http://localhost:8000/services/status

# View logs
tail -f logs/*.log
tail -f logs/orchestrator.log
tail -f logs/orchestrator_llm.log

# Run examples
python example_usage.py
python demo_workflow.py

# Test services
python test_all_services.py
```

## Additional Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute quick start guide
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Detailed configuration guide
- **[LLM_ORCHESTRATOR.md](LLM_ORCHESTRATOR.md)** - LLM orchestrator documentation

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs in `logs/` directory
3. Refer to TODO comments in the code for implementation guidance
4. Check the [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for environment setup
