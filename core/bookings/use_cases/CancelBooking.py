from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

from core.unit_of_work import UnitOfWork


class CancellerType(Enum):
    ADMIN = "admin"
    GUARDIAN = "guardian"


@dataclass
class CancelBookingInputDTO:
    """
    Input data transfer object for the CancelBooking use case.
    Contains all the data needed to cancel a booking.
    """
    booking_id: int
    canceller_id: int
    canceller_type: CancellerType
    reason: Optional[str] = None


@dataclass
class CancelBookingOutputDTO:
    """
    Output data transfer object for the CancelBooking use case.
    Contains the result of the booking cancellation.
    """
    success: bool
    error_message: Optional[str] = None


class CancelBookingUseCase:
    """
    Use case for cancelling an existing booking.
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
    
    def execute(self, input_dto: CancelBookingInputDTO) -> CancelBookingOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for cancelling a booking
            
        Returns:
            CancelBookingOutputDTO: The result of the operation
        """
        try:
            # Start a transaction
            with self.unit_of_work:
                # 1. Get the booking
                booking = self.unit_of_work.bookings.get_by_id(input_dto.booking_id)
                if not booking:
                    return CancelBookingOutputDTO(
                        success=False,
                        error_message=f"Booking with ID {input_dto.booking_id} not found"
                    )
                
                # 2. Validate the canceller has permission
                if not self._validate_canceller(booking, input_dto):
                    return CancelBookingOutputDTO(
                        success=False,
                        error_message="You do not have permission to cancel this booking"
                    )
                
                # 3. Get the workshop to update capacity
                workshop = self.unit_of_work.workshops.get_by_id(booking.workshop_id)
                if not workshop:
                    return CancelBookingOutputDTO(
                        success=False,
                        error_message=f"Workshop with ID {booking.workshop_id} not found"
                    )
                
                # 4. Update the workshop capacity - release slots
                child_count = booking.child_count()
                workshop.current_children -= child_count
                workshop.remove_family()  # Decrease family count
                self.unit_of_work.workshops.save(workshop)
                
                # 5. Mark the booking as cancelled
                booking.mark_as_cancelled(input_dto.reason)
                self.unit_of_work.bookings.save(booking)
                
                # 6. Send cancellation confirmation to guardian
                # This would typically be done by an infrastructure service,
                # but for now we'll just note that it needs to happen
                guardian = self.unit_of_work.guardians.get_by_id(booking.guardian_id)
                if guardian:
                    self._send_guardian_notification(guardian, booking, workshop)
                
                # 7. Send notification to admin
                self._send_admin_notification(booking, guardian, workshop)
                
                # 8. Commit the transaction - all operations succeed or fail together
                self.unit_of_work.commit()
                
                return CancelBookingOutputDTO(
                    success=True
                )
                
        except Exception as e:
            # Any exception will cause automatic rollback by the UnitOfWork.__exit__ method
            return CancelBookingOutputDTO(
                success=False,
                error_message=f"Failed to cancel booking: {str(e)}"
            )
    
    def _validate_canceller(self, booking, input_dto: CancelBookingInputDTO) -> bool:
        """
        Validate that the canceller has permission to cancel this booking.
        
        Args:
            booking: The booking to be cancelled
            input_dto: The input data with canceller information
            
        Returns:
            bool: True if the canceller has permission, False otherwise
        """
        # Admin can cancel any booking
        if input_dto.canceller_type == CancellerType.ADMIN:
            return True
        
        # Guardian can only cancel their own bookings
        if input_dto.canceller_type == CancellerType.GUARDIAN:
            return booking.guardian_id == input_dto.canceller_id
        
        return False
    
    def _send_guardian_notification(self, guardian, booking, workshop):
        """
        Send cancellation confirmation to the guardian.
        In Clean Architecture, this would typically be a call to a boundary/port,
        which would be implemented by an adapter in the infrastructure layer.
        
        For now, we'll just log the intent for testing purposes.
        """
        # This is a placeholder for notification logic
        # In a real application, this would call an infrastructure service
        pass
    
    def _send_admin_notification(self, booking, guardian, workshop):
        """
        Send notification to admin about the cancelled booking.
        In Clean Architecture, this would typically be a call to a boundary/port,
        which would be implemented by an adapter in the infrastructure layer.
        
        For now, we'll just log the intent for testing purposes.
        """
        # This is a placeholder for notification logic
        # In a real application, this would call an infrastructure service
        pass 