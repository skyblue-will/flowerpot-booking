from typing import List, Dict, Optional, TypeVar, Generic, Type
from copy import deepcopy

from core.repositories import Repository, WorkshopRepository, BookingRepository, GuardianRepository
from core.workshops.WorkshopEntity import WorkshopEntity
from core.bookings.BookingEntity import BookingEntity
from core.guardians.GuardianEntity import GuardianEntity

# Type variable for entities with ID
T = TypeVar('T')


class InMemoryRepository(Generic[T], Repository[T]):
    """
    Generic in-memory repository implementation for testing.
    """
    
    def __init__(self, entity_class: Type[T]):
        self.entity_class = entity_class
        self._entities: Dict[int, T] = {}
        self._next_id: int = 1
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get an entity by ID.
        """
        return deepcopy(self._entities.get(id))
    
    def get_all(self) -> List[T]:
        """
        Get all entities.
        """
        return [deepcopy(entity) for entity in self._entities.values()]
    
    def save(self, entity: T) -> T:
        """
        Save an entity (create or update).
        """
        # Create a copy to avoid modifying the original
        entity_copy = deepcopy(entity)
        
        # If entity has no ID, assign one (creation)
        if not getattr(entity_copy, 'id'):
            setattr(entity_copy, 'id', self._next_id)
            self._next_id += 1
        
        # Store in dictionary
        self._entities[getattr(entity_copy, 'id')] = entity_copy
        
        # Return a copy to avoid external modification
        return deepcopy(entity_copy)
    
    def delete(self, id: int) -> bool:
        """
        Delete an entity by ID.
        """
        if id in self._entities:
            del self._entities[id]
            return True
        return False


class InMemoryWorkshopRepository(InMemoryRepository[WorkshopEntity], WorkshopRepository):
    """
    In-memory workshop repository implementation.
    """
    
    def __init__(self):
        super().__init__(WorkshopEntity)


class InMemoryBookingRepository(InMemoryRepository[BookingEntity], BookingRepository):
    """
    In-memory booking repository implementation.
    """
    
    def __init__(self):
        super().__init__(BookingEntity)
    
    def get_by_workshop_id(self, workshop_id: int) -> List[BookingEntity]:
        """
        Get all bookings for a specific workshop.
        """
        return [deepcopy(booking) for booking in self._entities.values() 
                if booking.workshop_id == workshop_id]
    
    def get_by_guardian_id(self, guardian_id: int) -> List[BookingEntity]:
        """
        Get all bookings for a specific guardian.
        """
        return [deepcopy(booking) for booking in self._entities.values() 
                if booking.guardian_id == guardian_id]


class InMemoryGuardianRepository(InMemoryRepository[GuardianEntity], GuardianRepository):
    """
    In-memory guardian repository implementation.
    """
    
    def __init__(self):
        super().__init__(GuardianEntity) 