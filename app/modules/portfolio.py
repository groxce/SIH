import json
import os
from typing import Dict, Optional

DATA_FILE = "app/data/portfolio.json"

class PortfolioManager:
    """
    Manages a paper trading portfolio.
    """
    def __init__(self, initial_balance: float = 100000.0):
        self.filepath = DATA_FILE
        self.portfolio = {
            "balance": initial_balance,
            "holdings": {} # "BTC-USD": {"amount": 0.5, "avg_price": 50000}
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    self.portfolio = json.load(f)
            except Exception as e:
                print(f"Error loading portfolio: {e}")
        else:
            self.save_data()

    def save_data(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.portfolio, f, indent=4)
        except Exception as e:
            print(f"Error saving portfolio: {e}")

    def get_balance(self) -> float:
        return self.portfolio["balance"]

    def get_holdings(self) -> Dict:
        return self.portfolio["holdings"]

    def buy(self, ticker: str, price: float, amount_usd: float) -> bool:
        """
        Buys an asset worth amount_usd.
        """
        if amount_usd <= 0 or price <= 0:
            return False

        if self.portfolio["balance"] >= amount_usd:
            units = amount_usd / price

            # Update Balance
            self.portfolio["balance"] -= amount_usd

            # Update Holdings
            if ticker not in self.portfolio["holdings"]:
                self.portfolio["holdings"][ticker] = {"amount": 0.0, "avg_price": 0.0}

            current_amount = self.portfolio["holdings"][ticker]["amount"]
            current_avg_price = self.portfolio["holdings"][ticker]["avg_price"]

            # Calculate new weighted average price
            total_cost = (current_amount * current_avg_price) + amount_usd
            new_amount = current_amount + units
            new_avg_price = total_cost / new_amount

            self.portfolio["holdings"][ticker]["amount"] = new_amount
            self.portfolio["holdings"][ticker]["avg_price"] = new_avg_price

            self.save_data()
            return True
        return False

    def sell(self, ticker: str, price: float, amount_units: Optional[float] = None) -> bool:
        """
        Sells an asset. If amount_units is None, sell all.
        """
        if ticker not in self.portfolio["holdings"] or price <= 0:
            return False

        current_amount = self.portfolio["holdings"][ticker]["amount"]

        if amount_units is None or amount_units > current_amount:
            amount_units = current_amount

        if amount_units <= 0:
            return False

        sale_value = amount_units * price

        # Update Balance
        self.portfolio["balance"] += sale_value

        # Update Holdings
        self.portfolio["holdings"][ticker]["amount"] -= amount_units

        # Clean up if empty
        if self.portfolio["holdings"][ticker]["amount"] <= 0.0000001:
            del self.portfolio["holdings"][ticker]

        self.save_data()
        return True

    def get_valuation(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates total portfolio value (Cash + Assets).
        """
        total_value = self.portfolio["balance"]
        for ticker, data in self.portfolio["holdings"].items():
            price = current_prices.get(ticker, data["avg_price"]) # Fallback to avg_price if current not found
            total_value += data["amount"] * price
        return total_value
