import time
import sys
import os
import datetime

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.modules.openclaw import MarketFetcher, NewsScraper
from app.modules.brain import DecisionMaker
from app.modules.portfolio import PortfolioManager

# Config
WATCHLIST = ["BTC-USD", "ETH-USD", "AAPL", "EURUSD=X"]
TRADE_AMOUNT_USD = 1000.0 # Fixed bet size for simplicity
CONFIDENCE_THRESHOLD = 0.7
LOG_FILE = "app/data/trade_log.txt"

def log_trade(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def run_bot_cycle(fetcher, scraper, brain, portfolio):
    print(f"\n--- Bot Cycle Start ---")

    for ticker in WATCHLIST:
        try:
            print(f"Analyzing {ticker}...")

            # 1. Fetch Data
            history = fetcher.get_history(ticker, period="2y") # Need long history for ML
            current_price = fetcher.get_current_price(ticker)

            if history.empty or current_price == 0:
                print(f"Skipping {ticker}: No data.")
                continue

            # 2. Get News
            news = scraper.get_asset_news(ticker)
            if not news:
                news = scraper.get_general_market_news()

            # 3. Decide
            decision = brain.decide(history, news)
            action = decision["action"]
            confidence = decision["confidence"]

            log_message = f"{ticker}: {action} (Conf: {confidence:.2f}) | Price: {current_price:.2f}"
            print(log_message)

            # 4. Execute Trade
            if confidence >= CONFIDENCE_THRESHOLD:
                holdings = portfolio.get_holdings()

                if action == "BUY":
                    # Check if we already have a significant position? (Simple logic: Buy more if cash allows)
                    if portfolio.buy(ticker, current_price, TRADE_AMOUNT_USD):
                        log_trade(f"EXECUTED BUY: {ticker} @ {current_price} | Amount: ${TRADE_AMOUNT_USD}")
                    else:
                        print(f"Buy failed (Insufficient funds?).")

                elif action == "SELL":
                    # Check if we have it
                    if ticker in holdings:
                        # Sell all
                        amount_units = holdings[ticker]["amount"]
                        if portfolio.sell(ticker, current_price, amount_units):
                             log_trade(f"EXECUTED SELL: {ticker} @ {current_price} | Units: {amount_units:.4f}")
                    else:
                        print("Sell signal but no holdings.")

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    print("--- Bot Cycle End ---")

def main():
    print("Starting Intelligent Hedge Fund Bot...")

    # Initialize
    fetcher = MarketFetcher()
    scraper = NewsScraper()
    brain = DecisionMaker()
    portfolio = PortfolioManager()

    # Ensure log dir exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    while True:
        run_bot_cycle(fetcher, scraper, brain, portfolio)
        time.sleep(60) # Run every minute

if __name__ == "__main__":
    main()
