import subprocess
import webbrowser
import numpy as np
import psutil
import pyautogui
import win32con
import win32gui
import win32ui
import pygetwindow as gw
from PIL import Image
import cv2
from Exceptions.exceptions import *
from config import TEMP


def capture_window(window_name):
    # Find the window handle
    hwnd = win32gui.FindWindow(None, window_name)  # Replace with the window title
    if not hwnd:
        print("Window not found!")
        raise WindowNotFoundException(f"Window {window_name} not Found")

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
        return False


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
        raise ControlNotFoundException(f"Control {control_image_path} not found in window {window_name}")

    # Get the window position (to adjust relative coordinates)
    hwnd = win32gui.FindWindow(None, window_name)
    if not hwnd:
        print("Window not found!")
        raise WindowNotFoundException(f"Window {window_name} not Found")

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


def wait_for_control_to_be_visible(control_image_path, window_name, timeout=10, threshold=0.8):
    attempts = 0
    while attempts <= timeout:
        if not find_control(window_name, control_image_path, threshold=threshold):
            time.sleep(1)
            attempts += 1
        else:
            return True
    raise ControlNotFoundException(f"Control '{control_image_path}' not found in window '{window_name}' within {timeout} seconds.")

def wait_for_window_to_be_visible(window_name, timeout=10):
    """
    Waits for a window to become visible within a given timeout.

    Args:
        window_name (str): The title of the window to check.
        timeout (int): Maximum time (in seconds) to wait.

    Returns:
        bool: True if the window becomes visible, else raises an exception.
    """
    attempts = 0
    while attempts <= timeout:
        windows = gw.getWindowsWithTitle(window_name)
        if windows and windows[0].isActive:
            return True  # Window is found and visible
        time.sleep(1)
        attempts += 1

    raise WindowNotFoundException(f"Window '{window_name}' not found within {timeout} seconds.")


def keyboard_input(keys, interval=0.05):
    """
    Inputs a sequence of keypresses.

    Args:
        keys (str, list, or dict):
            - A single string (types characters individually)
            - A list of strings and keys (types words, presses keys like "tab", "enter")
            - A dictionary {key: count} (presses key multiple times)
        interval (float): Time delay between keypresses.
    """
    if isinstance(keys, str):
        # Type the string character by character
        pyautogui.write(keys, interval=interval)
    elif isinstance(keys, list):
        for item in keys:
            if isinstance(item, str):
                if len(item) > 1 and item.lower() not in pyautogui.KEYBOARD_KEYS:
                    pyautogui.write(item, interval=interval)  # Type full words
                else:
                    pyautogui.press(item)  # Press special keys like "tab", "enter"
            else:
                raise TypeError(f"Unsupported key type in list: {item}")
            time.sleep(interval)
    elif isinstance(keys, dict):
        for key, count in keys.items():
            if isinstance(key, str):
                for _ in range(count):
                    pyautogui.press(key)
                    time.sleep(interval)
            else:
                raise TypeError(f"Unsupported key type in dictionary: {key}")
    else:
        raise TypeError("keys must be a string, list of strings/keys, or a dictionary {key: count}")



def open_chrome(url):
    chrome_running = any("chrome" in p.name().lower() for p in psutil.process_iter(attrs=["name"]))

    if chrome_running:
        # Open a new tab in the existing Chrome window
        webbrowser.open_new_tab(url)
    else:
        # Start a new Chrome window with the URL
        subprocess.Popen(["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", url])

def open_chrome_and_wait_for_control(self, url, control_name):
    open_chrome(url)
    wait_for_control_to_be_visible()


def scroll_until_visible(control_image_path, scroll_amount=-500, max_attempts=50, delay=0.2):
    """
    Scrolls until a specific control (image) is visible on the screen.

    Args:
        control_image_path (str): Path to the image of the control to find.
        scroll_amount (int): The amount to scroll each attempt (-100 for up, 100 for down).
        max_attempts (int): Maximum number of scrolling attempts.
        delay (float): Time delay between each scroll attempt.

    Returns:
        bool: True if the control was found, False if it wasn't found within the limit.
    """
    attempts = 0

    while attempts < max_attempts:
        try:
            location = pyautogui.locateOnScreen(control_image_path, confidence=0.8)
            if location:
                return True  # Control found
        except pyautogui.ImageNotFoundException:  # Handles missing control
            pass  # Continue scrolling

        pyautogui.scroll(scroll_amount)
        time.sleep(delay)
        attempts += 1

    return False  # Control not found within max_attempts