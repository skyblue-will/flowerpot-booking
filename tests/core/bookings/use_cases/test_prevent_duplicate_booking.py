import unittest
from datetime import date, time
from unittest.mock import patch

from core.bookings.BookingEntity import BookingEntity
from core.guardians.GuardianEntity import GuardianEntity
from core.workshops.WorkshopEntity import WorkshopEntity
from core.bookings.use_cases.PreventDuplicateBooking import (
    PreventDuplicateBookingInputDTO,
    PreventDuplicateBookingOutputDTO,
    PreventDuplicateBookingUseCase
)
from core.memory_unit_of_work import InMemoryUnitOfWork


class TestPreventDuplicateBooking(unittest.TestCase):
    """
    Test the PreventDuplicateBooking use case with various scenarios.
    """
    
    def setUp(self):
        """Set up common test dependencies"""
        # Create a unit of work with test data
        self.uow = InMemoryUnitOfWork()
        
        # Create a test workshop
        self.workshop = WorkshopEntity(
            title="Test Workshop",
            date=date(2023, 1, 1),
            time=time(10, 0),
            location="Test Location",
            max_families=5,
            max_children=10,
            current_families=0,
            current_children=0
        )
        self.workshop = self.uow.workshops.save(self.workshop)
        
        # Create a second test workshop
        self.workshop2 = WorkshopEntity(
            title="Another Workshop",
            date=date(2023, 1, 8),
            time=time(14, 0),
            location="Another Location",
            max_families=3,
            max_children=6,
            current_families=0,
            current_children=0
        )
        self.workshop2 = self.uow.workshops.save(self.workshop2)
        
        # Create a test guardian
        self.guardian = GuardianEntity(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        self.guardian = self.uow.guardians.save(self.guardian)
        
        # Create a test booking for the first workshop
        self.booking = BookingEntity(
            workshop_id=self.workshop.id,
            guardian_id=self.guardian.id
        )
        self.booking.add_child("Child 1", 5)
        self.booking.add_child("Child 2", 7)
        self.booking = self.uow.bookings.save(self.booking)
        
        # Initialize the use case
        self.use_case = PreventDuplicateBookingUseCase(self.uow)
    
    def test_detect_duplicate_booking(self):
        """Test that a duplicate booking is correctly identified"""
        # Create input for a duplicate booking check
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="test@example.com",  # Same email as existing guardian
            workshop_id=self.workshop.id        # Same workshop that already has a booking
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify duplicate was detected
        self.assertTrue(result.is_duplicate)
        self.assertIsNotNone(result.error_message)
        self.assertIn("already has a booking", result.error_message)
    
    def test_allow_different_workshop_booking(self):
        """Test that a booking for a different workshop is not considered a duplicate"""
        # Create input for checking booking in a different workshop
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="test@example.com",  # Same email as existing guardian
            workshop_id=self.workshop2.id       # Different workshop
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify no duplicate was detected
        self.assertFalse(result.is_duplicate)
        self.assertIsNone(result.error_message)
    
    def test_allow_different_guardian_booking(self):
        """Test that a booking by a different guardian is not considered a duplicate"""
        # Create input for checking booking by a different guardian
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="another@example.com",  # Different email
            workshop_id=self.workshop.id           # Same workshop
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify no duplicate was detected
        self.assertFalse(result.is_duplicate)
        self.assertIsNone(result.error_message)
    
    def test_case_insensitive_email_check(self):
        """Test that email comparison is case-insensitive"""
        # Create input with same email but different case
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="TEST@example.com",  # Same email but uppercase
            workshop_id=self.workshop.id
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify duplicate was detected despite case difference
        self.assertTrue(result.is_duplicate)
        self.assertIsNotNone(result.error_message)
    
    def test_cancelled_booking_not_considered_duplicate(self):
        """Test that a cancelled booking is not considered a duplicate"""
        # Cancel the existing booking
        self.booking.mark_as_cancelled("Test cancellation")
        self.uow.bookings.save(self.booking)
        
        # Create input for a new booking with the same details
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="test@example.com",
            workshop_id=self.workshop.id
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify no duplicate was detected because previous booking was cancelled
        self.assertFalse(result.is_duplicate)
        self.assertIsNone(result.error_message)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid input"""
        # Create input with missing email
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="",  # Empty email
            workshop_id=self.workshop.id
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify error response
        self.assertFalse(result.is_duplicate)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Invalid input", result.error_message)
    
    def test_nonexistent_workshop_handling(self):
        """Test handling of non-existent workshop"""
        # Create input with non-existent workshop ID
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="test@example.com",
            workshop_id=9999  # Non-existent ID
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify error response
        self.assertFalse(result.is_duplicate)
        self.assertIsNotNone(result.error_message)
        self.assertIn("not found", result.error_message)
    
    def test_error_handling(self):
        """Test that exceptions are properly handled"""
        # Create valid input
        input_dto = PreventDuplicateBookingInputDTO(
            guardian_email="test@example.com",
            workshop_id=self.workshop.id
        )
        
        # Create a side effect to simulate an error
        def get_all_side_effect():
            raise ValueError("Simulated database error")
        
        # Patch the guardians repository's get_all method
        with patch.object(self.uow.guardians, 'get_all', side_effect=get_all_side_effect):
            # Execute the use case
            result = self.use_case.execute(input_dto)
            
            # Verify error handling
            self.assertFalse(result.is_duplicate)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Error checking for duplicate bookings", result.error_message)


if __name__ == "__main__":
    unittest.main() 