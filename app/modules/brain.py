import pandas as pd
import numpy as np
from textblob import TextBlob
from typing import List, Dict

class SentimentAnalyzer:
    """
    Analyzes sentiment of text.
    """
    def analyze(self, headlines: List[str]) -> float:
        """
        Returns average polarity (-1 to 1).
        """
        if not headlines:
            return 0.0

        scores = []
        # Simple financial keyword override/boost
        neg_keywords = ['crash', 'drop', 'loss', 'losses', 'bear', 'slump', 'down', 'panic', 'weak', 'worst']
        pos_keywords = ['soar', 'jump', 'profit', 'profits', 'bull', 'surge', 'up', 'strong', 'growth', 'best']

        for text in headlines:
            blob = TextBlob(text)
            score = blob.sentiment.polarity

            # Keyword adjustment
            lower_text = text.lower()
            for kw in neg_keywords:
                if kw in lower_text:
                    score -= 0.3
            for kw in pos_keywords:
                if kw in lower_text:
                    score += 0.3

            # Clamp between -1 and 1
            score = max(-1.0, min(1.0, score))
            scores.append(score)

        return np.mean(scores)

class TechnicalAnalyzer:
    """
    Calculates technical indicators.
    """
    def calculate_sma(self, df: pd.DataFrame, window: int = 20) -> pd.Series:
        return df['Close'].rolling(window=window).mean()

    def calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class DecisionMaker:
    """
    Combines signals to make a decision.
    """
    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.technical = TechnicalAnalyzer()

    def decide(self, history: pd.DataFrame, headlines: List[str]) -> Dict[str, any]:
        """
        Returns a decision dictionary: {action: 'BUY'|'SELL'|'HOLD', confidence: float, details: dict}
        """
        # Sentiment Score
        sentiment_score = self.sentiment.analyze(headlines)

        # Technical Indicators
        if len(history) < 20:
             # Not enough data
             return {"action": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

        rsi = self.technical.calculate_rsi(history).iloc[-1]
        sma_short = self.technical.calculate_sma(history, window=10).iloc[-1]
        sma_long = self.technical.calculate_sma(history, window=20).iloc[-1]
        current_price = history['Close'].iloc[-1]

        # Logic
        score = 0 # -10 to 10

        # Technical Logic
        if rsi < 30:
            score += 3 # Oversold -> Buy
        elif rsi > 70:
            score -= 3 # Overbought -> Sell

        if sma_short > sma_long:
            score += 2 # Golden Cross-ish
        elif sma_short < sma_long:
            score -= 2 # Death Cross-ish

        # Sentiment Logic
        if sentiment_score > 0.1:
            score += 2
        elif sentiment_score < -0.1:
            score -= 2

        # Final Decision
        action = "HOLD"
        confidence = 0.5

        if score >= 3:
            action = "BUY"
            confidence = min(0.5 + (score/20), 0.95)
        elif score <= -3:
            action = "SELL"
            confidence = min(0.5 + (abs(score)/20), 0.95)

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "details": {
                "sentiment_score": round(sentiment_score, 2),
                "rsi": round(rsi, 2) if not np.isnan(rsi) else 0,
                "sma_short": round(sma_short, 2) if not np.isnan(sma_short) else 0,
                "sma_long": round(sma_long, 2) if not np.isnan(sma_long) else 0,
                "score": score
            }
        }
