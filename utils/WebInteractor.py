import re
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
        # Connect to any window with "Google Chrome" in its title
        self.app = Application(backend="uia").connect(title_re=".*Google Chrome.*")
        self.browser_window = self.app.top_window()

        # Get the full window title
        full_title = self.browser_window.element_info.name

        # Extract the first word (assuming words are separated by spaces)
        first_word = re.split(r"\s+", full_title.strip())[0]  # Gets the first word

        # Use the first word to create a more general regex pattern
        window_pattern = rf".*{re.escape(first_word)}.*"

        # Reconnect using the refined regex pattern
        self.app = Application(backend="uia").connect(title_re=window_pattern)
        self.browser_window = self.app.top_window()
        self.window_name = window_pattern
        self.browser_window.set_focus()

        print(f"Full title: {full_title}")
        print(f"Using window pattern: {window_pattern}")

    def click_control(self, control_name, threshold=0.8):
        click_control(self.window_name, f"{CONTROLS}\\{self.sportsbook}\\{control_name}.png", threshold=threshold)

    def zoom_out_chrome(self, times=2):
        """
        Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses.

        :param times: Number of times to zoom out (default: 2).
        """
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)  # Small delay to ensure the zoom registers

    def login(self, login_button, login_dialogue, login_x, username, password):
        self.click_control(f"login\\{login_button}")
        wait_for_control_to_be_visible(f"{CONTROLS}\\{self.sportsbook}\\login\\{login_dialogue}.png", self.window_name, threshold=0.4)
        time.sleep(0.2)
        click_control(self.window_name, f"{CONTROLS}\\{self.sportsbook}\\login\\{login_x}.png")
        keyboard_input([username, "tab", "tab"])
        keyboard_input([password, "enter"])

    def login_bet365(self):
        # Open book and log in
        self.open_chrome_and_wait_for_window("https://www.co.bet365.com/#/HO/", self.sportsbook)
        self.activate_browser()  # Focus the browser window
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\login\\login_button.png", self.window_name, threshold=0.6)
        # web_interactor.zoom_out_chrome()
        self.login("login_button", "login_dialogue", "login_x", "ROTFLEZ", "56dFLJ4QvbHcz2e")
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\login\\continue_after_login_button.png", self.window_name, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\login\\continue_after_login_button.png", threshold=0.95)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\login\\close_after_login_button.png", self.window_name)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\login\\close_after_login_button.png")

    def choose_league_nfl(self):
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nfl\\nfl_button.png",
                                       self.window_name, timeout=5)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nfl\\nfl_button.png")

    def choose_league_nba(self):
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba\\nba_button.png",
                                       self.window_name, timeout=5)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba\\nba_button.png")

    def choose_props_nba(self):
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba\\props_button.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba\\props_button.png", threshold=0.95)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba\\all_props_button.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba\\all_props_button.png", threshold=0.95)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba\\player_props_button.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba\\player_props_button.png", threshold=0.95)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nba\\1q_assists_filter_selector.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nba\\1q_assists_filter_selector.png", threshold=0.95)

    def choose_prop_type_nba(self, bet_type):
        click_until_see_and_click_other_at_relative_point(f"{CONTROLS}\\bet365\\nba\\props\\{bet_type}.png",
                                                          self.window_name, 1661, 426, max_attempts=5, delay=0.5, threshold=0.9)

    def choose_bet_nba(self, player, bet_line, price_target, position):
        control_location = scroll_until_visible(f"{CONTROLS}\\bet365\\nba\\players\\{player}.png", self.window_name)
        if position == 'over':
            screenshot, location = take_screenshot_over(control_location, self.window_name)
        elif position == 'under':
            screenshot, location = take_screenshot_under(control_location, self.window_name)
        odds_in_sportsbook = extract_text_from_pillow_image(screenshot)
        odds_in_sportsbook = odds_in_sportsbook.replace('.', '')
        line, price = extract_line_and_price(odds_in_sportsbook)
        bet_line = bet_line.replace('.', '')
        if line == bet_line and price >= price_target:
            pyautogui.click(location)
            time.sleep(1)
            return True
        print(f"Odds in sportsbook {odds_in_sportsbook} dont meet betting criteria {bet_line} {price_target}, for {player} {position}, skipping bet")
        return False

    def place_bet_nba(self):
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\place_bet_button.png",
                                       self.window_name)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\wager_text.png",
                                       self.window_name, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\wager_text.png", threshold=0.95)
        keyboard_input("1")
        click_control(self.window_name, f"{CONTROLS}\\bet365\\place_bet_button.png", threshold=0.95)

    def choose_player_props(self):
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nfl\\player_props_button.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nfl\\player_props_button.png", threshold=0.95)
        wait_for_control_to_be_visible(f"{CONTROLS}\\bet365\\nfl\\view_by_player_button.png",
                                       self.window_name, timeout=5, threshold=0.95)
        click_control(self.window_name, f"{CONTROLS}\\bet365\\nfl\\view_by_player_button.png", threshold=0.95)

    def parse_bet_type(self, bet_type):
        if bet_type == "points":
            return 'points_ou'
        elif bet_type == 'threes':
            return 'threes_made_ou'
        elif bet_type == 'assists':
            return 'assists_ou'
        elif bet_type == 'blocks':
            return 'blocks_ou'
        else:
            return bet_type

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
            self.sportsbook = book
            # self.sportsbook = 'bet365'
            if book == 'bet365':
                # Open book and log in
                # self.login_bet365()
                self.activate_browser()
                for league in bets[book]:
                    if league == 'afl':
                        self.choose_league_nfl()
                        for game in bets[book][league]:
                            print(game)
                            for bet_index in range(len(bets[book][league][game])):
                                if bets[book][league][game][bet_index]['Player']:
                                    self.choose_player_props()
                                    # Leave this for now since football season is almost over
                    elif league == 'nba':
                        self.choose_league_nba()
                        self.choose_props_nba()
                        for game in bets[book][league]:
                            print(game)
                            for bet_index in range(len(bets[book][league][game])):
                                bet_type = bets[book][league][game][bet_index]['Type']
                                bet_line = bets[book][league][game][bet_index]['Line']
                                price_target = bets[book][league][game][bet_index]['Price Target']
                                position = bets[book][league][game][bet_index]['Position']
                                player = bets[book][league][game][bet_index]['Player']
                                if 'ht_' in bet_type:
                                    break
                                bet_type = self.parse_bet_type(bet_type)
                                self.choose_prop_type_nba(bet_type)
                                if self.choose_bet_nba(player, bet_line, price_target, position):
                                    self.place_bet_nba()
