#!/bin/bash
set -e

# Build the core container to verify it's isolated and properly built
echo "Building core container..."
docker-compose -f docker/docker-compose.yml build

# Run tests from outside the container against the core domain
# This follows Clean Architecture by keeping tests independent of infrastructure
echo "Running tests against core domain..."
PYTHONPATH=${PWD} pytest -xvs tests/core/

echo "Tests completed successfully." 