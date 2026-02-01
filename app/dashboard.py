import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

# Add app directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.openclaw import MarketFetcher, NewsScraper
from app.modules.brain import DecisionMaker

st.set_page_config(page_title="Hedge Fund AI", layout="wide")

st.title("🤖 Intelligent Hedge Fund System")
st.markdown("### Powered by Machine Learning & OpenClaw Data Engine")

# Sidebar
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Asset Ticker", value="BTC-USD")
period = st.sidebar.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "max"], index=1)

if st.sidebar.button("Analyze Market"):
    with st.spinner('Fetching data and crunching numbers...'):
        # Initialize Modules
        fetcher = MarketFetcher()
        scraper = NewsScraper()
        brain = DecisionMaker()

        # 1. Fetch Data
        history = fetcher.get_history(ticker, period=period)
        if history.empty:
            st.error(f"Could not fetch data for {ticker}")
        else:
            current_price = fetcher.get_current_price(ticker)

            # 2. Scrape News
            news_headlines = scraper.get_asset_news(ticker)
            if not news_headlines:
                news_headlines = scraper.get_general_market_news()
                st.warning("No specific news found for asset. Using general market news.")

            # 3. Analyze
            decision = brain.decide(history, news_headlines)

            # Layout
            col1, col2 = st.columns([2, 1])

            with col1:
                # Price Chart
                st.subheader(f"{ticker} Price Action")
                fig = go.Figure(data=[go.Candlestick(x=history.index,
                                open=history['Open'],
                                high=history['High'],
                                low=history['Low'],
                                close=history['Close'])])
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Decision Card
                st.subheader("AI Decision")
                action = decision['action']
                color = "grey"
                if action == "BUY": color = "green"
                elif action == "SELL": color = "red"

                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background-color: {color}; color: white; border-radius: 10px;">
                    <h1>{action}</h1>
                    <h3>Confidence: {int(decision['confidence']*100)}%</h3>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### Analysis Details")
                details = decision['details']
                st.write(f"**Score:** {details['score']}")
                st.write(f"**RSI:** {details['rsi']}")
                st.write(f"**Sentiment:** {details['sentiment_score']}")

                if details['rsi'] < 30:
                    st.success("RSI indicates Oversold")
                elif details['rsi'] > 70:
                    st.error("RSI indicates Overbought")

            # News Section
            st.subheader("Market Intelligence (OpenClaw)")
            for i, headline in enumerate(news_headlines[:5]):
                st.text(f"📰 {headline}")

else:
    st.info("Enter a ticker and click 'Analyze Market' to start.")
