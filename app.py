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
st.subheader("SMC & ICT Advanced Execution Engine - Premium Edition")

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
        
        # High-precision Peak and Trough Detection
        peaks, _ = find_peaks(high_prices, distance=7, prominence=np.std(high_prices)*0.15)
        troughs, _ = find_peaks(-low_prices, distance=7, prominence=np.std(low_prices)*0.15)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ SMC/ICT Advanced Controls")
        show_ob = st.sidebar.checkbox("Show Order Blocks (OB)", value=True)
        show_structure = st.sidebar.checkbox("Show BOS & Liquidity Sweeps", value=True)
        show_trade_setup = st.sidebar.checkbox("Show Entry, SL & TP Signals", value=True)
        
        # TradingView Color Theme
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor='#089981', increasing_line_color='#089981',
            decreasing_fillcolor='#f23645', decreasing_line_color='#f23645',
            name="Candlesticks"
        )])
        
        trade_alerts = []
        
        # --- 1. LIQUIDITY SWEEP & BOS/MSS ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        
        if show_structure:
            for idx in range(20, len(data)):
                # Liquidity Sweep (Price pierces high/low but closes inside)
                if high_prices[idx] > last_high and close_prices[idx] < last_high:
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="✖️ LQ SWEEP (Buy Side)",
                                       showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#ffcc00", size=9),
                                       bgcolor="rgba(11, 14, 20, 0.85)", ay=-25)
                elif low_prices[idx] < last_low and close_prices[idx] > last_low:
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="✖️ LQ SWEEP (Sell Side)",
                                       showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#ffcc00", size=9),
                                       bgcolor="rgba(11, 14, 20, 0.85)", ay=25)
                
                # BOS - Break of Structure (Candle closes completely past the previous structural peak/trough)
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_high, x1=data.index[idx], y1=last_high,
                                  line=dict(color="#089981", width=1.5, dash="dot"))
                    fig.add_annotation(x=data.index[idx], y=last_high, text="➔ BOS (Bullish)", showarrow=False,
                                       font=dict(color="#089981", size=9), bgcolor="rgba(11, 14, 20, 0.8)", yanchor="bottom")
                    last_high = high_prices[idx] # Update Structure
                    
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_low, x1=data.index[idx], y1=last_low,
                                  line=dict(color="#f23645", width=1.5, dash="dot"))
                    fig.add_annotation(x=data.index[idx], y=last_low, text="➔ BOS (Bearish)", showarrow=False,
                                       font=dict(color="#f23645", size=9), bgcolor="rgba(11, 14, 20, 0.8)", yanchor="top")
                    last_low = low_prices[idx] # Update Structure

        # --- 2. ORDER BLOCK & METRIC CALCULATOR ---
        active_bullish_ob = None
        active_bearish_ob = None

        if show_ob:
            for p in peaks[-3:]: # Check recent peaks
                if p < len(data) - 2:
                    active_bearish_ob = {"top": high_prices[p], "bottom": min(open_prices[p], close_prices[p]), "idx": p}
                    fig.add_shape(type="rect", x0=data.index[p-1], y0=active_bearish_ob["bottom"], x1=data.index[-1], y1=active_bearish_ob["top"],
                                  fillcolor="rgba(242, 54, 69, 0.1)", line=dict(color="rgba(242, 54, 69, 0.4)", width=1))
            
            for t in troughs[-3:]: # Check recent troughs
                if t < len(data) - 2:
                    active_bullish_ob = {"bottom": low_prices[t], "top": max(open_prices[t], close_prices[t]), "idx": t}
                    fig.add_shape(type="rect", x0=data.index[t-1], y0=active_bullish_ob["bottom"], x1=data.index[-1], y1=active_bullish_ob["top"],
                                  fillcolor="rgba(8, 153, 129, 0.1)", line=dict(color="rgba(8, 153, 129, 0.4)", width=1))

        # --- 3. RISK MANAGEMENT SETUP (ENTRY, SL, TP) ---
        if show_trade_setup and len(data) > 2:
            latest_idx = len(data) - 1
            latest_close = close_prices[latest_idx]
            
            # Scenario A: Price mitigation of Bullish Order Block (Long Setup)
            if active_bullish_ob and active_bullish_ob["bottom"] <= latest_close <= active_bullish_ob["top"]:
                entry = round(latest_close, 2)
                sl = round(active_bullish_ob["bottom"] - (active_bullish_ob["top"] - active_bullish_ob["bottom"])*0.2, 2)
                risk = entry - sl
                tp = round(entry + (risk * 2.5), 2) # 1:2.5 Risk to Reward Ratio
                
                # Plot Setup on Chart
                fig.add_shape(type="line", x0=data.index[-5], y0=entry, x1=data.index[-1], y1=entry, line=dict(color="#00ffcc", width=2.5))
                fig.add_shape(type="line", x0=data.index[-5], y0=sl, x1=data.index[-1], y1=sl, line=dict(color="#ff3333", width=2, dash="dash"))
                fig.add_shape(type="line", x0=data.index[-5], y0=tp, x1=data.index[-1], y1=tp, line=dict(color="#00ff66", width=2, dash="dash"))
                
                fig.add_annotation(x=data.index[-1], y=entry, text=f"🎯 ENTRY: {entry}", showarrow=False, bgcolor="#00ffcc", font=dict(color="black", size=10))
                fig.add_annotation(x=data.index[-1], y=sl, text=f"🛑 SL: {sl}", showarrow=False, bgcolor="#ff3333", font=dict(color="white", size=10))
                fig.add_annotation(x=data.index[-1], y=tp, text=f"💰 TP: {tp}", showarrow=False, bgcolor="#00ff66", font=dict(color="black", size=10))
                
                trade_alerts.append(("BUY/LONG Setup Active", entry, sl, tp, "1:2.5"))

            # Scenario B: Price mitigation of Bearish Order Block (Short Setup)
            elif active_bearish_ob and active_bearish_ob["bottom"] <= latest_close <= active_bearish_ob["top"]:
                entry = round(latest_close, 2)
                sl = round(active_bearish_ob["top"] + (active_bearish_ob["top"] - active_bearish_ob["bottom"])*0.2, 2)
                risk = sl - entry
                tp = round(entry - (risk * 2.5), 2)
                
                # Plot Setup on Chart
                fig.add_shape(type="line", x0=data.index[-5], y0=entry, x1=data.index[-1], y1=entry, line=dict(color="#00ffcc", width=2.5))
                fig.add_shape(type="line", x0=data.index[-5], y0=sl, x1=data.index[-1], y1=sl, line=dict(color="#ff3333", width=2, dash="dash"))
                fig.add_shape(type="line", x0=data.index[-5], y0=tp, x1=data.index[-1], y1=tp, line=dict(color="#00ff66", width=2, dash="dash"))
                
                fig.add_annotation(x=data.index[-1], y=entry, text=f"🎯 ENTRY: {entry}", showarrow=False, bgcolor="#00ffcc", font=dict(color="black", size=10))
                fig.add_annotation(x=data.index[-1], y=sl, text=f"🛑 SL: {sl}", showarrow=False, bgcolor="#ff3333", font=dict(color="white", size=10))
                fig.add_annotation(x=data.index[-1], y=tp, text=f"💰 TP: {tp}", showarrow=False, bgcolor="#00ff66", font=dict(color="black", size=10))
                
                trade_alerts.append(("SELL/SHORT Setup Active", entry, sl, tp, "1:2.5"))

        fig.update_layout(
            title=f"{ticker} Live Chart | Advanced Institutional SMC & ICT Execution Engine",
            yaxis_title="Price", xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14', xaxis_rangeslider_visible=False,
            height=780, font=dict(color="#8a99ad")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- INSTITUTIONAL EXECUTIVE PANEL ---
        st.write("### 🚨 Institutional Risk Management Panel")
        if trade_alerts:
            for setup, entry, sl, tp, rr in trade_alerts:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric(label="🎯 Setup Direction", value=setup)
                col2.metric(label="📊 Entry Level", value=entry)
                col3.metric(label="🛑 Stop Loss (SL)", value=sl, delta=round(sl-entry, 2))
                col4.metric(label="💰 Take Profit (TP)", value=tp, delta=round(tp-entry, 2))
                st.success(f"🔥 Smart Money Trade Setup is confirmed with a Risk-to-Reward ratio of {rr}!")
        else:
            st.info("Market is currently searching for clear Order Block Mitigation. Waiting for an Institutional Entry...")

except Exception as e:
    st.error(f"Something went wrong: {e}")
