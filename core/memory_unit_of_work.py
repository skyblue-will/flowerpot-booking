from core.unit_of_work import UnitOfWork
from core.memory_repositories import (
    InMemoryWorkshopRepository,
    InMemoryBookingRepository,
    InMemoryGuardianRepository
)


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory implementation of the UnitOfWork interface for testing purposes.
    
    This implementation demonstrates how a UnitOfWork works, but doesn't actually
    provide true atomicity or isolation since the in-memory repositories are not
    transactional. In a real application, this would typically use a database
    with proper transaction support.
    """
    
    def __init__(self):
        self._workshops = InMemoryWorkshopRepository()
        self._bookings = InMemoryBookingRepository()
        self._guardians = InMemoryGuardianRepository()
        
        # Snapshots for rollback
        self._workshop_snapshots = {}
        self._booking_snapshots = {}
        self._guardian_snapshots = {}
        
        # Transaction state
        self._is_active = False
    
    @property
    def workshops(self):
        return self._workshops
    
    @property
    def bookings(self):
        return self._bookings
    
    @property
    def guardians(self):
        return self._guardians
    
    def __enter__(self):
        """
        Begin a transaction by taking snapshots of the current state.
        """
        self._take_snapshots()
        self._is_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the transaction context. If an exception occurred, rollback.
        Otherwise, the transaction is left open for explicit commit.
        """
        if exc_type:
            self.rollback()
        
        self._is_active = False
    
    def _take_snapshots(self):
        """
        Take snapshots of all repositories for potential rollback.
        """
        self._workshop_snapshots = {id: entity for id, entity in self._workshops._entities.items()}
        self._booking_snapshots = {id: entity for id, entity in self._bookings._entities.items()}
        self._guardian_snapshots = {id: entity for id, entity in self._guardians._entities.items()}
    
    def commit(self):
        """
        Commit the transaction by discarding the snapshots.
        """
        if not self._is_active:
            raise ValueError("Cannot commit - no active transaction")
        
        # Clear snapshots to release memory
        self._workshop_snapshots = {}
        self._booking_snapshots = {}
        self._guardian_snapshots = {}
        
        self._is_active = False
    
    def rollback(self):
        """
        Rollback the transaction by restoring from snapshots.
        """
        if not self._is_active:
            raise ValueError("Cannot rollback - no active transaction")
        
        # Restore from snapshots
        self._workshops._entities = self._workshop_snapshots
        self._bookings._entities = self._booking_snapshots
        self._guardians._entities = self._guardian_snapshots
        
        # Clear snapshots to release memory
        self._workshop_snapshots = {}
        self._booking_snapshots = {}
        self._guardian_snapshots = {}
        
        self._is_active = False 