from abc import ABC, abstractmethod
from typing import Callable, TypeVar

from core.repositories import WorkshopRepository, BookingRepository, GuardianRepository


class UnitOfWork(ABC):
    """
    The UnitOfWork defines a transaction boundary for domain operations.
    It encapsulates repositories and ensures that all operations either succeed together
    or fail together, maintaining data consistency.
    """
    
    @property
    @abstractmethod
    def workshops(self) -> WorkshopRepository:
        """
        Get the workshop repository.
        """
        pass
    
    @property
    @abstractmethod
    def bookings(self) -> BookingRepository:
        """
        Get the booking repository.
        """
        pass
    
    @property
    @abstractmethod
    def guardians(self) -> GuardianRepository:
        """
        Get the guardian repository.
        """
        pass
    
    @abstractmethod
    def __enter__(self):
        """
        Enter the context manager, begin a transaction.
        """
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, commit or rollback based on whether an exception occurred.
        
        Args:
            exc_type: Exception type if an exception was raised, otherwise None
            exc_val: Exception value if an exception was raised, otherwise None
            exc_tb: Exception traceback if an exception was raised, otherwise None
        """
        pass
    
    @abstractmethod
    def commit(self):
        """
        Commit the current transaction.
        """
        pass
    
    @abstractmethod
    def rollback(self):
        """
        Rollback the current transaction.
        """
        pass


# Type variable for the return value of the function to be executed in a transaction
R = TypeVar('R')


def execute_in_transaction(uow: UnitOfWork, function: Callable[[UnitOfWork], R]) -> R:
    """
    Execute a function within a transaction.
    
    Args:
        uow: The UnitOfWork to use for the transaction
        function: The function to execute, which takes a UnitOfWork as its only argument
        
    Returns:
        The return value of the function
        
    Raises:
        Any exception raised by the function
    """
    with uow:
        result = function(uow)
        uow.commit()
        return result 