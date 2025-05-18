class WorkshopEntity:
    """
    WorkshopEntity represents the core business concept of a workshop.
    This is a pure entity class following clean architecture principles.
    It has no dependencies on frameworks, UI, database, or other external systems.
    """
    
    def __init__(self, id=None, title="", date=None, time=None, location="", 
                 max_families=0, max_children=0, current_families=0, current_children=0):
        """
        Initialize a new Workshop entity
        """
        self.id = id
        self.title = title
        self.date = date
        self.time = time
        self.location = location
        self.max_families = max_families
        self.max_children = max_children
        self.current_families = current_families
        self.current_children = current_children
    
    def has_family_capacity(self):
        """
        Check if there is capacity for more families
        """
        return self.current_families < self.max_families
    
    def has_child_capacity(self):
        """
        Check if there is capacity for more children
        """
        return self.current_children < self.max_children
    
    def add_family(self):
        """
        Add a family to the workshop if capacity exists
        """
        if not self.has_family_capacity():
            return False
        
        self.current_families += 1
        return True
    
    def add_children(self, count):
        """
        Add children to the workshop if capacity exists
        """
        if self.current_children + count > self.max_children:
            return False
        
        self.current_children += count
        return True
    
    def remove_family(self):
        """
        Remove a family from the workshop
        """
        if self.current_families > 0:
            self.current_families -= 1
            return True
        return False
    
    def remove_children(self, count):
        """
        Remove children from the workshop
        """
        if self.current_children >= count:
            self.current_children -= count
            return True
        return False
    
    def remaining_family_slots(self):
        """
        Get the number of remaining family slots
        """
        return max(0, self.max_families - self.current_families)
    
    def remaining_child_slots(self):
        """
        Get the number of remaining child slots
        """
        return max(0, self.max_children - self.current_children)
