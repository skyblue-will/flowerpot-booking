# This file marks core as a Python package
# Following Clean Architecture, this package contains domain entities and use cases
# with no dependencies on external frameworks or infrastructure

# Import and expose key core modules and interfaces
from core.repositories import Repository, WorkshopRepository, BookingRepository, GuardianRepository
from core.unit_of_work import UnitOfWork, execute_in_transaction 