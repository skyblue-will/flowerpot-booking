from dataclasses import dataclass
from typing import List, Optional

from core.unit_of_work import UnitOfWork


@dataclass
class LinkBookingsToGuardiansInputDTO:
    """
    Input data transfer object for the LinkBookingsToGuardians use case.
    Contains the guardian ID and list of booking IDs to link.
    """
    guardian_id: int
    booking_ids: List[int]


@dataclass
class LinkBookingsToGuardiansOutputDTO:
    """
    Output data transfer object for the LinkBookingsToGuardians use case.
    Contains the result of the linking operation.
    """
    success: bool
    linked_booking_ids: Optional[List[int]] = None
    error_message: Optional[str] = None


class LinkBookingsToGuardiansUseCase:
    """
    Use case for linking multiple bookings to a specific guardian.
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
    
    def execute(self, input_dto: LinkBookingsToGuardiansInputDTO) -> LinkBookingsToGuardiansOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for linking bookings to a guardian
            
        Returns:
            LinkBookingsToGuardiansOutputDTO: The result of the operation
        """
        # Validate input
        if not self._validate_input(input_dto):
            return LinkBookingsToGuardiansOutputDTO(
                success=False,
                error_message="Invalid input data provided"
            )
        
        try:
            # Start transaction
            with self.unit_of_work:
                # Get the guardian
                guardian = self.unit_of_work.guardians.get_by_id(input_dto.guardian_id)
                if not guardian:
                    return LinkBookingsToGuardiansOutputDTO(
                        success=False,
                        error_message=f"Guardian with ID {input_dto.guardian_id} not found"
                    )
                
                # Process each booking
                successfully_linked_booking_ids = []
                for booking_id in input_dto.booking_ids:
                    # Get the booking
                    booking = self.unit_of_work.bookings.get_by_id(booking_id)
                    
                    # Validate booking exists
                    if not booking:
                        return LinkBookingsToGuardiansOutputDTO(
                            success=False,
                            linked_booking_ids=successfully_linked_booking_ids if successfully_linked_booking_ids else None,
                            error_message=f"Booking with ID {booking_id} not found"
                        )
                    
                    # Check if booking is already linked to a different guardian
                    if booking.guardian_id is not None and booking.guardian_id != input_dto.guardian_id:
                        return LinkBookingsToGuardiansOutputDTO(
                            success=False,
                            linked_booking_ids=successfully_linked_booking_ids if successfully_linked_booking_ids else None,
                            error_message=f"Booking with ID {booking_id} is already linked to guardian with ID {booking.guardian_id}"
                        )
                    
                    # Link booking to guardian
                    booking.guardian_id = input_dto.guardian_id
                    self.unit_of_work.bookings.save(booking)
                    successfully_linked_booking_ids.append(booking_id)
                
                # Commit transaction
                self.unit_of_work.commit()
                
                # Return success response
                return LinkBookingsToGuardiansOutputDTO(
                    success=True,
                    linked_booking_ids=successfully_linked_booking_ids
                )
                
        except Exception as e:
            # Transaction is automatically rolled back by UnitOfWork.__exit__
            # Return failure response
            return LinkBookingsToGuardiansOutputDTO(
                success=False,
                linked_booking_ids=None,
                error_message=f"Failed to link bookings to guardian: {str(e)}"
            )
    
    def _validate_input(self, input_dto: LinkBookingsToGuardiansInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Guardian ID must be positive
        if input_dto.guardian_id <= 0:
            return False
        
        # Must have at least one booking ID
        if not input_dto.booking_ids or len(input_dto.booking_ids) == 0:
            return False
        
        # All booking IDs must be positive
        if any(booking_id <= 0 for booking_id in input_dto.booking_ids):
            return False
        
        return True 