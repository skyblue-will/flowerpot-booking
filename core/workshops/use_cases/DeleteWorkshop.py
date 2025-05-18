from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GuardianToNotifyDTO:
    """
    Data transfer object representing a guardian that needs to be notified
    about a deleted workshop.
    """
    guardian_id: int
    name: str
    email: str
    booking_ids: List[int]


@dataclass
class DeleteWorkshopInputDTO:
    """
    Input data transfer object for the DeleteWorkshop use case.
    Contains the ID of the workshop to delete.
    """
    workshop_id: int


@dataclass
class DeleteWorkshopOutputDTO:
    """
    Output data transfer object for the DeleteWorkshop use case.
    Contains the result of the deletion operation.
    """
    success: bool
    guardians_to_notify: Optional[List[GuardianToNotifyDTO]] = None
    error_message: Optional[str] = None


class DeleteWorkshopUseCase:
    """
    Use case for deleting a workshop from the system.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, workshop_repository, booking_repository):
        """
        Initialize the use case with repository dependencies.
        
        Args:
            workshop_repository: An object that implements methods to retrieve and delete workshops
            booking_repository: An object that implements methods to retrieve bookings for a workshop
        """
        self.workshop_repository = workshop_repository
        self.booking_repository = booking_repository
    
    def execute(self, input_dto: DeleteWorkshopInputDTO) -> DeleteWorkshopOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for deleting a workshop
            
        Returns:
            DeleteWorkshopOutputDTO: The result of the operation
        """
        try:
            # Validate input
            if not self._validate_input(input_dto):
                return DeleteWorkshopOutputDTO(
                    success=False,
                    error_message="Invalid workshop ID provided"
                )
            
            # Retrieve the workshop to delete
            workshop = self.workshop_repository.get_by_id(input_dto.workshop_id)
            if not workshop:
                return DeleteWorkshopOutputDTO(
                    success=False,
                    error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                )
            
            # Check if there are any bookings for this workshop
            bookings = self.booking_repository.get_by_workshop_id(workshop.id)
            
            # Create a list of guardians to notify if there are bookings
            guardians_to_notify = None
            if bookings:
                guardian_map = {}  # Map to group bookings by guardian
                
                # Group bookings by guardian
                for booking in bookings:
                    guardian = self.booking_repository.get_guardian_for_booking(booking.id)
                    
                    if guardian.id not in guardian_map:
                        guardian_map[guardian.id] = {
                            "guardian": guardian,
                            "booking_ids": []
                        }
                    
                    guardian_map[guardian.id]["booking_ids"].append(booking.id)
                
                # Create DTOs for each guardian
                guardians_to_notify = [
                    GuardianToNotifyDTO(
                        guardian_id=item["guardian"].id,
                        name=item["guardian"].name,
                        email=item["guardian"].email,
                        booking_ids=item["booking_ids"]
                    )
                    for item in guardian_map.values()
                ]
                
                # Delete all bookings for this workshop
                for booking in bookings:
                    self.booking_repository.delete(booking.id)
            
            # Delete the workshop
            self.workshop_repository.delete(workshop.id)
            
            # Return success response
            return DeleteWorkshopOutputDTO(
                success=True,
                guardians_to_notify=guardians_to_notify
            )
            
        except Exception as e:
            # Return failure response
            return DeleteWorkshopOutputDTO(
                success=False,
                error_message=f"Failed to delete workshop: {str(e)}"
            )
    
    def _validate_input(self, input_dto: DeleteWorkshopInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Workshop ID must be positive
        return input_dto.workshop_id > 0 