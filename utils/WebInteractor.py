import os

from utils.ControlMeta import ControlMeta
from utils.utils import *


class WebInteractor(metaclass=ControlMeta):
    def __init__(self, leagues):
        self.window_name = None
        self.browser_window = None
        self.app = None
        self.leagues = leagues

    def activate_browser(self):
        """Activate the browser window."""
        self.app = Application(backend="uia").connect(title_re=".*Google Chrome.*")
        self.browser_window = self.app.top_window()
        full_title = self.browser_window.element_info.name
        self.browser_window.set_focus()
        print(f"Full title: {full_title}")
        print(f"Using window pattern: {self.window_name}")

    def click_control(self, control_name, threshold=0.8):
        return click_control(f"{CONTROLS}/{self.sportsbook}/{control_name}.png", threshold=threshold)

    def wait_and_click_log_failure_to_csv(self, control_path, bet_dict, failure_message, timeout=5, threshold=0.95):
        """Waits for a control to be visible, then clicks it. Logs failure, prints message, pauses for input, refreshes, and waits."""

        if not isinstance(control_path, list):
            control_path = [control_path]  # Convert single string to list for consistency

        # Wait for any control to be visible
        control_found = False
        for path in control_path:
            if wait_for_control_to_be_visible(path, timeout=timeout, threshold=threshold):
                control_found = path  # Store the first found control path
                break

        if not control_found:
            if pause_and_log_failure(failure_message, bet_dict):  # Pause if failure, decide whether to continue
                pass
            else:
                self.refresh_page()  # Refresh page if failure
                time.sleep(3)
                return False
        else:
            click_control(control_found, threshold=threshold)
            return True

    def wait_and_click_log_failure_to_console(self, control_path, failure_message, timeout=5, threshold=0.95,
                                              window_name=None):
        """Waits for a control to be visible, then clicks it. Logs failure, prints message, pauses for input, refreshes, and waits."""
        if not wait_for_control_to_be_visible(control_path, window_name=window_name, timeout=timeout, threshold=threshold):
            if pause_and_print_failure(failure_message + ". Failure at wait to be visible"):
                pass
            else:
                self.refresh_page()  # Assuming you have a refresh method
                time.sleep(3)  # Wait a few seconds after refreshing
                return False
        click_control(control_path, window_name=window_name, threshold=threshold)
        return True

    def refresh_page(self):
        """Refreshes the page by simulating an F5 key press."""
        self.activate_browser()
        pyautogui.press('f5')
        time.sleep(2)  # Wait a few seconds to allow reload

    def zoom_out_chrome(self, times=2):
        """Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses."""
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)

    def zoom_in_chrome(self, times=2):
        """Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses."""
        for _ in range(times):
            pyautogui.hotkey("ctrl", "+")
            time.sleep(0.2)

    def set_zoom(self):
        pyautogui.hotkey("ctrl", "0")

    def login(self, control_path, steps_1, keyboard_strokes, steps_2):
        for step, threshold in steps_1:
            control_path_step_1 = f"{control_path}\\{step}.png"
            if not self.wait_and_click_log_failure_to_console(control_path_step_1, f"Login failed, could not find {step}", threshold=threshold):
                return False
            time.sleep(0.2)
        keyboard_input(keyboard_strokes)

        for step, threshold in steps_2:
            control_path_step_2 = f"{control_path}\\{step}.png"
            if not self.wait_and_click_log_failure_to_console(control_path_step_2, f"Login failed, could not find {step}", threshold=threshold):
                return False
            time.sleep(0.2)
        return True

    def choose_league(self, league, control_path):
        league_controls = {"nfl": "nfl_button", "nba": "nba_button"}
        control = league_controls.get(league)
        if control:
            control_path = f"{control_path}\\{league}\\{control}.png"
            if not wait_for_control_to_be_visible(control_path, timeout=5):
                if not pause_and_print_failure(f"Failed to find league button for {league}"):
                    return False
            if not click_control(control_path):
                if not pause_and_print_failure(f"Failed to click league button for {league}"):
                    return False
        return True

    def open_chrome_and_wait_for_window(self, url, window_name):
        if not open_chrome(url):
            if not pause_and_print_failure(f"Failed to open chrome window at {url}"):
                return False
        if not wait_for_window_to_be_visible(window_name):
            if not pause_and_print_failure(f"Chrome window did not become visible at {url}"):
                return False
        return True
