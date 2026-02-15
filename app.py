import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Global Vibe Tracker", layout="wide")

# --- 1. SEARCH LOGIC (The "Autocomplete" Brain) ---
def get_ticker_suggestions(search_term):
    if not search_term or len(search_term) < 2:
        return []
    try:
        # Use yfinance's search function to find matches
        search = yf.Search(search_term, max_results=8)
        # Format the results as "TICKER - Company Name"
        return [f"{q['symbol']} - {q['shortname']}" for q in search.quotes]
    except:
        return []

# --- 2. SIDEBAR: WATCHLIST ---
st.sidebar.title("🌍 Global Watchlist")
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "RELIANCE.NS", "TSLA"]

# Search Box for Autocomplete
search_input = st.sidebar.text_input("🔍 Search & Add Stock (e.g. 'Hind')", key="ticker_search")
suggestions = get_ticker_suggestions(search_input)

if suggestions:
    selected_from_search = st.sidebar.selectbox("Suggestions (click to add):", ["Select..."] + suggestions)
    if selected_from_search != "Select...":
        new_ticker = selected_from_search.split(" - ")[0]
        if new_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_ticker)
            st.success(f"Added {new_ticker}!")
            st.rerun()

st.sidebar.write("Current Watchlist:", ", ".join(st.session_state.watchlist))
if st.sidebar.button("Clear Watchlist"):
    st.session_state.watchlist = []
    st.rerun()

# --- 3. THE WATCHLIST SUMMARY ---
st.header("📋 Portfolio Overview")
with st.container(height=350):
    cols = st.columns([2, 2, 2, 2])
    cols[0].write("**Company**")
    cols[1].write("**Price**")
    cols[2].write("**52W High**")
    cols[3].write("**Change %**")
    st.divider()

    for t in st.session_state.watchlist:
        try:
            stock = yf.Ticker(t)
            price = stock.fast_info['lastPrice']
            high_52 = stock.fast_info['yearHigh']
            change = ((price - stock.fast_info['previousClose']) / stock.fast_info['previousClose']) * 100
            
            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            c1.write(f"**{t}**")
            c2.write(f"${price:,.2f}")
            c3.write(f"${high_52:,.2f}")
            color = "green" if change >= 0 else "red"
            c4.markdown(f":{color}[{change:.2f}%]")
        except:
            continue

# --- 4. INTERACTIVE CHART ---
st.divider()
st.header("📈 Technical Analysis")
if st.session_state.watchlist:
    selected_stock = st.selectbox("Select stock to view chart", st.session_state.watchlist)
    
    time_options = {
        "Today (15m)": {"p": "1d", "i": "15m"},
        "1 Month": {"p": "1mo", "i": "1d"},
        "1 Year": {"p": "1y", "i": "1d"},
        "Max": {"p": "max", "i": "1mo"}
    }
    choice = st.radio("Interval", list(time_options.keys()), horizontal=True)
    
    data = yf.download(selected_stock, period=time_options[choice]["p"], interval=time_options[choice]["i"])
    
    if not data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Price", line=dict(color="#00D4FF")))
        
        # Add 50 DMA if looking at 1Y or more
        if choice in ["1 Year", "Max"]:
            data['50DMA'] = data['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(x=data.index, y=data['50DMA'], name="50 DMA", line=dict(dash='dash', color="#FF9900")))

        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
