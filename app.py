import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox
import pandas as pd

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- 1. SEARCH LOGIC (The Screener Bridge) ---
def search_stocks(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    try:
        # This fetches results in real-time as you type
        search = yf.Search(searchterm, max_results=8)
        return [(f"{q['shortname']} ({q['symbol']})", q['symbol']) for q in search.quotes]
    except:
        return []

st.title("📈 VibeStock Pro")

# The Actual Search Bar (Screener-style)
selected_ticker = st_searchbox(
    search_stocks,
    placeholder="Start typing (e.g. Hindalco, Reliance, Google...)",
    key="stock_search",
)

# --- 2. WATCHLIST & STATE ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]
if 'period' not in st.session_state:
    st.session_state.period = "1y"

# If user selects from search, set it as current
if selected_ticker:
    st.session_state.current_ticker = selected_ticker

ticker = st.session_state.get('current_ticker', "AAPL")
stock = yf.Ticker(ticker)

# --- 3. THE CHART ---
st.subheader(f"Current View: {ticker}")
p_map = {"1D": "1d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "10Y": "10y", "MAX": "max"}
interval = "15m" if st.session_state.period == "1d" else "1d"

data = stock.history(period=st.session_state.period, interval=interval)

if not data.empty:
    fig = go.Figure(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF")))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Timeframe Buttons at the bottom
    cols = st.columns(len(p_map))
    for i, (label, p_code) in enumerate(p_map.items()):
        if cols[i].button(label):
            st.session_state.period = p_code
            st.rerun()

# --- 4. COLOR-CODED WATCHLIST ---
st.divider()
if st.button("➕ Add Current to Watchlist"):
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)
        st.rerun()

with st.container(height=300):
    for t in st.session_state.watchlist:
        try:
            s = yf.Ticker(t).fast_info
            price, prev = s['lastPrice'], s['previousClose']
            change = ((price - prev) / prev) * 100
            color = "green" if change >= 0 else "red"
            
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            if c1.button(f"{t}", key=f"btn_{t}"):
                st.session_state.current_ticker = t
                st.rerun()
            c2.write(f"₹{price:,.2f}" if ".NS" in t else f"${price:,.2f}")
            c3.markdown(f":{color}[{'+' if change > 0 else ''}{change:.2f}%]")
            if c4.button("🗑️", key=f"del_{t}"):
                st.session_state.watchlist.remove(t)
                st.rerun()
        except: continue
