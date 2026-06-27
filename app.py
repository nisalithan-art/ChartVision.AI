import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0e14;
        color: #ecf0f1;
    }
    .css-1d391kg {
        }
    h1, h2, h3 {
        color: #00ffcc !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
        
        zone_high = float(high_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].max())
        zone_low = float(low_prices[min(start_idx, end_idx):max(start_idx, end_idx)+1].min())
        zone_range = zone_high - zone_low

        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_line_color='#00ff66',
            decreasing_line_color='#ff3366',
            name="Candlesticks"
        )])

        for peak in peaks:
            fig.add_shape(
                type="line", x0=data.index[0], y0=high_prices[peak],
                x1=data.index[-1], y1=high_prices[peak],
                line=dict(color="#ff3366", width=1.5, dash="dash"),
            )

        for trough in troughs:
            fig.add_shape(
                type="line", x0=data.index[0], y0=low_prices[trough],
                x1=data.index[-1], y1=low_prices[trough],
                line=dict(color="#00ff66", width=1.5, dash="dash"),
            )

        fib_levels = {
            '0.0%': zone_high,
            '23.6%': zone_high - (zone_range * 0.236),
            '38.2%': zone_high - (zone_range * 0.382),
            '50.0%': zone_high - (zone_range * 0.500),
            '61.8%': zone_high - (zone_range * 0.618),
            '78.6%': zone_high - (zone_range * 0.786),
            '100.0%': zone_low
        }

        fib_start_date = data.index[min(start_idx, end_idx)]
        fib_end_date = data.index[max(start_idx, end_idx)]

        for level, price in fib_levels.items():
            fig.add_shape(
                type="line",
                x0=fib_start_date, y0=price,
                x1=fib_end_date, y1=price,
                line=dict(color="rgba(255, 165, 0, 0.75)", width=2, dash="dot"),
            )
            fig.add_annotation(
                x=fib_end_date, y=price,
                text=f"Fib {level} ({price:.2f})",
                showarrow=False,
                xanchor="left",
                yanchor="bottom",
                font=dict(color="#ffcc00", size=10),
                bgcolor="rgba(11, 14, 20, 0.7)"
            )

        fig.update_layout(
            title=f"{ticker} Live Chart with Auto S&R & Fibonacci Levels",
            yaxis_title="Price",
            xaxis_title="Date/Time",
            template="plotly_dark",
            paper_bgcolor='#11151c',
            plot_bgcolor='#11151c',
            xaxis_rangeslider_visible=False,
            height=680,
            font=dict(color="#8a99ad")
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
