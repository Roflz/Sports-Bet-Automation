import time

class ControlNotFoundException(Exception):
    """Exception raised when the control is not found within the timeout period."""
    pass

def wait_for_control_to_be_visible(control, window_name, timeout=10):
    """
    Waits for a control to become visible within a specified timeout period.

    Args:
        control (str): The control identifier.
        window_name (str): The name of the window where the control should be found.
        timeout (int): Maximum time (in seconds) to wait for the control.

    Returns:
        bool: True if the control is found.

    Raises:
        ControlNotFoundException: If the control is not found within the timeout.
    """
    attempts = 0
    while attempts <= timeout:
        if not find_control(window_name, control):
            time.sleep(1)
            attempts += 1
        else:
            return True

    raise ControlNotFoundException(f"Control '{control}' not found in window '{window_name}' within {timeout} seconds.")
