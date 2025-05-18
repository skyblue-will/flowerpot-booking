import unittest
from datetime import date, time
from unittest.mock import patch

from core.bookings.BookingEntity import BookingEntity, Child
from core.guardians.GuardianEntity import GuardianEntity
from core.workshops.WorkshopEntity import WorkshopEntity
from core.bookings.use_cases.ViewBookingsForWorkshop import (
    ViewBookingsForWorkshopInputDTO,
    ViewBookingsForWorkshopOutputDTO,
    ViewBookingsForWorkshopUseCase,
    BookingDetails
)
from core.memory_unit_of_work import InMemoryUnitOfWork


class TestViewBookingsForWorkshop(unittest.TestCase):
    """
    Test the ViewBookingsForWorkshop use case with various scenarios.
    """
    
    def setUp(self):
        """Set up common test dependencies"""
        # Create a unit of work with test data
        self.uow = InMemoryUnitOfWork()
        
        # Create test workshops
        self.workshop1 = WorkshopEntity(
            title="Workshop 1",
            date=date(2023, 1, 1),
            time=time(10, 0),
            location="Location 1",
            max_families=5,
            max_children=10,
            current_families=2,
            current_children=3
        )
        self.workshop1 = self.uow.workshops.save(self.workshop1)
        
        self.workshop2 = WorkshopEntity(
            title="Workshop 2",
            date=date(2023, 2, 1),
            time=time(14, 0),
            location="Location 2",
            max_families=3,
            max_children=6,
            current_families=1,
            current_children=2
        )
        self.workshop2 = self.uow.workshops.save(self.workshop2)
        
        # Create test guardians
        self.guardian1 = GuardianEntity(
            name="Guardian 1",
            email="guardian1@example.com",
            phone="1111111111",
            postcode="12345"
        )
        self.guardian1 = self.uow.guardians.save(self.guardian1)
        
        self.guardian2 = GuardianEntity(
            name="Guardian 2",
            email="guardian2@example.com",
            phone="2222222222",
            postcode="23456"
        )
        self.guardian2 = self.uow.guardians.save(self.guardian2)
        
        # Create bookings for the first workshop
        self.booking1 = BookingEntity(
            workshop_id=self.workshop1.id,
            guardian_id=self.guardian1.id
        )
        self.booking1.add_child("Child 1", 5)
        self.booking1.add_child("Child 2", 7)
        self.booking1 = self.uow.bookings.save(self.booking1)
        
        self.booking2 = BookingEntity(
            workshop_id=self.workshop1.id,
            guardian_id=self.guardian2.id
        )
        self.booking2.add_child("Child 3", 6)
        self.booking2 = self.uow.bookings.save(self.booking2)
        
        # Create a booking for the second workshop
        self.booking3 = BookingEntity(
            workshop_id=self.workshop2.id,
            guardian_id=self.guardian1.id
        )
        self.booking3.add_child("Child 4", 8)
        self.booking3 = self.uow.bookings.save(self.booking3)
        
        # Initialize the use case
        self.use_case = ViewBookingsForWorkshopUseCase(self.uow)
    
    def test_admin_views_all_bookings(self):
        """Test that an admin can view all bookings for a workshop"""
        # Create input for admin viewing workshop1
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=self.workshop1.id,
            viewer_is_admin=True
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        
        # Verify all bookings for workshop1 are returned
        self.assertEqual(len(result.bookings), 2)
        
        # Check booking details
        booking_ids = [b.booking_id for b in result.bookings]
        guardian_names = [b.guardian_name for b in result.bookings]
        
        self.assertIn(self.booking1.id, booking_ids)
        self.assertIn(self.booking2.id, booking_ids)
        self.assertIn("Guardian 1", guardian_names)
        self.assertIn("Guardian 2", guardian_names)
        
        # Verify children are included
        for booking in result.bookings:
            if booking.booking_id == self.booking1.id:
                self.assertEqual(len(booking.children), 2)
            elif booking.booking_id == self.booking2.id:
                self.assertEqual(len(booking.children), 1)
    
    def test_guardian_views_own_bookings(self):
        """Test that a guardian can only view their own bookings"""
        # Create input for guardian1 viewing workshop1
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=self.workshop1.id,
            viewer_id=self.guardian1.id,
            viewer_is_admin=False
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        
        # Verify only guardian1's booking for workshop1 is returned
        self.assertEqual(len(result.bookings), 1)
        self.assertEqual(result.bookings[0].booking_id, self.booking1.id)
        self.assertEqual(result.bookings[0].guardian_name, "Guardian 1")
    
    def test_nonexistent_workshop(self):
        """Test handling of non-existent workshop"""
        # Create input with non-existent workshop ID
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=9999,
            viewer_is_admin=True
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("not found", result.error_message)
    
    def test_workshop_with_no_bookings(self):
        """Test handling of a workshop with no bookings"""
        # Create a new workshop with no bookings
        empty_workshop = WorkshopEntity(
            title="Empty Workshop",
            date=date(2023, 3, 1),
            time=time(15, 0),
            location="Location 3",
            max_families=5,
            max_children=10,
            current_families=0,
            current_children=0
        )
        empty_workshop = self.uow.workshops.save(empty_workshop)
        
        # Create input for viewing the empty workshop
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=empty_workshop.id,
            viewer_is_admin=True
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success but empty bookings list
        self.assertTrue(result.success)
        self.assertEqual(len(result.bookings), 0)
    
    def test_cancelled_bookings_included(self):
        """Test that cancelled bookings are included in the results"""
        # Cancel one of the bookings
        self.booking1.mark_as_cancelled("Test cancellation")
        self.uow.bookings.save(self.booking1)
        
        # Create input for admin viewing workshop1
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=self.workshop1.id,
            viewer_is_admin=True
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        
        # Verify all bookings including cancelled ones are returned
        self.assertEqual(len(result.bookings), 2)
        
        # Check for cancelled status
        for booking in result.bookings:
            if booking.booking_id == self.booking1.id:
                self.assertEqual(booking.status, "cancelled")
            else:
                self.assertEqual(booking.status, "active")
    
    def test_guardian_viewing_other_guardians_bookings(self):
        """Test that a guardian cannot view other guardians' bookings"""
        # Guardian 2 tries to view all bookings for workshop1
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=self.workshop1.id,
            viewer_id=self.guardian2.id,
            viewer_is_admin=False
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        
        # Verify only guardian2's booking is returned
        self.assertEqual(len(result.bookings), 1)
        self.assertEqual(result.bookings[0].booking_id, self.booking2.id)
        self.assertEqual(result.bookings[0].guardian_name, "Guardian 2")
    
    def test_error_handling(self):
        """Test that exceptions are properly handled"""
        # Create valid input
        input_dto = ViewBookingsForWorkshopInputDTO(
            workshop_id=self.workshop1.id,
            viewer_is_admin=True
        )
        
        # Create a side effect to simulate an error
        def get_all_side_effect():
            raise ValueError("Simulated database error")
        
        # Patch the bookings repository's get_all method
        with patch.object(self.uow.bookings, 'get_all', side_effect=get_all_side_effect):
            # Execute the use case
            result = self.use_case.execute(input_dto)
            
            # Verify error handling
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Error retrieving bookings", result.error_message)


if __name__ == "__main__":
    unittest.main() 