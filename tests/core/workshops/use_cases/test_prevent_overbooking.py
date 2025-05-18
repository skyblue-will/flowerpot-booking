import unittest
from typing import Optional

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.PreventOverbooking import (
    PreventOverbookingInputDTO,
    PreventOverbookingOutputDTO,
    PreventOverbookingUseCase
)


class MockWorkshopRepository:
    """
    Mock repository for testing the PreventOverbooking use case.
    """
    def __init__(self, workshops=None, should_fail=False):
        self.workshops = {w.id: w for w in (workshops or [])}
        self.should_fail = should_fail
    
    def get_by_id(self, workshop_id) -> Optional[WorkshopEntity]:
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        return self.workshops.get(workshop_id)


class TestPreventOverbookingUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Create test workshops with different capacities
        self.workshop_with_capacity = WorkshopEntity(
            id=1,
            title="Workshop With Capacity",
            date=None,  # Not relevant for this test
            time=None,  # Not relevant for this test
            location="Test Location",
            max_families=10,
            max_children=20,
            current_families=5,
            current_children=10
        )
        
        self.workshop_full_families = WorkshopEntity(
            id=2,
            title="Workshop Full Families",
            date=None,
            time=None,
            location="Test Location 2",
            max_families=5,
            max_children=20,
            current_families=5,  # Full
            current_children=10
        )
        
        self.workshop_full_children = WorkshopEntity(
            id=3,
            title="Workshop Full Children",
            date=None,
            time=None,
            location="Test Location 3",
            max_families=10,
            max_children=15,
            current_families=5,
            current_children=15  # Full
        )
        
        self.workshop_almost_full = WorkshopEntity(
            id=4,
            title="Workshop Almost Full",
            date=None,
            time=None,
            location="Test Location 4",
            max_families=10,
            max_children=20,
            current_families=9,  # Only 1 slot left
            current_children=18  # Only 2 slots left
        )
        
        # Create repository with test workshops
        self.workshop_repository = MockWorkshopRepository(workshops=[
            self.workshop_with_capacity,
            self.workshop_full_families,
            self.workshop_full_children,
            self.workshop_almost_full
        ])
        
        # Create use case
        self.use_case = PreventOverbookingUseCase(self.workshop_repository)
    
    def test_has_capacity_success(self):
        """
        Test a booking request when there is sufficient capacity.
        """
        # Create input for a valid booking request
        input_dto = PreventOverbookingInputDTO(
            workshop_id=1,
            requested_family_slots=2,
            requested_child_slots=4
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.has_capacity)
        self.assertEqual(result.remaining_family_slots, 5)  # 10 max - 5 used
        self.assertEqual(result.remaining_child_slots, 10)  # 20 max - 10 used
        self.assertIsNone(result.error_message)
    
    def test_not_enough_family_slots(self):
        """
        Test a booking request when there are not enough family slots.
        """
        # Create input requesting more family slots than available
        input_dto = PreventOverbookingInputDTO(
            workshop_id=2,  # workshop_full_families
            requested_family_slots=1,  # But 0 available
            requested_child_slots=2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.has_capacity)
        self.assertEqual(result.remaining_family_slots, 0)  # 5 max - 5 used
        self.assertEqual(result.remaining_child_slots, 10)  # 20 max - 10 used
        self.assertTrue("Not enough family slots" in result.error_message)
    
    def test_not_enough_child_slots(self):
        """
        Test a booking request when there are not enough child slots.
        """
        # Create input requesting more child slots than available
        input_dto = PreventOverbookingInputDTO(
            workshop_id=3,  # workshop_full_children
            requested_family_slots=1,
            requested_child_slots=1  # But 0 available
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.has_capacity)
        self.assertEqual(result.remaining_family_slots, 5)  # 10 max - 5 used
        self.assertEqual(result.remaining_child_slots, 0)  # 15 max - 15 used
        self.assertTrue("Not enough child slots" in result.error_message)
    
    def test_exact_remaining_capacity(self):
        """
        Test a booking request that uses the exact remaining capacity.
        """
        # Create input that uses all remaining slots
        input_dto = PreventOverbookingInputDTO(
            workshop_id=4,  # workshop_almost_full
            requested_family_slots=1,  # Exact remaining amount
            requested_child_slots=2    # Exact remaining amount
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertTrue(result.has_capacity)
        self.assertEqual(result.remaining_family_slots, 1)  # 10 max - 9 used
        self.assertEqual(result.remaining_child_slots, 2)   # 20 max - 18 used
        self.assertIsNone(result.error_message)
    
    def test_exceeding_capacity(self):
        """
        Test a booking request that exceeds the remaining capacity.
        """
        # Create input that exceeds remaining capacity
        input_dto = PreventOverbookingInputDTO(
            workshop_id=4,  # workshop_almost_full
            requested_family_slots=2,  # More than 1 remaining
            requested_child_slots=1
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.has_capacity)
        self.assertEqual(result.remaining_family_slots, 1)  # 10 max - 9 used
        self.assertEqual(result.remaining_child_slots, 2)   # 20 max - 18 used
        self.assertTrue("Not enough family slots" in result.error_message)
    
    def test_workshop_not_found(self):
        """
        Test a booking request for a non-existent workshop.
        """
        # Create input with non-existent workshop ID
        input_dto = PreventOverbookingInputDTO(
            workshop_id=999,
            requested_family_slots=1,
            requested_child_slots=2
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.has_capacity)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertEqual(result.error_message, "Workshop with ID 999 not found")
    
    def test_invalid_input(self):
        """
        Test validation failures.
        """
        # Test cases with invalid inputs
        invalid_inputs = [
            # Invalid workshop ID
            PreventOverbookingInputDTO(
                workshop_id=0,
                requested_family_slots=1,
                requested_child_slots=2
            ),
            # Invalid family slots
            PreventOverbookingInputDTO(
                workshop_id=1,
                requested_family_slots=0,
                requested_child_slots=2
            ),
            # Invalid child slots
            PreventOverbookingInputDTO(
                workshop_id=1,
                requested_family_slots=1,
                requested_child_slots=0
            )
        ]
        
        for invalid_input in invalid_inputs:
            result = self.use_case.execute(invalid_input)
            
            # Assertions
            self.assertFalse(result.has_capacity)
            self.assertIsNone(result.remaining_family_slots)
            self.assertIsNone(result.remaining_child_slots)
            self.assertEqual(result.error_message, "Invalid booking request data provided")
    
    def test_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a repository that will fail
        failing_repository = MockWorkshopRepository(
            workshops=[self.workshop_with_capacity], 
            should_fail=True
        )
        
        failing_use_case = PreventOverbookingUseCase(failing_repository)
        
        # Create valid input
        input_dto = PreventOverbookingInputDTO(
            workshop_id=1,
            requested_family_slots=1,
            requested_child_slots=2
        )
        
        # Execute the use case
        result = failing_use_case.execute(input_dto)
        
        # Assertions
        self.assertFalse(result.has_capacity)
        self.assertIsNone(result.remaining_family_slots)
        self.assertIsNone(result.remaining_child_slots)
        self.assertTrue(result.error_message.startswith("Failed to check workshop capacity:"))


if __name__ == "__main__":
    unittest.main() 