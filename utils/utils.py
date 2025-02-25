import csv
import functools
import os
import re
import smtplib
import subprocess
import webbrowser
from email.mime.text import MIMEText

import keyboard
import mss
import numpy as np
import psutil
import pyautogui
import pytesseract
import win32con
import win32gui
import win32ui
import pygetwindow as gw
from PIL import Image
import cv2
from pywinauto import Application
from datetime import datetime

from Exceptions.exceptions import *
from config import TEMP, CONTROLS


def find_window_by_partial_title(partial_title):
    def callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if re.search(partial_title, title, re.IGNORECASE):
                result.append(hwnd)
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None  # Return the first matching window handle

# This function checks the currently focused window and returns the window title if it's Chrome
def get_chrome_window_name():
    def callback(hwnd, window_list):
        window_name = win32gui.GetWindowText(hwnd)
        if "Google Chrome" in window_name and win32gui.IsWindowVisible(hwnd):  # Ensure it's visible
            window_list.append(window_name)

    chrome_windows = []
    win32gui.EnumWindows(callback, chrome_windows)

    if chrome_windows:
        return chrome_windows[0]  # Return the first (topmost) Chrome window
    else:
        print("No visible Chrome window found!")
        return None

def capture_window(window_name=None):
    # If no window name is provided, dynamically get the active Chrome window name
    if window_name is None:
        window_name = get_chrome_window_name()

    if window_name is None:
        print("No Chrome window found!")
        raise WindowNotFoundException("Chrome window not found!")

    # Find the window handle using the updated window name
    for trys in range(10):
        hwnd = find_window_by_partial_title(window_name)  # Replace with your window search logic
        if hwnd:
            break
        trys += 1
        time.sleep(0.1)

    if not hwnd:
        print(f"Window with title '{window_name}' not found!")
        raise WindowNotFoundException(f"Window '{window_name}' not Found")

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


def find_control(control_image_path, window_name=None, threshold=0.8, output_path="temp\\annotated_output.png"):
    """
    Locate a UI control in the given window using template matching and return its center coordinates.
    The function also saves an annotated image to disk:
      - If found, a rectangle is drawn around the control.
      - If not found, "Control not found" is written on the image.

    :param window_name: The title of the window to capture.
    :param control_image_path: Path to the reference image of the control.
    :param threshold: Similarity threshold (default: 0.8).
    :param output_path: File path to save the annotated image.
    :return: (center_x, center_y) coordinates if control is found, otherwise False.
    """
    # Capture the window image (ensure capture_window is defined elsewhere)
    window_image = capture_window(window_name=window_name)
    if window_image is None:
        return False

    # Load the reference control image
    control_image = cv2.imread(control_image_path, cv2.IMREAD_UNCHANGED)
    if control_image is None:
        print("Error: Could not load control image.")
        return False

    # Convert images to grayscale for template matching
    window_gray = cv2.cvtColor(window_image, cv2.COLOR_BGR2GRAY)
    control_gray = cv2.cvtColor(control_image, cv2.COLOR_BGR2GRAY)

    # Perform template matching
    result = cv2.matchTemplate(window_gray, control_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Create a copy of the window image to annotate
    annotated_image = window_image.copy()

    # Check if match confidence is above threshold
    if max_val >= threshold:
        control_w, control_h = control_gray.shape[::-1]
        center_x = max_loc[0] + control_w // 2
        center_y = max_loc[1] + control_h // 2

        # Draw a rectangle around the found control
        top_left = max_loc
        bottom_right = (max_loc[0] + control_w, max_loc[1] + control_h)
        cv2.rectangle(annotated_image, top_left, bottom_right, (0, 255, 0), 2)

        # Save the annotated image
        cv2.imwrite(output_path, annotated_image)
        return (center_x, center_y)
    else:
        # Annotate with a message if control is not found
        cv2.putText(annotated_image, "Control not found", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imwrite(output_path, annotated_image)
        return False


def click_control(control_image_path, window_name=None, threshold=0.8):
    """
    Clicks on a UI control found using image matching.

    :param window_name: The title of the target window.
    :param control_image_path: Path(s) to the control's image (string or list of strings).
    :param threshold: Confidence threshold (default: 0.8).
    """
    if not isinstance(control_image_path, list):
        control_image_path = [control_image_path]  # Convert single string to list

    # Locate the control
    control_location = None
    for path in control_image_path:
        control_location = find_control(path, window_name, threshold)
        if control_location:
            break  # Stop at the first found control

    if not control_location:
        print("Control not found, cannot click.")
        return False

    # Get the window position (to adjust relative coordinates)
    if not window_name:
        window_name = get_chrome_window_name()

    # Find the window handle using the updated window name
    for _ in range(10):
        hwnd = find_window_by_partial_title(window_name)  # Replace with your window search logic
        if hwnd:
            break
        time.sleep(0.1)
    else:
        print(f"Window with title '{window_name}' not found!")
        raise WindowNotFoundException(f"Window '{window_name}' not Found")

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    # Convert relative coordinates to absolute screen coordinates
    control_x, control_y = control_location
    screen_x = left + control_x
    screen_y = top + control_y

    # Move the mouse to the control and click
    pyautogui.moveTo(screen_x, screen_y, duration=0.2)  # Smooth move
    time.sleep(0.1)
    pyautogui.click()

    return True

def drag_control(control_image_path, window_name=None, threshold=0.8, drag_distance=200, drag_duration=0.4):
    """
    Clicks and drags a UI control horizontally using relative coordinates inside a window.

    Args:
        control_image_path (str): Path to the control's image.
        window_name (str): The title of the target window.
        threshold (float): Confidence threshold for image matching.
        drag_distance (int): Distance to drag (positive for right, negative for left).
        drag_duration (float): Duration of the drag motion.

    Returns:
        bool: True if the drag action was performed successfully, False otherwise.
    """
    # Locate the control
    control_location = find_control(control_image_path, window_name, threshold)
    if not control_location:
        print("Control not found, cannot drag.")
        return False

    # Get the window position (to adjust relative coordinates)
    window_name = get_chrome_window_name()
    hwnd = find_window_by_partial_title(window_name)
    if not hwnd:
        print("Window not found!")
        return False

    left, top, _, _ = win32gui.GetWindowRect(hwnd)

    # Convert relative coordinates to absolute screen coordinates
    control_x, control_y = control_location
    start_x = left + control_x
    start_y = top + control_y
    end_x = start_x + drag_distance  # Target x-coordinate for drag

    # Perform the drag action
    pyautogui.moveTo(start_x, start_y, duration=0.2)  # Move to start position
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.moveTo(end_x, start_y, duration=drag_duration)  # Drag horizontally
    time.sleep(0.1)
    pyautogui.mouseUp()

    return True


def wait_for_control_to_be_visible(control_image_path, window_name=None, timeout=10, threshold=0.8):
    attempts = 0
    if window_name is None:
        window_name = get_chrome_window_name()  # Assuming this function returns the window name

    if not isinstance(control_image_path, list):
        control_image_path = [control_image_path]  # Convert single path to list for consistency

    while attempts <= timeout:
        for path in control_image_path:
            if find_control(path, window_name=window_name, threshold=threshold):
                return True  # Return immediately if any control is found
        time.sleep(1)
        attempts += 1

    return False  # Return False if none of the controls are found within the timeout

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
        if windows:
            return True  # Window is found and visible
        time.sleep(1)
        attempts += 1

    return False


def keyboard_input(keys, interval=0.05):
    if not isinstance(keys, list):
        raise TypeError("keys must be a list of strings or tuples.")

    for item in keys:
        if isinstance(item, str):
            if len(item) > 1 and item.lower() not in pyautogui.KEYBOARD_KEYS:
                pyautogui.write(item, interval=interval)  # Type full words
            else:
                # Handle special keys like 'win'
                if item.lower() == 'win':
                    keyboard.press('win')  # Press the Windows key
                    time.sleep(interval)
                    keyboard.release('win')  # Release the Windows key
                else:
                    pyautogui.press(item)  # Press regular special keys like "tab", "enter"
        elif isinstance(item, tuple):
            # Press multiple keys simultaneously
            for key in item:
                keyboard.press(key)
            time.sleep(0.05)  # Short delay while keys are held down
            for key in reversed(item):
                keyboard.release(key)  # Release keys in reverse order
        else:
            raise TypeError(f"Unsupported key type in list: {item}")

        time.sleep(interval)  # Delay between key presses


def open_chrome(url):
    chrome_running = any("chrome" in p.name().lower() for p in psutil.process_iter(attrs=["name"]))

    if chrome_running:
        # Open a new tab in the existing Chrome window
        webbrowser.open_new_tab(url)
    else:
        # Start a new Chrome window with the URL
        subprocess.Popen(["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", url])
    return True

def open_chrome_and_wait_for_control(self, url, control_name):
    open_chrome(url)
    wait_for_control_to_be_visible()


def scroll_until_visible(control_image_path, window_name=None, threshold=0.8, scroll_amount=-300, max_attempts=20, delay=0.3):
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
            location = find_control(control_image_path, window_name=window_name, threshold=threshold)
            if location:
                return location # Control found
        except pyautogui.ImageNotFoundException:  # Handles missing control
            pass  # Continue scrolling

        pyautogui.scroll(scroll_amount)
        time.sleep(delay)
        attempts += 1

    return False

def scroll_until_visible_and_click(control_image_path, window_name=None, threshold=0.8, scroll_amount=-300, max_attempts=20, delay=0.3):
    """
    Scrolls until a specific control (image) is visible on the screen and clicks it.

    Args:
        control_image_path (str): Path to the image of the control to find.
        window_name (str): The title of the target window.
        threshold (float): Confidence threshold for image matching.
        scroll_amount (int): The amount to scroll each attempt (-100 for up, 100 for down).
        max_attempts (int): Maximum number of scrolling attempts.
        delay (float): Time delay between each scroll attempt.

    Returns:
        bool: True if the control was found and clicked, False if it wasn't found within the limit.
    """
    attempts = 0

    while attempts < max_attempts:
        try:
            location = find_control(control_image_path, window_name=window_name, threshold=threshold)
            if location:
                # Click the found control
                time.sleep(0.3)
                return click_control(control_image_path, window_name=window_name, threshold=threshold)
        except pyautogui.ImageNotFoundException:
            pass  # Continue scrolling if the control is not found

        pyautogui.scroll(scroll_amount)
        time.sleep(delay)
        attempts += 1

    return False

def drag_until_visible_and_click(control_image_path, target_image_path, window_name=None, threshold=0.8, drag_distance=200, drag_duration=0.4, max_attempts=10, delay=0.3):
    """
    Clicks and drags horizontally until the target control is visible, then clicks it.

    Args:
        control_image_path (str): Image path of the control to initiate the drag.
        target_image_path (str): Image path of the control to click once visible.
        window_name (str): Name of the window to search within.
        threshold (float): Similarity threshold for image matching.
        drag_distance (int): Distance to drag each attempt (positive for right, negative for left).
        drag_duration (float): Duration of the drag motion.
        max_attempts (int): Maximum number of dragging attempts.
        delay (float): Time delay between each drag attempt.

    Returns:
        bool: True if the target control was found and clicked, False otherwise.
    """
    attempts = 0

    while attempts < max_attempts:
        # Check if the target control is visible
        try:
            location = find_control(target_image_path, window_name=window_name, threshold=threshold)
            if location:
                click_control(target_image_path, window_name=window_name, threshold=threshold)
                return True
        except pyautogui.ImageNotFoundException:
            pass  # Continue dragging if target is not found

        # Try finding the control to initiate the drag
        try:
            start_location = find_control(control_image_path, window_name=window_name, threshold=threshold)
            if start_location:
                drag_control(control_image_path, window_name=window_name, threshold=threshold, drag_distance=drag_distance)
                time.sleep(delay)
        except pyautogui.ImageNotFoundException:
            pass  # Continue searching if control is not found

        attempts += 1

    return False  # Return False if target control was never found

def move_mouse_by(x_offset, y_offset):
    """
    Moves the mouse cursor by a specified number of pixels in the x and y direction.

    Args:
        x_offset (int): Number of pixels to move the mouse horizontally.
        y_offset (int): Number of pixels to move the mouse vertically.
    """
    # Get current mouse position
    current_x, current_y = pyautogui.position()

    # Move mouse by the offsets
    new_x = current_x + x_offset
    new_y = current_y + y_offset

    # Move the mouse to the new position
    pyautogui.moveTo(new_x, new_y)

def click_point_til_control_visible_click_control(control_image_path, click_x_rel, click_y_rel, window_name=None, threshold=0.8, max_attempts=50, delay=0.3):
    """
    Clicks at a specific point relative to the window until control 2 is visible, then clicks control 2.

    Args:
        control_image_path_2 (str): Path to the second control image (the one we click after seeing it).
        window_name (str): Name of the window to search within.
        click_x_rel (int): The x-coordinate relative to the window where the mouse will click.
        click_y_rel (int): The y-coordinate relative to the window where the mouse will click.
        threshold (float): Similarity threshold for image matching.
        max_attempts (int): Maximum number of scrolling attempts.
        delay (float): Time delay between each click attempt.

    Raises:
        ControlNotFoundException: If control 2 is not found after all attempts.
    """
    # If no window name is provided, dynamically get the active Chrome window name
    if window_name is None:
        window_name = get_chrome_window_name()

    if window_name is None:
        print("No Chrome window found!")
        raise WindowNotFoundException("Chrome window not found!")

    # Get the window position using pywinauto
    app = Application(backend="uia").connect(title_re=window_name)
    window = app.top_window()
    window_rect = window.rectangle()  # Get the window's coordinates (left, top, right, bottom)

    window_x = window_rect.left
    window_y = window_rect.top

    # Calculate the absolute coordinates by adding the window's position to the relative coordinates
    click_x = window_x + click_x_rel
    click_y = window_y + click_y_rel

    attempts = 0

    while attempts < max_attempts:
        try:
            # Try finding the second control (control to click when it appears)

            if find_control(control_image_path, threshold=threshold):
                click_control(control_image_path, threshold=threshold)
                return True  # Exit after clicking control 2

            # If control 2 isn't found, click at the specified relative point
            pyautogui.moveTo(click_x, click_y)
            time.sleep(0.2)
            pyautogui.click(click_x, click_y)  # Click at the calculated position
            time.sleep(delay)  # Pause between clicks

        except pyautogui.ImageNotFoundException:
            pass  # Continue if control 2 isn't found

        attempts += 1

    if find_control(control_image_path, threshold=threshold):
        click_control(control_image_path, threshold=threshold)
        return True  # Exit after clicking control 2

    # If we exhaust all attempts and find nothing, raise an exception
    return False

def extract_text_from_pillow_image(image):
    """
    Extracts text from a Pillow image using Tesseract OCR.

    Args:
        image (PIL.Image.Image): A Pillow image object.

    Returns:
        str: Extracted text from the image.
    """
    text = pytesseract.image_to_string(image)
    return text


def extract_line_and_price(text):
    """
    Extracts up to two numbers from the given text as strings.

    Args:
        text (str): The input text containing one or two numbers.

    Returns:
        tuple: (line, price) where both are strings. If only one number is found, price is None.
    """
    numbers = re.findall(r'-?\d+', text)  # Find all numbers (including negatives)

    if not numbers:
        raise ValueError("Could not find any numbers in the text")

    line = numbers[0]  # First number is always present
    price = numbers[1] if len(numbers) > 1 else None  # Second number if available

    return line, price

def get_window_position(window_name):
    """
    Get the absolute position (x, y) of the top-left corner of a window.

    Args:
        window_name (str): The title of the window.

    Returns:
        tuple: (x, y) coordinates of the window's top-left corner.
    """
    hwnd = find_window_by_partial_title(window_name)
    if not hwnd:
        raise Exception(f"Window '{window_name}' not found")

    rect = win32gui.GetWindowRect(hwnd)  # Get window position
    return rect[0], rect[1]  # (left, top)

def take_screenshot_over(control_coordinates, window_name=None, distance_to_right=609, screenshot_width=87, screenshot_height=38):
    """
    Takes a screenshot centered around a point, relative to a control, and outputs the center coordinates.

    Args:
        control_coordinates (tuple): (x, y) relative to the window (top-left corner).
        distance_to_right (int): The horizontal distance to the right of the control (in pixels).
        window_name (str): The title of the window where the control exists.
        screenshot_width (int): The width of the screenshot region (default 87px).
        screenshot_height (int): The height of the screenshot region (default 38px).

    Returns:
        tuple: (PIL Image, center_coordinates) where:
            - PIL Image is the screenshot.
            - center_coordinates is a tuple (center_x, center_y).
    """
    # If no window name is provided, dynamically get the active Chrome window name
    if window_name is None:
        window_name = get_chrome_window_name()

    if window_name is None:
        print("No Chrome window found!")
        raise WindowNotFoundException("Chrome window not found!")

    # Get absolute window position
    window_x, window_y = get_window_position(window_name)

    # Convert control coordinates to absolute screen coordinates
    center_x = window_x + control_coordinates[0] + distance_to_right
    center_y = window_y + control_coordinates[1]

    # Adjust coordinates to make the screenshot centered
    x = int(center_x - screenshot_width / 2)
    y = int(center_y - screenshot_height / 2)

    # Take the screenshot
    screenshot = take_screenshot_mss({"top": y, "left": x, "width": screenshot_width, "height": screenshot_height})

    # Return the screenshot and the center coordinates
    return screenshot, (center_x, center_y)

def take_screenshot_under(control_coordinates, window_name=None, distance_to_right=872, screenshot_width=87, screenshot_height=38):
    """
    Takes a screenshot centered around a point, relative to a control.

    Args:
        control_coordinates (tuple): (x, y) relative to the window (top-left corner).
        distance_to_right (int): The horizontal distance to the right of the control (in pixels).
        window_name (str): The title of the window where the control exists.
        screenshot_width (int): The width of the screenshot region (default 87px).
        screenshot_height (int): The height of the screenshot region (default 38px).

    Returns:
        PIL Image: Screenshot as a PIL Image object.
    """
    # If no window name is provided, dynamically get the active Chrome window name
    if window_name is None:
        window_name = get_chrome_window_name()

    if window_name is None:
        print("No Chrome window found!")
        raise WindowNotFoundException("Chrome window not found!")

    # Get absolute window position
    window_x, window_y = get_window_position(window_name)

    # Convert control coordinates to absolute screen coordinates
    center_x = window_x + control_coordinates[0] + distance_to_right
    center_y = window_y + control_coordinates[1]

    # Adjust coordinates to make the screenshot centered
    x = int(center_x - screenshot_width / 2)
    y = int(center_y - screenshot_height / 2)

    # Take the screenshot
    screenshot = take_screenshot_mss({"top": y, "left": x, "width": screenshot_width, "height": screenshot_height})

    return screenshot, (center_x, center_y)

def take_screenshot_side(control_coordinates, window_name=None, distance_to_right=728, screenshot_width=87, screenshot_height=38):
    """
    Takes a screenshot centered around a point, relative to a control.

    Args:
        control_coordinates (tuple): (x, y) relative to the window (top-left corner).
        distance_to_right (int): The horizontal distance to the right of the control (in pixels).
        window_name (str): The title of the window where the control exists.
        screenshot_width (int): The width of the screenshot region (default 87px).
        screenshot_height (int): The height of the screenshot region (default 38px).

    Returns:
        PIL Image: Screenshot as a PIL Image object.
    """
    # If no window name is provided, dynamically get the active Chrome window name
    if window_name is None:
        window_name = get_chrome_window_name()

    if window_name is None:
        print("No Chrome window found!")
        raise WindowNotFoundException("Chrome window not found!")

    # Get absolute window position
    window_x, window_y = get_window_position(window_name)

    # Convert control coordinates to absolute screen coordinates
    center_x = window_x + control_coordinates[0] + distance_to_right
    center_y = window_y + control_coordinates[1]

    # Adjust coordinates to make the screenshot centered
    x = int(center_x - screenshot_width / 2)
    y = int(center_y - screenshot_height / 2)

    # Take the screenshot
    screenshot = take_screenshot_mss({"top": y, "left": x, "width": screenshot_width, "height": screenshot_height})

    return screenshot, (center_x, center_y)

def take_screenshot_mss(region):
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)


def append_dict_to_csv(data_dict, filename, result=None):
    """
    Appends data from a dictionary to an existing CSV file, ensuring a specific column order.

    Args:
        data_dict (dict): The dictionary containing data to be added to the CSV file.
        filename (str): The name of the CSV file to append to.
        result (str): The result to append as the 'result' column.

    Returns:
        None
    """
    # Define the exact order of columns
    field_order = [
        "EV", "Price Target", "Team", "league", "Price", "Book",
        "Position", "Time Until", "Player", "Game", "Type", "Line", "result"
    ]

    # Ensure the dictionary contains all necessary keys (missing keys will be empty)
    ordered_data = {key: data_dict.get(key, "") for key in field_order}

    # Add 'result' if provided
    if result is not None:
        ordered_data["result"] = result

    # Check if the file exists to determine whether we need to write headers
    try:
        with open(filename, mode='r', newline='') as file:
            file_exists = bool(file.readline())
    except FileNotFoundError:
        file_exists = False

    # Open the file in append mode to add data
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_order)

        # Write the header if the file is new
        if not file_exists:
            writer.writeheader()

        # Write the data from the dictionary as a row
        writer.writerow(ordered_data)

    print(f"Data has been appended to {filename}")

def is_bet_in_csv(player, bet_type, game, filename=f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv"):
    """
    Checks if a bet with the given player, bet type, and game already exists in the CSV file.

    Args:
        player (str): The player's name.
        bet_type (str): The bet type (e.g., assists, points).
        game (str): The game description.
        filename (str): The name of the CSV file to check.

    Returns:
        bool: True if a matching bet is found, False otherwise.
    """
    try:
        with open(filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Player'] == player and row['Type'] == bet_type and row['Game'] == game:
                    return True
    except FileNotFoundError:
        # If the file does not exist, assume no previous bets are saved
        return False
    return False

# def pause_and_log_failure(failure_message, bet_dict):
#     # Create a more descriptive failure message, including bet details like player, price, and lines
#     print_bet_details(bet_dict)
#     print(f"Failure: {failure_message}")
#     print("Press 'Ctrl+L' to log the failure and move to next bet, or 'Ctrl+C' to continue without logging.")
#
#     result = None  # Store user choice
#
#     def set_result(value):
#         nonlocal result
#         result = value
#
#     # Register hotkeys
#     keyboard.add_hotkey('ctrl+l', lambda: set_result(False))  # Log failure
#     keyboard.add_hotkey('ctrl+c', lambda: set_result(True))   # Continue
#
#     # Wait for user input
#     while result is None:
#         time.sleep(0.1)
#
#     # Cleanup hotkeys
#     keyboard.remove_hotkey('ctrl+l')
#     keyboard.remove_hotkey('ctrl+c')
#
#     # Log failure if needed
#     if result is False:
#         append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", failure_message)
#
#     return result
#
#
# def pause_and_print_failure(failure_message):
#     print(f"Failure: {failure_message}")
#     print("Press 'Ctrl+N' to move to the next book, or 'Ctrl+C' to continue.")
#
#     result = None  # Store user choice
#
#     def set_result(value):
#         nonlocal result
#         result = value
#
#     # Register hotkeys
#     keyboard.add_hotkey('ctrl+n', lambda: set_result(False))  # Move to next book
#     keyboard.add_hotkey('ctrl+c', lambda: set_result(True))   # Continue
#
#     # Wait for user input
#     while result is None:
#         time.sleep(0.1)
#
#     # Cleanup hotkeys
#     keyboard.remove_hotkey('ctrl+n')
#     keyboard.remove_hotkey('ctrl+c')
#
#     return result

def scroll_to_top():
    """Scrolls to the top of the page by simulating multiple scroll-up actions."""
    pyautogui.scroll(10000)  # Large positive number to ensure scrolling to the top

def print_bet_details(bet):
    """Prints a formatted summary of a bet dictionary."""
    print(f"""
📢 **Bet Details** 📢
------------------------
📖 Book: {bet.get('Book', 'N/A')}
🏀 League: {bet.get('league', 'N/A')}
🕒 Game: {bet.get('Game', 'N/A')}
⏳ Time Until Start: {bet.get('Time Until', 'N/A')}
👤 Player: {bet.get('Player', 'N/A')}
🎯 Bet Type: {bet.get('Type', 'N/A')}
📌 Position: {bet.get('Position', 'N/A')} {bet.get('Line', 'N/A')}
💰 Price: {bet.get('Price', 'N/A')} (Target: {bet.get('Price Target', 'N/A')})
📊 EV: {float(bet.get('EV', 0)):.2%}
🏷️ Team: {bet.get('Team', 'N/A')}
------------------------
""")


def remove_matched_bets(bets_dict, csv_filepath):
    # Return original dictionary if CSV file does not exist
    if not os.path.exists(csv_filepath):
        return bets_dict

    # Load CSV file and store (Player, Game, Type, Result) as a set for quick lookup
    filter_set = set()
    csv_data = []  # To store CSV rows for later rewriting

    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        csv_data = list(reader)  # Store all rows in memory
        for row in csv_data:
            filter_set.add((row["Player"].lower(), row["Game"].lower(), row["Type"].lower(), row["result"].lower()))

    # filter_set.add(('max christie', 'houston rockets @ dallas mavericks ', 'blocks'))
    # Iterate through the dictionary and remove matching bets
    for book in list(bets_dict.keys()):
        for league in list(bets_dict[book].keys()):
            for game in list(bets_dict[book][league].keys()):
                bets_dict[book][league][game] = [
                    bet for bet in bets_dict[book][league][game]
                    if (bet["Player"].lower(), bet["Game"].lower(), bet["Type"].lower(), 'successful bet') not in filter_set
                ]
                # Remove game if no bets remain
                if not bets_dict[book][league][game]:
                    del bets_dict[book][league][game]

            # Remove league if no games remain
            if not bets_dict[book][league]:
                del bets_dict[book][league]

        # Remove book if no leagues remain
        if not bets_dict[book]:
            del bets_dict[book]

    return bets_dict


def read_csv_to_dict(csv_filepath):
    bets_list = []

    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bets_list.append(row)

    return bets_list

def has_nba_bets(bets_dict):
    for bookmaker, leagues in bets_dict.items():
        if 'nba' in leagues:  # Check if 'nba' exists in the leagues under the bookmaker
            return True
    return False  # No NBA bets found

def wait_for_resolution(failure_message, bet_dict=None):
    # print(f"Player image not found for {player} from team {bet_dict['Team']}.")
    # print("Press Ctrl + R to resume after resolving the issue, or Ctrl + S to skip bet.")
    # send_sms_via_email('Script paused in Bet365', f"Error Message:\n"
    #                                               f"Player image not found for {player} from team {bet_dict['Team']}.\n"
    #                                               f"Press Ctrl + R to resume after resolving the issue, or Ctrl + S to skip bet.")
    send_sms_via_email('Script paused in Bet365', f"Error Message:\n"
                                                  f"{failure_message}\n"
                                                  f"Press Alt + R to resume after resolving the issue, or Alt + S to skip bet.")
    print(failure_message)
    print("Press Alt + R to resume after resolving the issue, or Alt + S to skip bet.")

    while True:
        if keyboard.is_pressed("alt+r"):
            print("Resuming...")
            time.sleep(0.5)  # Avoid multiple detections
            return True
        elif keyboard.is_pressed("alt+s"):
            print("Operation skipped.")
            if bet_dict:
                append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv",
                                   failure_message)
            time.sleep(0.5)  # Avoid multiple detections
            return False


def send_sms_via_email(subject, message):
    email_sender = "mahnriley@gmail.com"
    email_password = "ekgp pmkt iths nhza"

    # Lookup carrier's email-to-SMS gateway (e.g., AT&T: number@txt.att.net)
    sms_gateway = "9197603117@tmomail.net"

    # Format the email with a subject
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = email_sender
    msg["To"] = sms_gateway

    server = smtplib.SMTP("smtp.gmail.com", 587)
    # server.set_debuglevel(1)
    server.starttls()
    server.login(email_sender, email_password)
    server.sendmail(email_sender, sms_gateway, message)
    server.quit()

def send_simple_email():
    email_sender = "mahnriley@gmail.com"
    email_password = "ekgp pmkt iths nhza"  # Use an app-specific password if necessary
    sms_gateway = "9197603117@tmomail.net"  # Ensure this is correct for the intended recipient

    # Construct a very simple email message with a subject header.
    message = "Subject: Test\n\nHello, this is a test message."

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_sender, email_password)
        server.sendmail(email_sender, sms_gateway, message)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)
    finally:
        server.quit()

def print_bets_summary(bets_dict):
    output_lines = []
    for book, leagues in bets_dict.items():
        line = f"Book: {book}"
        print(line)
        output_lines.append(line)
        for league, games in leagues.items():
            line = f"  League: {league}"
            print(line)
            output_lines.append(line)
            for game, bet_list in games.items():
                line = f"    Game: '{game}' has {len(bet_list)} bet(s)"
                print(line)
                output_lines.append(line)
        print()  # Print a blank line between books
        output_lines.append("")
    message = "\n".join(output_lines)
    return message
