from dataclasses import dataclass
from typing import List, Optional

from core.bookings.BookingEntity import BookingEntity
from core.guardians.GuardianEntity import GuardianEntity
from core.unit_of_work import UnitOfWork


@dataclass
class CreateBookingInputDTO:
    """
    Input data transfer object for the CreateBooking use case.
    Contains all the data needed to create a booking.
    """
    workshop_id: int
    guardian_name: str
    guardian_email: str
    guardian_phone: str
    guardian_postcode: str
    children: List[dict]  # List of child name/age dicts


@dataclass
class CreateBookingOutputDTO:
    """
    Output data transfer object for the CreateBooking use case.
    Contains the result of the booking creation.
    """
    success: bool
    booking_id: Optional[int] = None
    error_message: Optional[str] = None


class CreateBookingUseCase:
    """
    Use case for creating a new booking.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initialize the use case with a UnitOfWork dependency.
        The UnitOfWork is passed in as a dependency, following Dependency Inversion Principle.
        
        Args:
            unit_of_work: An object that implements UnitOfWork interface to manage transactions
        """
        self.unit_of_work = unit_of_work
    
    def execute(self, input_dto: CreateBookingInputDTO) -> CreateBookingOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for creating a booking
            
        Returns:
            CreateBookingOutputDTO: The result of the operation
        """
        # Validate input
        if not self._validate_input(input_dto):
            return CreateBookingOutputDTO(
                success=False,
                error_message="Invalid booking data provided"
            )
        
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
            # Any exception will cause automatic rollback by the UnitOfWork.__exit__ method
            return CreateBookingOutputDTO(
                success=False,
                error_message=f"Failed to create booking: {str(e)}"
            )
    
    def _validate_input(self, input_dto: CreateBookingInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Guardian name must not be empty
        if not input_dto.guardian_name.strip():
            return False
        
        # Guardian email must not be empty and should be valid format
        if not input_dto.guardian_email.strip() or '@' not in input_dto.guardian_email:
            return False
        
        # Guardian phone must not be empty
        if not input_dto.guardian_phone.strip():
            return False
        
        # Guardian postcode must not be empty
        if not input_dto.guardian_postcode.strip():
            return False
        
        # Must have at least one child
        if not input_dto.children or len(input_dto.children) == 0:
            return False
        
        # Each child must have a name and age
        for child in input_dto.children:
            if 'name' not in child or not child['name'].strip():
                return False
            if 'age' not in child or not isinstance(child['age'], int) or child['age'] <= 0:
                return False
        
        return True 