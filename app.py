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
        start_idx = st.sidebar.slider("Fibonacci Start Point", 0, max_idx, 0)
        end_idx = st.sidebar.slider("Fibonacci End Point", 0, max_idx, max_idx)
        
        # Checkbox to toggle Circles
        show_circles = st.sidebar.checkbox("Show Fibonacci Circles", value=True)
        
        zone_high = float(high_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].max())
        zone_low = float(low_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].min())
        zone_range = zone_high - zone_low
        
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_line_color='#00ff66', decreasing_line_color='#ff3366', name="Candlesticks"
        )])
        
        # Auto Support & Resistance Lines
        for peak in peaks:
            fig.add_shape(type="line", x0=data.index[0], y0=high_prices[peak], x1=data.index[-1], y1=high_prices[peak],
                          line=dict(color="#ff3366", width=1.5, dash="dash"))
        for trough in troughs:
            fig.add_shape(type="line", x0=data.index[0], y0=low_prices[trough], x1=data.index[-1], y1=low_prices[trough],
                          line=dict(color="#00ff66", width=1.5, dash="dash"))
            
        # Fibonacci Levels
        fib_ratios = [0.0, 0.236, 0.382, 0.500, 0.618, 0.786, 1.0]
        fib_start_date = data.index[start_idx]
        fib_end_date = data.index[end_idx]
        
        # Base dimensions for circles (Time delta and Price delta)
        time_delta = fib_end_date - fib_start_date
        center_price = zone_high if start_idx < end_idx else zone_low
        
        for ratio in fib_ratios:
            price = zone_high - (zone_range * ratio)
            
            # Draw standard Retrement Lines
            fig.add_shape(type="line", x0=min(fib_start_date, fib_end_date), y0=price, x1=max(fib_start_date, fib_end_date), y1=price,
                          line=dict(color="rgba(255, 165, 0, 0.4)", width=1.5, dash="dot"))
            
            fig.add_annotation(x=max(fib_start_date, fib_end_date), y=price, text=f"Fib {ratio*100:.1f}% ({price:.2f})",
                               showarrow=False, xanchor="left", yanchor="bottom",
                               font=dict(color="#ffcc00", size=10), bgcolor="rgba(11, 14, 20, 0.7)")
            
            # Draw Fibonacci Circles if enabled
            if show_circles and ratio > 0:
                current_time_radius = time_delta * ratio
                current_price_radius = zone_range * ratio
                
                fig.add_shape(
                    type="circle",
                    x0=fib_start_date - current_time_radius,
                    y0=center_price - current_price_radius,
                    x1=fib_start_date + current_time_radius,
                    y1=center_price + current_price_radius,
                    line=dict(color="rgba(0, 255, 204, 0.35)", width=1.5, dash="dashdot"),
                    fillcolor="rgba(0, 255, 204, 0.01)"
                )

        fig.update_layout(
            title=f"{ticker} Live Chart with Auto S&R, Fib Levels & Circles",
            yaxis_title="Price", xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#11151c', plot_bgcolor='#11151c', xaxis_rangeslider_visible=False,
            height=720, font=dict(color="#8a99ad")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("### 🔍 Detected Chart Patterns (Maths Engine)")
        detected_patterns = []
        for i in range(len(peaks)-1):
            p1, p2 = high_prices[peaks[i]], high_prices[peaks[i+1]]
            if abs(p1 - p2) / p1 < 0.005:
                detected_patterns.append(f"⚠️ Potential **Double Top** detected near price {round(p1, 2)}")
                
        for i in range(len(troughs)-1):
            t1, t2 = low_prices[troughs[i]], low_prices[troughs[i+1]]
            if abs(t1 - t2) / t1 < 0.005:
                detected_patterns.append(f"✅ Potential **Double Bottom** detected near price {round(t1, 2)}")
                
        if detected_patterns:
            for pattern in detected_patterns:
                st.info(pattern)
        else:
            st.success("No clear patterns detected at this moment. Market is moving smoothly.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
