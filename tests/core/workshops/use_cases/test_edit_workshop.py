import unittest
from datetime import date, time
from typing import List, Optional
from unittest.mock import Mock

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.EditWorkshop import (
    EditWorkshopInputDTO,
    EditWorkshopOutputDTO,
    EditWorkshopUseCase,
    AffectedBookingDTO
)


class MockBooking:
    """Simple mock booking class for testing."""
    def __init__(self, id, workshop_id, guardian_id, children):
        self.id = id
        self.workshop_id = workshop_id
        self.guardian_id = guardian_id
        self.children = children or []
    
    def child_count(self):
        return len(self.children)


class MockGuardian:
    """Simple mock guardian class for testing."""
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


class MockWorkshopRepository:
    """
    Mock repository for testing the EditWorkshop use case.
    """
    def __init__(self, workshops=None, should_fail=False):
        self.workshops = {w.id: w for w in (workshops or [])}
        self.should_fail = should_fail
    
    def get_by_id(self, workshop_id) -> Optional[WorkshopEntity]:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        return self.workshops.get(workshop_id)
    
    def update(self, workshop) -> WorkshopEntity:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        self.workshops[workshop.id] = workshop
        return workshop


class MockBookingRepository:
    """
    Mock repository for testing bookings in the EditWorkshop use case.
    """
    def __init__(self, bookings=None, guardians=None, should_fail=False):
        self.bookings = bookings or []
        self.guardians = guardians or []
        self.should_fail = should_fail
    
    def get_by_workshop_id(self, workshop_id) -> List[MockBooking]:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        return [b for b in self.bookings if b.workshop_id == workshop_id]
    
    def get_guardian_for_booking(self, booking_id) -> Optional[MockGuardian]:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        booking = next((b for b in self.bookings if b.id == booking_id), None)
        if not booking:
            return None
        
        return next((g for g in self.guardians if g.id == booking.guardian_id), None)


class TestEditWorkshopUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Create a test workshop
        self.workshop = WorkshopEntity(
            id=1,
            title="Original Workshop",
            date=date(2023, 12, 1),
            time=time(14, 0),
            location="Original Location",
            max_families=10,
            max_children=20,
            current_families=5,
            current_children=10
        )
        
        # Create mock guardians
        self.guardians = [
            MockGuardian(id=1, name="Guardian 1", email="guardian1@example.com"),
            MockGuardian(id=2, name="Guardian 2", email="guardian2@example.com")
        ]
        
        # Create mock bookings
        self.bookings = [
            MockBooking(id=1, workshop_id=1, guardian_id=1, children=["Child 1", "Child 2"]),
            MockBooking(id=2, workshop_id=1, guardian_id=2, children=["Child 3"])
        ]
        
        # Create repositories
        self.workshop_repository = MockWorkshopRepository(workshops=[self.workshop])
        self.booking_repository = MockBookingRepository(
            bookings=self.bookings, 
            guardians=self.guardians
        )
        
        # Create use case
        self.use_case = EditWorkshopUseCase(
            workshop_repository=self.workshop_repository,
            booking_repository=self.booking_repository
        )
        
        # Create a valid input DTO for testing
        self.valid_input = EditWorkshopInputDTO(
            workshop_id=1,
            title="Updated Workshop",
            workshop_date=date(2023, 12, 15),
            workshop_time=time(16, 0),
            location="Updated Location",
            max_families=15,
            max_children=30
        )
    
    def test_edit_workshop_success(self):
        """
        Test editing a workshop successfully without reducing slots.
        """
        # Execute the use case
        result = self.use_case.execute(self.valid_input)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.workshop_id, 1)
        self.assertIsNone(result.affected_bookings)
        self.assertIsNone(result.error_message)
        
        # Verify the workshop was updated in the repository
        updated_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(updated_workshop.title, "Updated Workshop")
        self.assertEqual(updated_workshop.date, date(2023, 12, 15))
        self.assertEqual(updated_workshop.time, time(16, 0))
        self.assertEqual(updated_workshop.location, "Updated Location")
        self.assertEqual(updated_workshop.max_families, 15)
        self.assertEqual(updated_workshop.max_children, 30)
        
        # Verify current values weren't changed
        self.assertEqual(updated_workshop.current_families, 5)
        self.assertEqual(updated_workshop.current_children, 10)
    
    def test_edit_workshop_reducing_slots(self):
        """
        Test editing a workshop with reducing slots below current usage.
        """
        # Create input that reduces slots below current usage
        input_reducing_slots = EditWorkshopInputDTO(
            workshop_id=1,
            title="Updated Workshop",
            workshop_date=date(2023, 12, 15),
            workshop_time=time(16, 0),
            location="Updated Location",
            max_families=3,  # Reduced from 10 to 3 (current is 5)
            max_children=8   # Reduced from 20 to 8 (current is 10)
        )
        
        # Execute the use case
        result = self.use_case.execute(input_reducing_slots)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.workshop_id, 1)
        self.assertIsNotNone(result.affected_bookings)
        self.assertEqual(len(result.affected_bookings), 2)
        
        # Verify affected bookings data
        affected_booking_ids = [b.booking_id for b in result.affected_bookings]
        self.assertIn(1, affected_booking_ids)
        self.assertIn(2, affected_booking_ids)
        
        # Verify the workshop was updated in the repository
        updated_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(updated_workshop.max_families, 3)
        self.assertEqual(updated_workshop.max_children, 8)
    
    def test_edit_workshop_not_found(self):
        """
        Test editing a non-existent workshop.
        """
        # Create input with non-existent workshop ID
        input_not_found = EditWorkshopInputDTO(
            workshop_id=999,
            title="Updated Workshop",
            workshop_date=date(2023, 12, 15),
            workshop_time=time(16, 0),
            location="Updated Location",
            max_families=15,
            max_children=30
        )
        
        # Execute the use case
        result = self.use_case.execute(input_not_found)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.affected_bookings)
        self.assertEqual(result.error_message, "Workshop with ID 999 not found")
    
    def test_edit_workshop_validation_failure(self):
        """
        Test validation failures.
        """
        # Create invalid inputs to test validation
        invalid_inputs = [
            # Invalid workshop ID
            EditWorkshopInputDTO(
                workshop_id=0,
                title="Updated Workshop",
                workshop_date=date(2023, 12, 15),
                workshop_time=time(16, 0),
                location="Updated Location",
                max_families=15,
                max_children=30
            ),
            # Empty title
            EditWorkshopInputDTO(
                workshop_id=1,
                title="",
                workshop_date=date(2023, 12, 15),
                workshop_time=time(16, 0),
                location="Updated Location",
                max_families=15,
                max_children=30
            ),
            # Empty location
            EditWorkshopInputDTO(
                workshop_id=1,
                title="Updated Workshop",
                workshop_date=date(2023, 12, 15),
                workshop_time=time(16, 0),
                location="",
                max_families=15,
                max_children=30
            ),
            # Invalid max families
            EditWorkshopInputDTO(
                workshop_id=1,
                title="Updated Workshop",
                workshop_date=date(2023, 12, 15),
                workshop_time=time(16, 0),
                location="Updated Location",
                max_families=0,
                max_children=30
            ),
            # Invalid max children
            EditWorkshopInputDTO(
                workshop_id=1,
                title="Updated Workshop",
                workshop_date=date(2023, 12, 15),
                workshop_time=time(16, 0),
                location="Updated Location",
                max_families=15,
                max_children=0
            )
        ]
        
        # Test each invalid input
        for invalid_input in invalid_inputs:
            result = self.use_case.execute(invalid_input)
            
            # Verify validation failure
            self.assertFalse(result.success)
            self.assertIsNone(result.workshop_id)
            self.assertIsNone(result.affected_bookings)
            self.assertEqual(result.error_message, "Invalid workshop data provided")
    
    def test_edit_workshop_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create repositories that will fail
        failing_workshop_repository = MockWorkshopRepository(
            workshops=[self.workshop], 
            should_fail=True
        )
        
        failing_use_case = EditWorkshopUseCase(
            workshop_repository=failing_workshop_repository,
            booking_repository=self.booking_repository
        )
        
        # Execute the use case
        result = failing_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.affected_bookings)
        self.assertTrue(result.error_message.startswith("Failed to edit workshop:"))


if __name__ == "__main__":
    unittest.main() 