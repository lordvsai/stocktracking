import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- Initialize Session States ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"
if 'chart_period' not in st.session_state:
    st.session_state.chart_period = "1y"

# --- 1. SEARCH & ADD (Single Combined Interaction) ---
st.title("📊 Global Stock Vibe")

# Search query
query = st.text_input("Search Company Name (e.g. 'Hindalco', 'Google')", placeholder="Type and press Enter")

if query:
    search_results = yf.Search(query, max_results=5).quotes
    if search_results:
        # This creates the "Screener.in" dropdown effect
        options = {f"{q['shortname']} ({q['symbol']})": q['symbol'] for q in search_results}
        selection = st.selectbox("Select the correct match:", ["Select..."] + list(options.keys()))
        
        if selection != "Select...":
            st.session_state.current_ticker = options[selection]
            # Add to watchlist button appears only for the selected stock
            if st.session_state.current_ticker not in st.session_state.watchlist:
                if st.button(f"➕ Add {st.session_state.current_ticker} to Watchlist"):
                    st.session_state.watchlist.append(st.session_state.current_ticker)
                    st.rerun()

# --- 2. MAIN CHART SECTION ---
ticker = st.session_state.current_ticker
stock_obj = yf.Ticker(ticker)

# Fetch Data based on selected period
# Mapping user-friendly names to yfinance periods
period_map = {
    "1 Day": "1d", "1 Month": "1mo", "3 Months": "3mo", 
    "6 Months": "6mo", "1 Year": "1y", "5 Years": "5y", 
    "10 Years": "10y", "Lifetime": "max"
}

# Auto-determine interval based on period
current_p = st.session_state.chart_period
interval = "15m" if current_p == "1d" else "1d" if current_p in ["1mo", "3mo", "6mo", "1y"] else "1wk"

data = stock_obj.history(period=current_p, interval=interval)

if not data.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF", width=2)))
    
    # Simple DMA Overlays (50 & 200)
    if current_p not in ["1d"]:
        data['50DMA'] = data['Close'].rolling(50).mean()
        data['200DMA'] = data['Close'].rolling(200).mean()
        fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(color="orange", width=1)))
        fig.add_trace(go.Scatter(x=data.index, y=data['200DMA'], name="200 DMA", line=dict(color="red", width=1)))

    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- Timeframe Buttons (At the Bottom of Graph) ---
    st.write("Select Timeframe:")
    cols = st.columns(len(period_map))
    for i, (label, p_code) in enumerate(period_map.items()):
        if cols[i].button(label):
            st.session_state.chart_period = p_code
            st.rerun()

# --- 3. WATCHLIST WITH COLOR-CODED CHANGES ---
st.divider()
st.subheader("📋 Your Watchlist")

if st.session_state.watchlist:
    # Use a container to make it scrollable
    with st.container(height=400):
        # Header Row
        h1, h2, h3, h4 = st.columns([2, 1, 1, 1])
        h1.write("**Stock**")
        h2.write("**Price**")
        h3.write("**Change %**")
        h4.write("**Action**")
        st.divider()

        for t in st.session_state.watchlist:
            try:
                s = yf.Ticker(t)
                # Getting clean data
                info = s.fast_info
                price = info['lastPrice']
                # Calculate change from previous close
                prev_close = info['previousClose']
                change_pct = ((price - prev_close) / prev_close) * 100
                
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                
                # Column 1: Clickable Name to switch chart
                if c1.button(f"{t}", key=f"btn_{t}"):
                    st.session_state.current_ticker = t
                    st.rerun()
                
                # Column 2: Price
                c2.write(f"${price:,.2f}" if ".NS" not in t else f"₹{price:,.2f}")
                
                # Column 3: Change % (Red/Green)
                color = "green" if change_pct >= 0 else "red"
                c3.markdown(f":{color}[{'+' if change_pct > 0 else ''}{change_pct:.2f}%]")
                
                # Column 4: Remove Button
                if c4.button("🗑️", key=f"del_{t}"):
                    st.session_state.watchlist.remove(t)
                    st.rerun()
            except:
                continue
