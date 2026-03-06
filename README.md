# Ad Campaign AI Agent System

A production-ready AI-powered ad campaign orchestration system built with FastAPI microservices, Google Gemini/OpenAI for intelligent intent parsing, and a deterministic pipeline for reliable campaign creation and deployment to Meta platforms.

## Architecture Overview

The system uses a **microservices architecture** with an orchestrator agent that coordinates specialized services via a fixed pipeline:

```
User Request (Natural Language)
        |
[Orchestrator: LLM Intent Parsing]
        |
    CampaignSpec (Structured)
        |
  Fixed Pipeline Execution
  1. Product Service   -> Select & Score Products
  2. Creative Service  -> Generate Ad Copy & Images
  3. Strategy Service  -> Allocate Budget & Targeting
  4. Meta Service      -> Deploy Campaign to Meta
  5. Logs Service      -> Record Events
        |
[Orchestrator: LLM Summary Generation]
        |
Human-Readable Campaign Result
```

### Design Principles

- **LLM for Understanding, Not Execution**: LLM handles intent parsing and summary generation only; all business decisions use deterministic rule-based logic
- **Deterministic Business Logic**: Scoring, budget allocation, and targeting are rule-based for reproducible, explainable results with no hallucinations in critical paths
- **Service Independence**: Each microservice has its own data source, business logic, error handling, and can be tested/deployed separately

### Services

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| **orchestrator_agent** | 8000 | Implemented | LLM intent parsing, pipeline orchestration, summary generation |
| **product_service** | 8001 | Implemented | Database/CSV product loading, rule-based scoring, priority grouping |
| **creative_service** | 8002 | Implemented | LLM copy generation (OpenAI/Gemini), DALL-E 3 image generation, Replicate video generation, QA validation |
| **strategy_service** | 8003 | Implemented | Budget allocation, Meta audience targeting, bidding strategy, adset structure |
| **meta_service** | 8004 | Mock | Campaign deployment to Meta (TODO: Facebook Marketing API) |
| **logs_service** | 8005 | Mock | Event logging (TODO: database persistence) |
| **optimizer_service** | 8007 | Mock | Performance optimization (TODO: analytics integration) |

## Tech Stack

- **Python 3.11+** / **FastAPI** / **Uvicorn**
- **Pydantic** - Data validation and settings management
- **google-generativeai** - Google Gemini API (orchestrator + creative fallback)
- **OpenAI** - Text generation (GPT-4.1-mini) and image generation (DALL-E 3)
- **Replicate** - Video generation (Wan 2.5)
- **httpx** - Async HTTP client for service communication
- **Docker** - Containerization (optional)

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) Docker and Docker Compose
- (Optional) API keys: `OPENAI_REAL_KEY`, `GEMINI_API_KEY`, `REPLICATE_API_TOKEN`

### Installation

```bash
cd ad-campaign-agent
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Quick Start

```bash
# 1. Start all microservices (ports 8001-8005, 8007)
make start-services

# 2. Wait for services to initialize
sleep 3

# 3. Start orchestrator (port 8000, LLM mode)
make start-orchestrator

# 4. Verify
curl http://localhost:8000/health
curl http://localhost:8000/services/status

# 5. Run example workflow
python example_usage.py
```

To start the **simple mode** orchestrator (no LLM required, structured API only):

```bash
python -m app.orchestrator.simple_service
```

### Stopping Services

```bash
make stop-orchestrator
make stop-services
```

### Alternative: Manual Startup

Start each service in a separate terminal for debugging:

```bash
python -m app.services.product_service.main      # Port 8001
python -m app.services.creative_service.main      # Port 8002
python -m app.services.strategy_service.main      # Port 8003
python -m app.services.meta_service.main          # Port 8004
python -m app.services.logs_service.main          # Port 8005
python -m app.services.optimizer_service.main     # Port 8007
python -m app.orchestrator.llm_service            # Port 8000
```

### Alternative: Docker Compose

```bash
docker-compose up --build
```

## API Overview

Each service provides interactive Swagger docs at `http://localhost:<port>/docs`.

**Key Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/create_campaign_nl` (8000) | POST | Create campaign from natural language |
| `/create_campaign` (8000) | POST | Create campaign with structured input |
| `/services/status` (8000) | GET | Check all service statuses |
| `/select_products` (8001) | POST | Select and score products for campaign |
| `/generate_creatives` (8002) | POST | Generate ad creatives with A/B variants |
| `/generate_strategy` (8003) | POST | Generate campaign strategy and budget allocation |
| `/create_campaign` (8004) | POST | Deploy campaign to Meta (mock) |
| `/append_event` (8005) | POST | Log events |
| `/summarize_recent_runs` (8007) | POST | Get optimization suggestions (mock) |

For complete API reference, see [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

## Configuration

### Environment Variables

The system works out of the box for local development with default `localhost` URLs. For production or LLM features, set these variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_REAL_KEY` | `None` | OpenAI API key (text + image generation) |
| `OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI model |
| `GEMINI_API_KEY` | `None` | Google Gemini API key (fallback) |
| `GEMINI_MODEL` | `gemini-2.0-flash-lite` | Gemini text model |
| `REPLICATE_API_TOKEN` | `None` | Replicate token (video generation) |
| `DATABASE_URL` | `None` | PostgreSQL connection (product service) |
| `ENVIRONMENT` | `development` | Environment identifier |
| `LOG_LEVEL` | `INFO` | Logging level |

Service URLs (`PRODUCT_SERVICE_URL`, `CREATIVE_SERVICE_URL`, etc.) default to `http://localhost:<port>` and only need to be set for production deployments.

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full configuration guide.

## Development

### Testing

```bash
make test              # Run all tests
make test-parallel     # Run tests in parallel (faster)
make test-fast         # Skip slow tests
make test-coverage     # Generate coverage report
```

### Code Quality

```bash
make lint              # Run flake8 + mypy
make format            # Format with black
make format-check      # Check formatting
```

### Adding New Services

1. Create directory under `app/services/`
2. Implement FastAPI app in `main.py` using shared models from `app.common.schemas`
3. Add tests in `tests/services/<service_name>/`
4. Create HTTP client in `app/orchestrator/clients/`
5. Update orchestrator pipeline

### Useful Commands

```bash
make help              # Show all available commands
make health-check      # Check all service health
make logs              # Tail all service logs
make restart-all       # Restart everything
make clean             # Clean cache files
```

## Project Structure

```
ad-campaign-agent/
├── app/
│   ├── orchestrator/           # Orchestrator agent (port 8000)
│   │   ├── llm_service.py      # LLM-enhanced orchestrator
│   │   ├── simple_service.py   # Simple structured API orchestrator
│   │   └── clients/            # HTTP clients for each service
│   ├── services/               # Microservices
│   │   ├── product_service/    # Product selection & scoring
│   │   ├── creative_service/   # Ad creative generation
│   │   ├── strategy_service/   # Campaign strategy & budgeting
│   │   ├── meta_service/       # Meta platform deployment (mock)
│   │   ├── logs_service/       # Event logging (mock)
│   │   └── optimizer_service/  # Performance optimization (mock)
│   └── common/                 # Shared config, schemas, utilities
├── tests/                      # Test suite
├── docs/                       # Documentation
├── scripts/                    # Startup and utility scripts
├── reports/                    # Analysis reports
├── Makefile                    # Command management
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── pyproject.toml              # Project configuration
└── requirements.txt            # Python dependencies
```

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [LLM Orchestrator Guide](docs/LLM_ORCHESTRATOR.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Docker Compose Guide](docs/DOCKER_COMPOSE_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Troubleshooting

```bash
# Port already in use
lsof -ti:8000 | xargs kill

# Check service logs
tail -f logs/*.log

# Import errors - ensure venv is active
source venv/bin/activate

# LLM mode issues - verify API keys
echo $OPENAI_REAL_KEY
echo $GEMINI_API_KEY
python scripts/check_gemini.py
```

For more, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## License

This is a scaffold/template project. Add your own license as needed.
