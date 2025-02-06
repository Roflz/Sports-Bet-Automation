import csv
import re
import subprocess
import webbrowser

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

def capture_window(window_name):
    # Find the window handle
    hwnd = find_window_by_partial_title(window_name)  # Replace with the window title
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
        return False

    # Get the window position (to adjust relative coordinates)
    hwnd = find_window_by_partial_title(window_name)
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


def wait_for_control_to_be_visible(control_image_path, window_name, timeout=10, threshold=0.8):
    attempts = 0
    while attempts <= timeout:
        if not find_control(window_name, control_image_path, threshold=threshold):
            time.sleep(1)
            attempts += 1
        else:
            return True
    return False

def wait_for_place_bet_button_to_be_visible(window_name, timeout=10, threshold=0.8):
    attempts = 0
    while attempts <= timeout:
        if not find_control(window_name, f"{CONTROLS}\\bet365\\place_bet_button.png", threshold=threshold):
            if find_control(window_name, f"{CONTROLS}\\bet365\\price_changed.png", threshold=threshold):
                return False
            time.sleep(1)
            attempts += 1
        else:
            return True
    raise ControlNotFoundException(f"Control 'place_bet_button' not found in window '{window_name}' within {timeout} seconds.")

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


def scroll_until_visible(control_image_path, window_name, threshold=0.8, scroll_amount=-300, max_attempts=50, delay=0.3):
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
            location = find_control(window_name, control_image_path, threshold)
            if location:
                return location # Control found
        except pyautogui.ImageNotFoundException:  # Handles missing control
            pass  # Continue scrolling

        pyautogui.scroll(scroll_amount)
        time.sleep(delay)
        attempts += 1

    raise ControlNotFoundException(f"Control {control_image_path} not found after scrolling through page")

def scroll_until_visible_and_click(control_image_paths, window_name, threshold=0.8, scroll_amount=-300, max_attempts=50, delay=0.3):
    """
    Scrolls until one of the specified controls (images) is visible on the screen and clicks it.

    Args:
        control_image_paths (list): List of control image paths.
        window_name (str): Name of the window to search within.
        threshold (float): Similarity threshold for image matching.
        scroll_amount (int): The amount to scroll each attempt (-100 for up, 100 for down).
        max_attempts (int): Maximum number of scrolling attempts.
        delay (float): Time delay between each scroll attempt.

    Raises:
        ControlNotFoundException: If none of the controls are found after all scrolling attempts.
    """
    attempts = 0

    while attempts < max_attempts:
        for control_image_path in control_image_paths:
            try:
                # Try finding the control in the current list
                location = find_control(window_name, control_image_path, threshold)
                if location:
                    click_control(window_name, control_image_path, threshold)
                    return  # Clicked the found control, exit function

            except pyautogui.ImageNotFoundException:
                pass  # Continue searching if control is not found

        # Scroll if no control is found
        pyautogui.scroll(scroll_amount)
        time.sleep(delay)
        attempts += 1

    # If we exhaust all attempts and find nothing, raise an exception
    raise ControlNotFoundException(f"None of the controls {control_image_paths} were found after scrolling through the page.")

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

def click_point_til_control_visible_click_control(control_image_path, window_name, click_x_rel, click_y_rel, threshold=0.8, max_attempts=50, delay=0.3):
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

            if find_control(window_name, control_image_path, threshold):
                click_control(window_name, control_image_path, threshold)
                return True  # Exit after clicking control 2

            # If control 2 isn't found, click at the specified relative point
            pyautogui.click(click_x, click_y)  # Click at the calculated position
            time.sleep(delay)  # Pause between clicks

        except pyautogui.ImageNotFoundException:
            pass  # Continue if control 2 isn't found

        attempts += 1

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
    Extracts the first and second number from the given text as strings.

    Args:
        text (str): The input text containing two numbers.

    Returns:
        tuple: (line, price) where both are strings.
    """
    numbers = re.findall(r'-?\d+', text)  # Find all numbers (including negatives)

    if len(numbers) < 2:
        raise ValueError("Could not find two numbers in the text")

    line = numbers[0]  # Keep as string
    price = numbers[1]  # Keep as string

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

def take_screenshot_over(control_coordinates, window_name, distance_to_right=609, screenshot_width=87, screenshot_height=38):
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

def take_screenshot_under(control_coordinates, window_name, distance_to_right=872, screenshot_width=87, screenshot_height=38):
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
    Appends data from a dictionary to an existing CSV file, creating headers if necessary,
    and adding a 'result' column at the end.

    Args:
        data_dict (dict): The dictionary containing data to be added to the CSV file.
        filename (str): The name of the CSV file to append to.
        result (str): The result to append as the 'result' column.

    Returns:
        None
    """
    # Add 'result' to the dictionary
    if result is not None:
        data_dict['result'] = result

    # Check if the file exists to determine whether we need to write headers
    try:
        with open(filename, mode='r', newline='') as file:
            pass
        file_exists = True
    except FileNotFoundError:
        file_exists = False

    # Open the file in append mode to add data
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data_dict.keys())

        # Write the header if the file is new
        if not file_exists:
            writer.writeheader()

        # Write the data from the dictionary as a row
        writer.writerow(data_dict)

    print(f"Data has been appended to {filename}")

def is_bet_in_csv(player, bet_type, game, filename="output.csv"):
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

def wait_and_click(self, control_path, bet_dict, failure_message, timeout=5, threshold=0.95):
    """Waits for a control to be visible, then clicks it. Logs failure and returns False if unsuccessful."""
    if not wait_for_control_to_be_visible(control_path, self.window_name, timeout=timeout, threshold=threshold):
        append_dict_to_csv(bet_dict, "results.csv", failure_message)
        return False
    if not click_control(self.window_name, control_path, threshold=threshold):
        append_dict_to_csv(bet_dict, "results.csv", failure_message)
        return False
    return True