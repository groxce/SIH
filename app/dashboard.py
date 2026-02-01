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
st.markdown("### Powered by Machine Learning, OpenClaw & AI")

# Sidebar
st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Asset Ticker", value="BTC-USD")
period = st.sidebar.selectbox("Period", ["6mo", "1y", "2y", "5y", "max"], index=1)
st.sidebar.caption("Note: Longer periods provide better training data for the ML model.")

if st.sidebar.button("Analyze Market"):
    with st.spinner('Fetching data, Scraping news, Training ML models...'):
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

            # 3. Analyze (Includes Training ML)
            decision = brain.decide(history, news_headlines)
            details = decision['details']

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

                # ML Feature Importance Chart
                if 'ml_features' in details and details['ml_features']:
                    st.subheader("🧠 ML Model: Feature Importance")
                    feat_imp = details['ml_features']
                    feat_df = pd.DataFrame(list(feat_imp.items()), columns=['Feature', 'Importance'])
                    feat_df = feat_df.sort_values(by='Importance', ascending=True)

                    fig_feat = go.Figure(go.Bar(
                        x=feat_df['Importance'],
                        y=feat_df['Feature'],
                        orientation='h'
                    ))
                    fig_feat.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                    st.plotly_chart(fig_feat, use_container_width=True)

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

                # Metrics
                st.markdown("#### Analysis Details")
                st.metric("Total Score", details['score'])

                # ML Section
                st.markdown("---")
                st.markdown("##### 🔮 Predictive Model")
                ml_pred = details.get('ml_prediction', 'N/A')
                ml_prob = details.get('ml_probability', 0)

                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Prediction", ml_pred)
                col_m2.metric("Probability", f"{int(ml_prob*100)}%")

                # Sentiment Section
                st.markdown("---")
                st.markdown("##### 📰 Sentiment Analysis")
                st.metric("Sentiment Score", details['sentiment_score'])

                # Technical Section
                st.markdown("---")
                st.markdown("##### 📈 Technical Indicators")
                st.metric("RSI", details['rsi'])
                if details['rsi'] < 30:
                    st.success("Oversold")
                elif details['rsi'] > 70:
                    st.error("Overbought")

            # News Section
            st.subheader("Market Intelligence (OpenClaw)")
            for i, headline in enumerate(news_headlines[:10]):
                st.markdown(f"- {headline}")

else:
    st.info("Enter a ticker (e.g., BTC-USD, AAPL, EURUSD=X) and click 'Analyze Market' to start.")
