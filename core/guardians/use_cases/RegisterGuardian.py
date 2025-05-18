from dataclasses import dataclass
from typing import Optional

from core.guardians.GuardianEntity import GuardianEntity
from core.unit_of_work import UnitOfWork


@dataclass
class RegisterGuardianInputDTO:
    """
    Input data transfer object for the RegisterGuardian use case.
    Contains all the data needed to register a guardian.
    """
    name: str
    email: str
    phone: str
    postcode: str


@dataclass
class RegisterGuardianOutputDTO:
    """
    Output data transfer object for the RegisterGuardian use case.
    Contains the result of the guardian registration.
    """
    success: bool
    guardian_id: Optional[int] = None
    error_message: Optional[str] = None


class RegisterGuardianUseCase:
    """
    Use case for registering a guardian in the system.
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
    
    def execute(self, input_dto: RegisterGuardianInputDTO) -> RegisterGuardianOutputDTO:
        """
        Execute the use case with the provided input data.
        
        Args:
            input_dto: The input data required for registering a guardian
            
        Returns:
            RegisterGuardianOutputDTO: The result of the operation
        """
        # Validate input
        if not self._validate_input(input_dto):
            return RegisterGuardianOutputDTO(
                success=False,
                error_message="Invalid guardian data provided"
            )
        
        try:
            # Start a transaction
            with self.unit_of_work:
                # Check if guardian with this email already exists
                existing_guardian = self._find_by_email(input_dto.email)
                
                if existing_guardian:
                    # Return the existing guardian ID if already registered
                    return RegisterGuardianOutputDTO(
                        success=True,
                        guardian_id=existing_guardian.id
                    )
                
                # Create a new guardian
                guardian = GuardianEntity(
                    name=input_dto.name,
                    email=input_dto.email,
                    phone=input_dto.phone,
                    postcode=input_dto.postcode
                )
                
                # Save the guardian
                saved_guardian = self.unit_of_work.guardians.save(guardian)
                
                # Commit the transaction
                self.unit_of_work.commit()
                
                return RegisterGuardianOutputDTO(
                    success=True,
                    guardian_id=saved_guardian.id
                )
                
        except Exception as e:
            # Any exception will cause automatic rollback by the UnitOfWork.__exit__ method
            return RegisterGuardianOutputDTO(
                success=False,
                error_message=f"Failed to register guardian: {str(e)}"
            )
    
    def _validate_input(self, input_dto: RegisterGuardianInputDTO) -> bool:
        """
        Validate the input data according to business rules.
        
        Args:
            input_dto: The input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Name must not be empty
        if not input_dto.name.strip():
            return False
        
        # Email must not be empty and should be valid format
        if not input_dto.email.strip() or '@' not in input_dto.email:
            return False
        
        # Phone must not be empty
        if not input_dto.phone.strip():
            return False
        
        # Postcode must not be empty
        if not input_dto.postcode.strip():
            return False
        
        return True
    
    def _find_by_email(self, email: str) -> Optional[GuardianEntity]:
        """
        Find a guardian by email address (case-insensitive).
        
        Args:
            email: Email address to search for
            
        Returns:
            GuardianEntity or None if not found
        """
        all_guardians = self.unit_of_work.guardians.get_all()
        
        for guardian in all_guardians:
            if guardian.email.lower() == email.lower():
                return guardian
        
        return None 