import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- Initialize Memory ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"

# --- 1. SEARCH BAR (Screener Style) ---
st.title("🔍 Stock Vibe Pro")
search_query = st.text_input("Search Company Name or Ticker", placeholder="e.g. Hindalco or RELIANCE")

if search_query:
    search_results = yf.Search(search_query, max_results=5).quotes
    if search_results:
        options = {f"{q['shortname']} ({q['symbol']})": q['symbol'] for q in search_results}
        selection = st.selectbox("Select Result", options.keys())
        if selection:
            st.session_state.current_ticker = options[selection]

# --- 2. THE ACTION ZONE ---
ticker = st.session_state.current_ticker
stock_obj = yf.Ticker(ticker)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.subheader(f"Analyzing: {ticker}")
with col_btn:
    if ticker not in st.session_state.watchlist:
        if st.button("➕ Add to Watchlist"):
            st.session_state.watchlist.append(ticker)
            st.rerun()

# --- 3. INDICATOR SETTINGS ---
with st.expander("🛠️ Technical Indicators & Timeframe"):
    c1, c2, c3 = st.columns(3)
    with c1:
        timeframe = st.selectbox("Time Interval", ["Weekly", "Daily", "15 Min"], index=0)
        # Map selection to yfinance intervals
        interval_map = {"Weekly": "1wk", "Daily": "1d", "15 Min": "15m"}
        period_map = {"Weekly": "max", "Daily": "2y", "15 Min": "1d"}
    with c2:
        ma_options = st.multiselect("Moving Averages", ["50 DMA", "200 DMA", "200 WMA"], default=["50 DMA"])
    with c3:
        others = st.multiselect("Other Overlays", ["Bollinger Bands", "RSI"])

# --- 4. FETCH DATA & CALCULATE ---
data = stock_obj.history(period=period_map[timeframe], interval=interval_map[timeframe])

if not data.empty:
    # Calculations
    if "50 DMA" in ma_options: data['50DMA'] = data['Close'].rolling(50).mean()
    if "200 DMA" in ma_options: data['200DMA'] = data['Close'].rolling(200).mean()
    if "200 WMA" in ma_options: data['200WMA'] = data['Close'].rolling(200).mean()
    
    if "Bollinger Bands" in others:
        sma = data['Close'].rolling(20).mean()
        std = data['Close'].rolling(20).std()
        data['BB_Up'] = sma + (std * 2)
        data['BB_Low'] = sma - (std * 2)

    # --- 5. THE CHART ---
    fig = go.Figure()
    # Main Price Line
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF", width=2)))
    
    # Overlays
    if "50 DMA" in ma_options: fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(color="orange")))
    if "200 DMA" in ma_options: fig.add_trace(go.Scatter(x=data.index, y=data['200DMA'], name="200 DMA", line=dict(color="red")))
    if "200 WMA" in ma_options: fig.add_trace(go.Scatter(x=data.index, y=data['200WMA'], name="200 WMA", line=dict(color="purple", dash="dot")))
    
    if "Bollinger Bands" in others:
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Up'], name="BB Upper", line=dict(color="rgba(173,216,230,0.4)")))
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Low'], name="BB Lower", line=dict(color="rgba(173,216,230,0.4)"), fill='tonexty'))

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. FILINGS & NEWS (The Screener Section) ---
    st.divider()
    st.subheader("📁 Exchange Filings & News")
    news = stock_obj.news
    if news:
        for item in news[:5]:
            st.markdown(f"**[{item['title']}]({item['link']})**")
            st.caption(f"Source: {item['publisher']} | Type: {item['type']}")
    else:
        st.write("No recent filings or news found for this ticker.")
