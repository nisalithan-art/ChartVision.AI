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
st.subheader("Pure Maths & Code - Premium Dark Edition")

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
        
        peaks, _ = find_peaks(high_prices, distance=10, prominence=np.std(high_prices)*0.2)
        troughs, _ = find_peaks(-low_prices, distance=10, prominence=np.std(low_prices)*0.2)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Custom Fibonacci Zone")
        
        max_idx = len(data) - 1
        start_idx = st.sidebar.slider("Fibonacci Start Point", 0, max_idx, int(max_idx * 0.2))
        end_idx = st.sidebar.slider("Fibonacci End Point", 0, max_idx, int(max_idx * 0.8))
        
        show_circles = st.sidebar.checkbox("Show Fibonacci Circles", value=True)
        show_entries = st.sidebar.checkbox("Show Auto Entry Signals", value=True)
        
        zone_high = float(high_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].max())
        zone_low = float(low_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].min())
        zone_range = zone_high - zone_low
        
        # TradingView Color Theme applied for Candlesticks
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor='#089981', increasing_line_color='#089981',
            decreasing_fillcolor='#f23645', decreasing_line_color='#f23645',
            name="Candlesticks"
        )])
        
        # Auto Support & Resistance Lines
        for peak in peaks:
            fig.add_shape(type="line", x0=data.index[0], y0=high_prices[peak], x1=data.index[-1], y1=high_prices[peak],
                          line=dict(color="rgba(242, 54, 69, 0.4)", width=1.5, dash="dash"))
        for trough in troughs:
            fig.add_shape(type="line", x0=data.index[0], y0=low_prices[trough], x1=data.index[-1], y1=low_prices[trough],
                          line=dict(color="rgba(8, 153, 129, 0.4)", width=1.5, dash="dash"))
            
        # Fibonacci Calculation
        fib_ratios = [0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        fib_start_date = data.index[start_idx]
        fib_end_date = data.index[end_idx]
        
        time_delta = fib_end_date - fib_start_date
        center_price = zone_high if start_idx < end_idx else zone_low
        trend_up = start_idx < end_idx
        
        # Array to track entries to prevent duplication
        detected_entries = []

        for ratio in fib_ratios:
            price = zone_high - (zone_range * ratio) if trend_up else zone_low + (zone_range * ratio)
            
            # Draw standard Retrement Lines
            fig.add_shape(type="line", x0=min(fib_start_date, fib_end_date), y0=price, x1=max(fib_start_date, fib_end_date), y1=price,
                          line=dict(color="rgba(255, 165, 0, 0.3)", width=1, dash="dot"))
            
            if show_circles:
                current_time_radius = time_delta * ratio
                current_price_radius = zone_range * ratio
                
                fig.add_shape(
                    type="circle",
                    x0=fib_start_date - current_time_radius,
                    y0=center_price - current_price_radius,
                    x1=fib_start_date + current_time_radius,
                    y1=center_price + current_price_radius,
                    line=dict(color="rgba(0, 255, 204, 0.25)", width=1.2, dash="dashdot"),
                    fillcolor="rgba(0, 255, 204, 0.005)"
                )
            
            # --- AUTOMATIC ENTRY ENGINE (MATH BASED) ---
            if show_entries:
                for idx in range(max(start_idx, end_idx), len(data)):
                    current_date = data.index[idx]
                    
                    # 1. Calculate time distance from center
                    t_dist = abs((current_date - fib_start_date).total_seconds())
                    r_time_seconds = abs((time_delta * ratio).total_seconds())
                    
                    # 2. Check if candle is on the Fib Circle time boundary (with 5% tolerance)
                    if abs(t_dist - r_time_seconds) <= (r_time_seconds * 0.05):
                        c_low = low_prices[idx]
                        c_high = high_prices[idx]
                        
                        # Buy Entry Condition (Retracement to Golden Ratios in Up-trend)
                        if trend_up and ratio in [0.5, 0.618, 0.786]:
                            if c_low <= price <= c_high and current_date not in detected_entries:
                                fig.add_annotation(
                                    x=current_date, y=c_low,
                                    text="🟢 BUY ENTRY", showarrow=True, arrowhead=2,
                                    arrowcolor="#089981", arrowsize=1, arrowwidth=2,
                                    ax=0, ay=35, font=dict(color="#ffffff", size=10, family="Arial Black"),
                                    bgcolor="#089981", bordercolor="#089981", borderwidth=2, borderpad=4
                                )
                                detected_entries.append(current_date)
                        
                        # Sell Entry Condition (Retracement to Golden Ratios in Down-trend)
                        elif not trend_up and ratio in [0.5, 0.618, 0.786]:
                            if c_low <= price <= c_high and current_date not in detected_entries:
                                fig.add_annotation(
                                    x=current_date, y=c_high,
                                    text="🔴 SELL ENTRY", showarrow=True, arrowhead=2,
                                    arrowcolor="#f23645", arrowsize=1, arrowwidth=2,
                                    ax=0, ay=-35, font=dict(color="#ffffff", size=10, family="Arial Black"),
                                    bgcolor="#f23645", bordercolor="#f23645", borderwidth=2, borderpad=4
                                )
                                detected_entries.append(current_date)

        fig.update_layout(
            title=f"{ticker} Live Chart | TradingView Colors & Auto Fib Circle Entries",
            yaxis_title="Price", xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14', xaxis_rangeslider_visible=False,
            height=750, font=dict(color="#8a99ad")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary Box
        st.write("### 📊 Live Trade Signals")
        if detected_entries:
            for entry_date in detected_entries:
                st.success(f"🎯 **Automated Entry Triggered** on {entry_date.strftime('%Y-%m-%d %H:%M')} via Golden Fib Circle Intersection.")
        else:
            st.info("Waiting for Price to intersect with Fibonacci Circle Golden Zones...")

except Exception as e:
    st.error(f"Something went wrong: {e}")
