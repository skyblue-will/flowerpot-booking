import unittest
from datetime import date, time
from unittest.mock import Mock, MagicMock

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.CreateWorkshop import (
    CreateWorkshopInputDTO,
    CreateWorkshopOutputDTO,
    CreateWorkshopUseCase
)
from core.unit_of_work import UnitOfWork
from core.memory_unit_of_work import InMemoryUnitOfWork


class MockUnitOfWork(UnitOfWork):
    """
    Mock UnitOfWork for testing the CreateWorkshop use case.
    """
    def __init__(self, should_fail=False):
        self._workshops = Mock()
        self._workshops.save = Mock()
        self._bookings = Mock()
        self._guardians = Mock()
        
        # Configure workshop repository mock
        if should_fail:
            self._workshops.save.side_effect = Exception("Mock repository failure")
        else:
            def save_side_effect(workshop):
                workshop_copy = WorkshopEntity(
                    id=1,  # Mocked ID assignment
                    title=workshop.title,
                    date=workshop.date,
                    time=workshop.time,
                    location=workshop.location,
                    max_families=workshop.max_families,
                    max_children=workshop.max_children,
                    current_families=workshop.current_families,
                    current_children=workshop.current_children
                )
                return workshop_copy
            
            self._workshops.save.side_effect = save_side_effect
        
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


class TestCreateWorkshopUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self.unit_of_work = MockUnitOfWork()
        self.use_case = CreateWorkshopUseCase(self.unit_of_work)
        
        # Create a valid input DTO for testing
        self.valid_input = CreateWorkshopInputDTO(
            title="Test Workshop",
            workshop_date=date(2023, 12, 1),
            workshop_time=time(14, 0),
            location="Test Location",
            max_families=10,
            max_children=20
        )
    
    def test_create_workshop_success(self):
        """
        Test creating a workshop successfully.
        """
        # Execute the use case
        result = self.use_case.execute(self.valid_input)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertIsNotNone(result.workshop_id)
        self.assertEqual(result.workshop_id, 1)
        self.assertIsNone(result.error_message)
        
        # Verify the workshop was saved and transaction was managed correctly
        self.unit_of_work.workshops.save.assert_called_once()
        saved_workshop = self.unit_of_work.workshops.save.call_args[0][0]
        
        # Check that the saved workshop has the correct properties
        self.assertEqual(saved_workshop.title, "Test Workshop")
        self.assertEqual(saved_workshop.date, date(2023, 12, 1))
        self.assertEqual(saved_workshop.time, time(14, 0))
        self.assertEqual(saved_workshop.location, "Test Location")
        self.assertEqual(saved_workshop.max_families, 10)
        self.assertEqual(saved_workshop.max_children, 20)
        self.assertEqual(saved_workshop.current_families, 0)
        self.assertEqual(saved_workshop.current_children, 0)
        
        # Verify transaction management
        self.assertTrue(self.unit_of_work.entered)
        self.assertTrue(self.unit_of_work.commit_called)
        self.assertTrue(self.unit_of_work.exited)
        self.assertFalse(self.unit_of_work.rollback_called)
    
    def test_create_workshop_validation_failure(self):
        """
        Test that validation fails for invalid input.
        """
        # Create invalid inputs to test validation
        invalid_inputs = [
            # Empty title
            CreateWorkshopInputDTO(
                title="",
                workshop_date=date(2023, 12, 1),
                workshop_time=time(14, 0),
                location="Test Location",
                max_families=10,
                max_children=20
            ),
            # Empty location
            CreateWorkshopInputDTO(
                title="Test Workshop",
                workshop_date=date(2023, 12, 1),
                workshop_time=time(14, 0),
                location="",
                max_families=10,
                max_children=20
            ),
            # Zero max families
            CreateWorkshopInputDTO(
                title="Test Workshop",
                workshop_date=date(2023, 12, 1),
                workshop_time=time(14, 0),
                location="Test Location",
                max_families=0,
                max_children=20
            ),
            # Zero max children
            CreateWorkshopInputDTO(
                title="Test Workshop",
                workshop_date=date(2023, 12, 1),
                workshop_time=time(14, 0),
                location="Test Location",
                max_families=10,
                max_children=0
            ),
        ]
        
        # Test each invalid input
        for invalid_input in invalid_inputs:
            result = self.use_case.execute(invalid_input)
            
            # Verify validation failure
            self.assertFalse(result.success)
            self.assertIsNone(result.workshop_id)
            self.assertEqual(result.error_message, "Invalid workshop data provided")
            
            # Verify save was not called and no transaction was started
            self.unit_of_work.workshops.save.assert_not_called()
            self.assertFalse(self.unit_of_work.entered)
            self.assertFalse(self.unit_of_work.commit_called)
            
            # Reset the mock for the next test
            self.unit_of_work.workshops.save.reset_mock()
    
    def test_create_workshop_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a unit of work that will fail on save
        failing_unit_of_work = MockUnitOfWork(should_fail=True)
        failing_use_case = CreateWorkshopUseCase(failing_unit_of_work)
        
        # Execute the use case
        result = failing_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertTrue(result.error_message.startswith("Failed to create workshop:"))
        
        # Verify transaction management - should have entered but not committed
        self.assertTrue(failing_unit_of_work.entered)
        self.assertFalse(failing_unit_of_work.commit_called)
        self.assertTrue(failing_unit_of_work.exited)
    
    def test_with_real_in_memory_unit_of_work(self):
        """
        Integration test using the real InMemoryUnitOfWork.
        """
        # Create a real InMemoryUnitOfWork
        real_uow = InMemoryUnitOfWork()
        real_use_case = CreateWorkshopUseCase(real_uow)
        
        # Execute the use case
        result = real_use_case.execute(self.valid_input)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNotNone(result.workshop_id)
        
        # Verify the workshop was persisted
        saved_workshop = real_uow.workshops.get_by_id(result.workshop_id)
        self.assertIsNotNone(saved_workshop)
        self.assertEqual(saved_workshop.title, "Test Workshop")


if __name__ == "__main__":
    unittest.main() 