import os

from utils.utils import *


class WebInteractor:
    def __init__(self, leagues):
        self.window_name = None
        self.browser_window = None
        self.app = None
        self.leagues = leagues

    def activate_browser(self):
        """Activate the browser window."""
        self.app = Application(backend="uia").connect(title_re=".*Google Chrome.*")
        self.browser_window = self.app.top_window()
        full_title = self.browser_window.element_info.name
        # first_word = re.split(r"\s+", full_title.strip())[0]
        # self.window_name = rf".*{re.escape(first_word)}.*"
        # self.app = Application(backend="uia").connect(title_re=self.window_name)
        # self.browser_window = self.app.top_window()
        self.browser_window.set_focus()
        print(f"Full title: {full_title}")
        print(f"Using window pattern: {self.window_name}")

    def click_control(self, control_name, threshold=0.8):
        return click_control(f"{CONTROLS}/{self.sportsbook}/{control_name}.png", threshold=threshold)

    def wait_and_click_log_failure_to_csv(self, control_path, bet_dict, failure_message, timeout=5, threshold=0.95):
        """Waits for a control to be visible, then clicks it. Logs failure, prints message, pauses for input, refreshes, and waits."""

        if not wait_for_control_to_be_visible(control_path, timeout=timeout, threshold=threshold):
            if pause_and_log_failure(failure_message, bet_dict): # pause if failure, decide whether to continue or move to next loop
                pass
            else:
                self.refresh_page()  # Assuming you have a refresh method
                time.sleep(3)  # Wait a few seconds after refreshing
                return False

        if not click_control(control_path, threshold=threshold):
            if pause_and_log_failure(failure_message, bet_dict):  # pause if failure, decide whether to continue or move to next loop
                pass
            else:
                self.refresh_page()  # Assuming you have a refresh method
                time.sleep(3)  # Wait a few seconds after refreshing
                return False

        return True

    def wait_and_click_log_failure_to_console(self, control_path, failure_message, timeout=5, threshold=0.95,
                                              window_name=None):
        """Waits for a control to be visible, then clicks it. Logs failure, prints message, pauses for input, refreshes, and waits."""
        if not wait_for_control_to_be_visible(control_path, timeout=timeout, threshold=threshold):
            if pause_and_print_failure(failure_message + ". Failure at wait to be visible"):
                pass
            else:
                self.refresh_page()  # Assuming you have a refresh method
                time.sleep(3)  # Wait a few seconds after refreshing
                return False

        if not click_control(control_path, threshold=threshold):
            if pause_and_print_failure(failure_message + ". Failure at click control"):
                pass
            else:
                self.refresh_page()  # Assuming you have a refresh method
                time.sleep(3)  # Wait a few seconds after refreshing
                return False

        return True

    def refresh_page(self):
        """Refreshes the page by simulating an F5 key press."""
        self.activate_browser()
        pyautogui.press('f5')
        time.sleep(3)  # Wait a few seconds to allow reload

    def zoom_out_chrome(self, times=2):
        """Zooms out in Google Chrome by simulating 'Ctrl + -' keypresses."""
        for _ in range(times):
            pyautogui.hotkey("ctrl", "-")
            time.sleep(0.2)

    def login(self, control_path, steps_1, keyboard_strokes, steps_2):
        for step, threshold in steps_1:
            control_path_step_1 = f"{control_path}\\{step}.png"
            if not self.wait_and_click_log_failure_to_console(control_path_step_1, f"Login failed, could not find {step}", threshold=threshold):
                return False
            time.sleep(0.2)

        keyboard_input(keyboard_strokes)

        for step, threshold in steps_2:
            control_path_step_2 = f"{control_path}\\{step}.png"
            if not self.wait_and_click_log_failure_to_console(control_path_step_2, f"Login failed, could not find {step}", threshold=threshold):
                return False
            time.sleep(0.2)
        return True

    def choose_league(self, league, control_path):
        league_controls = {"nfl": "nfl_button", "nba": "nba_button"}
        control = league_controls.get(league)
        if control:
            control_path = f"{control_path}\\{league}\\{control}.png"
            if not wait_for_control_to_be_visible(control_path, timeout=5):
                if not pause_and_print_failure(f"Failed to find league button for {league}"):
                    return False
            if not click_control(control_path):
                if not pause_and_print_failure(f"Failed to click league button for {league}"):
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
            time.sleep(2)
            pass  # fix the issue and continue

        move_mouse_by(0, 50)
        pyautogui.click()

        control_path = f"{CONTROLS}\\bet365\\nba\\players\\{player}.png"
        control_location = scroll_until_visible(control_path, self.window_name, delay=0.5)

        if not control_location:
            failure_message = f"Bet not made, could not find player {player}"
            if not pause_and_log_failure(failure_message, bet_dict):
                return False

        position_offset = control_location[0] - 641
        if position == 'over':
            screenshot, location = take_screenshot_over((control_location[0] - position_offset, control_location[1]), self.window_name)
        elif position == 'under':
            screenshot, location = take_screenshot_under((control_location[0] - position_offset, control_location[1]), self.window_name)
        elif position == 'side':
            screenshot, location = take_screenshot_side((control_location[0] - position_offset, control_location[1]), self.window_name)
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

    def place_bet_nba(self, bet_dict):
        if wait_for_place_bet_button_to_be_visible(self.window_name):
            # Wait and click the wager text, input the amount, and place the bet
            if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\wager_text.png", bet_dict, "Failed to find wager text"):
                return
            keyboard_input(["1"])
            if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\place_bet_button.png", bet_dict, "Failed to place bet"):
                return

            # Wait for the bet confirmation and close the confirmation popup
            if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\bet_placed_x_button.png", bet_dict,
                                       "Failed to confirm bet placement"):
                return
            append_dict_to_csv(bet_dict, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", "successful bet")
        else:
            # If the price changed, log the result and close the notification
            if not self.wait_and_click_log_failure_to_csv(f"{CONTROLS}\\bet365\\price_changed_x.png", bet_dict,
                                       "Failed to close price changed notification"):
                return

    def open_chrome_and_wait_for_window(self, url, window_name):
        if not open_chrome(url):
            if not pause_and_print_failure(f"Failed to open chrome window at {url}"):
                return False
        if not wait_for_window_to_be_visible(window_name):
            if not pause_and_print_failure(f"Chrome window did not become visible at {url}"):
                return False
        return True
