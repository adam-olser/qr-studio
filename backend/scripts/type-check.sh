#!/bin/bash

# Backend Type Checking Script
set -e

echo "🔍 Running mypy type checking..."

# Run mypy on all application modules
python3 -m mypy \
    app/main.py \
    app/api/ \
    app/core/ \
    app/models/ \
    app/services/ \
    --ignore-missing-imports \
    --show-error-codes \
    --show-column-numbers

echo "✅ Type checking completed!"
