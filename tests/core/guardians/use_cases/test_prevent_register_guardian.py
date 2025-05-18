import unittest
from unittest.mock import patch

from core.guardians.GuardianEntity import GuardianEntity
from core.guardians.use_cases.RegisterGuardian import (
    RegisterGuardianInputDTO,
    RegisterGuardianOutputDTO,
    RegisterGuardianUseCase
)
from core.memory_unit_of_work import InMemoryUnitOfWork


class TestRegisterGuardian(unittest.TestCase):
    """
    Test the RegisterGuardian use case with various scenarios.
    """
    
    def setUp(self):
        """Set up common test dependencies"""
        # Create a unit of work for testing
        self.uow = InMemoryUnitOfWork()
        
        # Initialize the use case
        self.use_case = RegisterGuardianUseCase(self.uow)
    
    def test_successful_registration(self):
        """Test successful registration of a new guardian"""
        # Create valid input data
        input_dto = RegisterGuardianInputDTO(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertIsNotNone(result.guardian_id)
        self.assertIsNone(result.error_message)
        
        # Verify the guardian was saved correctly
        saved_guardian = self.uow.guardians.get_by_id(result.guardian_id)
        self.assertEqual(saved_guardian.name, "Test Guardian")
        self.assertEqual(saved_guardian.email, "test@example.com")
        self.assertEqual(saved_guardian.phone, "1234567890")
        self.assertEqual(saved_guardian.postcode, "12345")
    
    def test_prevent_duplicate_registration(self):
        """Test that registering the same guardian twice returns the existing guardian"""
        # Register a guardian first
        existing_guardian = GuardianEntity(
            name="Existing Guardian",
            email="existing@example.com",
            phone="0987654321",
            postcode="54321"
        )
        existing_guardian = self.uow.guardians.save(existing_guardian)
        
        # Try to register a guardian with the same email
        input_dto = RegisterGuardianInputDTO(
            name="Different Name",  # Different name, but same email
            email="existing@example.com",
            phone="1111111111",
            postcode="99999"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify success with existing guardian ID
        self.assertTrue(result.success)
        self.assertEqual(result.guardian_id, existing_guardian.id)
        self.assertIsNone(result.error_message)
        
        # Verify no new guardian was created
        all_guardians = self.uow.guardians.get_all()
        self.assertEqual(len(all_guardians), 1)
        
        # Verify the guardian data was not updated
        saved_guardian = self.uow.guardians.get_by_id(result.guardian_id)
        self.assertEqual(saved_guardian.name, "Existing Guardian")  # Original name
        self.assertEqual(saved_guardian.phone, "0987654321")        # Original phone
    
    def test_case_insensitive_email_check(self):
        """Test that email comparison is case-insensitive"""
        # Register a guardian first
        existing_guardian = GuardianEntity(
            name="Existing Guardian",
            email="case@Example.com",  # Mixed case
            phone="0987654321",
            postcode="54321"
        )
        existing_guardian = self.uow.guardians.save(existing_guardian)
        
        # Try to register with different case in email
        input_dto = RegisterGuardianInputDTO(
            name="Another Name",
            email="CASE@example.COM",  # Different case
            phone="1111111111",
            postcode="99999"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify same guardian was found despite case difference
        self.assertTrue(result.success)
        self.assertEqual(result.guardian_id, existing_guardian.id)
    
    def test_validation_missing_name(self):
        """Test validation failure when name is missing"""
        input_dto = RegisterGuardianInputDTO(
            name="",  # Empty name
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNone(result.guardian_id)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Invalid guardian data", result.error_message)
    
    def test_validation_invalid_email(self):
        """Test validation failure when email is invalid"""
        input_dto = RegisterGuardianInputDTO(
            name="Test Guardian",
            email="invalid-email",  # Missing @ symbol
            phone="1234567890",
            postcode="12345"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNone(result.guardian_id)
        self.assertIsNotNone(result.error_message)
    
    def test_validation_missing_phone(self):
        """Test validation failure when phone is missing"""
        input_dto = RegisterGuardianInputDTO(
            name="Test Guardian",
            email="test@example.com",
            phone="",  # Empty phone
            postcode="12345"
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNone(result.guardian_id)
        self.assertIsNotNone(result.error_message)
    
    def test_validation_missing_postcode(self):
        """Test validation failure when postcode is missing"""
        input_dto = RegisterGuardianInputDTO(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode=""  # Empty postcode
        )
        
        # Execute the use case
        result = self.use_case.execute(input_dto)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertIsNone(result.guardian_id)
        self.assertIsNotNone(result.error_message)
    
    def test_transaction_rollback_on_error(self):
        """Test that all changes are rolled back when an error occurs"""
        # Create valid input data
        input_dto = RegisterGuardianInputDTO(
            name="Test Guardian",
            email="test@example.com",
            phone="1234567890",
            postcode="12345"
        )
        
        # Patch the guardians repository to raise an exception
        with patch.object(self.uow.guardians, 'save', side_effect=ValueError("Simulated database error")):
            # Execute the use case
            result = self.use_case.execute(input_dto)
            
            # Verify failure
            self.assertFalse(result.success)
            self.assertIsNone(result.guardian_id)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Failed to register guardian", result.error_message)
            
            # Verify no guardian was saved
            all_guardians = self.uow.guardians.get_all()
            self.assertEqual(len(all_guardians), 0)


if __name__ == "__main__":
    unittest.main() 