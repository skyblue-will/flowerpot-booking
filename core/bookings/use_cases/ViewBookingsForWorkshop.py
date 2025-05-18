from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from core.unit_of_work import UnitOfWork


@dataclass
class BookingDetails:
    """
    Data structure to represent simplified booking details,
    including guardian information and children.
    """
    booking_id: int
    guardian_name: str
    guardian_email: str
    guardian_phone: str
    guardian_postcode: str
    children: List[Dict[str, Any]]  # List of child details (name, age)
    status: str  # active, cancelled


@dataclass
class ViewBookingsForWorkshopInputDTO:
    """
    Input data transfer object for the ViewBookingsForWorkshop use case.
    Contains the data needed to view bookings for a workshop.
    """
    workshop_id: int
    viewer_id: Optional[int] = None  # Used for access control
    viewer_is_admin: bool = False


@dataclass
class ViewBookingsForWorkshopOutputDTO:
    """
    Output data transfer object for the ViewBookingsForWorkshop use case.
    Contains the result of the booking retrieval.
    """
    success: bool
    bookings: List[BookingDetails] = None
    error_message: Optional[str] = None


class ViewBookingsForWorkshopUseCase:
    """
    Use case for viewing all bookings for a specific workshop.
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
    
    def execute(self, input_dto: ViewBookingsForWorkshopInputDTO) -> ViewBookingsForWorkshopOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for viewing bookings
            
        Returns:
            ViewBookingsForWorkshopOutputDTO: The result of the operation
        """
        try:
            # Start a transaction (read-only in this case)
            with self.unit_of_work:
                # 1. Get the workshop
                workshop = self.unit_of_work.workshops.get_by_id(input_dto.workshop_id)
                if not workshop:
                    return ViewBookingsForWorkshopOutputDTO(
                        success=False,
                        error_message=f"Workshop with ID {input_dto.workshop_id} not found"
                    )
                
                # 2. Get all bookings for this workshop
                all_bookings = self.unit_of_work.bookings.get_all()
                workshop_bookings = [b for b in all_bookings if b.workshop_id == input_dto.workshop_id]
                
                # 3. If viewer is not admin, they can only see their own bookings
                if not input_dto.viewer_is_admin and input_dto.viewer_id is not None:
                    workshop_bookings = [b for b in workshop_bookings if b.guardian_id == input_dto.viewer_id]
                
                # 4. Transform bookings to DTOs with guardian information
                booking_details = []
                for booking in workshop_bookings:
                    guardian = self.unit_of_work.guardians.get_by_id(booking.guardian_id)
                    if not guardian:
                        continue  # Skip if guardian not found (shouldn't happen in a proper DB with constraints)
                    
                    # Convert child objects to dictionaries
                    children_data = [{"name": child.name, "age": child.age} for child in booking.children]
                    
                    booking_details.append(BookingDetails(
                        booking_id=booking.id,
                        guardian_name=guardian.name,
                        guardian_email=guardian.email,
                        guardian_phone=guardian.phone,
                        guardian_postcode=guardian.postcode,
                        children=children_data,
                        status=booking.status
                    ))
                
                return ViewBookingsForWorkshopOutputDTO(
                    success=True,
                    bookings=booking_details
                )
                
        except Exception as e:
            return ViewBookingsForWorkshopOutputDTO(
                success=False,
                error_message=f"Error retrieving bookings: {str(e)}"
            ) 