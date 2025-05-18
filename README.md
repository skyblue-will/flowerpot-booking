# Flowerpot Booking System

A workshop booking system built following Clean Architecture principles.

## Architecture

This project follows Uncle Bob's Clean Architecture principles with a strict focus on a testable and isolated core domain.

### Core Domain (Innermost Layer)
- **Entities**: Pure data objects representing business concepts (Workshop, Booking, Guardian)
- **Use Cases**: Business rules and application-specific logic

### Repository Interfaces (Boundary Layer)
- Abstract interfaces that the core domain depends on
- Following the Dependency Inversion Principle: high-level modules don't depend on low-level modules

### Tests
- Tests are kept outside the core container
- This ensures the core domain works independently of infrastructure
- Tests verify business rules in isolation

## Project Structure

```
flowerpot-booking/
├── core/                  # Core domain (entities and use cases)
│   ├── workshops/         # Workshop-related domain objects
│   ├── guardians/         # Guardian-related domain objects
│   └── bookings/          # Booking-related domain objects
├── tests/                 # Tests for the core domain
│   └── core/              # Core domain tests
├── docker/                # Docker configuration
│   └── core/              # Core domain container
└── README.md              # This file
```

## Development

### Running Tests

Tests are run from outside the container against the core domain:

```bash
./docker/core-test.sh
```

This approach follows Clean Architecture by ensuring the core domain is truly isolated and testable independently of infrastructure concerns. 