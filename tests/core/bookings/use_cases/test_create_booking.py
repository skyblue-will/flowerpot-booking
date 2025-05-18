import unittest
from datetime import date, time
from unittest.mock import Mock, patch

from core.bookings.BookingEntity import BookingEntity
from core.bookings.use_cases.CreateBooking import (
    CreateBookingInputDTO,
    CreateBookingOutputDTO,
    CreateBookingUseCase
)
from core.guardians.GuardianEntity import GuardianEntity
from core.workshops.WorkshopEntity import WorkshopEntity
from core.unit_of_work import UnitOfWork
from core.memory_unit_of_work import InMemoryUnitOfWork


class MockUnitOfWork(UnitOfWork):
    """
    Mock UnitOfWork for testing the CreateBooking use case.
    """
    def __init__(self, workshop_exists=True, has_family_capacity=True, has_child_capacity=True, should_fail=False):
        self._workshops = Mock()
        self._bookings = Mock()
        self._guardians = Mock()
        
        # Configure workshop repository mock
        self._workshop = None
        if workshop_exists:
            self._workshop = Mock(spec=WorkshopEntity)
            self._workshop.id = 1
            self._workshop.has_family_capacity.return_value = has_family_capacity
            self._workshop.current_children = 0
            self._workshop.max_children = 20 if has_child_capacity else 1
            self._workshop.add_family.return_value = True
        
        self._workshops.get_by_id.return_value = self._workshop
        
        # Configure guardian repository mock
        self._guardian = Mock(spec=GuardianEntity)
        self._guardian.id = 1
        self._guardians.save.return_value = self._guardian
        
        # Configure booking repository mock
        if should_fail:
            self._bookings.save.side_effect = Exception("Mock repository failure")
        else:
            self._booking = Mock(spec=BookingEntity)
            self._booking.id = 1
            self._bookings.save.return_value = self._booking
        
        # Transaction tracking
        self.commit_called = False
        self.rollback_called = False
        self.entered = False
        self.exited = False
    
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
        self.entered = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        if exc_type:
            self.rollback()
    
    def commit(self):
        self.commit_called = True
    
    def rollback(self):
        self.rollback_called = True


class TestCreateBookingUseCase(unittest.TestCase):
    """
    Test the CreateBooking use case.
    """
    
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self.unit_of_work = MockUnitOfWork()
        self.use_case = CreateBookingUseCase(self.unit_of_work)
        
        # Create a valid input DTO for testing
        self.valid_input = CreateBookingInputDTO(
            workshop_id=1,
            guardian_name="Test Guardian",
            guardian_email="test@example.com",
            guardian_phone="1234567890",
            guardian_postcode="12345",
            children=[
                {"name": "Child 1", "age": 5},
                {"name": "Child 2", "age": 7}
            ]
        )
    
    def test_create_booking_success(self):
        """
        Test creating a booking successfully.
        """
        # Execute the use case
        result = self.use_case.execute(self.valid_input)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertIsNotNone(result.booking_id)
        self.assertEqual(result.booking_id, 1)
        self.assertIsNone(result.error_message)
        
        # Verify the guardian was created
        self.unit_of_work.guardians.save.assert_called_once()
        
        # Verify the booking was created
        self.unit_of_work.bookings.save.assert_called_once()
        
        # Verify the workshop was updated
        self.unit_of_work.workshops.save.assert_called_once()
        self.unit_of_work._workshop.add_family.assert_called_once()
        
        # Verify transaction was managed correctly
        self.assertTrue(self.unit_of_work.entered)
        self.assertTrue(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
        self.assertFalse(self.unit_of_work.rollback_called)
    
    def test_workshop_not_found(self):
        """
        Test handling when workshop is not found.
        """
        # Create a unit of work that will return no workshop
        no_workshop_uow = MockUnitOfWork(workshop_exists=False)
        no_workshop_use_case = CreateBookingUseCase(no_workshop_uow)
        
        # Execute the use case
        result = no_workshop_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.booking_id)
        self.assertIn("not found", result.error_message)
        
        # Verify no entities were created or updated
        no_workshop_uow.guardians.save.assert_not_called()
        no_workshop_uow.bookings.save.assert_not_called()
    
    def test_no_family_capacity(self):
        """
        Test handling when there is no family capacity left.
        """
        # Create a unit of work that will return a workshop with no family capacity
        no_capacity_uow = MockUnitOfWork(has_family_capacity=False)
        no_capacity_use_case = CreateBookingUseCase(no_capacity_uow)
        
        # Execute the use case
        result = no_capacity_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.booking_id)
        self.assertIn("family capacity", result.error_message)
        
        # Verify no entities were created or updated
        no_capacity_uow.guardians.save.assert_not_called()
        no_capacity_uow.bookings.save.assert_not_called()
    
    def test_no_child_capacity(self):
        """
        Test handling when there is no child capacity left.
        """
        # Create a unit of work that will return a workshop with no child capacity
        no_capacity_uow = MockUnitOfWork(has_child_capacity=False)
        no_capacity_use_case = CreateBookingUseCase(no_capacity_uow)
        
        # Execute the use case
        result = no_capacity_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.booking_id)
        self.assertIn("child capacity", result.error_message)
        
        # Verify no entities were created or updated
        no_capacity_uow.guardians.save.assert_not_called()
        no_capacity_uow.bookings.save.assert_not_called()
    
    def test_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a unit of work that will fail on booking save
        failing_uow = MockUnitOfWork(should_fail=True)
        failing_use_case = CreateBookingUseCase(failing_uow)
        
        # Execute the use case
        result = failing_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.booking_id)
        self.assertIn("Failed to create booking", result.error_message)
    
    def test_input_validation_failure(self):
        """
        Test that validation fails for invalid input.
        """
        # Create different invalid inputs to test validation
        invalid_inputs = [
            # Empty guardian name
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[{"name": "Child 1", "age": 5}]
            ),
            # Invalid email
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="invalid-email",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[{"name": "Child 1", "age": 5}]
            ),
            # Empty phone
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="",
                guardian_postcode="12345",
                children=[{"name": "Child 1", "age": 5}]
            ),
            # Empty postcode
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="",
                children=[{"name": "Child 1", "age": 5}]
            ),
            # No children
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[]
            ),
            # Child with empty name
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[{"name": "", "age": 5}]
            ),
            # Child with invalid age
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[{"name": "Child 1", "age": 0}]
            ),
            # Child with missing age field
            CreateBookingInputDTO(
                workshop_id=1,
                guardian_name="Test Guardian",
                guardian_email="test@example.com",
                guardian_phone="1234567890",
                guardian_postcode="12345",
                children=[{"name": "Child 1"}]
            ),
        ]
        
        # Test each invalid input
        for input_dto in invalid_inputs:
            result = self.use_case.execute(input_dto)
            
            # Verify validation failure
            self.assertFalse(result.success)
            self.assertIsNone(result.booking_id)
            self.assertEqual(result.error_message, "Invalid booking data provided")
            
            # Verify no transaction was started
            self.assertFalse(self.unit_of_work.entered)
    
    def test_with_real_in_memory_unit_of_work(self):
        """
        Integration test using the real InMemoryUnitOfWork.
        """
        # Create a real InMemoryUnitOfWork
        real_uow = InMemoryUnitOfWork()
        
        # Create a test workshop
        workshop = WorkshopEntity(
            title="Test Workshop",
            date=date(2023, 1, 1),
            time=time(10, 0),
            location="Test Location",
            max_families=2,
            max_children=5,
            current_families=0,
            current_children=0
        )
        real_uow.workshops.save(workshop)
        
        # Create the use case
        real_use_case = CreateBookingUseCase(real_uow)
        
        # Execute the use case
        result = real_use_case.execute(self.valid_input)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNotNone(result.booking_id)
        
        # Verify all entities were persisted
        booking = real_uow.bookings.get_by_id(result.booking_id)
        self.assertIsNotNone(booking)
        
        guardian = real_uow.guardians.get_by_id(booking.guardian_id)
        self.assertIsNotNone(guardian)
        self.assertEqual(guardian.name, "Test Guardian")
        
        workshop = real_uow.workshops.get_by_id(booking.workshop_id)
        self.assertIsNotNone(workshop)
        self.assertEqual(workshop.current_families, 1)
        self.assertEqual(workshop.current_children, 2)


if __name__ == "__main__":
    unittest.main() 