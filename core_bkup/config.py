from dataclasses import dataclass


# a singleton, from the innertubes 
@dataclass
class Config:  
    _instance = None  # Class variable to store the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # If no instance exists, create one
            cls._instance = super().__new__(cls)
        return cls._instance  # Return the existing instance

    def __init__(self, invariants=True):
        # This __init__ will be called every time you try to create an instance,
        # but the actual object creation only happens once in __new__.
        # You might want to handle re-initialization carefully or only allow it once.
        if not hasattr(self, '_initialized'): # Prevent re-initialization logic
            self.invariants = invariants 
            self._initialized = True 


config = Config() 