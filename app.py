import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox
from datetime import datetime

# --- UI CONFIG & STYLING ---
st.set_page_config(page_title="VibeStock Pro", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #111827;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #374151;
        text-align: center;
    }
    .metric-label { color: #9ca3af; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 5px; }
    .news-card {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 4px solid #3b82f6;
    }
    .news-title { color: #f3f4f6; font-size: 14px; font-weight: 600; text-decoration: none; }
    .news-title:hover { color: #3b82f6; }
    .news-meta { color: #6b7280; font-size: 11px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- SEARCH FUNCTION ---
def search_stocks(searchterm: str):
    if not searchterm or len(searchterm) < 2: return []
    try:
        search = yf.Search(searchterm, max_results=5)
        return [(f"{q['shortname']} ({q['symbol']})", q['symbol']) for q in search.quotes]
    except: return []

# --- APP LAYOUT ---
with st.container():
    c1, c2 = st.columns([3, 1])
    with c1:
        selected_ticker = st_searchbox(search_stocks, placeholder="Search Ticker...", key="stock_search")
    with c2:
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

ticker = selected_ticker if selected_ticker else "AAPL"
stock_obj = yf.Ticker(ticker)

# --- MAIN CONTENT AREA ---
main_col, news_col = st.columns([3, 1])

with main_col:
    try:
        info = stock_obj.info
        hist = stock_obj.history(period="1y")
        
        # Row 1: The Claude-Style Metrics
        m_cols = st.columns(4)
        top_metrics = [
            ("Price", f"{info.get('currentPrice', 0):.2f}"),
            ("Market Cap", f"{info.get('marketCap', 0)/1e12:.2f}T"),
            ("P/E Ratio", info.get('trailingPE', 'N/A')),
            ("Day Change", f"{info.get('regularMarketChangePercent', 0):.2f}%")
        ]
        
        for i, (label, val) in enumerate(top_metrics):
            m_cols[i].markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{val}</div></div>', unsafe_allow_html=True)

        # Row 2: The Interactive Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Price", line=dict(color="#3b82f6", width=2), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'))
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error("Could not fetch data for this ticker.")

# --- THE LIVE NEWS FEED (The "Right Wing") ---
with news_col:
    st.markdown("### 📰 Market News")
    news_items = stock_obj.news
    
    if not news_items:
        st.write("No recent news found.")
    else:
        for item in news_items[:6]:  # Show top 6 stories
            # Convert timestamp to readable time
            pub_time = datetime.fromtimestamp(item['providerPublishTime']).strftime('%H:%M')
            st.markdown(f"""
                <div class="news-card">
                    <a href="{item['link']}" target="_blank" class="news-title">{item['title']}</a>
                    <div class="news-meta">{item['publisher']} • {pub_time}</div>
                </div>
            """, unsafe_allow_html=True)
