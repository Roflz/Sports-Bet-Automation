import os
import time
from datetime import datetime

from config import CONTROLS
from utils.WebInteractor import WebInteractor
from utils.utils import print_bet_details, is_bet_in_csv, append_dict_to_csv


class WebInteractorFanduel(WebInteractor):
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
        teams_folder = "controls/fanduel/nba/teams"
        # Check if the team's image exists in the folder
        team_image_path = os.path.join(teams_folder, f"{team}.png")
        if not os.path.exists(team_image_path):
            input(
                f"Team image not found for {team}. Press Enter to continue or resolve the issue.")
            time.sleep(2)
            pass  # fix the issue and continue

    def make_bets(self):
        # if not self.open_chrome_and_wait_for_window(self.url, self.window_name):
        #     return
        # time.sleep(0.5)
        # if not self.login_fanduel():
        #     return
        # self.activate_browser()
        for league, games in self.leagues.items():
            league = 'nba'
            if league == 'nfl':  # Skip NFL for now since it is almost over
                continue
            for game, bet_list in games.items():
                for bet in bet_list:
                    print_bet_details(bet)
                    # scroll_to_top()
                    if not self.choose_league_fanduel(league):
                        continue
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
                        team = bet['Game'].split(' @')
                        if not self.choose_team_nba(team):
                            continue