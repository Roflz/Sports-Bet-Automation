import os

from utils.WebInteractor import WebInteractor
from utils.utils import *


class WebInteractorBet365(WebInteractor):
    def __init__(self, leagues):
        super().__init__(leagues)
        self.sportsbook = 'bet365'
        self.url = "https://www.co.bet365.com/#/HO/"
        self.window_name = 'bet365'
        self.username = "ROTFLEZ"
        self.password = "56dFLJ4QvbHcz2e"

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

    def make_bets(self):
        if not self.open_chrome_and_wait_for_window(self.url, self.window_name):
            return
        time.sleep(0.5)
        if not self.login_bet365():
            return
        self.activate_browser()
        for league, games in self.leagues.items():
            if league == 'nfl':  # Skip NFL for now since it is almost over
                continue
            for game, bet_list in games.items():
                for bet in bet_list:
                    print_bet_details(bet)
                    # scroll_to_top()
                    if not self.choose_league_bet365(league):
                        continue
                    if is_bet_in_csv(bet['Player'], bet['Type'], game) or "ht_" in bet['Type']:
                        if "ht_" in bet['Type']:
                            append_dict_to_csv(bet, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv", "Halftime bet, not set up for halftime bets yet.")
                            print(f"Game at halftime, skipping bet, recording bet still to assess volume of halftime bets")
                            continue
                        else:
                            print(f"Skipping existing bet: {bet['Player']} - {bet['Type']} - {game}")
                            continue
                    if not self.choose_props_nba(bet) or not self.choose_prop_type_nba(bet['Type'], bet):
                        continue
                    if self.choose_bet_nba(bet['Player'], bet['Line'], bet['Price Target'], bet['Position'], bet):
                        time.sleep(0.5)
                        self.place_bet_nba(bet)