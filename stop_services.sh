#!/bin/bash
# Script to stop all running MCP services

echo "Stopping Ad Campaign Agent Services..."

if [ -f "logs/pids.txt" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid..."
            kill $pid
        fi
    done < logs/pids.txt
    
    rm logs/pids.txt
    echo "All services stopped."
else
    echo "No PID file found. Services may not be running."
    echo "Attempting to kill by port..."
    
    # Try to kill by port
    for port in 8001 8002 8003 8004 8005 8007; do
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo "Killing process on port $port (PID: $pid)"
            kill $pid
        fi
    done
fi

echo "Done."
