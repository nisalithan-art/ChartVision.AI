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
    div[data-testid="stMetricValue"] { color: #00ffcc !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Pro Trader Automated Chart Pattern & S&R Tool")
st.subheader("SMC & ICT Multi-OB Forecasting Engine - Premium Edition")

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
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor='#089981', increasing_line_color='#089981',
            decreasing_fillcolor='#f23645', decreasing_line_color='#f23645',
            name="Candlesticks"
        )])
        
        trade_table_data = []
        
        # --- 1. LIQUIDITY SWEEP & BOS ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        
        if show_structure:
            for idx in range(20, len(data)):
                if high_prices[idx] > last_high and close_prices[idx] < last_high:
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="✖️ LQ SWEEP",
                                       showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#ffcc00", size=9),
                                       bgcolor="rgba(11, 14, 20, 0.85)", ay=-25)
                elif low_prices[idx] < last_low and close_prices[idx] > last_low:
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="✖️ LQ SWEEP",
                                       showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#ffcc00", size=9),
                                       bgcolor="rgba(11, 14, 20, 0.85)", ay=25)
                
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_high, x1=data.index[idx], y1=last_high,
                                  line=dict(color="#089981", width=1.5, dash="dot"))
                    last_high = high_prices[idx]
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_low, x1=data.index[idx], y1=last_low,
                                  line=dict(color="#f23645", width=1.5, dash="dot"))
                    last_low = low_prices[idx]

        # --- 2. WHOLE-CHART MULTI ORDER BLOCK DETECTION & FORECASTING ---
        latest_close = close_prices[-1]
        
        if show_ob:
            # A. BEARISH ORDER BLOCKS (Analyze all detected peaks across the chart)
            for p in peaks:
                if p < len(data) - 2:
                    ob_top = high_prices[p]
                    ob_bottom = min(open_prices[p], close_prices[p])
                    
                    # Check if this OB is still UNMITIGATED (Price hasn't broken above it since creation)
                    future_candles_high = high_prices[p+1:]
                    if len(future_candles_high) > 0 and max(future_candles_high) < ob_top:
                        
                        # Plot on Chart
                        fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[-1], y1=ob_top,
                                      fillcolor="rgba(242, 54, 69, 0.05)", line=dict(color="rgba(242, 54, 69, 0.35)", width=1))
                        
                        # Generate Limit/Pending Trade Setup
                        entry = round(ob_bottom, 2)
                        sl = round(ob_top + (ob_top - ob_bottom) * 0.15, 2) # 15% Buffer above OB
                        risk = sl - entry
                        tp = round(entry - (risk * 3.0), 2) # Target 1:3 RR Matrix
                        
                        trade_table_data.append({
                            "Type": "🔴 BEARISH OB (Short Limit)",
                            "OB Zone (Top)": round(ob_top, 2),
                            "Entry / OB Bottom": entry,
                            "Stop Loss (SL)": sl,
                            "Take Profit (TP)": tp,
                            "Risk:Reward": "1 : 3.0",
                            "OB Formed Date": data.index[p].strftime('%Y-%m-%d %H:%M')
                        })

            # B. BULLISH ORDER BLOCKS (Analyze all detected troughs across the chart)
            for t in troughs:
                if t < len(data) - 2:
                    ob_bottom = low_prices[t]
                    ob_top = max(open_prices[t], close_prices[t])
                    
                    # Check if this OB is UNMITIGATED (Price hasn't broken below it since creation)
                    future_candles_low = low_prices[t+1:]
                    if len(future_candles_low) > 0 and min(future_candles_low) > ob_bottom:
                        
                        # Plot on Chart
                        fig.add_shape(type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[-1], y1=ob_top,
                                      fillcolor="rgba(8, 153, 129, 0.05)", line=dict(color="rgba(8, 153, 129, 0.35)", width=1))
                        
                        # Generate Limit/Pending Trade Setup
                        entry = round(ob_top, 2)
                        sl = round(ob_bottom - (ob_top - ob_bottom) * 0.15, 2) # 15% Buffer below OB
                        risk = entry - sl
                        tp = round(entry + (risk * 3.0), 2) # Target 1:3 RR Matrix
                        
                        trade_table_data.append({
                            "Type": "🟢 BULLISH OB (Long Limit)",
                            "OB Zone (Top)": entry,
                            "Entry / OB Bottom": round(ob_bottom, 2),
                            "Stop Loss (SL)": sl,
                            "Take Profit (TP)": tp,
                            "Risk:Reward": "1 : 3.0",
                            "OB Formed Date": data.index[t].strftime('%Y-%m-%d %H:%M')
                        })

        fig.update_layout(
            title=f"{ticker} Live Chart | Whole-Chart SMC Analytics Engine",
            yaxis_title="Price", xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14', xaxis_rangeslider_visible=False,
            height=700, font=dict(color="#8a99ad")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 3. ADVANCED SIGNAL TABLE AT THE BOTTOM ---
        st.markdown("---")
        st.write("### 📊 Active Institutional Order Blocks & Pending Setups")
        
        if trade_table_data:
            df_signals = pd.DataFrame(trade_table_data)
            
            # Re-ordering columns for cleaner look
            df_signals = df_signals[["Type", "OB Formed Date", "OB Zone (Top)", "Entry / OB Bottom", "Stop Loss (SL)", "Take Profit (TP)", "Risk:Reward"]]
            
            st.dataframe(
                df_signals, 
                use_container_width=True,
                hide_index=True
            )
            st.success(f"🔥 මුළු Chart එකම පරීක්ෂා කර සක්‍රීය (Unmitigated) Strong Order Blocks {len(df_signals)} ක් සොයාගෙන ඇත. මිල මෙම කලාප වලට පැමිණි විට ස්වයංක්‍රීයව Setup ක්‍රියාත්මක වේ.")
        else:
            st.info("⏳ දැනට මුළු Chart එකේම ප්‍රබල Unmitigated Order Blocks හමු නොවීය. සයිඩ්බාර් එකෙන් Sensitivity වෙනස් කර බලන්න.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
