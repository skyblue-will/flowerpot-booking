from dataclasses import dataclass
from typing import Optional


@dataclass
class PreventOverbookingInputDTO:
    """
    Input data transfer object for the PreventOverbooking use case.
    Contains the workshop ID and the requested slots to check.
    """
    workshop_id: int
    requested_family_slots: int  # Number of family slots being requested
    requested_child_slots: int   # Number of child slots being requested


@dataclass
class PreventOverbookingOutputDTO:
    """
    Output data transfer object for the PreventOverbooking use case.
    Contains the result of the booking availability check.
    """
    has_capacity: bool
    remaining_family_slots: Optional[int] = None
    remaining_child_slots: Optional[int] = None
    error_message: Optional[str] = None


class PreventOverbookingUseCase:
    """
    Use case for checking if a workshop has capacity for a requested booking.
    Follows Clean Architecture principles where use cases encapsulate
    and orchestrate the business rules specific to a particular use case.
    """
    
    def __init__(self, workshop_repository):
        """
        Initialize the use case with a repository dependency.
        The repository is passed in as a dependency, following Dependency Inversion Principle.
        
        Args:
            workshop_repository: An object that implements methods to retrieve workshops
        """
        self.workshop_repository = workshop_repository
    
    def execute(self, input_dto: PreventOverbookingInputDTO) -> PreventOverbookingOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for checking booking capacity
            
        Returns:
            PreventOverbookingOutputDTO: The result of the operation
        """
        try:
            # Validate input
            if not self._validate_input(input_dto):
                return PreventOverbookingOutputDTO(
                    has_capacity=False,
                    error_message="Invalid booking request data provided"
                )
            
            # Retrieve the workshop to check
            workshop = self.workshop_repository.get_by_id(input_dto.workshop_id)
            if not workshop:
                return PreventOverbookingOutputDTO(
                    has_capacity=False,
                    error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                )
            
            # Calculate remaining slots
            remaining_family_slots = workshop.remaining_family_slots()
            remaining_child_slots = workshop.remaining_child_slots()
            
            # Check if there's enough capacity for families
            if input_dto.requested_family_slots > remaining_family_slots:
                return PreventOverbookingOutputDTO(
                    has_capacity=False,
                    remaining_family_slots=remaining_family_slots,
                    remaining_child_slots=remaining_child_slots,
                    error_message=f"Not enough family slots available. Requested: {input_dto.requested_family_slots}, Available: {remaining_family_slots}"
                )
            
            # Check if there's enough capacity for children
            if input_dto.requested_child_slots > remaining_child_slots:
                return PreventOverbookingOutputDTO(
                    has_capacity=False,
                    remaining_family_slots=remaining_family_slots,
                    remaining_child_slots=remaining_child_slots,
                    error_message=f"Not enough child slots available. Requested: {input_dto.requested_child_slots}, Available: {remaining_child_slots}"
                )
            
            # All checks passed, there is enough capacity
            return PreventOverbookingOutputDTO(
                has_capacity=True,
                remaining_family_slots=remaining_family_slots,
                remaining_child_slots=remaining_child_slots
            )
            
        except Exception as e:
            # Return failure response
            return PreventOverbookingOutputDTO(
                has_capacity=False,
                error_message=f"Failed to check workshop capacity: {str(e)}"
            )
    
    def _validate_input(self, input_dto: PreventOverbookingInputDTO) -> bool:
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
        
        # Requested slots must be positive
        if input_dto.requested_family_slots <= 0:
            return False
        
        if input_dto.requested_child_slots <= 0:
            return False
        
        return True 