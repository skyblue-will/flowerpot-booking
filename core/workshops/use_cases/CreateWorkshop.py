from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from core.workshops.WorkshopEntity import WorkshopEntity
from core.unit_of_work import UnitOfWork


@dataclass
class CreateWorkshopInputDTO:
    """
    Input data transfer object for the CreateWorkshop use case.
    Contains all the data needed to create a workshop.
    """
    title: str
    workshop_date: date
    workshop_time: time
    location: str
    max_families: int
    max_children: int


@dataclass
class CreateWorkshopOutputDTO:
    """
    Output data transfer object for the CreateWorkshop use case.
    Contains the result of the workshop creation.
    """
    success: bool
    workshop_id: Optional[int] = None
    error_message: Optional[str] = None


class CreateWorkshopUseCase:
    """
    Use case for creating a new workshop.
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
    
    def execute(self, input_dto: CreateWorkshopInputDTO) -> CreateWorkshopOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for creating a workshop
            
        Returns:
            CreateWorkshopOutputDTO: The result of the operation
        """
        # Validate input
        if not self._validate_input(input_dto):
            return CreateWorkshopOutputDTO(
                success=False,
                error_message="Invalid workshop data provided"
            )
        
        # Create a new workshop entity
        workshop = WorkshopEntity(
            id=None,  # ID will be assigned by the repository
            title=input_dto.title,
            date=input_dto.workshop_date,
            time=input_dto.workshop_time,
            location=input_dto.location,
            max_families=input_dto.max_families,
            max_children=input_dto.max_children,
            current_families=0,  # New workshop starts with 0 families
            current_children=0   # New workshop starts with 0 children
        )
        
        # Use the UnitOfWork to manage the transaction
        try:
            with self.unit_of_work:
                # Save the workshop using the repository from the UnitOfWork
                saved_workshop = self.unit_of_work.workshops.save(workshop)
                # Commit the transaction
                self.unit_of_work.commit()
                
                # Return success response
                return CreateWorkshopOutputDTO(
                    success=True,
                    workshop_id=saved_workshop.id
                )
        except Exception as e:
            # Transaction is automatically rolled back by UnitOfWork.__exit__
            # Return failure response
            return CreateWorkshopOutputDTO(
                success=False,
                error_message=f"Failed to create workshop: {str(e)}"
            )
    
    def _validate_input(self, input_dto: CreateWorkshopInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
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
        
        # Workshop date must be valid (could add more validation here)
        if not isinstance(input_dto.workshop_date, date):
            return False
        
        # Workshop time must be valid
        if not isinstance(input_dto.workshop_time, time):
            return False
        
        return True 