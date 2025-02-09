from datetime import datetime

import keyboard
import time

from utils.ControlMeta import toggle_pause
from utils.WebInteractorBet365 import WebInteractorBet365
from utils.DataHandler import DataHandler
from utils.utils import remove_matched_bets, has_nba_bets

global WebInteractorBet365
# WebInteractorBet365 = None

if __name__ == "__main__":
    # Listen for Spacebar to toggle pause
    keyboard.add_hotkey("p", toggle_pause)

    while True:
        Database = DataHandler()
        bets = Database.bets
        remove_matched_bets(bets, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv")
        if has_nba_bets(bets):
            for book, leagues in bets.items():
                # book = 'fanduel'
                # book = 'bet365'
                if book == 'bet365':
                    WebInteractorBet365 = WebInteractorBet365(leagues)
                    WebInteractorBet365.make_bets()
                # elif book == 'fanduel':
                #     WebInteractorFanduel = WebInteractorFanduel(leagues)
                #     WebInteractorFanduel.make_bets()
        print('All bets made, waiting for 60 seconds before checking for more bets')
        time.sleep(60)