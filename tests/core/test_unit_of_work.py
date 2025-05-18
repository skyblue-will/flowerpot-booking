import unittest
from unittest.mock import patch, MagicMock

from core.unit_of_work import UnitOfWork, execute_in_transaction
from core.memory_unit_of_work import InMemoryUnitOfWork
from core.workshops.WorkshopEntity import WorkshopEntity
from core.bookings.BookingEntity import BookingEntity
from core.guardians.GuardianEntity import GuardianEntity


class TestUnitOfWork(unittest.TestCase):
    """
    Test the UnitOfWork pattern implementation.
    """
    
    def setUp(self):
        """
        Set up test dependencies
        """
        self.uow = InMemoryUnitOfWork()
        
        # Create test entities
        self.workshop = WorkshopEntity(
            title="Test Workshop",
            date="2023-01-01",
            time="10:00",
            location="Test Location",
            max_families=10,
            max_children=20
        )
        
        self.guardian = GuardianEntity(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
    
    def test_successful_transaction(self):
        """
        Test that a successful transaction commits all changes.
        """
        # Execute a transaction that should succeed
        with self.uow:
            # Save workshop and guardian
            saved_workshop = self.uow.workshops.save(self.workshop)
            saved_guardian = self.uow.guardians.save(self.guardian)
            
            # Create a booking linking them
            booking = BookingEntity(
                workshop_id=saved_workshop.id,
                guardian_id=saved_guardian.id
            )
            booking.add_child("Test Child", 5)
            saved_booking = self.uow.bookings.save(booking)
            
            # Commit the transaction
            self.uow.commit()
        
        # Verify all entities were persisted
        workshop_from_db = self.uow.workshops.get_by_id(saved_workshop.id)
        guardian_from_db = self.uow.guardians.get_by_id(saved_guardian.id)
        booking_from_db = self.uow.bookings.get_by_id(saved_booking.id)
        
        self.assertIsNotNone(workshop_from_db)
        self.assertIsNotNone(guardian_from_db)
        self.assertIsNotNone(booking_from_db)
        self.assertEqual(workshop_from_db.title, "Test Workshop")
        self.assertEqual(guardian_from_db.name, "Test Guardian")
        self.assertEqual(booking_from_db.child_count(), 1)
    
    def test_failed_transaction_rollback(self):
        """
        Test that a failed transaction rolls back all changes.
        """
        try:
            with self.uow:
                # Save workshop and guardian
                saved_workshop = self.uow.workshops.save(self.workshop)
                saved_guardian = self.uow.guardians.save(self.guardian)
                
                # Verify they're in memory before commit
                self.assertIsNotNone(self.uow.workshops.get_by_id(saved_workshop.id))
                self.assertIsNotNone(self.uow.guardians.get_by_id(saved_guardian.id))
                
                # Simulate an error
                raise ValueError("Simulated error in transaction")
                
                # This should never be reached
                self.uow.commit()
        except ValueError:
            pass  # Expected exception
        
        # Verify nothing was persisted due to rollback
        self.assertIsNone(self.uow.workshops.get_by_id(1))
        self.assertIsNone(self.uow.guardians.get_by_id(1))
    
    def test_explicit_rollback(self):
        """
        Test explicit rollback of a transaction.
        """
        with self.uow:
            # Save workshop
            saved_workshop = self.uow.workshops.save(self.workshop)
            
            # Verify it's in memory before rollback
            self.assertIsNotNone(self.uow.workshops.get_by_id(saved_workshop.id))
            
            # Explicitly rollback
            self.uow.rollback()
        
        # Verify nothing was persisted due to explicit rollback
        self.assertIsNone(self.uow.workshops.get_by_id(1))
    
    def test_execute_in_transaction_success(self):
        """
        Test the execute_in_transaction helper function for successful operations.
        """
        # Define a function to execute in a transaction
        def create_entities(uow):
            workshop = self.uow.workshops.save(self.workshop)
            guardian = self.uow.guardians.save(self.guardian)
            return workshop.id, guardian.id
        
        # Execute the function in a transaction
        workshop_id, guardian_id = execute_in_transaction(self.uow, create_entities)
        
        # Verify entities were persisted
        self.assertIsNotNone(self.uow.workshops.get_by_id(workshop_id))
        self.assertIsNotNone(self.uow.guardians.get_by_id(guardian_id))
    
    def test_execute_in_transaction_failure(self):
        """
        Test the execute_in_transaction helper function for failing operations.
        """
        # Define a function that will fail
        def failing_operation(uow):
            workshop = self.uow.workshops.save(self.workshop)
            # Verify it's in memory
            self.assertIsNotNone(uow.workshops.get_by_id(workshop.id))
            # Simulate an error
            raise ValueError("Simulated error")
        
        # Execute and expect exception
        with self.assertRaises(ValueError):
            execute_in_transaction(self.uow, failing_operation)
        
        # Verify nothing was persisted
        self.assertIsNone(self.uow.workshops.get_by_id(1))
    
    def test_nested_operations(self):
        """
        Test complex operations with multiple entity interactions.
        """
        with self.uow:
            # Create a workshop
            workshop = self.uow.workshops.save(self.workshop)
            
            # Create multiple guardians
            guardian1 = GuardianEntity(name="Guardian 1", email="g1@example.com", phone="111", postcode="ABC")
            guardian2 = GuardianEntity(name="Guardian 2", email="g2@example.com", phone="222", postcode="DEF")
            
            saved_guardian1 = self.uow.guardians.save(guardian1)
            saved_guardian2 = self.uow.guardians.save(guardian2)
            
            # Create bookings for each guardian
            booking1 = BookingEntity(workshop_id=workshop.id, guardian_id=saved_guardian1.id)
            booking1.add_child("Child 1", 4)
            booking1.add_child("Child 2", 5)
            
            booking2 = BookingEntity(workshop_id=workshop.id, guardian_id=saved_guardian2.id)
            booking2.add_child("Child 3", 6)
            
            self.uow.bookings.save(booking1)
            self.uow.bookings.save(booking2)
            
            # Commit all changes
            self.uow.commit()
        
        # Retrieve all bookings for the workshop
        bookings = self.uow.bookings.get_by_workshop_id(1)
        
        # Verify the correct number of bookings and children
        self.assertEqual(len(bookings), 2)
        total_children = sum(booking.child_count() for booking in bookings)
        self.assertEqual(total_children, 3)
    
    def test_transaction_state_checking(self):
        """
        Test that transaction state checking works properly.
        """
        # Cannot commit without entering transaction
        with self.assertRaises(ValueError):
            self.uow.commit()
        
        # Cannot rollback without entering transaction
        with self.assertRaises(ValueError):
            self.uow.rollback()
        
        # Can commit inside transaction
        with self.uow:
            self.uow.workshops.save(self.workshop)
            self.uow.commit()
            
            # Cannot commit twice in same transaction
            with self.assertRaises(ValueError):
                self.uow.commit()


if __name__ == "__main__":
    unittest.main() 