import time

from utils.control_state import control_state, control_flags
from config import CONTROLS
from utils.utils import find_control, keyboard_input


class ControlMeta(type):
    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            # Exclude methods that should not be wrapped (e.g., 'excluded_method')
            if callable(attr_value) and not attr_name.startswith("__") and not cls.should_exclude(attr_name):
                dct[attr_name] = cls.wrap_method(attr_value)  # Apply wrapper
        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def wrap_method(method):
        def wrapped_method(*args, **kwargs):
            result = method(*args, **kwargs)  # Run the original method
            check_control()  # Check the control condition after execution
            return result
        return wrapped_method

    @staticmethod
    def should_exclude(method_name):
        # List of methods to exclude from wrapping
        excluded_methods = ['initialize', 'login_bet365', 'login', 'wait_and_click_log_failure_to_csv', 'wait_and_click_log_failure_to_console', 'activate_browser', 'refresh_page', 'make_bets']
        return method_name in excluded_methods


def toggle_pause():
    """Toggle the pause state in control_flags."""
    control_flags["pause"] = not control_flags["pause"]
    # Toggle pause state
    if control_flags["pause"]:
        print("Script Paused... Press Alt+P to Resume")
    else:
        print("Script Resumed!")

def check_control():
    """Check each control flag and execute its corresponding action."""
    if control_flags["pause"]:
        handle_pause()
    # if bet_changed():
    #     handle_bet_changed()
    if random_logout():
        handle_random_logout()
    if reset_location_verifier():
        handle_reset_location_verifier()

def handle_pause():
    """Pause the execution based on the global flag."""
    while control_flags["pause"]:
        time.sleep(0.1)  # Sleep to prevent busy-waiting

#  Checks if there was a random logout
def random_logout():
    window_name = '.*bet365.*'
    control_image_path_1 = f"{CONTROLS}\\bet365\\login\\login_button.png"
    control_location_1 = find_control(control_image_path_1, window_name=window_name)

    control_image_path_2 = f"{CONTROLS}\\bet365\\login\\random_logout_error.png"
    control_location_2 = find_control(control_image_path_2, window_name=window_name)

    if control_location_1 or control_location_2:
        return True
    else:
        return False

# Handle Random Logout with a passed object
def handle_random_logout():
    web_interactor_bet365 = control_state.get_web_interactor_bet365()  # Retrieve instance
    if web_interactor_bet365:  # Ensure the instance is initialized
        print("Random logout detected.")
        web_interactor_bet365.refresh_page()
        web_interactor_bet365.login_bet365()
    else:
        print("Bet365 instance not initialized.")

def reset_location_verifier():
    window_name = '.*bet365.*'
    control_image_path_1 = f"{CONTROLS}\\bet365\\reset_location_verifier.png"
    control_location_1 = find_control(control_image_path_1, window_name=window_name)

    control_image_path_2 = f"{CONTROLS}\\bet365\\confirming_location.png"
    control_location_2 = find_control(control_image_path_2, window_name=window_name)

    if control_location_1 or control_location_2:
        print('reset location verifier')
        return True
    else:
        return False

def handle_reset_location_verifier():
    web_interactor_bet365 = control_state.get_web_interactor_bet365()  # Retrieve instance
    keyboard_input(['win', 'XpointVerifyGeolocationInstaller.exe', 'enter'])
    time.sleep(4)
    web_interactor_bet365.refresh_page()

    return True
