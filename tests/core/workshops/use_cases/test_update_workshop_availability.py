import unittest
from typing import Optional

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.UpdateWorkshopAvailability import (
    UpdateWorkshopAvailabilityInputDTO,
    UpdateWorkshopAvailabilityOutputDTO,
    UpdateWorkshopAvailabilityUseCase
)


class MockWorkshopRepository:
    """
    Mock repository for testing the UpdateWorkshopAvailability use case.
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


class TestUpdateWorkshopAvailabilityUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Create a test workshop
        self.workshop = WorkshopEntity(
            id=1,
            title="Test Workshop",
            date=None,  # Not relevant for this test
            time=None,  # Not relevant for this test
            location="Test Location",
            max_families=10,
            max_children=20,
            current_families=5,
            current_children=10
        )
        
        # Create repository with test workshop
        self.workshop_repository = MockWorkshopRepository(workshops=[self.workshop])
        
        # Create use case
        self.use_case = UpdateWorkshopAvailabilityUseCase(self.workshop_repository)
    
    def test_reduce_availability_success(self):
        """
        Test reducing workshop availability (booking made) successfully.
        """
        # Create input to reduce availability (booking made)
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=-1,  # Reduce by 1
            child_slots_change=-2    # Reduce by 2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.workshop_id, 1)
        self.assertEqual(result.remaining_family_slots, 4)  # 10 max - 6 used
        self.assertEqual(result.remaining_child_slots, 8)   # 20 max - 12 used
        self.assertIsNone(result.error_message)
        
        # Verify workshop state was updated correctly
        updated_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(updated_workshop.current_families, 6)  # 5 + 1
        self.assertEqual(updated_workshop.current_children, 12)  # 10 + 2
    
    def test_increase_availability_success(self):
        """
        Test increasing workshop availability (booking cancelled) successfully.
        """
        # Create input to increase availability (booking cancelled)
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=1,   # Increase by 1
            child_slots_change=3     # Increase by 3
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.workshop_id, 1)
        self.assertEqual(result.remaining_family_slots, 6)  # 10 max - 4 used
        self.assertEqual(result.remaining_child_slots, 13)  # 20 max - 7 used
        self.assertIsNone(result.error_message)
        
        # Verify workshop state was updated correctly
        updated_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(updated_workshop.current_families, 4)  # 5 - 1
        self.assertEqual(updated_workshop.current_children, 7)  # 10 - 3
    
    def test_workshop_not_found(self):
        """
        Test updating availability for a non-existent workshop.
        """
        # Create input with non-existent workshop ID
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=999,
            family_slots_change=-1,
            child_slots_change=-2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertEqual(result.error_message, "Workshop with ID 999 not found")
    
    def test_reduce_beyond_capacity(self):
        """
        Test reducing availability beyond capacity (overbooking).
        """
        # Try to reduce by more slots than available
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=-6,  # Would result in 11 used (max is 10)
            child_slots_change=-2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertEqual(
            result.error_message,
            "Not enough family slots available (requested: 11, max: 10)"
        )
        
        # Verify workshop state was not changed
        unchanged_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(unchanged_workshop.current_families, 5)
        self.assertEqual(unchanged_workshop.current_children, 10)
    
    def test_increase_beyond_zero(self):
        """
        Test increasing availability beyond zero (negative usage).
        """
        # Try to increase by more slots than currently used
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=6,  # Would result in -1 used
            child_slots_change=1
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertEqual(
            result.error_message,
            "Cannot have negative family slots used (-1)"
        )
        
        # Verify workshop state was not changed
        unchanged_workshop = self.workshop_repository.get_by_id(1)
        self.assertEqual(unchanged_workshop.current_families, 5)
        self.assertEqual(unchanged_workshop.current_children, 10)
    
    def test_validation_failure(self):
        """
        Test input validation failures.
        """
        # Invalid workshop ID
        invalid_id_input = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=0,
            family_slots_change=-1,
            child_slots_change=-2
        )
        
        result = self.use_case.execute(invalid_id_input)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Invalid input data provided")
        
        # No actual change requested
        no_change_input = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=0,
            child_slots_change=0
        )
        
        result = self.use_case.execute(no_change_input)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Invalid input data provided")
    
    def test_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a repository that will fail
        failing_repository = MockWorkshopRepository(
            workshops=[self.workshop], 
            should_fail=True
        )
        
        failing_use_case = UpdateWorkshopAvailabilityUseCase(failing_repository)
        
        # Create valid input
        input_dto = UpdateWorkshopAvailabilityInputDTO(
            workshop_id=1,
            family_slots_change=-1,
            child_slots_change=-2
        )
        
        # Execute the use case
        result = failing_use_case.execute(input_dto)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.workshop_id)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertTrue(result.error_message.startswith("Failed to update workshop availability:"))


if __name__ == "__main__":
    unittest.main() 