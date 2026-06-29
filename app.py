import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide")

# --- OPTIMIZED CSS FOR MAXIMUM CHART SPACE ---
st.markdown("""
<style>
.stApp {background-color: #0b0e14; color: #ecf0f1; }
/* Headline සහ Subheader වල Font Size සහ Margin අඩු කර ඉඩ ඉතිරි කිරීම */
h1 {
    color: #00ffcc !important; 
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
    font-size: 22px !important; 
    margin-top: -40px !important; 
    margin-bottom: 2px !important;
}
h3 {
    color: #8a99ad !important; 
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
    font-size: 13px !important; 
    margin-top: 0px !important; 
    margin-bottom: 10px !important;
}
div[data-testid="stMetricValue"] { color: #00ffcc !important; }
/* Streamlit වල default උඩ ඉඩ (Padding) අඩු කිරීම */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 0rem !important;
}
</style>
""", unsafe_allow_html=True)

# කුඩා කළ Headlines
st.markdown("<h1>📈 Pro Trader Automated Chart Pattern & S&R Tool</h1>", unsafe_allow_html=True)
st.markdown("<h3>SMC & ICT Multi-OB Forecasting Engine - Premium Edition</h3>", unsafe_allow_html=True)

ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, EURUSD=X, AAPL):", value="BTC-USD")

# --- TIMEFRAMES & PERIODS ---
timeframe = st.sidebar.selectbox("Select Timeframe:", ["1d", "4h", "2h", "1h", "30m", "15m", "5m"])
period = st.sidebar.selectbox("Select Period (Data Range):", ["1y", "6mo", "3mo", "1mo", "7d", "1d"])

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
        
        # --- DYNAMIC ORDER BLOCK CONTROLS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎛️ Custom Order Block Settings")
        ob_distance = st.sidebar.slider("OB Detection Range (Candle Distance)", 3, 20, 10)
        ob_sensitivity = st.sidebar.slider("OB Sensitivity Multiplier", 0.05, 0.50, 0.15, step=0.05)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Display Settings")
        show_ob = st.sidebar.checkbox("Show Order Blocks (OB)", value=True)
        show_structure = st.sidebar.checkbox("Show BOS & Liquidity Sweeps", value=True)
        
        # High-precision Peak and Trough Detection
        peaks, _ = find_peaks(high_prices, distance=ob_distance, prominence=np.std(high_prices) * ob_sensitivity)
        troughs, _ = find_peaks(-low_prices, distance=ob_distance, prominence=np.std(low_prices) * ob_sensitivity)
        
        # TradingView Color Theme
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_fillcolor='#089981',
            increasing_line_color='#089981',
            decreasing_fillcolor='#f23645',
            decreasing_line_color='#f23645',
            name="Candlesticks"
        )])
        
        trade_table_data = []
        
        # --- 1. LIQUIDITY SWEEP ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        
        if show_structure:
            for idx in range(20, len(data)):
                # High Liquidity Sweep Detection
                if high_prices[idx] > last_high and close_prices[idx] < last_high:
                    fig.add_annotation(
                        x=data.index[idx], y=high_prices[idx],
                        text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00",
                        font=dict(color="#000000", size=9, family="Arial Black"),
                        bgcolor="#ffcc00", ay=-35
                    )
                    fig.add_shape(
                        type="line",
                        x0=data.index[idx-10 if idx-10 >= 0 else 0], y0=last_high,
                        x1=data.index[-1], y1=last_high,
                        line=dict(color="#ffffff", width=2, dash="solid")
                    )
                    fig.add_annotation(
                        x=data.index[-1], y=last_high,
                        text="LQ SWEEP TRIGGER LEVEL", showarrow=False,
                        font=dict(color="#ffffff", size=9, family="Arial Black"),
                        xanchor="right", yanchor="bottom"
                    )
                    
                # Low Liquidity Sweep Detection
                elif low_prices[idx] < last_low and close_prices[idx] > last_low:
                    fig.add_annotation(
                        x=data.index[idx], y=low_prices[idx],
                        text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00",
                        font=dict(color="#000000", size=9, family="Arial Black"),
                        bgcolor="#ffcc00", ay=35
                    )
                    fig.add_shape(
                        type="line",
                        x0=data.index[idx-10 if idx-10 >= 0 else 0], y0=last_low,
                        x1=data.index[-1], y1=last_low,
                        line=dict(color="#ffffff", width=2, dash="solid")
                    )
                    fig.add_annotation(
                        x=data.index[-1], y=last_low,
                        text="LQ SWEEP TRIGGER LEVEL", showarrow=False,
                        font=dict(color="#ffffff", size=9, family="Arial Black"),
                        xanchor="right", yanchor="top"
                    )
                
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_high, x1=data.index[idx], y1=last_high, line=dict(color="#089981", width=1.5, dash="dot"))
                    last_high = high_prices[idx]
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_low, x1=data.index[idx], y1=last_low, line=dict(color="#f23645", width=1.5, dash="dot"))
                    last_low = low_prices[idx]
                    
        # --- 2. WHOLE-CHART MULTI ORDER BLOCK DETECTION ---
        if show_ob:
            for p in peaks:
                if p < len(data) - 2:
                    ob_top = high_prices[p]
                    ob_bottom = min(open_prices[p], close_prices[p])
                    future_candles_high = high_prices[p+1:]
                    if len(future_candles_high) > 0 and max(future_candles_high) < ob_top:
                        fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[-1], y1=ob_top, fillcolor="rgba(242, 54, 69, 0.05)", line=dict(color="rgba(242, 54, 69, 0.35)", width=1))
                        
                        trade_table_data.append({
                            "Type": "🔴 BEARISH OB (Short Limit)",
                            "OB Zone (Top)": round(ob_top, 2),
                            "Entry / OB Bottom": round(ob_bottom, 2),
                            "Stop Loss (SL)": round(ob_top + (ob_top - ob_bottom) * 0.15, 2),
                            "Take Profit (TP)": round(round(ob_bottom, 2) - ((round(ob_top + (ob_top - ob_bottom) * 0.15, 2) - round(ob_bottom, 2)) * 3.0), 2),
                            "Risk:Reward": "1 : 3.0",
                            "OB Formed Date": data.index[p].strftime('%Y-%m-%d %H:%M')
                        })
                        
            for t in troughs:
                if t < len(data) - 2:
                    ob_bottom = low_prices[t]
                    ob_top = max(open_prices[t], close_prices[t])
                    future_candles_low = low_prices[t+1:]
                    if len(future_candles_low) > 0 and min(future_candles_low) > ob_bottom:
                        fig.add_shape(type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[-1], y1=ob_top, fillcolor="rgba(8, 153, 129, 0.05)", line=dict(color="rgba(8, 153, 129, 0.35)", width=1))
                        
                        trade_table_data.append({
                            "Type": "🟢 BULLISH OB (Long Limit)",
                            "OB Zone (Top)": round(ob_top, 2),
                            "Entry / OB Bottom": round(ob_bottom, 2),
                            "Stop Loss (SL)": round(ob_bottom - (ob_top - ob_bottom) * 0.15, 2),
                            "Take Profit (TP)": round(round(ob_top, 2) + ((round(ob_top, 2) - round(ob_bottom - (ob_top - ob_bottom) * 0.15, 2)) * 3.0), 2),
                            "Risk:Reward": "1 : 3.0",
                            "OB Formed Date": data.index[t].strftime('%Y-%m-%d %H:%M')
                        })
                        
        fig.update_layout(
            title=f"{ticker} Live Chart | Whole-Chart SMC Analytics Engine",
            yaxis_title="Price",
            xaxis_title="Date/Time",
            template="plotly_dark",
            paper_bgcolor='#0b0e14',
            plot_bgcolor='#0b0e14',
            xaxis_rangeslider_visible=False,
            height=780,  # <--- CHART HEIGHT එක 700 සිට 780 දක්වා වැඩි කර ලොකු කරන ලදී
            font=dict(color="#8a99ad"),
            margin=dict(t=30, b=10, l=10, r=10) # Chart එක වටේ හිස් ඉඩ (Margin) අවම කිරීම
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 3. ADVANCED SIGNAL TABLE ---
        st.markdown("---")
        st.write("### 📊 Active Institutional Order Blocks & Pending Setups")
        
        if trade_table_data:
            df_signals = pd.DataFrame(trade_table_data)
            df_signals = df_signals[["Type", "OB Formed Date", "OB Zone (Top)", "Entry / OB Bottom", "Stop Loss (SL)", "Take Profit (TP)", "Risk:Reward"]]
            st.dataframe(df_signals, use_container_width=True, hide_index=True)
            st.success(f"🔥 Chart analysis complete. Successfully identified {len(df_signals)} active (Unmitigated) strong Order Blocks.")
        else:
            st.info("⏳ No strong unmitigated Order Blocks found across the chart currently.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
