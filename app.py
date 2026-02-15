import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- Memory Management ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"
if 'period' not in st.session_state:
    st.session_state.period = "1y"

# --- 1. THE SEARCH BAR (Single Box Style) ---
st.title("🔍 Stock Vibe Pro")
search_input = st.text_input("Search Company Name (e.g. 'Hindalco', 'Google')", placeholder="Type here and press Enter")

if search_input:
    try:
        # Fetching suggestions from Yahoo
        search = yf.Search(search_input, max_results=8)
        if search.quotes:
            # Create a dictionary for the dropdown
            options = {f"{q['shortname']} ({q['symbol']})": q['symbol'] for q in search.quotes}
            
            # The Selection Dropdown
            choice = st.selectbox("Is this what you're looking for?", ["Select a stock..."] + list(options.keys()))
            
            if choice != "Select a stock...":
                selected_symbol = options[choice]
                st.session_state.current_ticker = selected_symbol
                
                # Check if it's already in watchlist
                if selected_symbol not in st.session_state.watchlist:
                    if st.button(f"➕ Add {selected_symbol} to Watchlist"):
                        st.session_state.watchlist.append(selected_symbol)
                        st.rerun()
    except Exception as e:
        st.error("Search is currently unavailable. Try typing the exact ticker (e.g., TSLA).")

st.divider()

# --- 2. THE CHART AREA ---
ticker = st.session_state.current_ticker
stock = yf.Ticker(ticker)

# Fetching Data
p_map = {"1 Day": "1d", "1 Month": "1mo", "3 Month": "3mo", "6 Months": "6mo", "1 Year": "1y", "5 Years": "5y", "10 Years": "10y", "Lifetime": "max"}
interval = "15m" if st.session_state.period == "1d" else "1d" if st.session_state.period in ["1mo", "3mo", "6mo", "1y"] else "1wk"

data = stock.history(period=st.session_state.period, interval=interval)

if not data.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF", width=2)))
    
    # Simple DMA indicators
    if st.session_state.period != "1d":
        data['50DMA'] = data['Close'].rolling(50).mean()
        data['200DMA'] = data['Close'].rolling(200).mean()
        fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(color="orange", width=1)))
        fig.add_trace(go.Scatter(x=data.index, y=data['200DMA'], name="200 DMA", line=dict(color="red", width=1)))

    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Timeframe Buttons at Bottom
    cols = st.columns(len(p_map))
    for i, (label, p_code) in enumerate(p_map.items()):
        if cols[i].button(label):
            st.session_state.period = p_code
            st.rerun()

# --- 3. THE WATCHLIST (Scrollable with Colors) ---
st.divider()
st.subheader("📋 Watchlist Summary")

with st.container(height=350):
    # Header
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    c1.write("**Company**")
    c2.write("**Price**")
    c3.write("**Day Change**")
    c4.write("**Remove**")
    st.divider()

    for t in st.session_state.watchlist:
        try:
            s = yf.Ticker(t)
            price = s.fast_info['lastPrice']
            prev_close = s.fast_info['previousClose']
            change = ((price - prev_close) / prev_close) * 100
            
            row1, row2, row3, row4 = st.columns([2, 1, 1, 1])
            
            # Clickable name to switch chart
            if row1.button(f"{t}", key=f"view_{t}"):
                st.session_state.current_ticker = t
                st.rerun()
            
            # Price
            row2.write(f"₹{price:,.2f}" if ".NS" in t or ".BO" in t else f"${price:,.2f}")
            
            # Change % with Colors
            color = "green" if change >= 0 else "red"
            row3.markdown(f":{color}[{'+' if change > 0 else ''}{change:.2f}%]")
            
            # Remove
            if row4.button("🗑️", key=f"del_{t}"):
                st.session_state.watchlist.remove(t)
                st.rerun()
        except:
            continue
