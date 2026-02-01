import pandas as pd
import numpy as np
from textblob import TextBlob
from typing import List, Dict, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

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

class PredictiveModel:
    """
    Machine Learning model to predict market direction.
    """
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.technical = TechnicalAnalyzer()
        self.features = ['RSI', 'SMA_Diff', 'Returns', 'Volatility', 'Momentum']

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Feature Engineering from OHLCV data.
        """
        data = df.copy()

        # Calculate Indicators
        data['RSI'] = self.technical.calculate_rsi(data)
        data['SMA_Short'] = self.technical.calculate_sma(data, window=10)
        data['SMA_Long'] = self.technical.calculate_sma(data, window=20)
        data['SMA_Diff'] = (data['SMA_Short'] - data['SMA_Long']) / data['SMA_Long']
        data['Returns'] = data['Close'].pct_change()
        data['Volatility'] = data['Returns'].rolling(window=20).std()
        data['Momentum'] = data['Close'] - data['Close'].shift(5)

        # Target: 1 if Next Close > Current Close, else 0
        data['Target'] = (data['Close'].shift(-1) > data['Close']).astype(int)

        return data.dropna()

    def train(self, df: pd.DataFrame):
        """
        Trains the model on historical data.
        """
        if len(df) < 50:
            return # Not enough data

        processed_data = self.prepare_features(df)

        if processed_data.empty:
            return

        X = processed_data[self.features]
        y = processed_data['Target']

        self.model.fit(X, y)

    def predict(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Predicts direction for the latest data point.
        """
        if len(df) < 50:
             return {"prediction": 0, "probability": 0.5, "feature_importance": {}}

        processed_data = self.prepare_features(df) # Note: this drops the last row because of shift(-1) target, but we need the last row for features

        # Re-calculate features for the *very last* row (which has no target yet)
        last_row = df.iloc[[-1]].copy()
        # We need context for rolling windows, so take last 30 rows
        context = df.iloc[-30:].copy()

        # Calculate features on context
        context['RSI'] = self.technical.calculate_rsi(context)
        context['SMA_Short'] = self.technical.calculate_sma(context, window=10)
        context['SMA_Long'] = self.technical.calculate_sma(context, window=20)
        context['SMA_Diff'] = (context['SMA_Short'] - context['SMA_Long']) / context['SMA_Long']
        context['Returns'] = context['Close'].pct_change()
        context['Volatility'] = context['Returns'].rolling(window=20).std()
        context['Momentum'] = context['Close'] - context['Close'].shift(5)

        current_features = context.iloc[[-1]][self.features]

        # Handle NaNs if context wasn't enough (though 30 should be enough for 20 window)
        current_features = current_features.fillna(0)

        prediction = self.model.predict(current_features)[0]
        probability = self.model.predict_proba(current_features)[0][1] # Prob of class 1 (Up)

        importances = dict(zip(self.features, self.model.feature_importances_))

        return {
            "prediction": int(prediction), # 1 for Up, 0 for Down
            "probability": round(probability, 2),
            "feature_importance": importances
        }

class DecisionMaker:
    """
    Combines signals to make a decision.
    """
    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.technical = TechnicalAnalyzer()
        self.ml_model = PredictiveModel()

    def decide(self, history: pd.DataFrame, headlines: List[str]) -> Dict[str, any]:
        """
        Returns a decision dictionary.
        """
        # Sentiment Score
        sentiment_score = self.sentiment.analyze(headlines)

        # Technical Indicators (Classic)
        if len(history) < 50:
             return {"action": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

        rsi = self.technical.calculate_rsi(history).iloc[-1]

        # ML Prediction
        # 1. Train on history (excluding last day to avoid lookahead bias in testing, but here we train on all available closed candles)
        # In a real system, we'd retrain periodically. Here we retrain on every request for the demo.
        self.ml_model.train(history)
        ml_result = self.ml_model.predict(history)

        ml_pred = ml_result['prediction'] # 1 or 0
        ml_prob = ml_result['probability']

        # Logic Combination
        # Score ranges from -10 to 10
        score = 0

        # ML Contribution (Weight: 50%)
        # If ML says UP (1) with high prob, add score.
        if ml_pred == 1:
            score += 5 * (ml_prob - 0.5) * 2 # Scale prob 0.5-1.0 to 0-1 factor
        else:
            score -= 5 * (0.5 - ml_prob) * 2

        # Sentiment Contribution (Weight: 30%)
        # Sentiment score is -1 to 1.
        score += 3 * sentiment_score

        # Technical/Rule-Based Contribution (Weight: 20%)
        if rsi < 30:
            score += 2
        elif rsi > 70:
            score -= 2

        # Final Decision
        action = "HOLD"
        final_confidence = 0.5

        if score >= 1.5:
            action = "BUY"
            final_confidence = min(0.5 + (score/10), 0.95)
        elif score <= -1.5:
            action = "SELL"
            final_confidence = min(0.5 + (abs(score)/10), 0.95)

        return {
            "action": action,
            "confidence": round(final_confidence, 2),
            "details": {
                "sentiment_score": round(sentiment_score, 2),
                "rsi": round(rsi, 2) if not np.isnan(rsi) else 0,
                "ml_prediction": "UP" if ml_pred == 1 else "DOWN",
                "ml_probability": ml_prob,
                "ml_features": ml_result['feature_importance'],
                "score": round(score, 2)
            }
        }
