#!/bin/bash
# Startup script to run all MCP services locally

echo "Starting Ad Campaign Agent Services..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create logs directory
mkdir -p logs

# Start services in background
echo "Starting Product Service on port 8001..."
python -m app.services.product_service.main > logs/product_service.log 2>&1 &
PRODUCT_PID=$!

echo "Starting Creative Service on port 8002..."
python -m app.services.creative_service.main > logs/creative_service.log 2>&1 &
CREATIVE_PID=$!

echo "Starting Strategy Service on port 8003..."
python -m app.services.strategy_service.main > logs/strategy_service.log 2>&1 &
STRATEGY_PID=$!

echo "Starting Meta Service on port 8004..."
python -m app.services.meta_service.main > logs/meta_service.log 2>&1 &
META_PID=$!

echo "Starting Logs Service on port 8005..."
python -m app.services.logs_service.main > logs/logs_service.log 2>&1 &
LOGS_PID=$!

# Schema Validator Service removed - validation now uses local Pydantic models (app.common.validators)

echo "Starting Optimizer Service on port 8007..."
python -m app.services.optimizer_service.main > logs/optimizer_service.log 2>&1 &
OPTIMIZER_PID=$!

# Save PIDs to file for cleanup
echo $PRODUCT_PID > logs/pids.txt
echo $CREATIVE_PID >> logs/pids.txt
echo $STRATEGY_PID >> logs/pids.txt
echo $META_PID >> logs/pids.txt
echo $LOGS_PID >> logs/pids.txt
echo $OPTIMIZER_PID >> logs/pids.txt

echo ""
echo "All services started!"
echo "PIDs saved to logs/pids.txt"
echo ""
echo "Service URLs:"
echo "  Product Service:    http://localhost:8001"
echo "  Creative Service:   http://localhost:8002"
echo "  Strategy Service:   http://localhost:8003"
echo "  Meta Service:       http://localhost:8004"
echo "  Logs Service:       http://localhost:8005"
echo "  Optimizer Service:  http://localhost:8007"
echo ""
echo "Note: Schema validation now uses local Pydantic models (app.common.validators)"
echo ""
echo "To stop all services, run: ./stop_services.sh"
echo "Logs are available in the logs/ directory"
