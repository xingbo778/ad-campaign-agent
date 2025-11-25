#!/bin/bash
# Run pytest with real-time progress output
# This script shows each test as it runs, with progress percentage

cd "$(dirname "$0")"

# Check if pytest-xdist is available for parallel execution
if ./venv/bin/python -c "import xdist" 2>/dev/null; then
    echo "🚀 Starting test suite in PARALLEL mode (faster)..."
    echo "📊 Running tests with real-time progress (using pytest-xdist)..."
    echo ""
    PARALLEL_FLAG="-n auto"
else
    echo "🚀 Starting test suite..."
    echo "📊 Running tests with real-time progress..."
    echo "💡 Tip: Install pytest-xdist for parallel execution: pip install pytest-xdist"
    echo ""
    PARALLEL_FLAG=""
fi

# Run pytest with verbose output - shows each test as it runs
# -v: verbose (shows each test)
# --tb=short: short traceback format
# --durations=10: show 10 slowest tests at the end
# -ra: show extra test summary info (passed, failed, skipped, etc.)
# -n auto: parallel execution (if pytest-xdist available)
./venv/bin/python -m pytest tests/ \
    $PARALLEL_FLAG \
    -v \
    --tb=short \
    --durations=10 \
    --color=yes \
    -ra

echo ""
echo "✅ Test run completed!"
