import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# 1. Page Setup
st.set_page_config(page_title="VibeStock Tracker", layout="wide")
st.title("📈 Stock Vibe Check")

# 2. Sidebar - Your Watchlist
st.sidebar.header("Settings")
watchlist = st.sidebar.text_input("Watchlist (comma separated)", "AAPL, TSLA, BTC-USD, GOOGL")
tickers = [t.strip().upper() for t in watchlist.split(",")]

# 3. Main Display
selected_stock = st.selectbox("Select stock to analyze", tickers)

# Fetch Data
data = yf.download(selected_stock, period="1y", interval="1d")

if not data.empty:
    # Technical Analysis: 50 Day Moving Average
    data['50DMA'] = data['Close'].rolling(window=50).mean()
    current_price = float(data['Close'].iloc[-1])
    dma_50 = float(data['50DMA'].iloc[-1])

    # Visual Metrics
    col1, col2 = st.columns(2)
    col1.metric("Current Price", f"${current_price:.2f}")
    
    # ALERT LOGIC: This is your vibe check
    if current_price > dma_50:
        col2.success(f"Vibe: BULLISH. Price is above the 50 DMA (${dma_50:.2f})")
    else:
        col2.error(f"Vibe: BEARISH. Price is below the 50 DMA (${dma_50:.2f})")

    # The Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00ff00")))
    fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(dash='dash', color="white")))
    fig.update_layout(template="plotly_dark", title=f"{selected_stock} Performance")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("Enter a valid ticker to start.")
