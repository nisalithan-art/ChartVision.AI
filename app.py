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
        ob_length = st.sidebar.slider("Order Block Box Length (Candles to extend)", 5, 100, 30)
        
        # --- COLOR CUSTOMIZATION CONTROLS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎨 Customize Chart & Box Colors")
        
        st.sidebar.markdown("**🟢 Bullish Candle Settings**")
        bull_body_color = st.sidebar.color_picker("Bullish Body Color", "#089981")
        bull_border_color = st.sidebar.color_picker("Bullish Border & Wick Color", "#089981")
        
        st.sidebar.markdown("**🔴 Bearish Candle Settings**")
        bear_body_color = st.sidebar.color_picker("Bearish Body Color", "#f23645")
        bear_border_color = st.sidebar.color_picker("Bearish Border & Wick Color", "#f23645")
        
        st.sidebar.markdown("**📦 Order Block (OB) Box Colors**")
        bull_ob_color = st.sidebar.color_picker("Bullish OB Box Color", "#089981")
        bear_ob_color = st.sidebar.color_picker("Bearish OB Box Color", "#f23645")
        ob_opacity = st.sidebar.slider("OB Box Opacity", 0.01, 0.30, 0.05, step=0.01)
        
        # --- ICT DISPLAY SETTINGS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚡ ICT & SMC Premium Features")
        show_ob = st.sidebar.checkbox("Show Order Blocks (OB) / POI", value=True)
        show_structure = st.sidebar.checkbox("Show BOS & Liquidity Sweeps", value=True)
        show_ict_metrics = st.sidebar.checkbox("Show MSS, BSL, SSL & BPR", value=True)
        
        # High-precision Peak and Trough Detection
        peaks, _ = find_peaks(high_prices, distance=ob_distance, prominence=np.std(high_prices) * ob_sensitivity)
        troughs, _ = find_peaks(-low_prices, distance=ob_distance, prominence=np.std(low_prices) * ob_sensitivity)
        
        # Candlestick Generation
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_fillcolor=bull_body_color,
            increasing_line_color=bull_border_color,
            decreasing_fillcolor=bear_body_color,
            decreasing_line_color=bear_border_color,
            name="Candlesticks"
        )])
        
        trade_table_data = []
        
        # --- 1. LIQUIDITY SWEEP & BOS ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        
        if show_structure:
            for idx in range(20, len(data)):
                if high_prices[idx] > last_high and close_prices[idx] < last_high:
                    fig.add_annotation(
                        x=data.index[idx], y=high_prices[idx],
                        text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00",
                        font=dict(color="#000000", size=9, family="Arial Black"),
                        bgcolor="#ffcc00", ay=-35
                    )
                    fig.add_shape(
                        type="line", x0=data.index[idx-10 if idx-10 >= 0 else 0], y0=last_high,
                        x1=data.index[-1], y1=last_high, line=dict(color="#ffffff", width=2, dash="solid")
                    )
                    fig.add_annotation(
                        x=data.index[-1], y=last_high, text="LQ SWEEP TRIGGER LEVEL", showarrow=False,
                        font=dict(color="#ffffff", size=9, family="Arial Black"), xanchor="right", yanchor="bottom"
                    )
                    
                elif low_prices[idx] < last_low and close_prices[idx] > last_low:
                    fig.add_annotation(
                        x=data.index[idx], y=low_prices[idx],
                        text="✖️ LQ SWEEP", showarrow=True, arrowhead=2, arrowcolor="#ffcc00",
                        font=dict(color="#000000", size=9, family="Arial Black"),
                        bgcolor="#ffcc00", ay=35
                    )
                    fig.add_shape(
                        type="line", x0=data.index[idx-10 if idx-10 >= 0 else 0], y0=last_low,
                        x1=data.index[-1], y1=last_low, line=dict(color="#ffffff", width=2, dash="solid")
                    )
                    fig.add_annotation(
                        x=data.index[-1], y=last_low, text="LQ SWEEP TRIGGER LEVEL", showarrow=False,
                        font=dict(color="#ffffff", size=9, family="Arial Black"), xanchor="right", yanchor="top"
                    )
                
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_high, x1=data.index[idx], y1=last_high, line=dict(color=bull_body_color, width=1.5, dash="dot"))
                    last_high = high_prices[idx]
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-5], y0=last_low, x1=data.index[idx], y1=last_low, line=dict(color=bear_body_color, width=1.5, dash="dot"))
                    last_low = low_prices[idx]

        # --- 2. ADVANCED ICT METRICS ENGINE (MSS, BSL, SSL, BPR) ---
        if show_ict_metrics:
            if len(peaks) > 0:
                bsl_level = high_prices[peaks[-1]]
                fig.add_shape(type="line", x0=data.index[peaks[-1]], y0=bsl_level, x1=data.index[-1], y1=bsl_level, line=dict(color="#00ffcc", width=1.5, dash="dash"))
                fig.add_annotation(x=data.index[-1], y=bsl_level, text="BSL (Buyside Liquidity)", showarrow=False, font=dict(color="#00ffcc", size=9), xanchor="right", yanchor="bottom")
                
            if len(troughs) > 0:
                ssl_level = low_prices[troughs[-1]]
                fig.add_shape(type="line", x0=data.index[troughs[-1]], y0=ssl_level, x1=data.index[-1], y1=ssl_level, line=dict(color="#ff33aa", width=1.5, dash="dash"))
                fig.add_annotation(x=data.index[-1], y=ssl_level, text="SSL (Sellside Liquidity)", showarrow=False, font=dict(color="#ff33aa", size=9), xanchor="right", yanchor="top")

            # --- HIGH-PROBABILITY FILTERED MSS DETECTION ---
            # හුදෙක් ඉටිපන්දම් මාරුවක් නොවී, පෙර පැවති ප්‍රධාන Swing High/Low මට්ටම් පමණක් බිඳීම සලකා බලයි
            recent_highs = [high_prices[p] for p in peaks if p < len(data)]
            recent_lows = [low_prices[t] for t in troughs if t < len(data)]

            for idx in range(ob_distance, len(data)):
                # Bullish MSS: Price explicitly closes ABOVE the last valid strong swing high
                if len(recent_highs) > 0 and close_prices[idx] > recent_highs[-1] and close_prices[idx-1] <= recent_highs[-1]:
                    fig.add_annotation(
                        x=data.index[idx], y=high_prices[idx], 
                        text="⚡ MSS (Bullish Shift)", showarrow=True, arrowhead=1, arrowcolor="#00ffcc", 
                        font=dict(color="#00ffcc", size=9, family="Arial Black"), 
                        bgcolor="rgba(11, 14, 20, 0.9)", ay=-45
                    )
                    # එකම මට්ටම නැවත මාර්ක් වීම වැළැක්වීමට අගය අලුත් කරයි
                    recent_highs.append(high_prices[idx])
                
                # Bearish MSS: Price explicitly closes BELOW the last valid strong swing low
                elif len(recent_lows) > 0 and close_prices[idx] < recent_lows[-1] and close_prices[idx-1] >= recent_lows[-1]:
                    fig.add_annotation(
                        x=data.index[idx], y=low_prices[idx], 
                        text="⚡ MSS (Bearish Shift)", showarrow=True, arrowhead=1, arrowcolor="#ff3344", 
                        font=dict(color="#ff3344", size=9, family="Arial Black"), 
                        bgcolor="rgba(11, 14, 20, 0.9)", ay=45
                    )
                    recent_lows.append(low_prices[idx])
                
                # BPR Zone Detection
                if idx < len(data) - 2:
                    if low_prices[idx] > high_prices[idx+2] and high_prices[idx+1] < low_prices[idx]:
                        bpr_top = low_prices[idx]
                        bpr_bottom = high_prices[idx+2]
                        fig.add_shape(type="rect", x0=data.index[idx], y0=bpr_bottom, x1=data.index[-1], y1=bpr_top, fillcolor="rgba(255, 165, 0, 0.03)", line=dict(color="rgba(255, 165, 0, 0.2)", width=1, dash="dot"))
                        fig.add_annotation(x=data.index[-1], y=bpr_top, text="BPR Zone", showarrow=False, font=dict(color="orange", size=8), xanchor="right")

        # --- 3. WHOLE-CHART POI / ORDER BLOCK DETECTION ---
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
                        fig.add_shape(
                            type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top,
                            fillcolor=hex_to_rgba(bear_ob_color, ob_opacity), line=dict(color=bear_ob_color, width=1)
                        )
                        fig.add_annotation(x=data.index[p], y=ob_top, text="POI (Bearish OB)", showarrow=False, font=dict(color=bear_ob_color, size=8), yanchor="bottom")
                        
                        trade_table_data.append({
                            "Type": "🔴 POI / BEARISH OB",
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
                        end_idx = min(t + ob_length, len(data) - 1)
                        fig.add_shape(
                            type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top,
                            fillcolor=hex_to_rgba(bull_ob_color, ob_opacity), line=dict(color=bull_ob_color, width=1)
                        )
                        fig.add_annotation(x=data.index[t], y=ob_bottom, text="POI (Bullish OB)", showarrow=False, font=dict(color=bull_ob_color, size=8), yanchor="top")
                        
                        trade_table_data.append({
                            "Type": "🟢 POI / BULLISH OB",
                            "OB Zone (Top)": round(ob_top, 2),
                            "Entry / OB Bottom": round(ob_bottom, 2),
                            "Stop Loss (SL)": round(ob_bottom - (ob_top - ob_bottom) * 0.15, 2),
                            "Take Profit (TP)": round(round(ob_top, 2) + ((round(ob_top, 2) - round(ob_bottom - (ob_top - ob_bottom) * 0.15, 2)) * 3.0), 2),
                            "Risk:Reward": "1 : 3.0",
                            "OB Formed Date": data.index[t].strftime('%Y-%m-%d %H:%M')
                        })
                        
        fig.update_layout(
            title=f"{ticker} Live Chart | Premium ICT/SMC Analytics Engine",
            xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
            xaxis_rangeslider_visible=False, height=780, font=dict(color="#8a99ad"),
            margin=dict(t=30, b=10, l=10, r=50),
            
            yaxis=dict(
                title="Price", side="right", showgrid=True,
                gridcolor="rgba(42, 46, 57, 0.4)", ticks="outside", tickfont=dict(color="#8a99ad")
            ),
            xaxis=dict(showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)")
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # --- 4. ADVANCED SIGNAL TABLE ---
        st.markdown("---")
        st.write("### 📊 Active Institutional POIs & Premium Pending Setups")
        
        if trade_table_data:
            df_signals = pd.DataFrame(trade_table_data)
            df_signals = df_signals[["Type", "OB Formed Date", "OB Zone (Top)", "Entry / OB Bottom", "Stop Loss (SL)", "Take Profit (TP)", "Risk:Reward"]]
            st.dataframe(df_signals, use_container_width=True, hide_index=True)
            st.success(f"🔥 Chart analysis complete. Successfully identified {len(df_signals)} active (Unmitigated) POI Order Blocks.")
        else:
            st.info("⏳ No strong unmitigated Order Blocks found across the chart currently.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
