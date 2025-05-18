class GuardianEntity:
    """
    GuardianEntity represents the core business concept of a guardian (parent).
    This is a pure entity class following clean architecture principles.
    It has no dependencies on frameworks, UI, database, or other external systems.
    """
    
    def __init__(self, id=None, name="", email="", phone="", postcode=""):
        """
        Initialize a new Guardian entity
        """
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.postcode = postcode
    
    def has_valid_contact_info(self):
        """
        Check if the guardian has valid contact information
        """
        return (
            self.name and 
            self.email and 
            self.phone and 
            self.postcode
        )
    
    def update_contact_info(self, name=None, email=None, phone=None, postcode=None):
        """
        Update the guardian's contact information
        """
        if name is not None:
            self.name = name
        
        if email is not None:
            self.email = email
            
        if phone is not None:
            self.phone = phone
            
        if postcode is not None:
            self.postcode = postcode
    
    def get_contact_info(self):
        """
        Get the guardian's contact information as a dictionary
        """
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "postcode": self.postcode
        }
