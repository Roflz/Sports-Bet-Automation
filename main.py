import argparse
from datetime import datetime
import keyboard
import time

from utils.ControlMeta import toggle_pause
from utils.WebInteractorBet365 import WebInteractorBet365
from utils.DataHandler import DataHandler
from utils.utils import remove_matched_bets, has_nba_bets, send_sms_via_email, print_bets_summary, send_simple_email

# Global instance to be used by other scripts
webinteractor365_instance = None

def main(bet_amount, bet_amount_first_basket):
    global webinteractor365_instance
    starting_cash = 79.30

    while True:
        Database = DataHandler()
        bets = Database.bets
        # Remove matched bets and log results
        remove_matched_bets(bets, f"results/results_{datetime.today().strftime('%Y-%m-%d')}.csv")

        if has_nba_bets(bets):
            printed_bets = print_bets_summary(bets)
            # Uncomment the following if needed
            # send_sms_via_email('Bot is placing bets on Bet365', 'sup')
            # send_simple_email()
            for book, leagues in bets.items():
                if book == 'bet365':
                    # Uncomment the following if needed
                    # send_sms_via_email('Bot is placing bets on Bet365', printed_bets)
                    webinteractor365_instance = WebInteractorBet365(leagues)
                    webinteractor365_instance.make_bets(bet_amount, bet_amount_first_basket)
                # Add handling for other books if needed
        print('All bets made, waiting for 60 seconds before checking for more bets')
        time.sleep(60)

if __name__ == "__main__":
    # Set up the hotkey for toggling pause
    keyboard.add_hotkey("alt+p", toggle_pause)
    print("Press alt+p to pause.")

    # Set up argparse to accept command-line arguments for bet amounts
    parser = argparse.ArgumentParser(description="Start the betting script with custom bet amounts.")
    parser.add_argument("--bet_amount", type=float, default=3,
                        help="The amount to bet on each regular bet (default: 3)")
    parser.add_argument("--bet_amount_first_basket", type=float, default=1,
                        help="The amount to bet on the first basket bet (default: 1)")
    args = parser.parse_args()

    # Pass the command-line values to the main function
    main(args.bet_amount, args.bet_amount_first_basket)
