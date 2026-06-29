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

# --- NEW: ADVANCED RISK CALCULATOR INPUTS ON SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Live Risk & Leverage Calculator")
account_balance = st.sidebar.number_input("Account Balance ($)", min_value=10.0, value=1000.0, step=50.0)
risk_percentage = st.sidebar.slider("Risk per Trade (%)", 0.25, 5.0, 1.0, step=0.25)
leverage = st.sidebar.slider("Leverage (x)", 1, 125, 10, step=1)

@st.cache_data
def load_data(symbol, p, tf):
    df = yf.download(symbol, period=p, interval=tf)
    return df

# Helper function to calculate risk metrics dynamically per signal
def calculate_trade_metrics(entry, sl, tp, direction="LONG"):
    allowed_risk_usd = account_balance * (risk_percentage / 100.0)
    
    # Calculate price change percentage for SL
    if direction == "LONG":
        price_diff_sl = entry - sl
        price_diff_tp = tp - entry
    else:
        price_diff_sl = sl - entry
        price_diff_tp = entry - tp
        
    if price_diff_sl <= 0:
        return 0, 0, 0, 0
        
    # Standard Position Sizing formula: Position Size = Risk Amount / SL Distance
    position_size = allowed_risk_usd / price_diff_sl
    total_position_value = position_size * entry
    
    # Margin Required based on Leverage
    margin_required = total_position_value / leverage
    
    # Expected Profit/Loss
    expected_loss = price_diff_sl * position_size
    expected_profit = price_diff_tp * position_size
    
    return round(margin_required, 2), round(position_size, 4), round(expected_loss, 2), round(expected_profit, 2)

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
        show_eqh_eql = st.sidebar.checkbox("Show EQH / EQL (Equal Highs/Lows)", value=True)
        show_patterns = st.sidebar.checkbox("Show Chart Patterns", value=True)
        show_ob = st.sidebar.checkbox("Show Order Blocks & FVGs", value=True)
        show_structure = st.sidebar.checkbox("Show BOS / CHoCH", value=True)
        show_ict_metrics = st.sidebar.checkbox("Show MSS, BSL, SSL", value=True)
        
        bull_body_color = "#089981"
        bear_body_color = "#f23645"
        
        peaks, _ = find_peaks(high_prices, distance=ob_distance, prominence=np.std(high_prices) * ob_sensitivity)
        troughs, _ = find_peaks(-low_prices, distance=ob_distance, prominence=np.std(low_prices) * ob_sensitivity)
        
        fig = go.Figure(data=[go.Candlestick(
            x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
            increasing_fillcolor=bull_body_color, increasing_line_color=bull_body_color,
            decreasing_fillcolor=bear_body_color, decreasing_line_color=bear_body_color,
            name="Candlesticks"
        )])
        
        trade_table_data = [] 
        
        # --- 1. BOS & CHoCH (STRUCTURE) ENGINE ---
        last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
        last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
        structure_state = "IDLE" 

        if show_structure:
            for idx in range(20, len(data)):
                if close_prices[idx] > last_high and structure_state == "BEAR":
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="🔄 CHoCH (Bullish)", showarrow=True, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=-30)
                    entry_v = close_prices[idx]
                    sl_val = low_prices[idx-3:idx+1].min()
                    tp_val = entry_v + (entry_v - sl_val) * 2.5
                    margin, p_size, loss, profit = calculate_trade_metrics(entry_v, sl_val, tp_val, "LONG")
                    trade_table_data.append({"Type": "🔄 CHoCH (Bullish)", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Entry": round(entry_v, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                    structure_state = "BULL"
                    
                elif close_prices[idx] < last_low and structure_state == "BULL":
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="🔄 CHoCH (Bearish)", showarrow=True, arrowcolor="#ff3344", font=dict(color="#ff3344", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=30)
                    entry_v = close_prices[idx]
                    sl_val = high_prices[idx-3:idx+1].max()
                    tp_val = entry_v - (sl_val - entry_v) * 2.5
                    margin, p_size, loss, profit = calculate_trade_metrics(entry_v, sl_val, tp_val, "SHORT")
                    trade_table_data.append({"Type": "🔄 CHoCH (Bearish)", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Entry": round(entry_v, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                    structure_state = "BEAR"
                
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_high, x1=data.index[idx], y1=last_high, line=dict(color="#089981", width=1.5, dash="dot"))
                    last_high = high_prices[idx]
                    if structure_state == "IDLE": structure_state = "BULL"
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_low, x1=data.index[idx], y1=last_low, line=dict(color="#f23645", width=1.5, dash="dot"))
                    last_low = low_prices[idx]
                    if structure_state == "IDLE": structure_state = "BEAR"

        # --- 2. BSL / SSL & MSS ENGINE ---
        if show_ict_metrics:
            display_peaks = peaks[-liquidity_count:] if len(peaks) >= liquidity_count else peaks
            display_troughs = troughs[-liquidity_count:] if len(troughs) >= liquidity_count else troughs

            for p_idx in display_peaks:
                fig.add_shape(type="line", x0=data.index[p_idx], y0=high_prices[p_idx], x1=data.index[-1], y1=high_prices[p_idx], line=dict(color="#00ffcc", width=1.2, dash="dash"))
            for t_idx in display_troughs:
                fig.add_shape(type="line", x0=data.index[t_idx], y0=low_prices[t_idx], x1=data.index[-1], y1=low_prices[t_idx], line=dict(color="#ff33aa", width=1.2, dash="dash"))

            for idx in range(ob_distance, len(data)):
                if len(peaks) > 0 and close_prices[idx] > high_prices[peaks[-1]] and close_prices[idx-1] <= high_prices[peaks[-1]]:
                    entry_v = close_prices[idx]
                    sl_val = low_prices[idx-4:idx+1].min()
                    tp_val = entry_v + (entry_v - sl_val) * 3.0
                    margin, p_size, loss, profit = calculate_trade_metrics(entry_v, sl_val, tp_val, "LONG")
                    trade_table_data.append({"Type": "⚡ BULLISH MSS", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Entry": round(entry_v, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                elif len(troughs) > 0 and close_prices[idx] < low_prices[troughs[-1]] and close_prices[idx-1] >= low_prices[troughs[-1]]:
                    entry_v = close_prices[idx]
                    sl_val = high_prices[idx-4:idx+1].max()
                    tp_val = entry_v - (sl_val - entry_v) * 3.0
                    margin, p_size, loss, profit = calculate_trade_metrics(entry_v, sl_val, tp_val, "SHORT")
                    trade_table_data.append({"Type": "⚡ BEARISH MSS", "Signal Date": data.index[idx].strftime('%Y-%m-%d %H:%M'), "Entry": round(entry_v, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})

        # --- 3. AUTO EQH & EQL LIQUIDITY DETECTOR ---
        if show_eqh_eql and len(peaks) >= 2:
            for i in range(len(peaks)-1, max(0, len(peaks)-4), -1):
                p1, p2 = peaks[i-1], peaks[i]
                diff = abs(high_prices[p1] - high_prices[p2]) / high_prices[p1]
                if diff < 0.005:
                    eqh_level = (high_prices[p1] + high_prices[p2]) / 2
                    fig.add_shape(type="line", x0=data.index[p1], y0=eqh_level, x1=data.index[-1], y1=eqh_level, line=dict(color="#ff4455", width=2, dash="dashdot"))
                    sl_val = eqh_level * 1.008
                    tp_val = eqh_level - (sl_val - eqh_level) * 3.0
                    margin, p_size, loss, profit = calculate_trade_metrics(eqh_level, sl_val, tp_val, "SHORT")
                    trade_table_data.append({"Type": "🔴 EQH Liquidity", "Signal Date": data.index[p2].strftime('%Y-%m-%d %H:%M'), "Entry": round(eqh_level, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                    break

        if show_eqh_eql and len(troughs) >= 2:
            for i in range(len(troughs)-1, max(0, len(troughs)-4), -1):
                t1, t2 = troughs[i-1], troughs[i]
                diff = abs(low_prices[t1] - low_prices[t2]) / low_prices[t1]
                if diff < 0.005:
                    eql_level = (low_prices[t1] + low_prices[t2]) / 2
                    fig.add_shape(type="line", x0=data.index[t1], y0=eql_level, x1=data.index[-1], y1=eql_level, line=dict(color="#00ffaa", width=2, dash="dashdot"))
                    sl_val = eql_level * 0.992
                    tp_val = eql_level + (eql_level - sl_val) * 3.0
                    margin, p_size, loss, profit = calculate_trade_metrics(eql_level, sl_val, tp_val, "LONG")
                    trade_table_data.append({"Type": "🟢 EQL Liquidity", "Signal Date": data.index[t2].strftime('%Y-%m-%d %H:%M'), "Entry": round(eql_level, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                    break

        # --- 4. VALID FVG (FAIR VALUE GAP) DETECTION ---
        if show_ob:
            for i in range(2, len(data)):
                if low_prices[i] > high_prices[i-2] and (close_prices[i-1] > open_prices[i-1]):
                    fvg_top, fvg_bottom = low_prices[i], high_prices[i-2]
                    if min(low_prices[i-1:]) >= fvg_bottom:
                        fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(0, 255, 204, 0.03)", line=dict(color="rgba(0, 255, 204, 0.15)", width=1))
                        sl_val = fvg_bottom - (fvg_top - fvg_bottom) * 0.5
                        tp_val = fvg_top + (fvg_top - sl_val) * 3.0
                        margin, p_size, loss, profit = calculate_trade_metrics(fvg_top, sl_val, tp_val, "LONG")
                        trade_table_data.append({"Type": "🟢 FVG Buy Zone", "Signal Date": data.index[i-1].strftime('%Y-%m-%d %H:%M'), "Entry": round(fvg_top, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})

                elif high_prices[i] < low_prices[i-2] and (close_prices[i-1] < open_prices[i-1]):
                    fvg_top, fvg_bottom = low_prices[i-2], high_prices[i]
                    if max(high_prices[i-1:]) <= fvg_top:
                        fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(255, 51, 68, 0.03)", line=dict(color="rgba(255, 51, 68, 0.15)", width=1))
                        sl_val = fvg_top + (fvg_top - fvg_bottom) * 0.5
                        tp_val = fvg_bottom - (sl_val - fvg_bottom) * 3.0
                        margin, p_size, loss, profit = calculate_trade_metrics(fvg_bottom, sl_val, tp_val, "SHORT")
                        trade_table_data.append({"Type": "🔴 FVG Sell Zone", "Signal Date": data.index[i-1].strftime('%Y-%m-%d %H:%M'), "Entry": round(fvg_bottom, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})

        # --- 5. VALID ORDER BLOCK DETECTION ---
        if show_ob:
            for p in peaks:
                if p < len(data) - 2:
                    ob_top, ob_bottom = high_prices[p], min(open_prices[p], close_prices[p])
                    if max(high_prices[p+1:]) < ob_top:
                        end_idx = min(p + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(242, 54, 69, 0.05)", line=dict(color="#f23645", width=1))
                        sl_val = ob_top + (ob_top - ob_bottom) * 0.15
                        tp_val = ob_bottom - (sl_val - ob_bottom) * 3.0
                        margin, p_size, loss, profit = calculate_trade_metrics(ob_bottom, sl_val, tp_val, "SHORT")
                        trade_table_data.append({"Type": "🔴 Bearish OB", "Signal Date": data.index[p].strftime('%Y-%m-%d %H:%M'), "Entry": round(ob_bottom, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
                        
            for t in troughs:
                if t < len(data) - 2:
                    ob_bottom, ob_top = low_prices[t], max(open_prices[t], close_prices[t])
                    if min(low_prices[t+1:]) > ob_bottom:
                        end_idx = min(t + ob_length, len(data) - 1)
                        fig.add_shape(type="rect", x0=data.index[t-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(8, 153, 129, 0.05)", line=dict(color="#089981", width=1))
                        sl_val = ob_bottom - (ob_top - ob_bottom) * 0.15
                        tp_val = ob_top + (ob_top - sl_val) * 3.0
                        margin, p_size, loss, profit = calculate_trade_metrics(ob_top, sl_val, tp_val, "LONG")
                        trade_table_data.append({"Type": "🟢 Bullish OB", "Signal Date": data.index[t].strftime('%Y-%m-%d %H:%M'), "Entry": round(ob_top, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})

        # --- 6. CLASSIC CHART PATTERNS ENGINE ---
        if show_patterns and len(peaks) >= 3 and len(troughs) >= 3:
            if abs(high_prices[peaks[-2]] - high_prices[peaks[-1]]) / high_prices[peaks[-2]] < 0.015:
                fig.add_shape(type="line", x0=data.index[peaks[-2]], y0=high_prices[peaks[-2]], x1=data.index[peaks[-1]], y1=high_prices[peaks[-1]], line=dict(color="#ffaa00", width=3))
                entry_p = high_prices[peaks[-1]]
                sl_val = entry_p * 1.01
                tp_val = entry_p - (sl_val - entry_p) * 2.0
                margin, p_size, loss, profit = calculate_trade_metrics(entry_p, sl_val, tp_val, "SHORT")
                trade_table_data.append({"Type": "⚠️ Double Top", "Signal Date": data.index[peaks[-1]].strftime('%Y-%m-%d'), "Entry": round(entry_p, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})
            if abs(low_prices[troughs[-2]] - low_prices[troughs[-1]]) / low_prices[troughs[-2]] < 0.015:
                fig.add_shape(type="line", x0=data.index[troughs[-2]], y0=low_prices[troughs[-2]], x1=data.index[troughs[-1]], y1=low_prices[troughs[-1]], line=dict(color="#00aaff", width=3))
                entry_p = low_prices[troughs[-1]]
                sl_val = entry_p * 0.99
                tp_val = entry_p + (entry_p - sl_val) * 2.0
                margin, p_size, loss, profit = calculate_trade_metrics(entry_p, sl_val, tp_val, "LONG")
                trade_table_data.append({"Type": "⚠️ Double Bottom", "Signal Date": data.index[troughs[-1]].strftime('%Y-%m-%d'), "Entry": round(entry_p, 2), "Stop Loss (SL)": round(sl_val, 2), "Take Profit (TP)": round(tp_val, 2), "Size (Units)": p_size, "Req. Margin ($)": margin, "If Profit ($)": f"+${profit}", "If Loss ($)": f"-${loss}"})

        # Display Chart
        fig.update_layout(
            title=f"{ticker} Live Chart | Multi-Forecast Engine with Live Risk Planner",
            xaxis_title="Date/Time", template="plotly_dark",
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
            xaxis_rangeslider_visible=False, height=700, font=dict(color="#8a99ad"),
            margin=dict(t=30, b=10, l=10, r=50),
            yaxis=dict(title="Price", side="right", showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)", ticks="outside")
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- 7. PREMIUM SIGNAL TABLE WITH RISK MANAGEMENT ---
        st.markdown("---")
        st.write("### 📊 Live Actionable Signals & Risk-Sizing Matrix")
        
        if trade_table_data:
            df_signals = pd.DataFrame(trade_table_data)
            df_signals = df_signals.drop_duplicates(subset=["Type", "Entry"]).sort_values(by="Signal Date", ascending=False)
            
            # Show all required trading variables dynamically
            st.dataframe(df_signals, use_container_width=True, hide_index=True)
            st.success(f"🎯 Sizing Calculated: Position values successfully formatted to risk exactly {risk_percentage}% of a ${account_balance} balance at {leverage}x leverage.")
        else:
            st.info("⏳ Scanning Matrix... No valid unmitigated entry conditions met on the immediate horizon.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
    
