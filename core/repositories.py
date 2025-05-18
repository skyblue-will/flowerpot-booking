from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

# Define entity type variable for generic repository
T = TypeVar('T')

class Repository(Generic[T], ABC):
    """
    Abstract base class for repositories, following the Repository pattern.
    Defines the interface that all repository implementations must follow.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Retrieve an entity by its ID.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """
        Retrieve all entities.
        
        Returns:
            A list of all entities
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save an entity to the repository.
        If the entity has no ID, it is created, otherwise it is updated.
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity with assigned ID if newly created
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete an entity by its ID.
        
        Args:
            id: The ID of the entity to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass


class WorkshopRepository(Repository['WorkshopEntity'], ABC):
    """
    Workshop-specific repository interface that extends the base Repository interface.
    May add workshop-specific query methods.
    """
    pass


class BookingRepository(Repository['BookingEntity'], ABC):
    """
    Booking-specific repository interface that extends the base Repository interface.
    """
    
    @abstractmethod
    def get_by_workshop_id(self, workshop_id: int) -> List['BookingEntity']:
        """
        Get all bookings for a specific workshop.
        
        Args:
            workshop_id: The ID of the workshop
            
        Returns:
            A list of bookings for the workshop
        """
        pass
    
    @abstractmethod
    def get_by_guardian_id(self, guardian_id: int) -> List['BookingEntity']:
        """
        Get all bookings for a specific guardian.
        
        Args:
            guardian_id: The ID of the guardian
            
        Returns:
            A list of bookings for the guardian
        """
        pass


class GuardianRepository(Repository['GuardianEntity'], ABC):
    """
    Guardian-specific repository interface that extends the base Repository interface.
    """
    pass 