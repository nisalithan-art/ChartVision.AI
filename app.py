import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide")

# --- OPTIMIZED CSS FOR MAXIMUM CHART SPACE & THEME ---
st.markdown("""
<style>
.stApp {background-color: #0b0e14; color: #ecf0f1; }
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
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 0rem !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>📈 Pro Trader Automated Chart Pattern & S&R Tool</h1>", unsafe_allow_html=True)
st.markdown("<h3>SMC, ICT & Classic Chart Pattern Forecasting Engine - Ultra Edition</h3>", unsafe_allow_html=True)

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
        
        # --- DYNAMIC CONTROLS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎛️ Custom Settings")
        ob_distance = st.sidebar.slider("Pattern Detection Distance (Candles)", 3, 20, 7)
        ob_sensitivity = st.sidebar.slider("Sensitivity Multiplier", 0.05, 0.50, 0.10, step=0.05)
        ob_length = st.sidebar.slider("Order Block Box Length", 5, 100, 30)
        
        # --- DISPLAY TOGGLES ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Display Settings")
        liquidity_count = st.sidebar.slider("BSL / SSL Levels to Display", 1, 10, 3)
        show_patterns = st.sidebar.checkbox("Show Chart Patterns", value=True)
        show_ob = st.sidebar.checkbox("Show Order Blocks & FVGs", value=True)
        show_structure = st.sidebar.checkbox("Show BOS / CHoCH", value=True)
        show_ict_metrics = st.sidebar.checkbox("Show MSS, BSL, SSL", value=True)
        
        # Colors
        bull_body_color = "#089981"
        bear_body_color = "#f23645"
        
        # High-precision Peak and Trough Detection
        peaks, _ = find_peaks(high_prices, distance=ob_distance, prominence=np.std(high_prices) * ob_sensitivity)
        troughs, _ = find_peaks(-low_prices, distance=ob_distance, prominence=np.std(low_prices) * ob_sensitivity)
        
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor=bull_body_color, increasing_line_color=bull_body_color,
            decreasing_fillcolor=bear_body_color, decreasing_line_color=bear_body_color,
            name="Candlesticks"
        )])
        
        trade_table_data = [] # මෙතන තමයි සේරම Table Signals එකතු වෙන්නේ
        
        # --- 1. BOS & CHoCH (STRUCTURE) ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        structure_state = "IDLE" 

        if show_structure:
            for idx in range(20, len(data)):
                # CHoCH (Change of Character) - පළමු වරට ව්‍යුහය මාරු වීම
                if close_prices[idx] > last_high and structure_state == "BEAR":
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="🔄 CHoCH (Bullish)", showarrow=True, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=-30)
                    structure_state = "BULL"
                elif close_prices[idx] < last_low and structure_state == "BULL":
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="🔄 CHoCH (Bearish)", showarrow=True, arrowcolor="#ff3344", font=dict(color="#ff3344", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=30)
                    structure_state = "BEAR"
                
                # BOS (Break of Structure) - Trend එක දිගේම දිගටම බිඳගෙන යාම
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_high, x1=data.index[idx], y1=last_high, line=dict(color="#089981", width=1.5, dash="dot"))
                    fig.add_annotation(x=data.index[idx], y=last_high, text="BOS", showarrow=False, font=dict(color="#089981", size=8))
                    last_high = high_prices[idx]
                    if structure_state == "IDLE": structure_state = "BULL"
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_low, x1=data.index[idx], y1=last_low, line=dict(color="#f23645", width=1.5, dash="dot"))
                    fig.add_annotation(x=data.index[idx], y=last_low, text="BOS", showarrow=False, font=dict(color="#f23645", size=8), yanchor="top")
                    last_low = low_prices[idx]
                    if structure_state == "IDLE": structure_state = "BEAR"

        # --- 2. BSL / SSL & MSS ENGINE ---
        if show_ict_metrics:
            display_peaks = peaks[-liquidity_count:] if len(peaks) >= liquidity_count else peaks
            display_troughs = troughs[-liquidity_count:] if len(troughs) >= liquidity_count else troughs

            for p_idx in display_peaks:
                fig.add_shape(type="line", x0=data.index[p_idx], y0=high_prices[p_idx], x1=data.index[-1], y1=high_prices[p_idx], line=dict(color="#00ffcc", width=1.2, dash="dash"))
                fig.add_annotation(x=data.index[-1], y=high_prices[p_idx], text="BSL", showarrow=False, font=dict(color="#00ffcc", size=8), xanchor="right")
            for t_idx in display_troughs:
                fig.add_shape(type="line", x0=data.index[t_idx], y0=low_prices[t_idx], x1=data.index[-1], y1=low_prices[t_idx], line=dict(color="#ff33aa", width=1.2, dash="dash"))
                fig.add_annotation(x=data.index[-1], y=low_prices[t_idx], text="SSL", showarrow=False, font=dict(color="#ff33aa", size=8), xanchor="right", yanchor="top")

            # Filtered MSS
            recent_highs = [high_prices[p] for p in peaks if p < len(data)]
            recent_lows = [low_prices[t] for t in troughs if t < len(data)]
            for idx in range(ob_distance, len(data)):
                if len(recent_highs) > 0 and close_prices[idx] > recent_highs[-1] and close_prices[idx-1] <= recent_highs[-1]:
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="⚡ MSS (Bullish)", showarrow=True, arrowhead=1, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9, family="Arial Black"), bgcolor="rgba(11, 14, 20, 0.9)", ay=-45)
                    trade_table_data.append({"Type": "⚡ BULLISH MSS", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Price / Level": round(high_prices[idx], 2), "Action / Target": "Look for Buy Setup (🎯 Next BSL)", "Status": "Active Structure Shift"})
                    recent_highs.append(high_prices[idx])
                elif len(recent_lows) > 0 and close_prices[idx] < recent_lows[-1] and close_prices[idx-1] >= recent_lows[-1]:
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="⚡ MSS (Bearish)", showarrow=True, arrowhead=1, arrowcolor="#ff3344", font=dict(color="#ff3344", size=9, family="Arial Black"), bgcolor="rgba(11, 14, 20, 0.9)", ay=45)
                    trade_table_data.append({"Type": "⚡ BEARISH MSS", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Price / Level": round(low_prices[idx], 2), "Action / Target": "Look for Sell Setup (🎯 Next SSL)", "Status": "Active Structure Shift"})
                    recent_lows.append(low_prices[idx])

        # --- 3. VALID FVG (FAIR VALUE GAP) DETECTION ---
        if show_ob:
            for i in range(2, len(data)):
                # Bullish FVG (Candle 1 High < Candle 3 Low)
                if low_prices[i] > high_prices[i-2] and (close_prices[i-1] > open_prices[i-1]):
                    fvg_top = low_prices[i]
                    fvg_bottom = high_prices[i-2]
                    # Check if FVG is unmitigated yet
                    if min(low_prices[i-1:]) >= fvg_bottom:
                        fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(0, 255, 204, 0.03)", line=dict(color="rgba(0, 255, 204, 0.15)", width=1))
                        trade_table_data.append({"Type": "🟢 UNMITIGATED FVG (Bullish)", "Signal Date": data.index[i-1].strftime('%Y-%m-%d %H:%M'), "Price / Level": f"{round(fvg_bottom,2)} - {round(fvg_top,2)}", "Action / Target": "Buy Entry Zone", "Status": "Pending Mitigation"})

                # Bearish FVG (Candle 1 Low > Candle 3 High)
                elif high_prices[i] < low_prices[i-2] and (close_prices[i-1] < open_prices[i-1]):
                    fvg_top = low_prices[i-2]
                    fvg_bottom = high_prices[i]
                    if max(high_prices[i-1:]) <= fvg_top:
                        fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(255, 51, 68, 0.03)", line=dict(color="rgba(255, 51, 68, 0.15)", width=1))
                        trade_table_data.append({"Type": "🔴 UNMITIGATED FVG (Bearish)", "Signal Date": data.index[i-1].strftime('%Y-%m-%d %H:%M'), "Price / Level": f"{round(fvg_bottom,2)} - {round(fvg_top,2)}", "Action / Target": "Sell Entry Zone", "Status": "Pending Mitigation"})

        # --- 4. VALID ORDER BLOCK DETECTION ---
        if show_ob:
            for p in peaks:
                if p < len(data) - 2:
                    ob_top, ob_bottom = high_prices[p], min(open_prices[p], close_prices[p])
                    if max(high_prices[p+1:]) < ob_top: # Unmitigated check
                        end_idx = min(p + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(242, 54, 69, 0.05)", line=dict(color="#f23645", width=1))
                        trade_table_data.append({"Type": "🔴 BEARISH ORDER BLOCK", "Signal Date": data.index[p].strftime('%Y-%m-%d %H:%M'), "Price / Level": round(ob_bottom, 2), "Action / Target": "Premium Sell Entry", "Status": "POI Active"})
                        
            for t in troughs:
                if t < len(data) - 2:
                    ob_bottom, ob_top = low_prices[t], max(open_prices[t], close_prices[t])
                    if min(low_prices[t+1:]) > ob_bottom:
                        end_idx = min(t + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(8, 153, 129, 0.05)", line=dict(color="#089981", width=1))
                        trade_table_data.append({"Type": "🟢 BULLISH ORDER BLOCK", "Signal Date": data.index[t].strftime('%Y-%m-%d %H:%M'), "Price / Level": round(ob_top, 2), "Action / Target": "Discount Buy Entry", "Status": "POI Active"})

        # --- 5. CLASSIC CHART PATTERNS ENGINE ---
        if show_patterns and len(peaks) >= 3 and len(troughs) >= 3:
            # Double Top
            if abs(high_prices[peaks[-2]] - high_prices[peaks[-1]]) / high_prices[peaks[-2]] < 0.015:
                fig.add_shape(type="line", x0=data.index[peaks[-2]], y0=high_prices[peaks[-2]], x1=data.index[peaks[-1]], y1=high_prices[peaks[-1]], line=dict(color="#ffaa00", width=3))
                trade_table_data.append({"Type": "⚠️ DOUBLE TOP DETECTED", "Signal Date": data.index[peaks[-1]].strftime('%Y-%m-%d'), "Price / Level": round(high_prices[peaks[-1]], 2), "Action / Target": "Reversal / Short Setup", "Status": "Pattern Formed"})
            # Double Bottom
            if abs(low_prices[troughs[-2]] - low_prices[troughs[-1]]) / low_prices[troughs[-2]] < 0.015:
                fig.add_shape(type="line", x0=data.index[troughs[-2]], y0=low_prices[troughs[-2]], x1=data.index[troughs[-1]], y1=low_prices[troughs[-1]], line=dict(color="#00aaff", width=3))
                trade_table_data.append({"Type": "⚠️ DOUBLE BOTTOM DETECTED", "Signal Date": data.index[troughs[-1]].strftime('%Y-%m-%d'), "Price / Level": round(low_prices[troughs[-1]], 2), "Action / Target": "Reversal / Long Setup", "Status": "Pattern Formed"})

        # Layout & Display Chart
        fig.update_layout(
            title=f"{ticker} Live Chart | Premium Multi-Forecast Smart Tool",
            xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
            xaxis_rangeslider_visible=False, height=750, font=dict(color="#8a99ad"),
            margin=dict(t=30, b=10, l=10, r=50),
            yaxis=dict(title="Price", side="right", showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)", ticks="outside")
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- 6. DYNAMIC SIGNAL TABLE (THE SOLUTION) ---
        st.markdown("---")
        st.write("### 📊 Active Trading Signals & Institutional POIs Matrix")
        
        if trade_table_data:
            df_signals = pd.DataFrame(trade_table_data)
            # Sort by date to show latest signals first
            df_signals = df_signals.drop_duplicates(subset=["Type", "Price / Level"]).sort_values(by="Signal Date", ascending=False)
            st.dataframe(df_signals, use_container_width=True, hide_index=True)
            st.success(f"🔥 Analysis Complete. {len(df_signals)} Valid High-Probability Action Zones/Patterns identified successfully.")
        else:
            st.info("⏳ Scanning Chart... No strong unmitigated FVG, Order Blocks, or Geometric Patterns forming right now.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
