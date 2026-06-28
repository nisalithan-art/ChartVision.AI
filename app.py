import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide")

st.markdown("""
    <style>
    .stApp {background-color: #0b0e14; color: #ecf0f1; }
    h1, h2, h3 {color: #00ffcc !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Pro Trader Automated Chart Pattern & S&R Tool")
st.subheader("SMC & ICT Automated Analytics Engine - Premium Edition")

ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, EURUSD=X, AAPL):", value="BTC-USD")
timeframe = st.sidebar.selectbox("Select Timeframe:", ["1d", "1h", "15m", "5m"])
period = st.sidebar.selectbox("Select Period (Data Range):", ["3mo", "1mo", "7d", "1d"])

@st.cache_data
def load_data(symbol, p, tf):
    df = yf.download(symbol, period=p, interval=tf)
    return df

try:
    data = load_data(ticker, period, timeframe)
    
    if data.empty:
        st.error("No data found! Please check the Ticker symbol.")
    else:
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        else:
            data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
            
        close_prices = data['Close'].values
        high_prices = data['High'].values
        low_prices = data['Low'].values
        open_prices = data['Open'].values
        
        # Base Peak/Trough Detection for Structure
        peaks, _ = find_peaks(high_prices, distance=10, prominence=np.std(high_prices)*0.2)
        troughs, _ = find_peaks(-low_prices, distance=10, prominence=np.std(low_prices)*0.2)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ SMC & ICT Display Settings")
        show_fvg = st.sidebar.checkbox("Show Fair Value Gaps (FVG)", value=True)
        show_ob = st.sidebar.checkbox("Show Order Blocks (OB)", value=True)
        show_structure = st.sidebar.checkbox("Show Market Structure (MSS/BOS)", value=True)
        
        # TradingView Colors
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor='#089981', increasing_line_color='#089981',
            decreasing_fillcolor='#f23645', decreasing_line_color='#f23645',
            name="Candlesticks"
        )])
        
        # --- 1. ICT FAIR VALUE GAP (FVG) DETECTION ---
        fvg_count = 0
        if show_fvg:
            for i in range(1, len(data) - 1):
                # Bullish FVG (Gap between Candle i-1 High and Candle i+1 Low)
                if low_prices[i+1] > high_prices[i-1] and close_prices[i] > open_prices[i]:
                    fig.add_shape(type="rect",
                                  x0=data.index[i-1], y0=high_prices[i-1],
                                  x1=data.index[i+1], y1=low_prices[i+1],
                                  fillcolor="rgba(8, 153, 129, 0.15)", line_width=0,
                                  name="Bullish FVG")
                    fvg_count += 1
                # Bearish FVG (Gap between Candle i-1 Low and Candle i+1 High)
                elif high_prices[i+1] < low_prices[i-1] and close_prices[i] < open_prices[i]:
                    fig.add_shape(type="rect",
                                  x0=data.index[i-1], y0=low_prices[i-1],
                                  x1=data.index[i+1], y1=high_prices[i+1],
                                  fillcolor="rgba(242, 54, 69, 0.15)", line_width=0,
                                  name="Bearish FVG")
                    fvg_count += 1

        # --- 2. SMC ORDER BLOCK (OB) DETECTION ---
        ob_signals = []
        if show_ob:
            for p in peaks:
                if p < len(data) - 2:
                    # Bearish OB: Last bullish candle before a sharp drop
                    fig.add_shape(type="rect",
                                  x0=data.index[p-1], y0=low_prices[p-1],
                                  x1=data.index[p+2], y1=high_prices[p],
                                  fillcolor="rgba(242, 54, 69, 0.25)", line=dict(color="#f23645", width=1),
                                  name="Bearish OB")
                    ob_signals.append(f"🔴 Bearish Order Block identified near {round(high_prices[p], 2)}")
                    
            for t in troughs:
                if t < len(data) - 2:
                    # Bullish OB: Last bearish candle before a sharp move up
                    fig.add_shape(type="rect",
                                  x0=data.index[t-1], y0=low_prices[t],
                                  x1=data.index[t+2], y1=high_prices[t+1],
                                  fillcolor="rgba(8, 153, 129, 0.25)", line=dict(color="#089981", width=1),
                                  name="Bullish OB")
                    ob_signals.append(f"🟢 Bullish Order Block identified near {round(low_prices[t], 2)}")

        # --- 3. MARKET STRUCTURE BREAKS (MSS / BOS) ---
        structure_alerts = []
        if show_structure:
            for idx in range(15, len(data)):
                # Market Structure Shift (MSS) Detection
                if close_prices[idx] > max(high_prices[idx-5:idx]):
                    if any(p < idx and p > idx-10 for p in peaks):
                        fig.add_annotation(x=data.index[idx], y=high_prices[idx],
                                           text="✈️ MSS (Bullish)", showarrow=True, arrowhead=1,
                                           arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9),
                                           bgcolor="rgba(11, 14, 20, 0.8)")
                        structure_alerts.append(f"🔄 Market Structure Shift (MSS) detected at {data.index[idx].strftime('%Y-%m-%d')}")
                        break

        fig.update_layout(
            title=f"{ticker} Live Chart | Automated SMC & ICT Technical Analysis Engine",
            yaxis_title="Price", xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14', xaxis_rangeslider_visible=False,
            height=750, font=dict(color="#8a99ad")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- SMC / ICT SMART INSIGHTS BOX ---
        st.write("### 🧠 Smart Money Intelligence Panel")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Order Blocks & Gaps Detected")
            st.metric(label="Total Fair Value Gaps (FVG)", value=fvg_count)
            if ob_signals:
                for ob in ob_signals[-3:]: # Display last 3 active OBs
                    st.write(ob)
            else:
                st.write("Looking for clean Order Blocks...")
                
        with col2:
            st.markdown("#### 🔄 Market Structure Analysis")
            if structure_alerts:
                for alert in structure_alerts[-3:]:
                    st.info(alert)
            else:
                st.success("Market Structure is maintaining current trend bounds. No fresh MSS/BOS break.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
