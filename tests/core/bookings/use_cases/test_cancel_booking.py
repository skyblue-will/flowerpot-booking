import unittest
from datetime import date, time
from unittest.mock import Mock, patch

from core.bookings.BookingEntity import BookingEntity, Child
from core.guardians.GuardianEntity import GuardianEntity
from core.workshops.WorkshopEntity import WorkshopEntity
from core.bookings.use_cases.CancelBooking import (
    CancelBookingInputDTO,
    CancelBookingOutputDTO,
    CancelBookingUseCase,
    CancellerType
)
from core.memory_unit_of_work import InMemoryUnitOfWork


class TestCancelBooking(unittest.TestCase):
    """
    Test the CancelBooking use case with various scenarios.
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
            current_families=2,  # We'll start with 2 families
            current_children=3   # And 3 children
        )
        self.workshop = self.uow.workshops.save(self.workshop)
        
        # Create a test guardian
        self.guardian = GuardianEntity(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        self.guardian = self.uow.guardians.save(self.guardian)
        
        # Create a test booking
        self.booking = BookingEntity(
            workshop_id=self.workshop.id,
            guardian_id=self.guardian.id
        )
        self.booking.add_child("Child 1", 5)
        self.booking.add_child("Child 2", 7)
        self.booking = self.uow.bookings.save(self.booking)
        
        # Initialize the use case
        self.use_case = CancelBookingUseCase(self.uow)
    
    def test_successful_cancellation_by_guardian(self):
        """Test that a guardian can cancel their own booking"""
        # Create input data for cancellation by guardian
        input_dto = CancelBookingInputDTO(
            booking_id=self.booking.id,
            canceller_id=self.guardian.id,
            canceller_type=CancellerType.GUARDIAN,
            reason="Change of plans"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        
        # Verify the booking was marked as cancelled
        updated_booking = self.uow.bookings.get_by_id(self.booking.id)
        self.assertTrue(updated_booking.is_cancelled())
        self.assertEqual(updated_booking.cancellation_reason, "Change of plans")
        
        # Verify the workshop capacity was updated
        updated_workshop = self.uow.workshops.get_by_id(self.workshop.id)
        self.assertEqual(updated_workshop.current_families, 1)  # Decreased by 1
        self.assertEqual(updated_workshop.current_children, 1)  # Decreased by booking's child count (2)
    
    def test_successful_cancellation_by_admin(self):
        """Test that an admin can cancel any booking"""
        # Create an admin ID (in a real app, this would be validated differently)
        admin_id = 999
        
        # Create input data for cancellation by admin
        input_dto = CancelBookingInputDTO(
            booking_id=self.booking.id,
            canceller_id=admin_id,
            canceller_type=CancellerType.ADMIN,
            reason="Workshop rescheduled"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        
        # Verify the booking was marked as cancelled
        updated_booking = self.uow.bookings.get_by_id(self.booking.id)
        self.assertTrue(updated_booking.is_cancelled())
        self.assertEqual(updated_booking.cancellation_reason, "Workshop rescheduled")
    
    def test_cancellation_with_nonexistent_booking(self):
        """Test that cancellation fails when the booking doesn't exist"""
        # Create input data with non-existent booking ID
        input_dto = CancelBookingInputDTO(
            booking_id=9999,  # Non-existent ID
            canceller_id=self.guardian.id,
            canceller_type=CancellerType.GUARDIAN
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message)
    
    def test_cancellation_by_unauthorized_guardian(self):
        """Test that a guardian cannot cancel someone else's booking"""
        # Create another guardian
        other_guardian = GuardianEntity(
            name="Other Guardian",
            email="other@example.com",
            phone="0987654321",
            postcode="54321"
        )
        other_guardian = self.uow.guardians.save(other_guardian)
        
        # Create input data with the wrong guardian
        input_dto = CancelBookingInputDTO(
            booking_id=self.booking.id,
            canceller_id=other_guardian.id,  # Different guardian
            canceller_type=CancellerType.GUARDIAN
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIn("permission", result.error_message)
        
        # Verify the booking was not cancelled
        updated_booking = self.uow.bookings.get_by_id(self.booking.id)
        self.assertFalse(updated_booking.is_cancelled())
        
        # Verify the workshop capacity was not changed
        updated_workshop = self.uow.workshops.get_by_id(self.workshop.id)
        self.assertEqual(updated_workshop.current_families, 2)  # Still 2
        self.assertEqual(updated_workshop.current_children, 3)  # Still 3
    
    def test_workshop_not_found(self):
        """Test handling of missing workshop scenario"""
        # Create a booking with a non-existent workshop ID
        booking_with_bad_workshop = BookingEntity(
            workshop_id=9999,  # Non-existent workshop
            guardian_id=self.guardian.id
        )
        booking_with_bad_workshop.add_child("Test Child", 5)
        booking_with_bad_workshop = self.uow.bookings.save(booking_with_bad_workshop)
        
        # Create cancellation input
        input_dto = CancelBookingInputDTO(
            booking_id=booking_with_bad_workshop.id,
            canceller_id=self.guardian.id,
            canceller_type=CancellerType.GUARDIAN
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIn("Workshop", result.error_message)
    
    def test_transaction_rollback_on_error(self):
        """Test that all changes are rolled back when an error occurs mid-transaction"""
        # Create input for a valid cancellation
        input_dto = CancelBookingInputDTO(
            booking_id=self.booking.id,
            canceller_id=self.guardian.id,
            canceller_type=CancellerType.GUARDIAN
        )
        
        # Create a side effect to simulate an error during workshop update
        def save_side_effect(workshop):
            if workshop.id == self.workshop.id:
                raise ValueError("Simulated database error")
            return workshop
        
        # Patch the workshop repository's save method
        with patch.object(self.uow.workshops, 'save', side_effect=save_side_effect):
            # Execute the use case
            result = self.use_case.execute(input_dto)
            
            # Verify failure
            self.assertFalse(result.success)
            self.assertIn("Failed to cancel booking", result.error_message)
            
            # Verify booking was not cancelled due to rollback
            updated_booking = self.uow.bookings.get_by_id(self.booking.id)
            self.assertFalse(updated_booking.is_cancelled())
            
            # Verify workshop capacity was not changed due to rollback
            updated_workshop = self.uow.workshops.get_by_id(self.workshop.id)
            self.assertEqual(updated_workshop.current_families, 2)
            self.assertEqual(updated_workshop.current_children, 3)
    
    def test_notifications_are_sent(self):
        """Test that notifications are attempted to be sent"""
        # Create mocks for the notification methods
        with patch.object(self.use_case, '_send_guardian_notification') as mock_guardian_notify, \
             patch.object(self.use_case, '_send_admin_notification') as mock_admin_notify:
            
            # Create input for a valid cancellation
            input_dto = CancelBookingInputDTO(
                booking_id=self.booking.id,
                canceller_id=self.guardian.id,
                canceller_type=CancellerType.GUARDIAN
            )
            
            # Execute the use case
            result = self.use_case.execute(input_dto)
            
            # Verify success
            self.assertTrue(result.success)
            
            # Verify notification methods were called
            mock_guardian_notify.assert_called_once()
            mock_admin_notify.assert_called_once()


if __name__ == "__main__":
    unittest.main() 