import unittest
from datetime import date, time
from unittest.mock import Mock

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.CreateWorkshop import (
    CreateWorkshopInputDTO,
    CreateWorkshopOutputDTO,
    CreateWorkshopUseCase
)


class MockWorkshopRepository:
    """
    Mock repository for testing the CreateWorkshop use case.
    """
    def __init__(self, should_fail=False):
        self.workshops = []
        self.next_id = 1
        self.should_fail = should_fail
    
    def save(self, workshop):
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        # Simulate DB saving by assigning an ID
        workshop.id = self.next_id
        self.next_id += 1
        
        # Store the workshop
        self.workshops.append(workshop)
        
        return workshop


class TestCreateWorkshopUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self.repository = MockWorkshopRepository()
        self.use_case = CreateWorkshopUseCase(self.repository)
        
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
        
        # Verify the workshop was saved to the repository
        self.assertEqual(len(self.repository.workshops), 1)
        saved_workshop = self.repository.workshops[0]
        
        # Check that the saved workshop has the correct properties
        self.assertEqual(saved_workshop.title, "Test Workshop")
        self.assertEqual(saved_workshop.date, date(2023, 12, 1))
        self.assertEqual(saved_workshop.time, time(14, 0))
        self.assertEqual(saved_workshop.location, "Test Location")
        self.assertEqual(saved_workshop.max_families, 10)
        self.assertEqual(saved_workshop.max_children, 20)
        self.assertEqual(saved_workshop.current_families, 0)
        self.assertEqual(saved_workshop.current_children, 0)
    
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
            
            # Verify nothing was saved to the repository
            self.assertEqual(len(self.repository.workshops), 0)
    
    def test_create_workshop_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a repository that will fail on save
        failing_repository = MockWorkshopRepository(should_fail=True)
        failing_use_case = CreateWorkshopUseCase(failing_repository)
        
        # Execute the use case
        result = failing_use_case.execute(self.valid_input)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertTrue(result.error_message.startswith("Failed to create workshop:"))


if __name__ == "__main__":
    unittest.main() 