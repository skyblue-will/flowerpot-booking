from dataclasses import dataclass
from datetime import date, time
from typing import Optional, List

from core.workshops.WorkshopEntity import WorkshopEntity


@dataclass
class EditWorkshopInputDTO:
    """
    Input data transfer object for the EditWorkshop use case.
    Contains the workshop ID and all fields that can be edited.
    """
    workshop_id: int
    title: str
    workshop_date: date
    workshop_time: time
    location: str
    max_families: int
    max_children: int


@dataclass
class AffectedBookingDTO:
    """
    Data transfer object representing a booking affected by reducing slots.
    """
    booking_id: int
    guardian_name: str
    guardian_email: str
    children_count: int


@dataclass
class EditWorkshopOutputDTO:
    """
    Output data transfer object for the EditWorkshop use case.
    Contains the result of the workshop edit operation.
    """
    success: bool
    workshop_id: Optional[int] = None
    affected_bookings: Optional[List[AffectedBookingDTO]] = None
    error_message: Optional[str] = None


class EditWorkshopUseCase:
    """
    Use case for editing an existing workshop.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, workshop_repository, booking_repository):
        """
        Initialize the use case with repository dependencies.
        
        Args:
            workshop_repository: An object that implements methods to retrieve and update workshops
            booking_repository: An object that implements methods to retrieve bookings for a workshop
        """
        self.workshop_repository = workshop_repository
        self.booking_repository = booking_repository
    
    def execute(self, input_dto: EditWorkshopInputDTO) -> EditWorkshopOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for editing the workshop
            
        Returns:
            EditWorkshopOutputDTO: The result of the operation
        """
        try:
            # Validate input
            if not self._validate_input(input_dto):
                return EditWorkshopOutputDTO(
                    success=False,
                    error_message="Invalid workshop data provided"
                )
            
            # Retrieve the workshop to edit
            workshop = self.workshop_repository.get_by_id(input_dto.workshop_id)
            if not workshop:
                return EditWorkshopOutputDTO(
                    success=False,
                    error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                )
            
            # Check if slots are being reduced
            slots_reduced = (
                input_dto.max_families < workshop.max_families or
                input_dto.max_children < workshop.max_children
            )
            
            affected_bookings = []
            
            # If slots are reduced, check for affected bookings
            if slots_reduced:
                # Check if new values are less than current usage
                if (input_dto.max_families < workshop.current_families or
                    input_dto.max_children < workshop.current_children):
                    
                    # Retrieve bookings for this workshop
                    bookings = self.booking_repository.get_by_workshop_id(workshop.id)
                    
                    # Find affected bookings (this is simplified - in a real system,
                    # you would need complex logic to determine which bookings are affected)
                    for booking in bookings:
                        guardian = self.booking_repository.get_guardian_for_booking(booking.id)
                        affected_bookings.append(
                            AffectedBookingDTO(
                                booking_id=booking.id,
                                guardian_name=guardian.name,
                                guardian_email=guardian.email,
                                children_count=booking.child_count()
                            )
                        )
            
            # Update the workshop with new values
            workshop.title = input_dto.title
            workshop.date = input_dto.workshop_date
            workshop.time = input_dto.workshop_time
            workshop.location = input_dto.location
            workshop.max_families = input_dto.max_families
            workshop.max_children = input_dto.max_children
            
            # Save the updated workshop
            updated_workshop = self.workshop_repository.update(workshop)
            
            # Return success response
            return EditWorkshopOutputDTO(
                success=True,
                workshop_id=updated_workshop.id,
                affected_bookings=affected_bookings if affected_bookings else None
            )
            
        except Exception as e:
            # Return failure response
            return EditWorkshopOutputDTO(
                success=False,
                error_message=f"Failed to edit workshop: {str(e)}"
            )
    
    def _validate_input(self, input_dto: EditWorkshopInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Workshop ID must be positive
        if input_dto.workshop_id <= 0:
            return False
        
        # Title must not be empty
        if not input_dto.title.strip():
            return False
        
        # Location must not be empty
        if not input_dto.location.strip():
            return False
        
        # Max families must be positive
        if input_dto.max_families <= 0:
            return False
        
        # Max children must be positive
        if input_dto.max_children <= 0:
            return False
        
        # Workshop date must be valid
        if not isinstance(input_dto.workshop_date, date):
            return False
        
        # Workshop time must be valid
        if not isinstance(input_dto.workshop_time, time):
            return False
        
        return True 