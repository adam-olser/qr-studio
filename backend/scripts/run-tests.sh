#!/bin/bash

# Backend Test Runner Script
set -e

echo "🧪 Running backend test suite..."

# Set test environment
export ENV=test
export REDIS_URL=redis://localhost:6379/1

# Run tests with coverage
python3 -m pytest \
    --verbose \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=70 \
    "$@"

echo "✅ Test suite completed!"
echo "📊 Coverage report generated in htmlcov/"
