# Flowerpot Booking - Core Domain Docker Setup

This directory contains Docker configuration for the core domain of the Flowerpot Booking system, following Clean Architecture principles.

## Overview

The setup focuses solely on containerizing the core domain with its business logic and entities, allowing for a testable and isolated core that follows Uncle Bob's Clean Architecture principles.

## Structure

- `core/` - Docker configuration for the core domain
  - `Dockerfile` - Builds the core domain container
- `docker-compose.yml` - Orchestrates the core container
- `core-test.sh` - Script to run tests against the core domain

## Testing Philosophy

Tests are deliberately kept outside the container to:

1. Verify the core domain works independently
2. Maintain clean separation of concerns
3. Allow faster feedback during development
4. Support the Dependency Inversion Principle (dependencies point inward)

## Usage

### Building the Core Container

```bash
docker-compose -f docker/docker-compose.yml build
```

### Running Tests

```bash
./docker/core-test.sh
```

This will build the core container and run the tests against it from outside the container, ensuring the core domain is properly isolated and testable. 