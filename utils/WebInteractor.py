import re
import time
import pyautogui
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
        full_title = self.browser_window.element_info.name
        first_word = re.split(r"\s+", full_title.strip())[0]
        self.window_name = rf".*{re.escape(first_word)}.*"
        self.app = Application(backend="uia").connect(title_re=self.window_name)
        self.browser_window = self.app.top_window()
        self.browser_window.set_focus()
        print(f"Full title: {full_title}")
        print(f"Using window pattern: {self.window_name}")

    def click_control(self, control_name, threshold=0.8):
        click_control(self.window_name, f"{CONTROLS}/{self.sportsbook}/{control_name}.png", threshold=threshold)

    def zoom_out_chrome(self, times=2):
        """Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses."""
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)

    def login(self, login_button, login_dialogue, login_x, username, password):
        self.click_control(f"login/{login_button}")
        wait_for_control_to_be_visible(f"{CONTROLS}/{self.sportsbook}/login/{login_dialogue}.png", self.window_name, threshold=0.4)
        time.sleep(0.2)
        click_control(self.window_name, f"{CONTROLS}/{self.sportsbook}/login/{login_x}.png")
        keyboard_input([username, "tab", "tab", password, "enter"])

    def login_bet365(self):
        self.open_chrome_and_wait_for_window("https://www.co.bet365.com/#/HO/", self.sportsbook)
        self.activate_browser()
        wait_for_control_to_be_visible(f"{CONTROLS}/bet365/login/login_button.png", self.window_name, threshold=0.6)
        self.login("login_button", "login_dialogue", "login_x", "ROTFLEZ", "56dFLJ4QvbHcz2e")
        for button in ["continue_after_login_button", "close_after_login_button"]:
            wait_for_control_to_be_visible(f"{CONTROLS}/bet365/login/{button}.png", self.window_name, threshold=0.95)
            click_control(self.window_name, f"{CONTROLS}/bet365/login/{button}.png", threshold=0.95)

    def choose_league(self, league):
        league_controls = {"nfl": "nfl_button", "nba": "nba_button"}
        control = league_controls.get(league)
        if control:
            wait_for_control_to_be_visible(f"{CONTROLS}/bet365/{league}/{control}.png", self.window_name, timeout=5)
            click_control(self.window_name, f"{CONTROLS}/bet365/{league}/{control}.png")

    def choose_props_nba(self, bet_dict):
        steps = [
            "props_button", "all_props_button", "player_props_button", "1q_assists_filter_selector"
        ]
        for step in steps:
            control_path = f"{CONTROLS}/bet365/nba/{step}.png"
            if not wait_and_click(control_path, bet_dict, f"Bet not made, could not find {step}"):
                return False
        return True

    def choose_prop_type_nba(self, bet_type, bet_dict):
        control_path = f"{CONTROLS}/bet365/nba/props/{bet_type}.png"
        if not click_point_til_control_visible_click_control(control_path, self.window_name, 1661, 426, max_attempts=5, delay=0.5, threshold=0.9):
            append_dict_to_csv(bet_dict, "results.csv", f"Bet not made, could not find {bet_type} prop")
            return False
        return True

    def choose_bet_nba(self, player, bet_line, price_target, position, bet_dict):
        control_path = f"{CONTROLS}/bet365/nba/players/{player}.png"
        control_location = scroll_until_visible(control_path, self.window_name)
        if not control_location:
            append_dict_to_csv(bet_dict, "results.csv", f"Bet not made, could not find player {player}")
            return False
        screenshot, location = take_screenshot_over(control_location, self.window_name) if position == 'over' else take_screenshot_under(control_location, self.window_name)
        odds = extract_text_from_pillow_image(screenshot).replace('.', '')
        line, price = extract_line_and_price(odds)
        if line == bet_line.replace('.', '') and int(price) >= int(price_target):
            pyautogui.click(location)
            time.sleep(1)
            return True
        append_dict_to_csv(bet_dict, "results.csv", f"Bet not made, odds don't match for {player}")
        return False

    def place_bet_nba(self, bet_dict):
        if wait_for_place_bet_button_to_be_visible(self.window_name):
            # Wait and click the wager text, input the amount, and place the bet
            if not wait_and_click(f"{CONTROLS}/bet365/wager_text.png", bet_dict, "Failed to find wager text"):
                return
            keyboard_input("1")
            if not wait_and_click(f"{CONTROLS}/bet365/place_bet_button.png", bet_dict, "Failed to place bet"):
                return

            # Wait for the bet confirmation and close the confirmation popup
            if not wait_and_click(f"{CONTROLS}/bet365/bet_placed_x_button.png", bet_dict,
                                       "Failed to confirm bet placement"):
                return
        else:
            # If the price changed, log the result and close the notification
            append_dict_to_csv(bet_dict, "results.csv", "Bet not made, price changed")
            if not wait_and_click(f"{CONTROLS}/bet365/price_changed_x.png", bet_dict,
                                       "Failed to close price changed notification"):
                return

    def open_chrome_and_wait_for_window(self, url, window_name):
        open_chrome(url)
        wait_for_window_to_be_visible(window_name)

    def make_bets(self, bets):
        for book, leagues in bets.items():
            self.sportsbook = book
            if book == 'bet365':
                self.login_bet365()
                self.activate_browser()
                for league, games in leagues.items():
                    self.choose_league(league)
                    for game, bet_list in games.items():
                        for bet in bet_list:
                            if is_bet_in_csv(bet['Player'], bet['Type'], game):
                                print(f"Skipping existing bet: {bet['Player']} - {bet['Type']} - {game}")
                                continue
                            if not self.choose_props_nba(bet) or not self.choose_prop_type_nba(bet['Type'], bet):
                                continue
                            if self.choose_bet_nba(bet['Player'], bet['Line'], bet['Price Target'], bet['Position'], bet):
                                self.place_bet_nba(bet)
