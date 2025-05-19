import unittest
from unittest.mock import Mock, patch, MagicMock

from core.guardians.GuardianEntity import GuardianEntity
from core.bookings.BookingEntity import BookingEntity
from core.guardians.use_cases.LinkBookingsToGuardians import (
    LinkBookingsToGuardiansUseCase,
    LinkBookingsToGuardiansInputDTO,
    LinkBookingsToGuardiansOutputDTO
)


class MockUnitOfWork:
    """Mock UnitOfWork for testing the LinkBookingsToGuardians use case."""
    
    def __init__(self):
        self.guardians = Mock()
        self.bookings = Mock()
        self.entered = False
        self.exited = False
        self.commit_called = False
        self.rollback_called = False
    
    def __enter__(self):
        self.entered = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        if exc_type:
            self.rollback_called = True
            return False
        return True
    
    def commit(self):
        self.commit_called = True
    
    def rollback(self):
        self.rollback_called = True


class TestLinkBookingsToGuardiansUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self.unit_of_work = MockUnitOfWork()
        self.use_case = LinkBookingsToGuardiansUseCase(self.unit_of_work)
        
        # Create a test guardian
        self.guardian = GuardianEntity(
            id=1,
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        
        # Create some test bookings
        self.booking1 = BookingEntity(
            id=1,
            workshop_id=1,
            guardian_id=None  # Not linked to a guardian yet
        )
        
        self.booking2 = BookingEntity(
            id=2,
            workshop_id=1,
            guardian_id=None  # Not linked to a guardian yet
        )
        
        self.booking3 = BookingEntity(
            id=3,
            workshop_id=2,
            guardian_id=2  # Already linked to a different guardian
        )
        
        # Configure the mocks to return our test entities
        self.unit_of_work.guardians.get_by_id = Mock(return_value=self.guardian)
        self.unit_of_work.bookings.get_by_id = Mock(side_effect=self._mock_get_booking_by_id)
        self.unit_of_work.bookings.save = Mock(return_value=None)
    
    def _mock_get_booking_by_id(self, booking_id):
        """Helper method to mock the get_by_id method of booking repository."""
        if booking_id == 1:
            return self.booking1
        elif booking_id == 2:
            return self.booking2
        elif booking_id == 3:
            return self.booking3
        else:
            return None
    
    def test_link_bookings_to_guardian_success(self):
        """
        Test linking multiple bookings to a guardian successfully.
        """
        # Create input DTO
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=1,
            booking_ids=[1, 2]
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.linked_booking_ids, [1, 2])
        self.assertIsNone(result.error_message)
        
        # Verify the guardian was retrieved
        self.unit_of_work.guardians.get_by_id.assert_called_once_with(1)
        
        # Verify the bookings were retrieved
        self.unit_of_work.bookings.get_by_id.assert_any_call(1)
        self.unit_of_work.bookings.get_by_id.assert_any_call(2)
        
        # Verify the bookings were saved
        self.assertEqual(self.unit_of_work.bookings.save.call_count, 2)
        
        # Verify the bookings were linked to the guardian
        self.assertEqual(self.booking1.guardian_id, 1)
        self.assertEqual(self.booking2.guardian_id, 1)
        
        # Verify transaction was managed correctly
        self.assertTrue(self.unit_of_work.entered)
        self.assertTrue(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
        self.assertFalse(self.unit_of_work.rollback_called)
    
    def test_guardian_not_found(self):
        """
        Test handling the case where the guardian is not found.
        """
        # Configure the mock to return None (guardian not found)
        self.unit_of_work.guardians.get_by_id = Mock(return_value=None)
        
        # Create input DTO
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=999,  # Non-existent guardian ID
            booking_ids=[1, 2]
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.linked_booking_ids)
        self.assertEqual(result.error_message, "Guardian with ID 999 not found")
        
        # Verify the guardian was looked up
        self.unit_of_work.guardians.get_by_id.assert_called_once_with(999)
        
        # Verify no bookings were saved
        self.unit_of_work.bookings.save.assert_not_called()
        
        # Verify transaction was managed correctly
        self.assertTrue(self.unit_of_work.entered)
        self.assertFalse(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
    
    def test_booking_not_found(self):
        """
        Test handling the case where a booking is not found.
        """
        # Create input DTO with a non-existent booking ID
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=1,
            booking_ids=[1, 999]  # 999 is a non-existent booking ID
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.linked_booking_ids, [1])  # First booking was processed successfully
        self.assertEqual(result.error_message, "Booking with ID 999 not found")
        
        # Verify the bookings were looked up
        self.unit_of_work.bookings.get_by_id.assert_any_call(1)
        self.unit_of_work.bookings.get_by_id.assert_any_call(999)
        
        # Verify only the first booking was saved
        self.assertEqual(self.unit_of_work.bookings.save.call_count, 1)
        
        # Verify the first booking was linked to the guardian
        self.assertEqual(self.booking1.guardian_id, 1)
        
        # Verify transaction was managed correctly
        self.assertTrue(self.unit_of_work.entered)
        self.assertFalse(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
    
    def test_booking_already_linked(self):
        """
        Test handling the case where a booking is already linked to a different guardian.
        """
        # Create input DTO with a booking already linked to another guardian
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=1,
            booking_ids=[1, 3]  # Booking 3 is already linked to guardian 2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertEqual(result.linked_booking_ids, [1])  # First booking was processed successfully
        self.assertEqual(result.error_message, "Booking with ID 3 is already linked to guardian with ID 2")
        
        # Verify the bookings were looked up
        self.unit_of_work.bookings.get_by_id.assert_any_call(1)
        self.unit_of_work.bookings.get_by_id.assert_any_call(3)
        
        # Verify only the first booking was saved
        self.assertEqual(self.unit_of_work.bookings.save.call_count, 1)
        
        # Verify the first booking was linked to the guardian
        self.assertEqual(self.booking1.guardian_id, 1)
        
        # Verify transaction was managed correctly
        self.assertTrue(self.unit_of_work.entered)
        self.assertFalse(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
    
    def test_invalid_input(self):
        """
        Test handling invalid input data.
        """
        # Create invalid input DTO (negative guardian ID)
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=-1,
            booking_ids=[1, 2]
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.linked_booking_ids)
        self.assertEqual(result.error_message, "Invalid input data provided")
        
        # Verify no repositories were called
        self.unit_of_work.guardians.get_by_id.assert_not_called()
        self.unit_of_work.bookings.get_by_id.assert_not_called()
        self.unit_of_work.bookings.save.assert_not_called()
    
    def test_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Configure the booking repository's save method to raise an exception
        self.unit_of_work.bookings.save = Mock(side_effect=Exception("Database error"))
        
        # Create valid input DTO
        input_dto = LinkBookingsToGuardiansInputDTO(
            guardian_id=1,
            booking_ids=[1, 2]
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.linked_booking_ids)
        self.assertEqual(result.error_message, "Failed to link bookings to guardian: Database error")
        
        # Verify transaction was rolled back
        self.assertTrue(self.unit_of_work.entered)
        self.assertFalse(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
        self.assertTrue(self.unit_of_work.rollback_called)


if __name__ == '__main__':
    unittest.main() 