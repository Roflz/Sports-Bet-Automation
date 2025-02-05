import csv
import requests
from collections import defaultdict


class DataHandler:
    def __init__(self):
        self.data = self.get_data()
        self.bets = self.filter_bets(self.data)
        self.split_bets_by_book_league_game(self.bets)

    def filter_bets(self, bets):
        allowed_keys = {
            "Book", "Game", "Type", "Team", "Player", "Line", "Price",
            "Price Target", "Time Until", "Position", "EV", "league"
        }
        allowed_books = {"bet365", "fanduel", "espnbet", "betrivers", "betmgm", "draftkings"}

        filtered_bets = []

        for bet in bets:
            if bet.get("Book") in allowed_books:
                filtered_bets.append({key: bet[key] for key in allowed_keys if key in bet})

        return filtered_bets

    def split_bets_by_book_league_game(self, bets):
        # Sort by Book, then League, then Game
        sorted_bets = sorted(bets,
                             key=lambda bet: (bet.get("Book", ""), bet.get("League", ""), bet.get("Game", "")))

        # Create a nested dictionary structure
        grouped_bets = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for bet in sorted_bets:
            book = bet["Book"]
            league = bet["league"]
            game = bet["Game"]
            grouped_bets[book][league][game].append(bet)

        # Convert defaultdict to a normal dictionary
        self.bets = {book: {league: dict(games) for league, games in leagues.items()} for book, leagues in
                grouped_bets.items()}

    def get_data(self):
        # Define the URL with query parameters
        url = "https://p5ohocy8m9.execute-api.us-west-1.amazonaws.com/prod/items/bets"

        # Query parameters (from the URL)
        params = {
            "dataset": "test",
            # "email": "mikaellund226@gmail.com",
            # "staticBalance": "20781.3878981",
            # "version": "1.16.36",
        }

        # Headers (copied from network request)
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "authorization": "AWS4-HMAC-SHA256 Credential=ASIA3ESVPS74RC7QYQ74/20250205/us-west-1/execute-api/aws4_request, SignedHeaders=host;x-amz-date;x-amz-security-token, Signature=bc3d53fb2955dca24035542ffa066b393a81741487d2e9a6d8215a9498d31a84",
            "origin": "https://www.cleatstreet.app",
            "referer": "https://www.cleatstreet.app/",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "x-amz-date": "20250205T052809Z",
            "x-amz-security-token": "IQoJb3JpZ2luX2VjECYaCXVzLXdlc3QtMSJIMEYCIQCBTtHx4DA1X8oMBQXW/uRHoOY3Q/MXNLFll6cZ/bGBeQIhAKpBkWNBnZuI+O9XsdiafbQXSpJEHkL1L44wobes48zpKsQECD8QABoMNzY1NzU3MjAwMzc3IgzyUSiyi1bVWBaDovIqoQRUjwShUg0d5DIooXpXHIpnc47BaW6/lYat/H+gR1fgtjhaJl0u3/yFbnK+phGtwpsbAgTK5Cy/7AJwzXKPr0zb+8uCegkVFSff5vK7RBkq4VXubzcOOKWBJHlR8ocVGL1Ld/G8HCw4hOltsSHrymzHnGVoGUJlj3Fm8KH/ePymdnzctRxegZx2OrFOeADpE2XXdsA97DKJqp8+WwEvTQqAfoHEGu6G6KlPTirx3Xl8dppUxu00r4LexT6zViyKWYyPcRejEgOVkIYrnmj1Fi7BtTpZa7pYKmw2uRZgsL5JUt+8BX1SyrBgaCjzJBS+mQ/cTRA787n3cmFvO17s7uuOj2j1md2K+4pQwVzJZxw9q+5+jvS5gWLxIKXBlP0hkIQopxqeyacVNLfh+zL+PIyM3qPX0SQHQzHYo3/5LplfCB7Zz62hg8VboAQuPnYpBEYE6JxgtcHb1tQGXjnvnuSyn+SAuCzcaznSRBg5AQZRBsnSNTrc2hs02XVoGlijm6LERHmo+EhxLBcn87pXaOBYhhlkUzSjLEhzcCdSEYX4GPc/0jfaDRO+T7gOfCohUwONQ5gZkEAe7VVOpo3HtGclGkhay9fEtcLqb8Qm/Y4P6hBV7sH5EoGZwVCJDBxHiSAaDiACmjrf2+yrxC7jYfVFCRlnnbqNTfEH8t3vl+ZINGcaGp7xjm3rOfHa0frsc2ZGp1iYBekEeKA/e+et/ppuvjDp7Yu9BjqEAr/Wm4WHE4avdMgjC9EEEZs0u4wEkoowpT5ele1gD8DQyzAg821Z0cSBzYyYl4g0amnEffFNALYLl1rXcITJ9n5AEqhCZJrl61GLyU0Xec8mxqng5PrDYb8iERrt2ePmywUspHWe4t7Swmo9FsLeDGOOgc+PyKdEHCXjKwLoHex3VUYKjfSkn8kG7bErlB2y0y+xbGDDzKXDM8sJmQqGj84rt3Ox3PymWRnq5uwJks30nxyBN85JZxxQuWB9yNgwC5zhaAzzfVzlQhJw4dCS3AjgjmGxAnP7kJy+sk6hPekZKN6FQk4xKAGvYf4VGLoky23fT39vMqkGI0lN0xhxA0OBsR6n",
        }

        # Make the GET request
        response = requests.get(url, headers=headers, params=params)

        # Check response status
        if response.status_code == 200:
            data = response.json()  # Parse response JSON
            print(data)
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")

        return data

