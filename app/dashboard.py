import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os
import time

# Add app directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.modules.openclaw import MarketFetcher, NewsScraper
from app.modules.brain import DecisionMaker
from app.modules.portfolio import PortfolioManager

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="QUANT-AI TERMINAL",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (STITCH INSPIRED) ---
st.markdown("""
<style>
    /* MAIN THEME */
    .stApp {
        background-color: #0B0E11;
        color: #E0E0E0;
    }

    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    /* HEADERS */
    h1, h2, h3 {
        color: #FFFFFF;
        font-weight: 700;
        letter-spacing: 1px;
    }

    .logo-text {
        color: #3B82F6; /* Blue Accent */
        font-size: 24px;
        font-weight: 800;
    }

    /* METRIC CARDS */
    div[data-testid="stMetric"] {
        background-color: #151A21;
        border: 1px solid #2D3748;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #00F0FF; /* Cyan Neon */
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }

    div[data-testid="stMetricLabel"] {
        color: #A0AEC0;
        font-size: 14px;
        text-transform: uppercase;
    }

    /* CUSTOM CARDS */
    .card {
        background-color: #151A21;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2D3748;
        margin-bottom: 20px;
    }

    .card-header {
        color: #A0AEC0;
        font-size: 12px;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 1.5px;
        font-weight: 600;
    }

    /* BUTTONS */
    .stButton > button {
        background-color: #00F0FF;
        color: #000000;
        border: none;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #00B8C4;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.6);
    }

    /* TABLES */
    div[data-testid="stTable"] {
        background-color: #151A21 !important;
        border-radius: 8px;
        overflow: hidden;
    }

    /* GAUGE & ACCENTS */
    .confidence-high { color: #00F0FF; }
    .confidence-low { color: #FF0055; }

</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_status = st.columns([4, 1])
with col_logo:
    st.markdown('<div class="logo-text">🔵 QUANT-AI TERMINAL <span style="font-size: 12px; color: #6B7280; font-weight: 400;">| v4.2 NEURAL ENGINE</span></div>', unsafe_allow_html=True)

with col_status:
    st.markdown('<div style="text-align: right; color: #10B981; font-weight: 600;">● LIVE SYSTEM</div>', unsafe_allow_html=True)

st.divider()

# --- INPUT SECTION (Sticky or Top) ---
col_input1, col_input2, col_input3 = st.columns([2, 1, 1])
with col_input1:
    ticker = st.text_input("ASSET TICKER", value="BTC-USD", label_visibility="visible")
with col_input2:
    period = st.selectbox("TIMEFRAME", ["1mo", "3mo", "6mo", "1y", "2y", "max"], index=3)
with col_input3:
    st.write("")
    st.write("")
    analyze_btn = st.button("RUN ANALYSIS ⚡")

# --- INITIALIZE STATE ---
if 'history' not in st.session_state:
    st.session_state['history'] = None
if 'decision' not in st.session_state:
    st.session_state['decision'] = None
if 'news' not in st.session_state:
    st.session_state['news'] = None

# --- ANALYSIS LOGIC ---
if analyze_btn:
    with st.spinner('NEURAL ENGINE PROCESSING...'):
        fetcher = MarketFetcher()
        scraper = NewsScraper()
        brain = DecisionMaker()

        hist = fetcher.get_history(ticker, period=period)
        if not hist.empty:
            st.session_state['history'] = hist
            st.session_state['news'] = scraper.get_asset_news(ticker) or scraper.get_general_market_news()
            st.session_state['decision'] = brain.decide(hist, st.session_state['news'])
        else:
            st.error("DATA FEED ERROR")

# --- DASHBOARD LAYOUT ---
# 2 Columns: Left (Analysis), Right (Portfolio/Decision)
col_left, col_right = st.columns([3, 1.5], gap="medium")

# === LEFT COLUMN: MARKET DATA ===
with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-header">{ticker} // PRICE ACTION</div>', unsafe_allow_html=True)

    if st.session_state['history'] is not None:
        hist = st.session_state['history']

        # Plotly Chart with Dark Theme
        fig = go.Figure(data=[go.Candlestick(x=hist.index,
                        open=hist['Open'],
                        high=hist['High'],
                        low=hist['Low'],
                        close=hist['Close'],
                        increasing_line_color='#00F0FF', # Cyan
                        decreasing_line_color='#FF0055'  # Neon Red
                        )])

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=500,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(family="Space Grotesk", color="#A0AEC0"),
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("AWAITING INPUT COMMAND...")

    st.markdown('</div>', unsafe_allow_html=True)

    # Feature Importance (Bar Chart)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">NEURAL FEATURE WEIGHTS</div>', unsafe_allow_html=True)

    if st.session_state['decision'] and st.session_state['decision']['details']['ml_features']:
        feat_imp = st.session_state['decision']['details']['ml_features']
        feat_df = pd.DataFrame(list(feat_imp.items()), columns=['Feature', 'Importance'])
        feat_df = feat_df.sort_values(by='Importance', ascending=True)

        fig_feat = go.Figure(go.Bar(
            x=feat_df['Importance'],
            y=feat_df['Feature'],
            orientation='h',
            marker_color='#3B82F6' # Blue
        ))
        fig_feat.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(family="Space Grotesk", color="#A0AEC0")
        )
        st.plotly_chart(fig_feat, use_container_width=True)
    else:
        st.text("NO MODEL DATA")
    st.markdown('</div>', unsafe_allow_html=True)

# === RIGHT COLUMN: INTELLIGENCE & PORTFOLIO ===
with col_right:

    # 1. AI Confidence Gauge (Simulated with Metric/Color)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">AI CONFIDENCE SCORE</div>', unsafe_allow_html=True)

    if st.session_state['decision']:
        decision = st.session_state['decision']
        conf = int(decision['confidence'] * 100)
        action = decision['action']

        # Circular Progress visualization hack or just big text
        color = "#00F0FF" if action == "BUY" else ("#FF0055" if action == "SELL" else "#A0AEC0")

        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">
            <div style="border: 4px solid {color}; border-radius: 50%; width: 120px; height: 120px; display: flex; justify-content: center; align-items: center; box-shadow: 0 0 20px {color}40;">
                <h1 style="color: {color}; margin: 0; font-size: 36px;">{conf}%</h1>
            </div>
            <h2 style="color: {color}; margin-top: 15px; letter-spacing: 2px;">{action}</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top: 20px; font-size: 14px; text-align: center; color: #888;">
            MODEL CONSENSUS: <b>{decision['details'].get('ml_prediction', 'N/A')}</b><br>
            SENTIMENT: <b>{decision['details']['sentiment_score']}</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='text-align: center; color: #444;'>OFFLINE</h3>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Live Portfolio Summary
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">MANAGED ASSETS</div>', unsafe_allow_html=True)

    pm = PortfolioManager()
    balance = pm.get_balance()
    holdings = pm.get_holdings()

    st.metric("TOTAL LIQUIDITY", f"${balance:,.2f}", delta=None)

    if holdings:
        data = []
        for tick, info in holdings.items():
            data.append({"ASSET": tick, "AMT": info["amount"], "AVG": f"${info['avg_price']:,.0f}"})
        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
    else:
        st.markdown("<div style='color: #666; font-size: 14px; text-align: center; padding: 10px;'>NO ACTIVE POSITIONS</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Trade Log (Mini)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">EXECUTION LOG</div>', unsafe_allow_html=True)

    log_file = "app/data/trade_log.txt"
    log_content = ""
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            # Get last 5 lines, format them slightly
            for line in reversed(lines[-5:]):
                # Simple parsing to remove timestamp for space
                parts = line.split("]", 1)
                msg = parts[1].strip() if len(parts) > 1 else line.strip()
                color = "#10B981" if "BUY" in msg else ("#F43F5E" if "SELL" in msg else "#6B7280")
                log_content += f"<div style='font-size: 12px; margin-bottom: 5px; color: {color}; border-left: 2px solid {color}; padding-left: 5px;'>{msg}</div>"

    if log_content:
        st.markdown(log_content, unsafe_allow_html=True)
    else:
        st.text("NO EXECUTIONS")

    st.markdown('</div>', unsafe_allow_html=True)
