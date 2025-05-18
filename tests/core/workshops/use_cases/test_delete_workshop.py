import unittest
from typing import List, Optional
from unittest.mock import Mock

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.DeleteWorkshop import (
    DeleteWorkshopInputDTO,
    DeleteWorkshopOutputDTO,
    DeleteWorkshopUseCase,
    GuardianToNotifyDTO
)


class MockBooking:
    """Simple mock booking class for testing."""
    def __init__(self, id, workshop_id, guardian_id):
        self.id = id
        self.workshop_id = workshop_id
        self.guardian_id = guardian_id


class MockGuardian:
    """Simple mock guardian class for testing."""
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


class MockWorkshopRepository:
    """
    Mock repository for testing the DeleteWorkshop use case.
    """
    def __init__(self, workshops=None, should_fail=False):
        self.workshops = {w.id: w for w in (workshops or [])}
        self.should_fail = should_fail
        self.deleted_ids = []
    
    def get_by_id(self, workshop_id) -> Optional[WorkshopEntity]:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        return self.workshops.get(workshop_id)
    
    def delete(self, workshop_id) -> bool:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        if workshop_id in self.workshops:
            del self.workshops[workshop_id]
            self.deleted_ids.append(workshop_id)
            return True
        
        return False


class MockBookingRepository:
    """
    Mock repository for testing bookings in the DeleteWorkshop use case.
    """
    def __init__(self, bookings=None, guardians=None, should_fail=False):
        self.bookings = bookings or []
        self.guardians = guardians or []
        self.should_fail = should_fail
        self.deleted_booking_ids = []
    
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
    
    def delete(self, booking_id) -> bool:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        booking_index = next((i for i, b in enumerate(self.bookings) if b.id == booking_id), -1)
        if booking_index >= 0:
            self.bookings.pop(booking_index)
            self.deleted_booking_ids.append(booking_id)
            return True
        
        return False


class TestDeleteWorkshopUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Create test workshops
        self.workshop = WorkshopEntity(
            id=1,
            title="Test Workshop",
            date=None,  # Not relevant for this test
            time=None,  # Not relevant for this test
            location="Test Location",
            max_families=10,
            max_children=20,
            current_families=2,
            current_children=3
        )
        
        self.workshop_no_bookings = WorkshopEntity(
            id=2,
            title="Workshop No Bookings",
            date=None,
            time=None,
            location="Test Location 2",
            max_families=5,
            max_children=10,
            current_families=0,
            current_children=0
        )
        
        # Create mock guardians
        self.guardians = [
            MockGuardian(id=1, name="Guardian 1", email="guardian1@example.com"),
            MockGuardian(id=2, name="Guardian 2", email="guardian2@example.com")
        ]
        
        # Create mock bookings
        self.bookings = [
            MockBooking(id=1, workshop_id=1, guardian_id=1),
            MockBooking(id=2, workshop_id=1, guardian_id=1),  # Same guardian, multiple bookings
            MockBooking(id=3, workshop_id=1, guardian_id=2)
        ]
        
        # Create repositories
        self.workshop_repository = MockWorkshopRepository(
            workshops=[self.workshop, self.workshop_no_bookings]
        )
        self.booking_repository = MockBookingRepository(
            bookings=self.bookings,
            guardians=self.guardians
        )
        
        # Create use case
        self.use_case = DeleteWorkshopUseCase(
            workshop_repository=self.workshop_repository,
            booking_repository=self.booking_repository
        )
    
    def test_delete_workshop_with_bookings(self):
        """
        Test deleting a workshop that has bookings, requiring guardian notifications.
        """
        # Create input to delete workshop with bookings
        input_dto = DeleteWorkshopInputDTO(workshop_id=1)
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertIsNotNone(result.guardians_to_notify)
        self.assertEqual(len(result.guardians_to_notify), 2)
        self.assertIsNone(result.error_message)
        
        # Verify workshop was deleted
        self.assertIn(1, self.workshop_repository.deleted_ids)
        self.assertNotIn(1, self.workshop_repository.workshops)
        
        # Verify bookings were deleted
        self.assertIn(1, self.booking_repository.deleted_booking_ids)
        self.assertIn(2, self.booking_repository.deleted_booking_ids)
        self.assertIn(3, self.booking_repository.deleted_booking_ids)
        
        # Verify guardian notification data
        guardian_ids = [g.guardian_id for g in result.guardians_to_notify]
        self.assertIn(1, guardian_ids)
        self.assertIn(2, guardian_ids)
        
        # Find guardian 1 (who has 2 bookings)
        guardian1 = next(g for g in result.guardians_to_notify if g.guardian_id == 1)
        self.assertEqual(guardian1.name, "Guardian 1")
        self.assertEqual(guardian1.email, "guardian1@example.com")
        self.assertEqual(len(guardian1.booking_ids), 2)
        self.assertIn(1, guardian1.booking_ids)
        self.assertIn(2, guardian1.booking_ids)
        
        # Find guardian 2 (who has 1 booking)
        guardian2 = next(g for g in result.guardians_to_notify if g.guardian_id == 2)
        self.assertEqual(guardian2.name, "Guardian 2")
        self.assertEqual(guardian2.email, "guardian2@example.com")
        self.assertEqual(len(guardian2.booking_ids), 1)
        self.assertIn(3, guardian2.booking_ids)
    
    def test_delete_workshop_without_bookings(self):
        """
        Test deleting a workshop that has no bookings.
        """
        # Create input to delete workshop without bookings
        input_dto = DeleteWorkshopInputDTO(workshop_id=2)
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertIsNone(result.guardians_to_notify)
        self.assertIsNone(result.error_message)
        
        # Verify workshop was deleted
        self.assertIn(2, self.workshop_repository.deleted_ids)
        self.assertNotIn(2, self.workshop_repository.workshops)
    
    def test_workshop_not_found(self):
        """
        Test deleting a non-existent workshop.
        """
        # Create input with non-existent workshop ID
        input_dto = DeleteWorkshopInputDTO(workshop_id=999)
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.guardians_to_notify)
        self.assertEqual(result.error_message, "Workshop with ID 999 not found")
        
        # Verify no workshops were deleted
        self.assertEqual(len(self.workshop_repository.deleted_ids), 0)
        self.assertEqual(len(self.workshop_repository.workshops), 2)
    
    def test_invalid_workshop_id(self):
        """
        Test with an invalid workshop ID.
        """
        # Create input with invalid workshop ID
        input_dto = DeleteWorkshopInputDTO(workshop_id=0)
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.guardians_to_notify)
        self.assertEqual(result.error_message, "Invalid workshop ID provided")
    
    def test_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create repositories that will fail
        failing_workshop_repository = MockWorkshopRepository(
            workshops=[self.workshop],
            should_fail=True
        )
        
        failing_use_case = DeleteWorkshopUseCase(
            workshop_repository=failing_workshop_repository,
            booking_repository=self.booking_repository
        )
        
        # Create valid input
        input_dto = DeleteWorkshopInputDTO(workshop_id=1)
        
        # Execute the use case
        result = failing_use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.guardians_to_notify)
        self.assertTrue(result.error_message.startswith("Failed to delete workshop:"))


if __name__ == "__main__":
    unittest.main() 