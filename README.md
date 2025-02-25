# Betting Bot Script

A Python-based script that automates placing bets on Bet365 by continuously monitoring and processing betting data. This script leverages web interaction and keyboard shortcuts to help manage and execute bets, and it supports command-line parameters for easy configuration.

## Features

- **Automated Betting:** Monitors and places bets on Bet365 by processing data from your configured data handler.
- **Dynamic Bet Configuration:** Set your regular bet amount and the first basket bet amount using command-line arguments.
- **Pause Functionality:** Easily pause the script at any time by pressing `alt+p`.
- **Bet Processing:** Continuously cleans up matched bets and logs the results daily.

## Requirements

- **Python 3.7+**
- **Python Libraries:**
  - `keyboard`
  - `time`
  - `datetime`
- Additional utility modules included in the `utils` folder:
  - `ControlMeta.py`
  - `WebInteractorBet365.py`
  - `DataHandler.py`
  - `utils.py`

*(Ensure you have these dependencies installed, either via a `requirements.txt` or manually.)*

## Installation

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>

2. **Navigate to the Repository Directory:**
   ```bash
   cd <repository-url>

3. **Install Required Dependencies:**
   ```bash
   pip install -r requirements.txt

## Usage

Run the script from the command line and optionally specify the bet amounts:

  ```bash
  python main.py --bet_amount 5 --bet_amount_first_basket 2

If no arguments are provided, the script defaults to:

- `bet_amount = 3`
- `bet_amount_first_basket = 1`

**Note:**  
You can pause the script at any time by pressing **alt+p**.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests with improvements or bug fixes.

## License

This project is licensed under the **MIT License**.
