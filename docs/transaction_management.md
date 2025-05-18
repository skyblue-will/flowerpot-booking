# Transaction Management in Flowerpot Booking System

This document outlines the transaction management design implemented in the Flowerpot Booking System following Clean Architecture principles.

## The Problem

One of the most severe shortcomings in the initial codebase was the lack of transaction management. Without proper transaction boundaries:

1. Multiple repository operations weren't guaranteed to succeed or fail atomically
2. Data consistency could be compromised in failure scenarios
3. Use cases had direct dependencies on repositories rather than a transaction abstraction
4. Error handling could leave the system in an inconsistent state

## The Solution: Unit of Work Pattern

We've implemented the Unit of Work pattern to address these issues. This pattern:

1. Encapsulates a business transaction with a clear boundary
2. Manages multiple repository operations as a single unit
3. Ensures data consistency through commit/rollback semantics
4. Simplifies use case implementations

## Implementation Components

### 1. Repository Interfaces

The `core/repositories.py` file defines abstract base interfaces for repositories:

```python
class Repository(Generic[T], ABC):
    """Abstract base repository interface"""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    # Other core repository methods...
```

Specific repository interfaces extend the base interface:

```python
class WorkshopRepository(Repository['WorkshopEntity'], ABC):
    """Workshop-specific repository interface"""
    pass

class BookingRepository(Repository['BookingEntity'], ABC):
    """Booking-specific repository interface"""
    # Additional booking-specific methods...
```

### 2. Unit of Work Interface

The `core/unit_of_work.py` file defines the UnitOfWork interface:

```python
class UnitOfWork(ABC):
    """Defines transaction boundaries for domain operations"""
    
    @property
    @abstractmethod
    def workshops(self) -> WorkshopRepository:
        pass
    
    # Other repository accessors...
    
    @abstractmethod
    def __enter__(self):
        """Begin a transaction"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End a transaction"""
        pass
    
    @abstractmethod
    def commit(self):
        """Commit the transaction"""
        pass
    
    @abstractmethod
    def rollback(self):
        """Rollback the transaction"""
        pass
```

### 3. Memory Implementations (For Testing)

The `core/memory_repositories.py` and `core/memory_unit_of_work.py` files provide in-memory implementations for testing:

```python
class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory UnitOfWork implementation for testing
    """
    
    def __init__(self):
        self._workshops = InMemoryWorkshopRepository()
        # Other repositories...
        
    # Transaction management methods...
```

### 4. Use Case Updates

Use cases have been updated to work with UnitOfWork instead of individual repositories:

```python
class CreateWorkshopUseCase:
    
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
    
    def execute(self, input_dto):
        # Use transaction boundary
        with self.unit_of_work:
            # Use repositories via unit_of_work
            workshop = self.unit_of_work.workshops.save(new_workshop)
            self.unit_of_work.commit()
```

## Usage Examples

### Basic Transaction

```python
def execute(self, input_dto):
    with self.unit_of_work:
        # Multiple repository operations
        workshop = self.unit_of_work.workshops.save(workshop)
        booking = self.unit_of_work.bookings.save(booking)
        # All operations succeed or fail together
        self.unit_of_work.commit()
```

### Error Handling

```python
def execute(self, input_dto):
    try:
        with self.unit_of_work:
            # Repository operations
            self.unit_of_work.commit()
    except Exception as e:
        # Transaction is automatically rolled back
        return ErrorOutputDTO(error=str(e))
```

## Future Enhancements

1. **Infrastructure Layer Implementation**: Implement concrete repositories and UnitOfWork using a real database
2. **Nested Transactions**: Support for nested transactions if needed
3. **Transaction Retries**: Add support for retrying failed transactions
4. **Transaction Logging**: Add comprehensive logging for transaction operations

## Testing

Unit tests have been updated to use the UnitOfWork pattern. Both mocked UnitOfWork and real InMemoryUnitOfWork implementations can be used for testing.

```python
def test_with_real_in_memory_unit_of_work(self):
    real_uow = InMemoryUnitOfWork()
    real_use_case = CreateWorkshopUseCase(real_uow)
    
    result = real_use_case.execute(self.valid_input)
    
    # Verify the state after the transaction completes
    saved_workshop = real_uow.workshops.get_by_id(result.workshop_id)
    self.assertIsNotNone(saved_workshop)
``` 