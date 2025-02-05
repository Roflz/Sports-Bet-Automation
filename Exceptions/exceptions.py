import time

class ControlNotFoundException(Exception):
    """Exception raised when the control is not found within the timeout period."""
    pass

class WindowNotFoundException(Exception):
    pass