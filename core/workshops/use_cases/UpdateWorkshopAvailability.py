from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateWorkshopAvailabilityInputDTO:
    """
    Input data transfer object for the UpdateWorkshopAvailability use case.
    Contains the workshop ID and the changes to make to family and child slots.
    Positive values increase available slots (booking cancelled).
    Negative values reduce available slots (booking made).
    """
    workshop_id: int
    family_slots_change: int  # Positive for increase, negative for decrease
    child_slots_change: int   # Positive for increase, negative for decrease


@dataclass
class UpdateWorkshopAvailabilityOutputDTO:
    """
    Output data transfer object for the UpdateWorkshopAvailability use case.
    Contains the result of the workshop availability update.
    """
    success: bool
    workshop_id: Optional[int] = None
    remaining_family_slots: Optional[int] = None
    remaining_child_slots: Optional[int] = None
    error_message: Optional[str] = None


class UpdateWorkshopAvailabilityUseCase:
    """
    Use case for updating workshop availability when bookings are made or cancelled.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, workshop_repository):
        """
        Initialize the use case with a repository dependency.
        The repository is passed in as a dependency, following Dependency Inversion Principle.
        
        Args:
            workshop_repository: An object that implements methods to retrieve and update workshops
        """
        self.workshop_repository = workshop_repository
    
    def execute(self, input_dto: UpdateWorkshopAvailabilityInputDTO) -> UpdateWorkshopAvailabilityOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for updating workshop availability
            
        Returns:
            UpdateWorkshopAvailabilityOutputDTO: The result of the operation
        """
        try:
            # Validate input
            if not self._validate_input(input_dto):
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message="Invalid input data provided"
                )
            
            # Retrieve the workshop to update
            workshop = self.workshop_repository.get_by_id(input_dto.workshop_id)
            if not workshop:
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                )
            
            # Calculate new values
            new_current_families = workshop.current_families - input_dto.family_slots_change
            new_current_children = workshop.current_children - input_dto.child_slots_change
            
            # Validate the new values don't go below 0 or above max
            if new_current_families < 0:
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message=f"Cannot have negative family slots used ({new_current_families})"
                )
            
            if new_current_children < 0:
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message=f"Cannot have negative child slots used ({new_current_children})"
                )
            
            if new_current_families > workshop.max_families:
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message=f"Not enough family slots available (requested: {new_current_families}, max: {workshop.max_families})"
                )
            
            if new_current_children > workshop.max_children:
                return UpdateWorkshopAvailabilityOutputDTO(
                    success=False,
                    error_message=f"Not enough child slots available (requested: {new_current_children}, max: {workshop.max_children})"
                )
            
            # Update workshop availability
            workshop.current_families = new_current_families
            workshop.current_children = new_current_children
            
            # Save the updated workshop
            updated_workshop = self.workshop_repository.update(workshop)
            
            # Return success response
            return UpdateWorkshopAvailabilityOutputDTO(
                success=True,
                workshop_id=updated_workshop.id,
                remaining_family_slots=updated_workshop.remaining_family_slots(),
                remaining_child_slots=updated_workshop.remaining_child_slots()
            )
            
        except Exception as e:
            # Return failure response
            return UpdateWorkshopAvailabilityOutputDTO(
                success=False,
                error_message=f"Failed to update workshop availability: {str(e)}"
            )
    
    def _validate_input(self, input_dto: UpdateWorkshopAvailabilityInputDTO) -> bool:
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
        
        # Family and child slots changes must not be zero (no change)
        if input_dto.family_slots_change == 0 and input_dto.child_slots_change == 0:
            return False
        
        return True 