from dataclasses import dataclass
from datetime import date, time
from typing import List, Optional


@dataclass
class WorkshopSummaryDTO:
    """
    Data transfer object for a workshop summary.
    Contains the essential information for displaying a workshop in a list.
    """
    id: int
    title: str
    workshop_date: date
    workshop_time: time
    location: str
    remaining_family_slots: int
    remaining_child_slots: int


@dataclass
class ViewAvailableWorkshopsInputDTO:
    """
    Input data transfer object for the ViewAvailableWorkshops use case.
    Could be extended to include filters, pagination, etc.
    """
    current_date: date  # Used to filter only upcoming workshops


@dataclass
class ViewAvailableWorkshopsOutputDTO:
    """
    Output data transfer object for the ViewAvailableWorkshops use case.
    Contains the result of the available workshops query.
    """
    success: bool
    workshops: List[WorkshopSummaryDTO] = None
    error_message: Optional[str] = None


class ViewAvailableWorkshopsUseCase:
    """
    Use case for viewing all available upcoming workshops.
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
    
    def execute(self, input_dto: ViewAvailableWorkshopsInputDTO) -> ViewAvailableWorkshopsOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data for filtering workshops
            
        Returns:
            ViewAvailableWorkshopsOutputDTO: The result of the operation
        """
        try:
            # Retrieve all workshops from the repository
            all_workshops = self.workshop_repository.get_all()
            
            # Filter for upcoming workshops (workshop date >= current date)
            upcoming_workshops = [
                workshop for workshop in all_workshops 
                if workshop.date >= input_dto.current_date
            ]
            
            # Convert to DTOs for the presentation layer
            workshop_dtos = [
                WorkshopSummaryDTO(
                    id=workshop.id,
                    title=workshop.title,
                    workshop_date=workshop.date,
                    workshop_time=workshop.time,
                    location=workshop.location,
                    remaining_family_slots=workshop.remaining_family_slots(),
                    remaining_child_slots=workshop.remaining_child_slots()
                )
                for workshop in upcoming_workshops
            ]
            
            # Sort workshops by date, then time
            workshop_dtos.sort(key=lambda w: (w.workshop_date, w.workshop_time))
            
            # Return success response with the workshop list
            return ViewAvailableWorkshopsOutputDTO(
                success=True,
                workshops=workshop_dtos
            )
            
        except Exception as e:
            # Return failure response
            return ViewAvailableWorkshopsOutputDTO(
                success=False,
                error_message=f"Failed to retrieve workshops: {str(e)}"
            ) 