import os

from utils.control_state import control_state
from utils.ControlMeta import ControlMeta
from utils.WebInteractor import WebInteractor
from utils.utils import *


class WebInteractorBet365(WebInteractor, metaclass=ControlMeta):
    def __init__(self, leagues):
        super().__init__(leagues)
        self.sportsbook = 'bet365'
        self.url = "https://www.co.bet365.com/#/HO/"
        self.window_name = 'bet365'
        self.username = "ROTFLEZ"
        self.password = "56dFLJ4QvbHcz2e"
        control_state.set_web_interactor_bet365(self)  # Set the instance globally

    def login_bet365(self):
        self.activate_browser()
        control_path = f"{CONTROLS}\\bet365\\login"
        steps_1 = [("login_button", 0.6), ("login_x", 0.8)]
        keyboard_input = [self.username, "tab", "tab", self.password, "enter"]
        steps_2 = [("continue_after_login_button", 0.95), ("close_after_login_button", 0.95)]
        if not self.login(control_path, steps_1, keyboard_input, steps_2):
            return False
        return True

    def choose_league_bet365(self, league):
        control_path = f"{CONTROLS}\\bet365"
        if not self.choose_league(league, control_path):
            return False
        return True

    def choose_props_nba(self, bet_dict):
        steps = [
            "all_props_button", "player_props_button", "1q_assists_filter_selector"
        ]
        for step in steps:
            control_path = f"{CONTROLS}\\bet365\\nba\\{step}.png"
            if not self.wait_and_click_log_failure_to_csv(control_path, bet_dict, f"Bet not made, could not find {step}"):
                return False
            time.sleep(0.5)
        time.sleep(1)
        return True

    def choose_prop_type_nba(self, bet_type, bet_dict):
        control_path = f"{CONTROLS}\\bet365\\nba\\props\\{bet_type}.png"
        if not click_point_til_control_visible_click_control(control_path, 1661, 426, max_attempts=5,
                                                             delay=0.5, threshold=0.95):
            if not pause_and_log_failure(f"Bet not made, could not find {bet_type} prop", bet_dict):
                return False
        return True

    def choose_bet_nba(self, player, bet_line, price_target, position, bet_dict):
        players_folder = "controls/bet365/nba/players"
        # Check if the player's image exists in the folder
        player_image_path = os.path.join(players_folder, f"{player}.png")
        if not os.path.exists(player_image_path):
            input(f"Player image not found for {player} from team {bet_dict['Team']}. Press Enter to continue or resolve the issue.")
            time.sleep(1)
            pass  # fix the issue and continue

        move_mouse_by(0, 50)
        pyautogui.click()

        control_path = f"{CONTROLS}\\bet365\\nba\\players\\{player}.png"
        control_location = scroll_until_visible(control_path, self.window_name, delay=0.5, threshold=0.95)

        if not control_location:
            failure_message = f"Bet not made, could not find player {player}"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False

        position_offset = control_location[0] - 641
        if position == 'over':
            screenshot, location = take_screenshot_over((control_location[0] - position_offset, control_location[1]), window_name=self.window_name)
        elif position == 'under':
            screenshot, location = take_screenshot_under((control_location[0] - position_offset, control_location[1]), window_name=self.window_name)
        elif position == 'side':
            screenshot, location = take_screenshot_side((control_location[0] - position_offset, control_location[1]), window_name=self.window_name)
        else:
            if not pause_and_log_failure(f"Bet not made, invalid position '{position}' for {player}", bet_dict):
                return False
            return False

        odds = extract_text_from_pillow_image(screenshot).replace('.', '')
        extracted_values = extract_line_and_price(odds)

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

        error_message = f"Bet not made, odds don't match for {player}\n{expected_odds}\n{actual_odds}"

        if not pause_and_log_failure(error_message, bet_dict):
            return False
        return False

    def wait_for_place_bet_button_to_be_visible(self, window_name=None, timeout=10, threshold=0.8):
        attempts = 0
        while attempts <= timeout:
            if not find_control(f"{CONTROLS}\\bet365\\place_bet_button.png", window_name=window_name,
                                threshold=threshold):
                time.sleep(1)
                attempts += 1
            else:
                return True
        return False

    def place_bet_nba(self, bet_dict):
        # Wait and click the wager text, input the amount, and place the bet
        control_path = f"{CONTROLS}\\bet365"
        control_image_paths = [f"{control_path}\\price_changed.png", f"{control_path}\\odds_changed.png",
                               f"{control_path}\\availability_changed.png"]  # Path to the image of the control you're looking for
        for control in control_image_paths:
            if find_control(control):
                control_path = f"{CONTROLS}\\bet365\\price_changed_x.png"
                print('odds or availability changed on bet')
                if not self.wait_and_click_log_failure_to_console(control_path,"Could not find x to cancel bet"):
                    return False
                append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv",
                                   "bet odds, availability or price changed")
                return
        if not self.wait_and_click_log_failure_to_csv([f"{CONTROLS}\\bet365\\wager_text.png", f"{CONTROLS}\\bet365\\set_lwager.png"], bet_dict, "Failed to find wager text"):
            return
        # Bet 1 for first basket cuz thats all i am allowed
        if bet_dict['Position'] == 'side':
            keyboard_input(['1'])
        else:
            keyboard_input(["4"])
        if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\place_bet_button.png", bet_dict, "Failed to place bet"):
            return

        # Wait for the bet confirmation and close the confirmation popup
        time.sleep(1)
        if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\bet_placed_x_button.png", bet_dict,
                                   "Failed to confirm bet placement"):
            return
        append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", "successful bet")
        return

    def initialize(self):
        if not self.open_chrome_and_wait_for_window(self.url, self.window_name):
            return False
        time.sleep(0.5)
        control_path = f"{CONTROLS}\\bet365\\login"
        if not wait_for_control_to_be_visible(f"{control_path}\\login_button.png", timeout=3):
            if not self.wait_and_click_log_failure_to_console(f"{control_path}\\close_after_login_button.png", "Failed logging in", ):
                return False
        else:
            self.login_bet365()
        self.activate_browser()
        return True

    def make_bets(self):
        self.initialize()
        for league, games in self.leagues.items():
            if league == 'nfl':  # Skip NFL for now since it is almost over
                continue
            for game, bet_list in games.items():
                for bet in bet_list:
                    print_bet_details(bet)
                    # scroll_to_top()
                    if "ht_" in bet['Type']:
                        append_dict_to_csv(bet, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", "Halftime bet, not set up for halftime bets yet.")
                        print(f"Game at halftime, skipping bet, recording bet still to assess volume of halftime bets")
                        continue
                    if not self.choose_league_bet365(league):
                        continue
                    if not self.choose_props_nba(bet) or not self.choose_prop_type_nba(bet['Type'], bet):
                        continue
                    if self.choose_bet_nba(bet['Player'], bet['Line'], bet['Price Target'], bet['Position'], bet):
                        time.sleep(0.5)
                        self.place_bet_nba(bet)