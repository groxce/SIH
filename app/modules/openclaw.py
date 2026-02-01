import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict, Optional

class MarketFetcher:
    """
    Fetches market data using yfinance.
    """
    def __init__(self):
        pass

    def get_history(self, ticker_symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches historical OHLCV data.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            history = ticker.history(period=period, interval=interval)
            return history
        except Exception as e:
            print(f"Error fetching history for {ticker_symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, ticker_symbol: str) -> float:
        """
        Fetches the current price.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Try fast info first, then regular info
            price = ticker.fast_info.last_price
            if price is None:
                 history = ticker.history(period="1d")
                 if not history.empty:
                     price = history['Close'].iloc[-1]
            return price
        except Exception as e:
            print(f"Error fetching price for {ticker_symbol}: {e}")
            return 0.0

class NewsScraper:
    """
    Scrapes news from various sources.
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_asset_news(self, ticker_symbol: str) -> List[str]:
        """
        Fetches specific news for an asset using yfinance API.
        Returns a list of headlines.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            news_items = ticker.news
            headlines = []
            if news_items:
                for item in news_items:
                    # Handle different yfinance news structures
                    if 'content' in item and 'title' in item['content']:
                        headlines.append(item['content']['title'])
                    elif 'title' in item:
                        headlines.append(item['title'])
            return headlines
        except Exception as e:
            print(f"Error fetching news for {ticker_symbol}: {e}")
            return []

    def get_general_market_news(self) -> List[str]:
        """
        Scrapes general market news from a public RSS feed (e.g., Yahoo Finance).
        """
        url = "https://finance.yahoo.com/news/rssindex"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                headlines = [item.title.text for item in items[:10]] # Get top 10
                return headlines
            else:
                print(f"Failed to fetch general news. Status: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error scraping general news: {e}")
            return []
