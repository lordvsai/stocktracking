import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="VibeStock Pro", layout="wide")

# --- 1. SEARCH LOGIC ---
st.title("📈 VibeStock Pro Dashboard")
search_term = st.text_input("Start typing a company (e.g., 'Hindalco' or 'Reliance')", key="main_search")

# State management for current stock
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS"]

# Dropdown suggestion logic
if len(search_term) > 1:
    search = yf.Search(search_term, max_results=5)
    if search.quotes:
        options = {f"{q['shortname']} ({q['symbol']})": q['symbol'] for q in search.quotes}
        selection = st.selectbox("Search Results:", options.keys())
        if selection:
            st.session_state.current_ticker = options[selection]

# --- 2. THE ACTION ZONE ---
ticker = st.session_state.current_ticker
stock_obj = yf.Ticker(ticker)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Analyzing: {ticker}")
with col2:
    if ticker not in st.session_state.watchlist:
        if st.button("➕ Add to Watchlist"):
            st.session_state.watchlist.append(ticker)
            st.rerun()

# --- 3. INDICATOR PANEL ---
with st.expander("📊 Chart Settings & Technicals"):
    c1, c2, c3 = st.columns(3)
    with c1:
        interval = st.selectbox("Interval", ["1wk", "1d", "15m"], index=1)
        period = "max" if interval == "1wk" else "2y" if interval == "1d" else "1d"
    with c2:
        ma_list = st.multiselect("Moving Averages", ["50 DMA", "200 DMA", "200 WMA"], default=["50 DMA"])
    with c3:
        overlays = st.multiselect("Other Indicators", ["Bollinger Bands", "RSI"], default=["RSI"])

# --- 4. DATA PROCESSING ---
data = stock_obj.history(period=period, interval=interval)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if not data.empty:
    # Calculations
    if "50 DMA" in ma_list: data['50DMA'] = data['Close'].rolling(50).mean()
    if "200 DMA" in ma_list: data['200DMA'] = data['Close'].rolling(200).mean()
    if "200 WMA" in ma_list: data['200WMA'] = data['Close'].rolling(200).mean()
    if "Bollinger Bands" in overlays:
        sma = data['Close'].rolling(20).mean()
        std = data['Close'].rolling(20).std()
        data['BB_Up'] = sma + (std * 2)
        data['BB_Low'] = sma - (std * 2)
    if "RSI" in overlays:
        data['RSI'] = calculate_rsi(data['Close'])

    # --- 5. THE CHART ---
    # Create Subplots: Row 1 for Price, Row 2 for RSI (if selected)
    rows = 2 if "RSI" in overlays else 1
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3] if rows==2 else [1])

    # Price Line
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF")), row=1, col=1)
    
    # Overlays
    if "50 DMA" in ma_list: fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA"), row=1, col=1)
    if "200 DMA" in ma_list: fig.add_trace(go.Scatter(x=data.index, y=data['200DMA'], name="200 DMA"), row=1, col=1)
    if "200 WMA" in ma_list: fig.add_trace(go.Scatter(x=data.index, y=data['200WMA'], name="200 WMA", line=dict(dash="dot")), row=1, col=1)
    if "Bollinger Bands" in overlays:
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Up'], name="BB Upper", line=dict(width=0)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_Low'], name="BB Lower", fill='tonexty', line=dict(width=0)), row=1, col=1)

    # RSI Subplot
    if "RSI" in overlays:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name="RSI", line=dict(color="yellow")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# --- 6. WATCHLIST & EXPORT ---
st.divider()
st.subheader("📁 My Global Watchlist")
if st.session_state.watchlist:
    wl_data = []
    for t in st.session_state.watchlist:
        s = yf.Ticker(t).fast_info
        wl_data.append({"Ticker": t, "Price": s['lastPrice'], "52W High": s['yearHigh']})
    
    df_wl = pd.DataFrame(wl_data)
    st.dataframe(df_wl, use_container_width=True)
    
    # Download Button
    csv = df_wl.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Watchlist as CSV", data=csv, file_name="my_watchlist.csv", mime="text/csv")

# --- 7. FILINGS ---
st.subheader("📰 Recent Filings & News")
news = stock_obj.news[:5]
for n in news:
    st.markdown(f"**[{n['title']}]({n['link']})**")
