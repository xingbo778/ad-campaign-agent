# Ad Campaign AI Agent System

A production-ready scaffold for an AI-powered ad campaign orchestration system built with Google ADK/Gemini and MCP-style microservices.

## Architecture Overview

This system uses a **microservices architecture** with an orchestrator agent that coordinates multiple specialized services:

- **Orchestrator Agent**: Built with Google ADK / Gemini, coordinates all services
- **MCP Microservices**: Independent FastAPI services handling specific domains

### Services

| Service | Port | Description | Startup Script |
|---------|------|-------------|----------------|
| **product_service** | 8001 | Selects optimal products for campaigns | `make start-services` or `./scripts/start_services.sh` |
| **creative_service** | 8002 | Generates ad creatives (text, images) | `make start-services` or `./scripts/start_services.sh` |
| **strategy_service** | 8003 | Creates campaign strategies and budget allocation | `make start-services` or `./scripts/start_services.sh` |
| **meta_service** | 8004 | Deploys campaigns to Meta platforms | `make start-services` or `./scripts/start_services.sh` |
| **logs_service** | 8005 | Logs events for auditing and monitoring | `make start-services` or `./scripts/start_services.sh` |
| **optimizer_service** | 8007 | Analyzes performance and suggests optimizations | `make start-services` or `./scripts/start_services.sh` |
| **orchestrator_agent** | 8000 | Coordinates all services (LLM-enhanced) | `make start-orchestrator` or `./scripts/start_orchestrator_llm.sh` |

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

## Current Implementation Status

### ✅ Implemented

- Complete project structure
- All 6 MCP microservices with FastAPI
- 1 Orchestrator service
- Pydantic schemas for type safety
- Mock data generators for all services
- HTTP client utilities
- Configuration management
- Orchestrator agent prompt and configuration
- Client libraries for all services
- Docker support
- Health check endpoints

### 🚧 TODO (Next Steps)

Each service contains `TODO` comments indicating where to add real implementations:

1. **Product Service**:
   - Connect to product database
   - Implement ML-based product selection
   - Add inventory management

2. **Creative Service**:
   - Integrate Gemini API for copywriting
   - Add image generation (DALL-E, Stable Diffusion)
   - Implement A/B testing variants

3. **Strategy Service**:
   - Add ML-based budget optimization
   - Use historical performance data
   - Implement platform-specific strategies

4. **Meta Service**:
   - Integrate Facebook Marketing API
   - Handle authentication and permissions
   - Add campaign status monitoring

5. **Logs Service**:
   - Connect to database (PostgreSQL, MongoDB)
   - Integrate with logging platforms (ELK, Datadog)
   - Add search and filtering

6. **Optimizer Service**:
   - Query analytics database
   - Implement ML-based optimization models
   - Add performance benchmarking

7. **Orchestrator Agent**:
   - Integrate with Google ADK
   - Implement agent runtime
   - Add error handling and retries

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

- **Creative Service** (`http://localhost:8002`)
  - `POST /generate_creatives` - Generate ad creatives

- **Strategy Service** (`http://localhost:8003`)
  - `POST /generate_strategy` - Generate campaign strategy

- **Meta Service** (`http://localhost:8004`)
  - `POST /create_campaign` - Deploy campaign to Meta

- **Logs Service** (`http://localhost:8005`)
  - `POST /append_event` - Log events

- **Optimizer Service** (`http://localhost:8007`)
  - `POST /summarize_recent_runs` - Get optimization suggestions

## Development Guidelines

### Adding New Services

1. Create a new directory under `app/services/`
2. Add `schemas.py` for Pydantic models
3. Add `main.py` with FastAPI app
4. (Optional) Add `mock_data.py` for testing
5. Create a client in `app/orchestrator/clients/`
6. Update `agent_config.yaml` with new tool definitions

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
