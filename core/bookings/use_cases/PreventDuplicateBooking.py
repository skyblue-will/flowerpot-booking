from dataclasses import dataclass
from typing import Optional, List

from core.unit_of_work import UnitOfWork


@dataclass
class PreventDuplicateBookingInputDTO:
    """
    Input data transfer object for the PreventDuplicateBooking use case.
    Contains the information needed to check for duplicate bookings.
    """
    guardian_email: str
    workshop_id: int


@dataclass
class PreventDuplicateBookingOutputDTO:
    """
    Output data transfer object for the PreventDuplicateBooking use case.
    Indicates whether the booking would be a duplicate or not.
    """
    is_duplicate: bool
    error_message: Optional[str] = None


class PreventDuplicateBookingUseCase:
    """
    Use case for preventing duplicate bookings by the same guardian for the same workshop.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, unit_of_work: UnitOfWork):
        """
        Initialize the use case with a UnitOfWork dependency.
        The UnitOfWork is passed in as a dependency, following Dependency Inversion Principle.
        
        Args:
            unit_of_work: An object that implements UnitOfWork interface
        """
        self.unit_of_work = unit_of_work
    
    def execute(self, input_dto: PreventDuplicateBookingInputDTO) -> PreventDuplicateBookingOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for checking duplicate bookings
            
        Returns:
            PreventDuplicateBookingOutputDTO: The result of the check
        """
        try:
            # Start a transaction (read-only in this case)
            with self.unit_of_work:
                # 1. Validate input
                if not input_dto.guardian_email or not input_dto.workshop_id:
                    return PreventDuplicateBookingOutputDTO(
                        is_duplicate=False,
                        error_message="Invalid input: email and workshop ID must be provided"
                    )
                
                # 2. Get the workshop
                workshop = self.unit_of_work.workshops.get_by_id(input_dto.workshop_id)
                if not workshop:
                    return PreventDuplicateBookingOutputDTO(
                        is_duplicate=False,
                        error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                    )
                
                # 3. Find guardian by email
                guardians = self._find_guardians_by_email(input_dto.guardian_email)
                if not guardians:
                    # No guardian exists with this email, so can't be a duplicate
                    return PreventDuplicateBookingOutputDTO(is_duplicate=False)
                
                # 4. Check if any of these guardians have already booked this workshop
                for guardian in guardians:
                    if self._has_existing_booking(guardian.id, input_dto.workshop_id):
                        return PreventDuplicateBookingOutputDTO(
                            is_duplicate=True,
                            error_message=f"Guardian with email {input_dto.guardian_email} already has a booking for this workshop"
                        )
                
                # No duplicate found
                return PreventDuplicateBookingOutputDTO(is_duplicate=False)
                
        except Exception as e:
            return PreventDuplicateBookingOutputDTO(
                is_duplicate=False,
                error_message=f"Error checking for duplicate bookings: {str(e)}"
            )
    
    def _find_guardians_by_email(self, email: str) -> List:
        """
        Find guardians by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            List of guardian entities with matching email
        """
        all_guardians = self.unit_of_work.guardians.get_all()
        return [g for g in all_guardians if g.email.lower() == email.lower()]
    
    def _has_existing_booking(self, guardian_id: int, workshop_id: int) -> bool:
        """
        Check if a guardian already has a booking for the specified workshop.
        
        Args:
            guardian_id: ID of the guardian to check
            workshop_id: ID of the workshop to check
            
        Returns:
            True if a booking exists, False otherwise
        """
        all_bookings = self.unit_of_work.bookings.get_all()
        
        # Filter active bookings (not cancelled) for this guardian and workshop
        existing_bookings = [
            b for b in all_bookings 
            if b.guardian_id == guardian_id 
            and b.workshop_id == workshop_id
            and b.is_active()  # Only consider active bookings, not cancelled ones
        ]
        
        return len(existing_bookings) > 0 