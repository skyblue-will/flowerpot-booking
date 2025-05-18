class Child:
    """
    Child represents a child included in a booking.
    This is a simple value object used within the BookingEntity.
    """
    
    def __init__(self, name="", age=0):
        """
        Initialize a new Child
        """
        self.name = name
        self.age = age


class BookingEntity:
    """
    BookingEntity represents the core business concept of a workshop booking.
    This is a pure entity class following clean architecture principles.
    It has no dependencies on frameworks, UI, database, or other external systems.
    """
    
    def __init__(self, id=None, workshop_id=None, guardian_id=None, children=None, status="active", cancellation_reason=None):
        """
        Initialize a new Booking entity
        """
        self.id = id
        self.workshop_id = workshop_id
        self.guardian_id = guardian_id
        self.children = children or []  # List of Child objects
        self.status = status  # active, cancelled
        self.cancellation_reason = cancellation_reason
    
    def add_child(self, name, age):
        """
        Add a child to the booking
        """
        child = Child(name, age)
        self.children.append(child)
        return child
    
    def remove_child(self, index):
        """
        Remove a child from the booking by index
        """
        if 0 <= index < len(self.children):
            removed_child = self.children.pop(index)
            return removed_child
        return None
    
    def child_count(self):
        """
        Get the number of children in this booking
        """
        return len(self.children)
    
    def is_valid(self):
        """
        Check if the booking has all required information
        """
        return (
            self.workshop_id is not None and
            self.guardian_id is not None and
            len(self.children) > 0
        )
    
    def update_workshop(self, workshop_id):
        """
        Update the workshop ID for this booking
        """
        self.workshop_id = workshop_id
    
    def update_guardian(self, guardian_id):
        """
        Update the guardian ID for this booking
        """
        self.guardian_id = guardian_id
        
    def mark_as_cancelled(self, reason=None):
        """
        Mark this booking as cancelled
        """
        self.status = "cancelled"
        self.cancellation_reason = reason
        
    def is_cancelled(self):
        """
        Check if this booking is cancelled
        """
        return self.status == "cancelled"
        
    def is_active(self):
        """
        Check if this booking is active
        """
        return self.status == "active"
