#!/bin/bash
set -e

# Build the core container to verify it's isolated and properly built
echo "Building core container..."
docker-compose -f docker/docker-compose.yml build

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install pytest pytest-cov
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run tests from outside the container against the core domain
# This follows Clean Architecture by keeping tests independent of infrastructure
echo "Running tests against core domain..."
PYTHONPATH=${PWD} python -m pytest -xvs tests/core/

echo "Tests completed successfully." 