import time

from config import CONTROLS
from utils.WebInteractor import WebInteractor
from utils.DataHandler import DataHandler

if __name__ == "__main__":
    Database = DataHandler()
    WebInteractor = WebInteractor(Database.bets)
    bets = Database.bets
    WebInteractor.make_bets(bets)
