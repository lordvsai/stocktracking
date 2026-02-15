import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox
import pandas as pd

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- 1. SEARCH LOGIC ---
def search_stocks(searchterm: str):
    if not searchterm or len(searchterm) < 2: return []
    try:
        search = yf.Search(searchterm, max_results=8)
        return [(f"{q['shortname']} ({q['symbol']})", q['symbol']) for q in search.quotes]
    except: return []

st.title("📈 VibeStock Pro")

selected_ticker = st_searchbox(search_stocks, placeholder="Search (e.g. Hindalco, Google...)", key="stock_search")

if 'watchlist' not in st.session_state: st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]
if 'period' not in st.session_state: st.session_state.period = "1y"
if selected_ticker: st.session_state.current_ticker = selected_ticker

ticker = st.session_state.get('current_ticker', "AAPL")
stock_obj = yf.Ticker(ticker)

# --- 2. TECHNICAL SETTINGS PANEL ---
with st.expander("🛠️ Technical Indicators"):
    c1, c2, c3 = st.columns(3)
    show_50dma = c1.checkbox("50 DMA", value=True)
    show_200dma = c1.checkbox("200 DMA")
    show_200wma = c2.checkbox("200 WMA")
    show_bb = c2.checkbox("Bollinger Bands")
    show_rsi = c3.checkbox("RSI (Relative Strength)")

# --- 3. DATA & CALCULATIONS ---
p_map = {"1D": "1d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "10Y": "10y", "MAX": "max"}
interval = "15m" if st.session_state.period == "1d" else "1d"
data = stock_obj.history(period=st.session_state.period, interval=interval)

if not data.empty:
    # Math for Indicators
    if show_50dma: data['50DMA'] = data['Close'].rolling(50).mean()
    if show_200dma: data['200DMA'] = data['Close'].rolling(200).mean()
    if show_200wma: 
        # For a true 200 WMA, we fetch weekly data separately
        weekly_data = stock_obj.history(period="max", interval="1wk")
        data['200WMA'] = weekly_data['Close'].rolling(200).mean()
    if show_bb:
        sma = data['Close'].rolling(20).mean()
        std = data['Close'].rolling(20).std()
        data['BB_Up'] = sma + (std * 2)
        data['BB_Low'] = sma - (std * 2)
    
    # --- 4. THE CHART ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF", width=2)))
    
    if show_50dma: fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(color="orange")))
    if show_200dma: fig.add_trace(go.Scatter(x=data.index, y=data['200DMA'], name="200 DMA", line=dict(color="red")))
    if show_200wma: fig.add_trace(go.Scatter(x=data.index, y=data['200WMA'], name="200 WMA", line=dict(color="purple", dash="dash")))
    
    if show_bb:
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Up'], name="BB Upper", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Low'], name="BB Lower", fill='tonexty', line=dict(width=0), fillcolor='rgba(173,216,230,0.2)'))

    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Timeframe Buttons
    cols = st.columns(len(p_map))
    for i, (label, p_code) in enumerate(p_map.items()):
        if cols[i].button(label):
            st.session_state.period = p_code
            st.rerun()

# --- 5. FUNDAMENTALS & WATCHLIST ---
st.divider()
try:
    info = stock_obj.info
    st.subheader(f"💎 Fundamentals: {info.get('longName', ticker)}")
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Market Cap", f"{info.get('marketCap', 0):,}")
    f2.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
    f3.metric("52W High", info.get('fiftyTwoWeekHigh', 'N/A'))
    f4.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
except: st.write("Fundamental data currently unavailable for this ticker.")

st.divider()
st.subheader("📋 Watchlist")
# ... (Watchlist code remains the same as previous version)
