import unittest
from datetime import date, time
from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import patch

from core.bookings.BookingEntity import BookingEntity, Child
from core.guardians.GuardianEntity import GuardianEntity
from core.workshops.WorkshopEntity import WorkshopEntity
from core.memory_unit_of_work import InMemoryUnitOfWork
from core.unit_of_work import UnitOfWork


@dataclass
class CreateBookingInputDTO:
    """Input DTO for creating a booking"""
    workshop_id: int
    guardian_name: str
    guardian_email: str
    guardian_phone: str
    guardian_postcode: str
    children: List[dict]  # List of child name/age dicts


@dataclass
class CreateBookingOutputDTO:
    """Output DTO for booking creation result"""
    success: bool
    booking_id: Optional[int] = None
    error_message: Optional[str] = None


class CreateBookingUseCase:
    """
    Use case for creating a booking with proper transaction management.
    This demonstrates how multiple repository operations should be
    handled atomically within a single transaction.
    """
    
    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work
    
    def execute(self, input_dto: CreateBookingInputDTO) -> CreateBookingOutputDTO:
        """Execute the use case with transaction management"""
        try:
            # Start a transaction
            with self.unit_of_work:
                # 1. Get the workshop
                workshop = self.unit_of_work.workshops.get_by_id(input_dto.workshop_id)
                if not workshop:
                    return CreateBookingOutputDTO(
                        success=False,
                        error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                    )
                
                # 2. Check workshop capacity
                child_count = len(input_dto.children)
                if not workshop.has_family_capacity():
                    return CreateBookingOutputDTO(
                        success=False,
                        error_message="Workshop has no family capacity left"
                    )
                
                if workshop.current_children + child_count > workshop.max_children:
                    return CreateBookingOutputDTO(
                        success=False,
                        error_message="Workshop has insufficient child capacity"
                    )
                
                # 3. Create or find guardian
                guardian = GuardianEntity(
                    name=input_dto.guardian_name,
                    email=input_dto.guardian_email,
                    phone=input_dto.guardian_phone,
                    postcode=input_dto.guardian_postcode
                )
                saved_guardian = self.unit_of_work.guardians.save(guardian)
                
                # 4. Create booking
                booking = BookingEntity(
                    workshop_id=workshop.id,
                    guardian_id=saved_guardian.id
                )
                
                # 5. Add children to booking
                for child_data in input_dto.children:
                    booking.add_child(child_data['name'], child_data['age'])
                
                saved_booking = self.unit_of_work.bookings.save(booking)
                
                # 6. Update workshop availability
                workshop.add_family()
                workshop.current_children += child_count
                self.unit_of_work.workshops.save(workshop)
                
                # 7. Commit the transaction - all operations succeed or fail together
                self.unit_of_work.commit()
                
                return CreateBookingOutputDTO(
                    success=True,
                    booking_id=saved_booking.id
                )
                
        except Exception as e:
            # Any exception will cause automatic rollback
            return CreateBookingOutputDTO(
                success=False,
                error_message=f"Failed to create booking: {str(e)}"
            )


class TestCreateBookingWithTransaction(unittest.TestCase):
    """
    Test the CreateBooking use case with transaction management.
    """
    
    def setUp(self):
        """Set up test dependencies"""
        # Create a unit of work
        self.uow = InMemoryUnitOfWork()
        
        # Create a test workshop with limited capacity
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
        self.uow.workshops.save(workshop)
        
        # Initialize the use case
        self.use_case = CreateBookingUseCase(self.uow)
        
        # Create valid input data
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
    
    def test_successful_booking_creation(self):
        """Test that a booking can be created successfully with all related entities"""
        # Execute the use case
        result = self.use_case.execute(self.valid_input)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNotNone(result.booking_id)
        
        # Verify all entities were created and linked properly
        booking = self.uow.bookings.get_by_id(result.booking_id)
        guardian = self.uow.guardians.get_by_id(booking.guardian_id)
        workshop = self.uow.workshops.get_by_id(booking.workshop_id)
        
        # Check booking details
        self.assertEqual(booking.child_count(), 2)
        self.assertEqual(booking.workshop_id, 1)
        
        # Check guardian details
        self.assertEqual(guardian.name, "Test Guardian")
        self.assertEqual(guardian.email, "test@example.com")
        
        # Check workshop availability was updated
        self.assertEqual(workshop.current_families, 1)
        self.assertEqual(workshop.current_children, 2)
    
    def test_exceeding_workshop_capacity(self):
        """Test that booking fails when workshop capacity is exceeded"""
        # First, create a booking that takes up some capacity
        first_result = self.use_case.execute(self.valid_input)
        self.assertTrue(first_result.success)
        
        # Create another booking that will exceed capacity
        exceeding_input = CreateBookingInputDTO(
            workshop_id=1,
            guardian_name="Another Guardian",
            guardian_email="another@example.com",
            guardian_phone="9876543210",
            guardian_postcode="54321",
            children=[
                {"name": "Child 3", "age": 4},
                {"name": "Child 4", "age": 6},
                {"name": "Child 5", "age": 8},
                {"name": "Child 6", "age": 3}
            ]
        )
        
        # Execute the use case
        result = self.use_case.execute(exceeding_input)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNone(result.booking_id)
        self.assertIn("insufficient child capacity", result.error_message)
        
        # Verify workshop capacity didn't change from the failed booking
        workshop = self.uow.workshops.get_by_id(1)
        self.assertEqual(workshop.current_families, 1)  # Still only 1 family
        self.assertEqual(workshop.current_children, 2)  # Still only 2 children
        
        # Verify no guardian or booking was created for the failed operation
        all_guardians = self.uow.guardians.get_all()
        self.assertEqual(len(all_guardians), 1)  # Only the first guardian exists
        
        all_bookings = self.uow.bookings.get_all()
        self.assertEqual(len(all_bookings), 1)  # Only the first booking exists
    
    def test_transaction_rollback_on_error(self):
        """Test that all changes are rolled back when an error occurs mid-transaction"""
        # Create a special input that will trigger an error after some operations succeed
        with patch.object(self.uow.bookings, 'save', side_effect=ValueError("Simulated database error")):
            # This should create a guardian but fail when saving the booking
            result = self.use_case.execute(self.valid_input)
            
            # Verify failure
            self.assertFalse(result.success)
            self.assertIn("Failed to create booking", result.error_message)
            
            # Verify nothing was persisted due to transaction rollback
            workshop = self.uow.workshops.get_by_id(1)
            self.assertEqual(workshop.current_families, 0)  # Should be rolled back to 0
            self.assertEqual(workshop.current_children, 0)  # Should be rolled back to 0
            
            all_guardians = self.uow.guardians.get_all()
            self.assertEqual(len(all_guardians), 0)  # Guardian creation should be rolled back
            
            all_bookings = self.uow.bookings.get_all()
            self.assertEqual(len(all_bookings), 0)  # No bookings should exist


if __name__ == "__main__":
    unittest.main() 