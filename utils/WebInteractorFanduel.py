import os
import time
from datetime import datetime

import pyautogui

from config import CONTROLS
from utils.ControlMeta import ControlMeta
from utils.WebInteractor import WebInteractor
from utils.utils import print_bet_details, is_bet_in_csv, append_dict_to_csv, scroll_until_visible, \
    pause_and_log_failure, click_control, drag_until_visible_and_click, pause_and_print_failure, \
    scroll_until_visible_and_click, take_screenshot_over, take_screenshot_under, take_screenshot_side, \
    extract_text_from_pillow_image, extract_line_and_price, keyboard_input


class WebInteractorFanduel(WebInteractor, metaclass=ControlMeta):
    def __init__(self, leagues):
        super().__init__(leagues)
        self.sportsbook = 'fanduel'
        self.url = "https://sportsbook.fanduel.com/"
        self.window_name = 'fanduel'
        self.username = "mahnriley@gmail.com"
        self.password = "-ip$U5e0+UFl+L9lst1W"

    def login_fanduel(self):
        self.activate_browser()
        control_path = f"{CONTROLS}\\fanduel\\login"
        steps_1 = [("login_button", 0.8), ("colorado_button", 0.95), ("login_to_fanduel_text", 0.95)]
        keyboard_input = ["tab", self.username, "tab", self.password, "enter"]
        steps_2 = []
        if not self.login(control_path, steps_1, keyboard_input, steps_2):
            return False
        return True

    def choose_league_fanduel(self, league):
        control_path = f"{CONTROLS}\\fanduel"
        if not self.choose_league(league, control_path):
            return False
        return True

    def choose_team_nba(self, team):
        teams_folder = "controls\\fanduel\\nba\\teams"
        # Check if the team's image exists in the folder
        team_image_path = os.path.join(teams_folder, f"{team}.png")
        if not os.path.exists(team_image_path):
            input(
                f"Team image not found for {team}. Press Enter to continue or resolve the issue.")
            time.sleep(2)
            pass  # fix the issue and continue

        control_location = scroll_until_visible(team_image_path, delay=0.5)

        if not control_location:
            failure_message = f"Bet not made, could not find team {team}"
            if not pause_and_print_failure(failure_message):
                return False

        if not click_control(team_image_path):
            failure_message = f"Bet not made, could not click on team {team}"
            if not pause_and_print_failure(failure_message):
                return False

        return True

    def parse_prop_types(self, bet_type):
        if bet_type in "1q_assists 1q_points 1q_rebounds":
            prop = '1q'
            return prop
        elif bet_type in "assists_rebounds points_assists points_rebounds points_rebounds_assists steals_blocks":
            prop = 'combos'
            return prop
        elif bet_type in 'blocks steals':
            prop = 'defense'
            return prop
        else:
            return bet_type


    def choose_prop_type_nba(self, bet_type, bet_dict):
        prop = self.parse_prop_types(bet_type)
        if prop == '1q':
            failure_message = f"{prop} bets not supported yet"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False

        scroll_bar_path = f"{CONTROLS}\\fanduel\\props_scroll_bar.png"
        prop_path = f"{CONTROLS}\\fanduel\\nba\\prop_types\\{prop}.png"

        if not drag_until_visible_and_click(scroll_bar_path, prop_path, threshold=0.95, drag_distance=100, max_attempts=20):
            failure_message = f"Could not find prop {prop}"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False
        return True

    def choose_prop_nba(self, prop, bet_dict):
        control_path = f"{CONTROLS}\\fanduel\\nba\\props\\{prop}.png"

        if not scroll_until_visible_and_click(control_path, delay=0.5, max_attempts=10, threshold=0.95):
            failure_message = f"Could not find prop {prop}"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False
        return True

    def choose_bet_nba(self, player, bet_line, price_target, position, bet_dict):
        players_folder = "controls/fanduel/nba/players"
        # Check if the player's image exists in the folder
        player_image_path = os.path.join(players_folder, f"{player}.png")
        if not os.path.exists(player_image_path):
            input(
                f"Player image not found for {player} from team {bet_dict['Team']}. Press Enter to continue or resolve the issue.")
            time.sleep(2)
            pass  # fix the issue and continue

        control_location = scroll_until_visible(player_image_path, delay=0.5, max_attempts=10, threshold=0.99)

        if not control_location:
            failure_message = f"Could not find player {player}"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False

        position_offset = control_location[0] - 485
        distance_x_over = 539
        distance_x_under = 658
        # distance_x_side = ''
        if position == 'over':
            screenshot, location = take_screenshot_over((control_location[0] - position_offset, control_location[1]),
                                                        distance_to_right=distance_x_over, screenshot_height=51, screenshot_width=74)
        elif position == 'under':
            screenshot, location = take_screenshot_under((control_location[0] - position_offset, control_location[1]),
                                                         distance_to_right=distance_x_under, screenshot_height=51, screenshot_width=74)
        # elif position == 'side':
        #     screenshot, location = take_screenshot_side((control_location[0] - position_offset, control_location[1]),
        #                                                 )
        else:
            if not pause_and_log_failure(f"Invalid position '{position}' for {player}", bet_dict):
                return False
            return False

        odds = extract_text_from_pillow_image(screenshot).replace('.', '')
        extracted_values = extract_line_and_price(odds)
        extracted_values = (extracted_values[0].lstrip("0U"), extracted_values[1])

        # Handle cases where only one number is extracted (for 'side' position)
        if isinstance(extracted_values, tuple) and len(extracted_values) == 2:
            line, price = extracted_values
        else:
            line, price = extracted_values, None  # If only one number is found, treat it as the line

        # Ensure price comparisons only happen when price is available
        if (line == bet_line.replace('.', '')) or (price is None and int(line) >= int(price_target)):
            pyautogui.moveTo(location)
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(0.5)
            return True

        expected_odds = f"Expected Line: {bet_line}, Expected Price: {price_target}"
        actual_odds = f"Actual Line: {line}, Actual Price: {price if price else 'N/A'}"

        error_message = f"Odds don't match for {player}\n{expected_odds}\n{actual_odds}"

        if not pause_and_log_failure(error_message, bet_dict):
            return False
        return False

    def place_bet_nba(self, bet_dict):
        control_path = f"{CONTROLS}\\fanduel"

        failure_message = "Could not find and click wager text"
        if not self.wait_and_click_log_failure_to_csv(f"{control_path}\\wager_text.png", bet_dict, failure_message, threshold=0.95):
            return False

        time.sleep(0.3)
        keyboard_input(["1"])
        time.sleep(0.3)

        if not self.wait_and_click_log_failure_to_csv(f"{control_path}\\place_bet_button.png", bet_dict, failure_message, threshold=0.95):
            return False

        append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", "successful bet")

        if not self.wait_and_click_log_failure_to_csv(f"{control_path}\\done_button.png", bet_dict, failure_message, threshold=0.95):
            return False
        return True


    def make_bets(self):
        if not self.open_chrome_and_wait_for_window(self.url, self.window_name):
            return
        # time.sleep(0.5)
        # if not self.login_fanduel():
        #     return
        self.activate_browser()
        self.set_zoom()
        self.zoom_in_chrome(times=4)
        for league, games in self.leagues.items():
            if league == 'nfl':  # Skip NFL for now since it is almost over
                continue
            for game, bet_list in games.items():
                team = game.split(' @')[0]
                time.sleep(0.5)
                for bet in bet_list:
                    print_bet_details(bet)
                    if is_bet_in_csv(bet['Player'], bet['Type'], game) or "ht_" in bet['Type']:
                        if "ht_" in bet['Type']:
                            append_dict_to_csv(bet, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv",
                                               "Halftime bet, not set up for halftime bets yet.")
                            print(
                                f"Game at halftime, skipping bet, recording bet still to assess volume of halftime bets")
                            continue
                        else:
                            print(f"Skipping existing bet: {bet['Player']} - {bet['Type']} - {game}")
                            continue
                    if not self.choose_league_fanduel(league):
                        self.refresh_page()
                        continue
                    time.sleep(1)
                    if not self.choose_team_nba(team):
                        self.refresh_page()
                        continue
                    # scroll_to_top()
                    if not self.choose_prop_type_nba(bet['Type'], bet):
                        self.refresh_page()
                        continue
                    if not self.choose_prop_nba(bet['Type'], bet):
                        self.refresh_page()
                        continue
                    time.sleep(0.3)
                    if not self.choose_bet_nba(bet['Player'], bet['Line'], bet['Price Target'], bet['Position'], bet):
                        self.refresh_page()
                        continue
                    if not self.place_bet_nba(bet):
                        self.refresh_page()
                        continue
                    self.refresh_page()
                    print('success')
        self.activate_browser()
        self.set_zoom()