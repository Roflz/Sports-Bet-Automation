
import time
from PIL import Image

import win32con
import win32gui
import win32ui
from pywinauto import Application
import pyautogui
import ctypes
import numpy as np
import cv2

from config import CONTROLS, PROJECT_PATH, TEMP


class WebInteractor:
    def __init__(self, browser_title=".*Google Chrome.*"):
        # Initialize the connection to the browser window using pywinauto
        self.app = Application(backend="uia").connect(title_re=browser_title)
        self.browser_window = self.app.top_window()
        self.window_name = self.browser_window.element_info.name  # Retrieves the window's title

    def activate_browser(self):
        """Activate the browser window."""
        self.browser_window.set_focus()

    def open_dev_tools(self):
        """Open Developer Tools (F12)."""
        self.browser_window.type_keys('^+i')  # Ctrl + Shift + I
        time.sleep(2)

    def switch_to_console(self):
        """Switch to the Console tab in Developer Tools."""
        self.browser_window.type_keys('^{TAB}')  # Switch to Console tab
        time.sleep(1)

    def inject_js(self, js_code):
        """Inject JavaScript code into the browser's console."""
        self.browser_window.type_keys(js_code + '{ENTER}')
        time.sleep(1)

    def get_element_coordinates(self, css_selector):
        """Get the coordinates (X, Y) of an element using JavaScript."""
        js_code = f"""
        var element = document.querySelector('{css_selector}');
        if (element) {{
            var rect = element.getBoundingClientRect();
            var coordinates = {{ x: rect.left + window.scrollX, y: rect.top + window.scrollY }};
            console.log(coordinates);  // This will log coordinates in the console
        }} else {{
            console.log("Element not found.");
        }}
        """
        self.inject_js(js_code)
        time.sleep(1)

    def click_at_coordinates(self, x, y):
        """Click at a specific (X, Y) screen coordinate using pyautogui."""
        print(f"Clicking at coordinates: ({x}, {y})")
        pyautogui.moveTo(x, y)
        pyautogui.click()

    def get_coordinates_from_console(self):
        """Retrieve the coordinates printed in the console using OCR or other methods."""
        # This method would require you to manually get the coordinates from the console
        # in the Developer Tools as pywinauto doesn't directly capture console output.
        print("Get the coordinates from the Developer Tools console manually.")
        return None, None  # Placeholder for manual retrieval

    def click_element_by_selector(self, css_selector):
        """Get element coordinates and click on it."""
        self.get_element_coordinates(css_selector)
        # You would manually capture the coordinates or use OCR here
        x, y = self.get_coordinates_from_console()
        if x is not None and y is not None:
            self.click_at_coordinates(x, y)
        else:
            print(f"Failed to click element: {css_selector}")

    def click_element_by_aria_label(self, aria_label):
        """Click on an element by its aria-label attribute."""
        css_selector = f'[aria-label="{aria_label}"]'
        self.click_element_by_selector(css_selector)

    def click_control(self, control_name):
        click_control(self.window_name, f"{CONTROLS}\\{control_name}.png")

    def zoom_out_chrome(times=2):
        """
        Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses.

        :param times: Number of times to zoom out (default: 2).
        """
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)  # Small delay to ensure the zoom registers

def capture_window(window_name):
    # Find the window handle
    hwnd = win32gui.FindWindow(None, window_name)  # Replace with the window title
    if not hwnd:
        print("Window not found!")
        return None

    # Get the window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    # Capture the window
    hdesktop = win32gui.GetDesktopWindow()
    hwndDC = win32gui.GetWindowDC(hdesktop)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(bitmap)

    saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
    bitmap.SaveBitmapFile(saveDC, f"{TEMP}\\window_screenshot.bmp")

    # Convert to an image
    img = Image.open(f"{TEMP}\\window_screenshot.bmp")
    return cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)

def find_control(window_name, control_image_path, threshold=0.8):
    """
    Locate a UI control in the given window using template matching and return its center coordinates.

    :param window_name: The title of the window to capture.
    :param control_image_path: Path to the reference image of the control.
    :param threshold: Similarity threshold (default: 0.8).
    :return: (center_x, center_y) coordinates of the control if found, otherwise None.
    """
    # Capture the window
    window_image = capture_window(window_name)
    if window_image is None:
        return None

    # Load the reference control image
    control_image = cv2.imread(control_image_path, cv2.IMREAD_UNCHANGED)
    if control_image is None:
        print("Error: Could not load control image.")
        return None

    # Convert images to grayscale for template matching
    window_gray = cv2.cvtColor(window_image, cv2.COLOR_BGR2GRAY)
    control_gray = cv2.cvtColor(control_image, cv2.COLOR_BGR2GRAY)

    # Perform template matching
    result = cv2.matchTemplate(window_gray, control_gray, cv2.TM_CCOEFF_NORMED)

    # Get the best match location
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if match confidence is above threshold
    if max_val >= threshold:
        control_w, control_h = control_gray.shape[::-1]  # Get control width and height
        center_x = max_loc[0] + control_w // 2  # Calculate center X
        center_y = max_loc[1] + control_h // 2  # Calculate center Y
        print(f"Control found at center ({center_x}, {center_y}) with confidence {max_val}")
        return center_x, center_y
    else:
        print("Control not found.")
        return None

def click_control(window_name, control_image_path, threshold=0.8):
    """
    Clicks on a UI control found using image matching.

    :param window_name: The title of the target window.
    :param control_image_path: Path to the control's image.
    :param threshold: Confidence threshold (default: 0.8).
    """
    # Locate the control
    control_location = find_control(window_name, control_image_path, threshold)
    if not control_location:
        print("Control not found, cannot click.")
        return False

    # Get the window position (to adjust relative coordinates)
    hwnd = win32gui.FindWindow(None, window_name)
    if not hwnd:
        print("Window not found!")
        return False

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    # Convert relative coordinates to absolute screen coordinates
    control_x, control_y = control_location
    screen_x = left + control_x
    screen_y = top + control_y

    # Move the mouse to the control and click
    pyautogui.moveTo(screen_x, screen_y, duration=0.2)  # Smooth move
    pyautogui.click()

    print(f"Clicked control at ({screen_x}, {screen_y})")
    return True

if __name__ == "__main__":
    # Example usage
    web_interactor = WebInteractor()

    web_interactor.activate_browser()  # Focus the browser window
    web_interactor.zoom_out_chrome()
    time.sleep(3)
    web_interactor.click_control("nba_button")
    time.sleep(1)

    # Example: Click an element by its aria-label
    web_interactor.click_element_by_aria_label('NBA')
