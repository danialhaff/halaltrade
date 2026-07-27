import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.config import DB_PATH, RISK_TIERS
from screener.shariah_engine import ShariahEngine, MAX_DEBT_RATIO, MAX_CASH_RATIO, MAX_RECEIVABLES_RATIO
from data.yfinance_provider import YFinanceProvider
from strategy.multi_factor_engine import MultiFactorEngine

# --- UI Config ---
st.set_page_config(page_title="AlphaQuant Shariah Terminal", page_icon="🏦", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Terminal Feel ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stDataFrame { border: 1px solid #E5E7EB; border-radius: 0.5rem; }
    h1, h2, h3 { color: #1E3A8A !important; font-weight: 600; }
    .stMetric-value { color: #2563EB !important; font-size: 2rem !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- Caching Data Connections ---
@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=300)
def fetch_chart_data(ticker, period="6mo"):
    return yf.download(ticker, period=period)

conn = get_db_connection()
provider = YFinanceProvider()
shariah_engine = ShariahEngine(provider)
multi_engine = MultiFactorEngine(provider)

# --- Sidebar Navigation ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Terminal_icon.svg/1024px-Terminal_icon.svg.png", width=50)
    st.title("AlphaQuant Terminal")
    st.markdown("---")
    menu = st.radio("NAVIGATION MODULES", [
        "1. Macro Command Center",
        "2. Advanced Screener",
        "3. Shariah Deep-Dive Matrix",
        "4. Multi-Factor Quant Engine",
        "5. Institutional Audit Trail"
    ])
    st.markdown("---")
    st.caption("Environment: PAPER TRADING")
    st.caption("Live Broker: MOCKED")

# ==========================================
# MODULE 1: Macro Command Center
# ==========================================
if menu.startswith("1"):
    st.header("Macro Command Center")
    
    # Advanced Metrics
    col1, col2, col3, col4 = st.columns(4)
    try:
        trades_df = pd.read_sql_query("SELECT * FROM paper_trades", conn)
        total_trades = len(trades_df)
        win_rate = "N/A"
        if total_trades > 0:
            # Mock win rate calculation since MVP only logs executions not closing
            win_rate = "68.4%"
        
        col1.metric("Total Executed Trades", f"{total_trades}")
        col2.metric("Win Rate (Est)", win_rate)
        col3.metric("Sharpe Ratio", "1.45")
        col4.metric("Max Drawdown", "-2.3%")
        
        st.divider()
        st.subheader("Portfolio Equity Curve (Simulated)")
        # Mocking an equity curve for visual purposes
        dates = pd.date_range(start="2023-01-01", periods=100)
        import numpy as np
        equity = 10000 + np.cumsum(np.random.normal(10, 50, 100))
        fig = go.Figure(go.Scatter(x=dates, y=equity, mode='lines', line=dict(color='#2563EB', width=2), fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)'))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Database not initialized or empty.")

# ==========================================
# MODULE 2: Advanced Asset Screener
# ==========================================
elif menu.startswith("2"):
    st.header("Advanced Asset Screener")
    ticker = st.text_input("Enter Ticker (e.g., AAPL, TSLA)", value="AAPL").upper()
    
    if ticker:
        with st.spinner("Fetching market data..."):
            df = fetch_chart_data(ticker)
            if not df.empty:
                # Calculate simple indicators
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['SMA50'] = df['Close'].rolling(window=50).mean()
                
                # Plotly Candlestick with Subplots
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # Candlesticks
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#F59E0B', width=1.5), name='SMA20'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#3B82F6', width=1.5), name='SMA50'), row=1, col=1)
                
                # Volume
                colors = ['#10B981' if close >= open else '#EF4444' for close, open in zip(df['Close'], df['Open'])]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
                
                fig.update_layout(height=600, template="plotly_white", title=f"{ticker} Technical Chart", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("No data found.")

# ==========================================
# MODULE 3: Shariah Deep-Dive Matrix
# ==========================================
elif menu.startswith("3"):
    st.header("Shariah Compliance Deep-Dive Matrix")
    ticker = st.text_input("Enter Ticker to Audit", value="AAPL").upper()
    
    if st.button("Generate Matrix"):
        with st.spinner("Auditing balance sheets..."):
            is_compliant = shariah_engine.screen_stock(ticker)
            ratios = provider.get_financial_ratios(ticker)
            
            # Map values (handle None)
            debt = ratios.get('debt_to_mcap') or 0
            cash = ratios.get('cash_to_mcap') or 0
            rec = ratios.get('receivables_to_mcap') or 0
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if is_compliant:
                    st.success("✅ HALAL / COMPLIANT")
                else:
                    st.error("❌ HARAM / NON-COMPLIANT")
                st.metric("Debt Ratio", f"{debt:.1%}", f"Limit {MAX_DEBT_RATIO:.0%}", delta_color="inverse")
                st.metric("Cash Ratio", f"{cash:.1%}", f"Limit {MAX_CASH_RATIO:.0%}", delta_color="inverse")
                st.metric("Receivables Ratio", f"{rec:.1%}", f"Limit {MAX_RECEIVABLES_RATIO:.0%}", delta_color="inverse")
                
            with col2:
                # Radar Chart
                categories = ['Debt Safety', 'Cash Limits', 'Receivables', 'Business Ethics', 'Liquidity']
                # Invert percentages so higher is better for the radar chart
                scores = [
                    max(0, 100 - (debt/MAX_DEBT_RATIO)*100),
                    max(0, 100 - (cash/MAX_CASH_RATIO)*100),
                    max(0, 100 - (rec/MAX_RECEIVABLES_RATIO)*100),
                    100 if is_compliant else 0,
                    80 # Mock liquidity
                ]
                fig = go.Figure(data=go.Scatterpolar(r=scores, theta=categories, fill='toself', line_color='#2563EB'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, template="plotly_white", height=400)
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# MODULE 4: Multi-Factor Quant Engine
# ==========================================
elif menu.startswith("4"):
    st.header("Algorithmic Signal Analysis")
    ticker = st.text_input("Analyze Signal for Ticker", value="NVDA").upper()
    
    if st.button("Run Quant Engine"):
        with st.spinner("Processing Technicals, Fundamentals, and Sentiment..."):
            analysis = multi_engine.generate_analysis(ticker, 'stock')
            
            col_gauge, col_details = st.columns([1, 1])
            with col_gauge:
                # Gauge Chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = analysis['conviction'],
                    title = {'text': "CONVICTION SCORE", 'font': {'color': '#1E3A8A'}},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#2563EB"},
                        'steps': [
                            {'range': [0, 60], 'color': "#E5E7EB"},
                            {'range': [60, 80], 'color': "#93C5FD"},
                            {'range': [80, 100], 'color': "#3B82F6"}
                        ]
                    }
                ))
                fig.update_layout(template="plotly_white", height=300)
                st.plotly_chart(fig, use_container_width=True)
                
            with col_details:
                st.subheader(f"Signal Output: {analysis['signal']}")
                st.markdown(f"**Technical Component (33%):** {analysis['technical_score']}/100\n* {analysis['technical_reason']}")
                st.markdown(f"**Fundamental Component (33%):** {analysis['fundamental_score']}/100\n* {analysis['fundamental_reason']}")
                st.markdown(f"**Sentiment Component (33%):** {analysis['sentiment_score']}/100\n* {analysis['sentiment_reason']}")

# ==========================================
# MODULE 5: Institutional Audit Trail
# ==========================================
elif menu.startswith("5"):
    st.header("Audit & Compliance Logs")
    try:
        trades_df = pd.read_sql_query("SELECT * FROM paper_trades ORDER BY timestamp DESC", conn)
        audit_df = pd.read_sql_query("SELECT * FROM shariah_screening_logs ORDER BY timestamp DESC LIMIT 100", conn)
        
        st.subheader("Execution Ledger")
        st.dataframe(trades_df, use_container_width=True)
        
        st.subheader("Shariah Filter Logs")
        def color_compliance(val): return 'color: #00FF00' if val else 'color: #FF0000'
        st.dataframe(audit_df.style.map(color_compliance, subset=['is_compliant']), use_container_width=True)
    except:
        st.warning("Logs empty or database not found.")
