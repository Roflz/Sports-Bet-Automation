import ctypes
import time

# Load user32.dll for Windows API calls
user32 = ctypes.WinDLL("user32")

# Mouse event constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Keyboard event constants
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

def move_mouse(x, y):
    """Move the mouse to an absolute screen position."""
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    # Convert x, y to absolute coordinates (0-65535 range)
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)

    user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y, 0, 0)

def click(button="left"):
    """Simulate a mouse click."""
    if button == "left":
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    elif button == "middle":
        user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)

def press_key(hex_key_code):
    """Simulate a key press using a virtual key code."""
    user32.keybd_event(hex_key_code, 0, KEYEVENTF_KEYDOWN, 0)
    time.sleep(0.05)  # Small delay to mimic a real press
    user32.keybd_event(hex_key_code, 0, KEYEVENTF_KEYUP, 0)

# Example usage
if __name__ == "__main__":
    from pywinauto import Application
    import time

    # Connect to Chrome window
    app = Application(backend="uia").connect(title_re=".*Chrome.*")
    chrome_window = app.top_window()
    time.sleep(1)

    # Focus the address bar
    chrome_window.type_keys("^l")  # Ctrl + L to select address bar
    time.sleep(1)

    # Inject JavaScript to click the element
    js_code = 'javascript:document.querySelector("[aria-label=\'NBA\']").click();{ENTER}'
    #
    chrome_window.type_keys(js_code, with_spaces=True)

    time.sleep(1)  # Wait for action
    print("Injected JavaScript to click the element!")

    time.sleep(2)  # Gives you time to switch to another window
    move_mouse(500, 300)  # Move to (500, 300) on screen
    click("left")  # Left-click
    press_key(0x41)  # Press "A" key (hex code for 'A')
