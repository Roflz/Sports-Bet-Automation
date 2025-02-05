import time

from pywinauto import Application
from config import CONTROLS
from utils.utils import *


class WebInteractor:
    def __init__(self, bets):
        self.sportsbook = None
        self.window_name = None
        self.browser_window = None
        self.app = None
        self.bets = bets

    def activate_browser(self):
        """Activate the browser window."""
        self.app = Application(backend="uia").connect(title_re=".*Google Chrome.*")
        self.browser_window = self.app.top_window()
        self.window_name = self.browser_window.element_info.name  # Retrieves the window's title
        self.browser_window.set_focus()

    def click_control(self, control_name):
        click_control(self.window_name, f"{CONTROLS}\\{self.sportsbook}\\{control_name}.png")

    def zoom_out_chrome(self, times=2):
        """
        Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses.

        :param times: Number of times to zoom out (default: 2).
        """
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)  # Small delay to ensure the zoom registers

    def login(self, login_button, login_dialogue, login_x, username, password):
        self.click_control(login_button)
        wait_for_control_to_be_visible(f"{CONTROLS}\\{self.sportsbook}\\{login_dialogue}.png", self.window_name)
        time.sleep(0.5)
        click_control(self.window_name, f"{CONTROLS}\\{self.sportsbook}\\{login_x}.png")
        keyboard_input([username, "tab", "tab"])
        keyboard_input([password, "enter"])

    def open_chrome(self, url):
        open_chrome(url)

    def open_chrome_and_wait_for_window(self, url, window_name):
        self.open_chrome(url)
        wait_for_window_to_be_visible(window_name)

    def open_chrome_and_wait_for_control(self, url, control_name, sportsbook):
        self.open_chrome(url)
        wait_for_window_to_be_visible("Google Chrome")
        time.sleep(1)
        wait_for_control_to_be_visible(f"{CONTROLS}\\{sportsbook}\\{control_name}.png", self.window_name)

    def make_bets(self, bets):
        for book in bets:

            # self.sportsbook = book
            self.sportsbook = 'bet365'
            book =  'bet365'
            if book == 'bet365':
                # Open book and log in
                self.open_chrome_and_wait_for_window("https://www.co.bet365.com/#/HO/", self.sportsbook)
                self.activate_browser()  # Focus the browser window
                wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\login_button.png", self.window_name)
                # web_interactor.zoom_out_chrome()
                self.login("login_button", "login_dialogue", "login_x", "ROTFLEZ", "56dFLJ4QvbHcz2e")
                wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\continue_after_login_button.png", self.window_name, timeout = 5, threshold=0.95)
                click_control(self.window_name, f"{CONTROLS}\\bet365\\continue_after_login_button.png")
                wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\close_after_login_button.png", self.window_name, timeout = 5)
                click_control(self.window_name, f"{CONTROLS}\\bet365\\close_after_login_button.png")
                book =  'betrivers'
                for league in bets[book]:
                    if league == 'nfl':
                        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nfl_button.png",
                                                       self.window_name, timeout=5)
                        click_control(self.window_name, f"{CONTROLS}\\bet365\\nfl_button.png")
                        for game in bets[book][league]:
                            print(game)
                            for bet_index in range(len(bets[book][league][game])):
                                if bets[book][league][game][bet_index]['Player']:
                                    wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\player_props_button.png",
                                                                   self.window_name, timeout=5, threshold=0.95)
                                    click_control(self.window_name, f"{CONTROLS}\\bet365\\player_props_button.png", threshold=0.95)
                                    scroll_until_visible(f"{CONTROLS}\\bet365\\pass_attempts_button.png")
                                    click_control(self.window_name, f"{CONTROLS}\\bet365\\pass_attempts_button.png",
                                                  threshold=0.95)
                    elif league == 'nba':
                        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba_button.png",
                                                       self.window_name, timeout=5)
                        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba_button.png")
                        for game in league:
                            print(game)
