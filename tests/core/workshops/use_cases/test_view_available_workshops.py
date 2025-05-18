import unittest
from datetime import date, time
from typing import List

from core.workshops.WorkshopEntity import WorkshopEntity
from core.workshops.use_cases.ViewAvailableWorkshops import (
    ViewAvailableWorkshopsInputDTO,
    ViewAvailableWorkshopsOutputDTO,
    ViewAvailableWorkshopsUseCase,
    WorkshopSummaryDTO
)


class MockWorkshopRepository:
    """
    Mock repository for testing the ViewAvailableWorkshops use case.
    """
    def __init__(self, workshops=None, should_fail=False):
        self.workshops = workshops or []
        self.should_fail = should_fail
    
    def get_all(self) -> List[WorkshopEntity]:
        """
        Return all workshops from the repository.
        """
        if self.should_fail:
            raise Exception("Mock repository failure")
        
        return self.workshops


class TestViewAvailableWorkshopsUseCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Create test workshops
        self.past_workshop = WorkshopEntity(
            id=1,
            title="Past Workshop",
            date=date(2022, 1, 1),
            time=time(10, 0),
            location="Test Location 1",
            max_families=10,
            max_children=20,
            current_families=5,
            current_children=10
        )
        
        self.future_workshop1 = WorkshopEntity(
            id=2,
            title="Future Workshop 1",
            date=date(2023, 6, 1),
            time=time(14, 0),
            location="Test Location 2",
            max_families=15,
            max_children=30,
            current_families=3,
            current_children=6
        )
        
        self.future_workshop2 = WorkshopEntity(
            id=3,
            title="Future Workshop 2",
            date=date(2023, 5, 15),  # Earlier date than future_workshop1
            time=time(9, 0),
            location="Test Location 3",
            max_families=8,
            max_children=16,
            current_families=8,  # Full
            current_children=12
        )
        
        # Create repository with test workshops
        self.workshops = [self.past_workshop, self.future_workshop1, self.future_workshop2]
        self.repository = MockWorkshopRepository(workshops=self.workshops)
        
        # Create use case
        self.use_case = ViewAvailableWorkshopsUseCase(self.repository)
        
        # Set current date for filtering
        self.current_date = date(2023, 1, 1)
        
        # Create input DTO
        self.input_dto = ViewAvailableWorkshopsInputDTO(current_date=self.current_date)
    
    def test_view_available_workshops_success(self):
        """
        Test retrieving available workshops successfully.
        """
        # Execute the use case
        result = self.use_case.execute(self.input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertIsNotNone(result.workshops)
        self.assertEqual(len(result.workshops), 2)  # Should only return future workshops
        self.assertIsNone(result.error_message)
        
        # Verify workshops are sorted by date
        self.assertEqual(result.workshops[0].id, 3)  # future_workshop2 comes first (earlier date)
        self.assertEqual(result.workshops[1].id, 2)  # future_workshop1 comes second
        
        # Verify workshop data is correct
        workshop1 = result.workshops[0]  # future_workshop2
        self.assertEqual(workshop1.id, 3)
        self.assertEqual(workshop1.title, "Future Workshop 2")
        self.assertEqual(workshop1.workshop_date, date(2023, 5, 15))
        self.assertEqual(workshop1.workshop_time, time(9, 0))
        self.assertEqual(workshop1.location, "Test Location 3")
        self.assertEqual(workshop1.remaining_family_slots, 0)  # Full
        self.assertEqual(workshop1.remaining_child_slots, 4)
        
        workshop2 = result.workshops[1]  # future_workshop1
        self.assertEqual(workshop2.id, 2)
        self.assertEqual(workshop2.title, "Future Workshop 1")
        self.assertEqual(workshop2.remaining_family_slots, 12)
        self.assertEqual(workshop2.remaining_child_slots, 24)
    
    def test_view_available_workshops_no_upcoming(self):
        """
        Test when there are no upcoming workshops.
        """
        # Set up repository with only past workshops
        past_only_repository = MockWorkshopRepository(workshops=[self.past_workshop])
        past_only_use_case = ViewAvailableWorkshopsUseCase(past_only_repository)
        
        # Execute the use case
        result = past_only_use_case.execute(self.input_dto)
        
        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(len(result.workshops), 0)  # Should return empty list
    
    def test_view_available_workshops_repository_failure(self):
        """
        Test handling of repository failures.
        """
        # Create a repository that will fail
        failing_repository = MockWorkshopRepository(should_fail=True)
        failing_use_case = ViewAvailableWorkshopsUseCase(failing_repository)
        
        # Execute the use case
        result = failing_use_case.execute(self.input_dto)
        
        # Verify failure handling
        self.assertFalse(result.success)
        self.assertIsNone(result.workshops)
        self.assertTrue(result.error_message.startswith("Failed to retrieve workshops:"))


if __name__ == "__main__":
    unittest.main() 