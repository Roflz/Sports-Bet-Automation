import time
from datetime import datetime

from config import CONTROLS
from utils.WebInteractor import WebInteractor
from utils.WebInteractorBet365 import WebInteractorBet365
from utils.WebInteractorFanduel import WebInteractorFanduel
from utils.DataHandler import DataHandler
from utils.utils import remove_matched_bets, read_csv_to_dict

if __name__ == "__main__":
    Database = DataHandler()
    # WebInteractor = WebInteractor(Database.bets)
    bets = Database.bets
    # bets = dict()
    # bets['bet365'] = dict()
    # bets['bet365']['nba'] = dict()
    # bets['bet365']['nba']['dallas mavericks @ boston celtics'] = read_csv_to_dict(f"results\\results_2025-02-06.csv")
    # not_filtered_bets = bets
    # bets = read_csv_to_dict(f"results\\results_2025-02-06.csv")
    remove_matched_bets(bets, f"results\\results_{datetime.today().strftime('%Y-%m-%d')}.csv")
    for book, leagues in bets.items():
        book = 'fanduel'
        # book = 'bet365'
        if book == 'bet365':
            WebInteractorBet365 = WebInteractorBet365(leagues)
            WebInteractorBet365.make_bets()
        elif book == 'fanduel':
            WebInteractorFanduel = WebInteractorFanduel(leagues)
            WebInteractorFanduel.make_bets()
