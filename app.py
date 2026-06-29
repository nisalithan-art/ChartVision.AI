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
        
        # --- DYNAMIC ORDER BLOCK CONTROLS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎛️ Custom Settings")
        ob_distance = st.sidebar.slider("Pattern Detection Distance (Candles)", 3, 20, 7)
        ob_sensitivity = st.sidebar.slider("Sensitivity Multiplier", 0.05, 0.50, 0.10, step=0.05)
        ob_length = st.sidebar.slider("Order Block Box Length", 5, 100, 30)
        
        # --- LIQUIDITY & PATTERN TOGGLES ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Display Settings")
        liquidity_count = st.sidebar.slider("BSL / SSL Levels to Display", 1, 10, 3)
        show_patterns = st.sidebar.checkbox("Show Chart Patterns (Double Top, H&S, Wedges)", value=True)
        show_ob = st.sidebar.checkbox("Show Order Blocks (OB) / POI", value=True)
        show_structure = st.sidebar.checkbox("Show BOS & Liquidity Sweeps", value=True)
        show_ict_metrics = st.sidebar.checkbox("Show MSS, BSL, SSL & BPR", value=True)
        
        # --- COLOR CUSTOMIZATION ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎨 Colors")
        bull_body_color = st.sidebar.color_picker("Bullish Candle", "#089981")
        bear_body_color = st.sidebar.color_picker("Bearish Candle", "#f23645")
        bull_ob_color = st.sidebar.color_picker("Bullish OB Box", "#089981")
        bear_ob_color = st.sidebar.color_picker("Bearish OB Box", "#f23645")
        ob_opacity = st.sidebar.slider("OB Box Opacity", 0.01, 0.30, 0.05, step=0.01)
        
        # High-precision Peak and Trough Detection for Patterns
        peaks, _ = find_peaks(high_prices, distance=ob_distance, prominence=np.std(high_prices) * ob_sensitivity)
        troughs, _ = find_peaks(-low_prices, distance=ob_distance, prominence=np.std(low_prices) * ob_sensitivity)
        
        # Candlestick Generation
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor=bull_body_color, increasing_line_color=bull_body_color,
            decreasing_fillcolor=bear_body_color, decreasing_line_color=bear_body_color,
            name="Candlesticks"
        )])
        
        trade_table_data = []
        
        # --- 1. LIQUIDITY SWEEP & BOS ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        
        if show_structure:
            for idx in range(20, len(data)):
                if high_prices[idx] > last_high and close_prices[idx] < last_high:
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#000000", size=9, family="Arial Black"), bgcolor="#ffcc00", ay=-35)
                elif low_prices[idx] < last_low and close_prices[idx] > last_low:
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00", font=dict(color="#000000", size=9, family="Arial Black"), bgcolor="#ffcc00", ay=35)
                
                if close_prices[idx] > last_high:
                    last_high = high_prices[idx]
                elif close_prices[idx] < last_low:
                    last_low = low_prices[idx]

        # --- 2. ADVANCED ICT METRICS ENGINE (MULTI BSL / SSL & MSS) ---
        if show_ict_metrics:
            display_peaks = peaks[-liquidity_count:] if len(peaks) >= liquidity_count else peaks
            display_troughs = troughs[-liquidity_count:] if len(troughs) >= liquidity_count else troughs

            for p_idx in display_peaks:
                fig.add_shape(type="line", x0=data.index[p_idx], y0=high_prices[p_idx], x1=data.index[-1], y1=high_prices[p_idx], line=dict(color="#00ffcc", width=1.2, dash="dash"))
            for t_idx in display_troughs:
                fig.add_shape(type="line", x0=data.index[t_idx], y0=low_prices[t_idx], x1=data.index[-1], y1=low_prices[t_idx], line=dict(color="#ff33aa", width=1.2, dash="dash"))

            # Filtered MSS
            recent_highs = [high_prices[p] for p in peaks if p < len(data)]
            recent_lows = [low_prices[t] for t in troughs if t < len(data)]
            for idx in range(ob_distance, len(data)):
                if len(recent_highs) > 0 and close_prices[idx] > recent_highs[-1] and close_prices[idx-1] <= recent_highs[-1]:
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="⚡ MSS (Bullish)", showarrow=True, arrowhead=1, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9, family="Arial Black"), bgcolor="rgba(11, 14, 20, 0.9)", ay=-45)
                    recent_highs.append(high_prices[idx])
                elif len(recent_lows) > 0 and close_prices[idx] < recent_lows[-1] and close_prices[idx-1] >= recent_lows[-1]:
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="⚡ MSS (Bearish)", showarrow=True, arrowhead=1, arrowcolor="#ff3344", font=dict(color="#ff3344", size=9, family="Arial Black"), bgcolor="rgba(11, 14, 20, 0.9)", ay=45)
                    recent_lows.append(low_prices[idx])

        # --- 3. CLASSIC AUTOMATED CHART PATTERNS ENGINE ---
        if show_patterns:
            # Look at the last 5 peaks and troughs to form reliable geometric structures
            if len(peaks) >= 3 and len(troughs) >= 2:
                # --- DOUBLE TOP DETECTION ---
                p1, p2 = peaks[-2], peaks[-1]
                if abs(high_prices[p1] - high_prices[p2]) / high_prices[p1] < 0.015:
                    fig.add_shape(type="line", x0=data.index[p1], y0=high_prices[p1], x1=data.index[p2], y1=high_prices[p2], line=dict(color="#ffaa00", width=3))
                    fig.add_annotation(x=data.index[p2], y=high_prices[p2], text="⚠️ DOUBLE TOP", showarrow=True, arrowcolor="#ffaa00", font=dict(color="#ffaa00", size=10, family="Arial Black"), ay=-50)

                # --- HEAD AND SHOULDERS (H&S) DETECTION ---
                if len(peaks) >= 3:
                    l_sh, head, r_sh = peaks[-3], peaks[-2], peaks[-1]
                    if high_prices[head] > high_prices[l_sh] and high_prices[head] > high_prices[r_sh]:
                        if abs(high_prices[l_sh] - high_prices[r_sh]) / high_prices[l_sh] < 0.03:
                            # Draw Head & Shoulders lines
                            fig.add_shape(type="line", x0=data.index[l_sh], y0=high_prices[l_sh], x1=data.index[head], y1=high_prices[head], line=dict(color="#ff3333", width=2.5))
                            fig.add_shape(type="line", x0=data.index[head], y0=high_prices[head], x1=data.index[r_sh], y1=high_prices[r_sh], line=dict(color="#ff3333", width=2.5))
                            fig.add_annotation(x=data.index[head], y=high_prices[head], text="👤 HEAD & SHOULDERS", showarrow=True, arrowcolor="#ff3333", font=dict(color="#ff3333", size=10, family="Arial Black"), ay=-55)

            if len(troughs) >= 3 and len(peaks) >= 2:
                # --- DOUBLE BOTTOM DETECTION ---
                t1, t2 = troughs[-2], troughs[-1]
                if abs(low_prices[t1] - low_prices[t2]) / low_prices[t1] < 0.015:
                    fig.add_shape(type="line", x0=data.index[t1], y0=low_prices[t1], x1=data.index[t2], y1=low_prices[t2], line=dict(color="#00aaff", width=3))
                    fig.add_annotation(x=data.index[t2], y=low_prices[t2], text="⚠️ DOUBLE BOTTOM", showarrow=True, arrowcolor="#00aaff", font=dict(color="#00aaff", size=10, family="Arial Black"), ay=50)

                # --- INVERTED HEAD AND SHOULDERS DETECTION ---
                l_sh_inv, head_inv, r_sh_inv = troughs[-3], troughs[-2], troughs[-1]
                if low_prices[head_inv] < low_prices[l_sh_inv] and low_prices[head_inv] < low_prices[r_sh_inv]:
                    if abs(low_prices[l_sh_inv] - low_prices[r_sh_inv]) / low_prices[l_sh_inv] < 0.03:
                        fig.add_shape(type="line", x0=data.index[l_sh_inv], y0=low_prices[l_sh_inv], x1=data.index[head_inv], y1=low_prices[head_inv], line=dict(color="#33cc33", width=2.5))
                        fig.add_shape(type="line", x0=data.index[head_inv], y0=low_prices[head_inv], x1=data.index[r_sh_inv], y1=low_prices[r_sh_inv], line=dict(color="#33cc33", width=2.5))
                        fig.add_annotation(x=data.index[head_inv], y=low_prices[head_inv], text="🙃 INVERTED H&S", showarrow=True, arrowcolor="#33cc33", font=dict(color="#33cc33", size=10, family="Arial Black"), ay=55)

            # --- WEDGES DETECTION (RISING & FALLING WEDGE) ---
            if len(peaks) >= 3 and len(troughs) >= 3:
                p_nodes = peaks[-3:]
                t_nodes = troughs[-3:]
                
                # Slopes calculation using simple linear regression fits
                slope_peaks = np.polyfit(p_nodes, [high_prices[x] for x in p_nodes], 1)[0]
                slope_troughs = np.polyfit(t_nodes, [low_prices[x] for x in t_nodes], 1)[0]
                
                # Rising Wedge: Both slopes are positive, but support is steeper than resistance (converging)
                if slope_peaks > 0 and slope_troughs > 0 and slope_troughs > slope_peaks:
                    fig.add_shape(type="line", x0=data.index[p_nodes[0]], y0=high_prices[p_nodes[0]], x1=data.index[-1], y1=high_prices[p_nodes[-1]], line=dict(color="#e67e22", width=2, dash="dashdot"))
                    fig.add_shape(type="line", x0=data.index[t_nodes[0]], y0=low_prices[t_nodes[0]], x1=data.index[-1], y1=low_prices[t_nodes[-1]], line=dict(color="#e67e22", width=2, dash="dashdot"))
                    fig.add_annotation(x=data.index[p_nodes[-1]], y=high_prices[p_nodes[-1]], text="📐 RISING WEDGE", showarrow=False, font=dict(color="#e67e22", size=10, family="Arial Black"), yanchor="bottom")
                
                # Falling Wedge: Both slopes are negative, but resistance is steeper than support (converging)
                elif slope_peaks < 0 and slope_troughs < 0 and slope_peaks < slope_troughs:
                    fig.add_shape(type="line", x0=data.index[p_nodes[0]], y0=high_prices[p_nodes[0]], x1=data.index[-1], y1=high_prices[p_nodes[-1]], line=dict(color="#9b59b6", width=2, dash="dashdot"))
                    fig.add_shape(type="line", x0=data.index[t_nodes[0]], y0=low_prices[t_nodes[0]], x1=data.index[-1], y1=low_prices[t_nodes[-1]], line=dict(color="#9b59b6", width=2, dash="dashdot"))
                    fig.add_annotation(x=data.index[t_nodes[-1]], y=low_prices[t_nodes[-1]], text="📐 FALLING WEDGE", showarrow=False, font=dict(color="#9b59b6", size=10, family="Arial Black"), yanchor="top")

        # --- 4. WHOLE-CHART POI / ORDER BLOCK DETECTION ---
        def hex_to_rgba(hex_str, opacity):
            hex_str = hex_str.lstrip('#')
            lv = len(hex_str)
            rgb = tuple(int(hex_str[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
            return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

        if show_ob:
            for p in peaks:
                if p < len(data) - 2:
                    ob_top = high_prices[p]
                    ob_bottom = min(open_prices[p], close_prices[p])
                    future_candles_high = high_prices[p+1:]
                    if len(future_candles_high) > 0 and max(future_candles_high) < ob_top:
                        end_idx = min(p + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor=hex_to_rgba(bear_ob_color, ob_opacity), line=dict(color=bear_ob_color, width=1))
                        
            for t in troughs:
                if t < len(data) - 2:
                    ob_bottom = low_prices[t]
                    ob_top = max(open_prices[t], close_prices[t])
                    future_candles_low = low_prices[t+1:]
                    if len(future_candles_low) > 0 and min(future_candles_low) > ob_bottom:
                        end_idx = min(t + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor=hex_to_rgba(bull_ob_color, ob_opacity), line=dict(color=bull_ob_color, width=1))

        fig.update_layout(
            title=f"{ticker} Live Chart | Premium ICT/SMC & Pattern Engine",
            xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
            xaxis_rangeslider_visible=False, height=780, font=dict(color="#8a99ad"),
            margin=dict(t=30, b=10, l=10, r=50),
            yaxis=dict(title="Price", side="right", showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)", ticks="outside"),
            xaxis=dict(showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)")
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")
