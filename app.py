import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks
import sqlite3
import hashlib

# --- 1. DATABASE SETUP FOR LOGIN & FEEDBACK SYSTEM ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY, 
            password TEXT
        )
    ''')
    # Permanent Feedback Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            feedback_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_password):
    return make_hashes(password) == hashed_password

def add_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(email, password) VALUES (?,?)', (email, make_hashes(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def login_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE email = ?', (email,))
    data = c.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False

init_db()

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide", initial_sidebar_state="expanded")

# --- OPTIMIZED CSS & JAVASCRIPT ---
st.markdown("""
<style>
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}

[data-testid="stSidebar"] {
    visibility: visible !important;
    display: flex !important;
}
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: block !important;
    color: #00ffcc !important;
}

.stApp {background-color: #0b0e14; color: #ecf0f1; }
h1 {
    color: #00ffcc !important; 
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
    font-size: 22px !important; 
    margin-top: -20px !important; 
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
    padding-top: 2rem !important;
    padding-bottom: 0rem !important;
}
</style>

<script>
    function removeManageAppButton() {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.textContent && (btn.textContent.includes('Manage app') || btn.textContent.includes('Manage'))) {
                btn.remove();
            }
        });

        const viewerBadge = document.querySelector('.stViewerBadge');
        if (viewerBadge) viewerBadge.remove();
        
        const hosts = document.querySelectorAll('*');
        hosts.forEach(host => {
            if (host.shadowRoot) {
                const shadowButtons = host.shadowRoot.querySelectorAll('button');
                shadowButtons.forEach(sBtn => {
                    if (sBtn.textContent && (sBtn.textContent.includes('Manage app') || sBtn.textContent.includes('Manage'))) {
                        sBtn.remove();
                    }
                });
            }
        });
    }

    document.addEventListener('DOMContentLoaded', removeManageAppButton);
    setInterval(removeManageAppButton, 1000);

    document.addEventListener('contextmenu', function(event) { event.preventDefault(); });
    document.addEventListener('keydown', function(e) {
        if (e.keyCode === 123) { e.preventDefault(); return false; }
        if (e.ctrlKey && e.shiftKey && e.keyCode === 73) { e.preventDefault(); return false; }
        if (e.ctrlKey && e.shiftKey && e.keyCode === 74) { e.preventDefault(); return false; }
        if (e.ctrlKey && e.keyCode === 85) { e.preventDefault(); return false; }
        if (e.ctrlKey && e.shiftKey && e.keyCode === 67) { e.preventDefault(); return false; }
        if (e.ctrlKey && e.keyCode === 83) { e.preventDefault(); return false; }
    });
</script>
""", unsafe_allow_html=True)

# --- LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1>🔑 ChartVision Portal Authentication</h1>", unsafe_allow_html=True)
    menu = ["Login", "Sign Up"]
    choice = st.tabs(menu)
    
    with choice[0]:
        st.subheader("Login to your Account")
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_pass_input")
        if st.button("Login", use_container_width=True):
            if login_email and login_password:
                if login_user(login_email, login_password):
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email
                    st.success(f"Welcome back, {login_email}!")
                    st.rerun()
                else:
                    st.error("Invalid Email or Password.")
            else:
                st.warning("Please fill out all fields.")

    with choice[1]:
        st.subheader("Create a New Account")
        new_email = st.text_input("Enter Email Address", key="signup_email_input")
        new_password = st.text_input("Create Password", type="password", key="signup_pass_input")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_input")
        if st.button("Sign Up (Register)", use_container_width=True):
            if new_email and new_password and confirm_password:
                if new_password == confirm_password:
                    if add_user(new_email, new_password):
                        st.success("Account created successfully! Please switch to Login tab.")
                    else:
                        st.error("This Email is already registered!")
                else:
                    st.error("Passwords do not match!")
            else:
                st.warning("Please fill out all fields.")

    st.sidebar.markdown("### 🔒 System Locked")
    st.sidebar.info("Please login to activate the Pro Trader Toolbox controls.")

# --- MAIN APPLICATION ---
else:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.user_email}**")
    if st.sidebar.button("Logout 🚪"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()
        
    st.markdown("<h1>📈 Pro Trader Automated Chart Pattern & S&R Tool</h1>", unsafe_allow_html=True)
    st.markdown("<h3>SMC, ICT & Classic Chart Pattern Forecasting Engine - Ultra Edition</h3>", unsafe_allow_html=True)

    ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, EURUSD=X, AAPL):", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Select Timeframe:", ["1d", "4h", "2h", "1h", "30m", "15m", "5m"])
    period = st.sidebar.selectbox("Select Period (Data Range):", ["1y", "6mo", "3mo", "1mo", "7d", "1d"])
    leverage = st.sidebar.slider("Global Leverage (x)", 1, 125, 10, step=1)

    @st.cache_data
    def load_data(symbol, p, tf):
        try:
            df = yf.download(symbol, period=p, interval=tf, progress=False)
            return df
        except Exception:
            return pd.DataFrame()

    # --- LOADING DATA WITH SAFETY CHECK ---
    with st.spinner("🔄 Fetching market matrix from Yahoo Finance... Please wait."):
        data = load_data(ticker, period, timeframe)
    
    # මෙතනින් තමයි අර කරදරකාරී Errors ඔක්කොම වැලැක්වෙන්නේ
    if data is None or data.empty or 'Close' not in data.columns:
        st.warning("⚠️ Waiting for data synchronisation... If this message persists for more than 5 seconds, please check your Ticker symbol or try switching the Timeframe/Period combination.")
    else:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
            else:
                data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
                
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            open_prices = data['Open'].values
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("🎛️ Custom Settings")
            ob_distance = st.sidebar.slider("Pattern Detection Distance (Candles)", 3, 20, 7)
            ob_sensitivity = st.sidebar.slider("Sensitivity Multiplier", 0.05, 0.50, 0.10, step=0.05)
            ob_length = st.sidebar.slider("Order Block Box Length", 5, 100, 30)
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("🎯 Display Settings")
            liquidity_count = st.sidebar.slider("BSL / SSL Levels to Display", 1, 10, 3)
            show_eqh_eql = st.sidebar.checkbox("Show EQH / EQL (Equal Highs/Lows)", value=True)
            show_patterns = st.sidebar.checkbox("Show Chart Patterns", value=True)
            show_ob = st.sidebar.checkbox("Show Order Blocks & FVGs", value=True)
            st.sidebar.checkbox("Show BOS / CHoCH", value=True)
            st.sidebar.checkbox("Show MSS, BSL, SSL", value=True)
            
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
            
            def append_signal_raw(stype, date, entry, sl, tp, side, raw_idx):
                trade_table_data.append({
                    "Type": str(stype), 
                    "Signal Date": str(date), 
                    "Entry": float(round(entry, 2)),
                    "Stop Loss (SL)": float(round(sl, 2)), 
                    "Take Profit (TP)": float(round(tp, 2)),
                    "Side": str(side),
                    "raw_idx": raw_idx
                })

            # --- STRUCTURE ENGINE (CHoCH / BOS) ---
            last_high = high_prices[peaks[-1]] if len(peaks) > 0 else max(high_prices)
            last_low = low_prices[troughs[-1]] if len(troughs) > 0 else min(low_prices)
            structure_state = "IDLE" 

            for idx in range(20, len(data)):
                if close_prices[idx] > last_high and structure_state == "BEAR":
                    fig.add_annotation(x=data.index[idx], y=high_prices[idx], text="🔄 CHoCH (Bullish)", showarrow=True, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=-30)
                    sl_val = low_prices[idx-3:idx+1].min()
                    tp_val = close_prices[idx] + (close_prices[idx] - sl_val) * 2.5
                    append_signal_raw("🔄 CHoCH (Bullish)", data.index[idx].strftime('%Y-%m-%d %H:%M'), close_prices[idx], sl_val, tp_val, "LONG", idx)
                    structure_state = "BULL"
                elif close_prices[idx] < last_low and structure_state == "BULL":
                    fig.add_annotation(x=data.index[idx], y=low_prices[idx], text="🔄 CHoCH (Bearish)", showarrow=True, arrowcolor="#ff3344", font=dict(color="#ff3344", size=9, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)", ay=30)
                    sl_val = high_prices[idx-3:idx+1].max()
                    tp_val = close_prices[idx] - (sl_val - close_prices[idx]) * 2.5
                    append_signal_raw("🔄 CHoCH (Bearish)", data.index[idx].strftime('%Y-%m-%d %H:%M'), close_prices[idx], sl_val, tp_val, "SHORT", idx)
                    structure_state = "BEAR"
                
                if close_prices[idx] > last_high:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_high, x1=data.index[idx], y1=last_high, line=dict(color="#089981", width=1.5, dash="dot"))
                    last_high = high_prices[idx]
                    if structure_state == "IDLE": structure_state = "BULL"
                elif close_prices[idx] < last_low:
                    fig.add_shape(type="line", x0=data.index[idx-4], y0=last_low, x1=data.index[idx], y1=last_low, line=dict(color="#f23645", width=1.5, dash="dot"))
                    last_low = low_prices[idx]
                    if structure_state == "IDLE": structure_state = "BEAR"

            # --- ICT METRICS (MSS, BSL, SSL) ---
            liquidity_count = int(liquidity_count)
            display_peaks = peaks[-liquidity_count:] if len(peaks) >= liquidity_count else peaks
            display_troughs = troughs[-liquidity_count:] if len(troughs) >= liquidity_count else troughs

            for p_idx in display_peaks:
                fig.add_shape(type="line", x0=data.index[p_idx], y0=high_prices[p_idx], x1=data.index[-1], y1=high_prices[p_idx], line=dict(color="#00ffcc", width=1.2, dash="dash"))
            for t_idx in display_troughs:
                fig.add_shape(type="line", x0=data.index[t_idx], y0=low_prices[t_idx], x1=data.index[-1], y1=low_prices[t_idx], line=dict(color="#ff33aa", width=1.2, dash="dash"))

            for idx in range(ob_distance, len(data)):
                if len(peaks) > 0 and close_prices[idx] > high_prices[peaks[-1]] and close_prices[idx-1] <= high_prices[peaks[-1]]:
                    sl_val = low_prices[idx-4:idx+1].min()
                    tp_val = close_prices[idx] + (close_prices[idx] - sl_val) * 3.0
                    append_signal_raw("⚡ BULLISH MSS", data.index[idx].strftime('%Y-%m-%d %H:%M'), close_prices[idx], sl_val, tp_val, "LONG", idx)
                elif len(troughs) > 0 and close_prices[idx] < low_prices[troughs[-1]] and close_prices[idx-1] >= low_prices[troughs[-1]]:
                    sl_val = high_prices[idx-4:idx+1].max()
                    tp_val = close_prices[idx] - (sl_val - close_prices[idx]) * 3.0
                    append_signal_raw("⚡ BEARISH MSS", data.index[idx].strftime('%Y-%m-%d %H:%M'), close_prices[idx], sl_val, tp_val, "SHORT", idx)

            # --- EQH & EQL ---
            if show_eqh_eql and len(peaks) >= 2:
                for i in range(len(peaks)-1, max(0, len(peaks)-4), -1):
                    p1, p2 = peaks[i-1], peaks[i]
                    if (abs(high_prices[p1] - high_prices[p2]) / high_prices[p1]) < 0.005:
                        eqh_level = (high_prices[p1] + high_prices[p2]) / 2
                        fig.add_shape(type="line", x0=data.index[p1], y0=eqh_level, x1=data.index[-1], y1=eqh_level, line=dict(color="#ff4455", width=2, dash="dashdot"))
                        append_signal_raw("🔴 EQH Liquidity", data.index[p2].strftime('%Y-%m-%d %H:%M'), eqh_level, eqh_level * 1.008, eqh_level - (eqh_level * 0.008) * 3, "SHORT", p2)
                        break
            if show_eqh_eql and len(troughs) >= 2:
                for i in range(len(troughs)-1, max(0, len(troughs)-4), -1):
                    t1, t2 = troughs[i-1], troughs[i]
                    if (abs(low_prices[t1] - low_prices[t2]) / low_prices[t1]) < 0.005:
                        eql_level = (low_prices[t1] + low_prices[t2]) / 2
                        fig.add_shape(type="line", x0=data.index[t1], y0=eql_level, x1=data.index[-1], y1=eql_level, line=dict(color="#00ffaa", width=2, dash="dashdot"))
                        append_signal_raw("🟢 EQL Liquidity", data.index[t2].strftime('%Y-%m-%d %H:%M'), eql_level, eql_level * 0.992, eql_level + (eql_level * 0.008) * 3, "LONG", t2)
                        break

            # --- FVG DETECTION ---
            if show_ob:
                for i in range(2, len(data)):
                    if low_prices[i] > high_prices[i-2] and (close_prices[i-1] > open_prices[i-1]):
                        fvg_top, fvg_bottom = low_prices[i], high_prices[i-2]
                        if min(low_prices[i-1:]) >= fvg_bottom:
                            fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(0, 255, 204, 0.03)", line=dict(color="rgba(0, 255, 204, 0.15)", width=1))
                            append_signal_raw("🟢 FVG Buy Zone", data.index[i-1].strftime('%Y-%m-%d %H:%M'), fvg_top, fvg_bottom - (fvg_top - fvg_bottom)*0.5, fvg_top + (fvg_top - fvg_bottom)*3, "LONG", i-1)
                    elif high_prices[i] < low_prices[i-2] and (close_prices[i-1] < open_prices[i-1]):
                        fvg_top, fvg_bottom = low_prices[i-2], high_prices[i]
                        if max(high_prices[i-1:]) <= fvg_top:
                            fig.add_shape(type="rect", x0=data.index[i-2], y0=fvg_bottom, x1=data.index[-1], y1=fvg_top, fillcolor="rgba(255, 51, 68, 0.03)", line=dict(color="rgba(255, 51, 68, 0.15)", width=1))
                            append_signal_raw("🔴 FVG Sell Zone", data.index[i-1].strftime('%Y-%m-%d %H:%M'), fvg_bottom, fvg_top + (fvg_top - fvg_bottom)*0.5, fvg_bottom - (fvg_top - fvg_bottom)*3, "SHORT", i-1)

            # --- ORDER BLOCK DETECTION ---
            if show_ob:
                for p in peaks:
                    if p < len(data) - 2 and p > 0:
                        ob_top = float(high_prices[p])
                        ob_bottom = float(min(open_prices[p], close_prices[p]))
                        if max(high_prices[p+1:]) < ob_top:
                            end_idx = min(p + ob_length, len(data) - 1)
                            fig.add_shape(type="rect", x0=data.index[p-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(242, 54, 69, 0.05)", line=dict(color="#f23645", width=1))
                            sl_val = ob_top + (ob_top - ob_bottom) * 0.15
                            tp_val = ob_bottom - (sl_val - ob_bottom) * 3.0
                            append_signal_raw("🔴 Bearish OB", data.index[p].strftime('%Y-%m-%d %H:%M'), ob_bottom, sl_val, tp_val, "SHORT", p)
                            
                for t in troughs:
                    if t < len(data) - 2 and t > 0:
                        ob_bottom = float(low_prices[t])
                        ob_top = float(max(open_prices[t], close_prices[t]))
                        if min(low_prices[t+1:]) > ob_bottom:
                            end_idx = min(t + ob_length, len(data) - 1)
                            fig.add_shape(type="rect", x0=t - 1 if isinstance(t, int) else data.index[t-1], y0=ob_bottom, x1=data.index[end_idx], y1=ob_top, fillcolor="rgba(8, 153, 129, 0.05)", line=dict(color="#089981", width=1))
                            sl_val = ob_bottom - (ob_top - ob_bottom) * 0.15
                            tp_val = ob_top + (ob_top - sl_val) * 3.0
                            append_signal_raw("🟢 Bullish OB", data.index[t].strftime('%Y-%m-%d %H:%M'), ob_top, sl_val, tp_val, "LONG", t)

            # --- CLASSIC CHART PATTERNS ENGINE ---
            if show_patterns and len(peaks) >= 3 and len(troughs) >= 3:
                if abs(high_prices[peaks[-2]] - high_prices[peaks[-1]]) / high_prices[peaks[-2]] < 0.015:
                    fig.add_shape(type="line", x0=data.index[peaks[-2]], y0=high_prices[peaks[-2]], x1=data.index[peaks[-1]], y1=high_prices[peaks[-1]], line=dict(color="#ffaa00", width=3))
                    append_signal_raw("⚠️ Double Top", data.index[peaks[-1]].strftime('%Y-%m-%d'), high_prices[peaks[-1]], high_prices[peaks[-1]]*1.01, high_prices[peaks[-1]]*0.98, "SHORT", peaks[-1])
                if abs(low_prices[troughs[-2]] - low_prices[troughs[-1]]) / low_prices[troughs[-2]] < 0.015:
                    fig.add_shape(type="line", x0=data.index[troughs[-2]], y0=low_prices[troughs[-2]], x1=data.index[troughs[-1]], y1=low_prices[troughs[-1]], line=dict(color="#00aaff", width=3))
                    append_signal_raw("⚠️ Double Bottom", data.index[troughs[-1]].strftime('%Y-%m-%d'), low_prices[troughs[-1]], low_prices[troughs[-1]]*0.99, low_prices[troughs[-1]]*1.02, "LONG", troughs[-1])

            # --- INTERACTIVE SELECTED ROW / POSITION OVERLAY ENGINE ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("🎯 Active Trade Visualizer")
            
            position_duration = st.sidebar.slider("Projection Box Length (Candles)", 5, 150, 35)
            selected_signal_idx = st.sidebar.number_input("Select Signal Row Index from Table Below to Project Overlay:", min_value=0, max_value=max(0, len(trade_table_data)-1), value=0, step=1)
            
            if trade_table_data:
                df_base = pd.DataFrame(trade_table_data).drop_duplicates(subset=["Type", "Entry"]).sort_values(by="Signal Date", ascending=False).reset_index(drop=True)
                
                if selected_signal_idx < len(df_base):
                    target_row = df_base.iloc[selected_signal_idx]
                    t_entry = target_row["Entry"]
                    t_sl = target_row["Stop Loss (SL)"]
                    t_tp = target_row["Take Profit (TP)"]
                    t_side = target_row["Side"]
                    t_type = target_row["Type"]
                    start_candle_idx = int(target_row["raw_idx"])
                    
                    end_candle_idx = min(start_candle_idx + position_duration, len(data) - 1)
                    x0_date = data.index[start_candle_idx]
                    x1_date = data.index[end_candle_idx]
                    
                    if t_side == "LONG":
                        fig.add_shape(type="rect", x0=x0_date, y0=t_entry, x1=x1_date, y1=t_tp, fillcolor="rgba(8, 153, 129, 0.22)", line=dict(width=0))
                        fig.add_shape(type="rect", x0=x0_date, y0=t_sl, x1=x1_date, y1=t_entry, fillcolor="rgba(242, 54, 69, 0.22)", line=dict(width=0))
                        fig.add_shape(type="line", x0=x0_date, y0=t_entry, x1=x1_date, y1=t_entry, line=dict(color="#00ffcc", width=2))
                        fig.add_annotation(x=x1_date, y=t_tp, text=f"🎯 TP: {t_tp}", showarrow=False, xanchor="left", font=dict(color="#089981", size=11, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)")
                        fig.add_annotation(x=x1_date, y=t_sl, text=f"🛑 SL: {t_sl}", showarrow=False, xanchor="left", font=dict(color="#f23645", size=11, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)")
                        fig.add_annotation(x=x0_date, y=t_entry, text=f"🟢 LONG ({t_type})", showarrow=True, arrowcolor="#00ffcc", font=dict(color="#00ffcc", size=10), bgcolor="rgba(11,14,20,0.9)", ay=-40)
                    else:
                        fig.add_shape(type="rect", x0=x0_date, y0=t_tp, x1=x1_date, y1=t_entry, fillcolor="rgba(8, 153, 129, 0.22)", line=dict(width=0))
                        fig.add_shape(type="rect", x0=x0_date, y0=t_entry, x1=x1_date, y1=t_sl, fillcolor="rgba(242, 54, 69, 0.22)", line=dict(width=0))
                        fig.add_shape(type="line", x0=x0_date, y0=t_entry, x1=x1_date, y1=t_entry, line=dict(color="#ff3344", width=2))
                        fig.add_annotation(x=x1_date, y=t_tp, text=f"🎯 TP: {t_tp}", showarrow=False, xanchor="left", font=dict(color="#089981", size=11, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)")
                        fig.add_annotation(x=x1_date, y=t_sl, text=f"🛑 SL: {t_sl}", showarrow=False, xanchor="left", font=dict(color="#f23645", size=11, family="Arial Black"), bgcolor="rgba(11,14,20,0.9)")
                        fig.add_annotation(x=x0_date, y=t_entry, text=f"🔴 SHORT ({t_type})", showarrow=True, arrowcolor="#ff3344", font=dict(color="#ff3344", size=10), bgcolor="rgba(11,14,20,0.9)", ay=40)

            fig.update_layout(
                title=f"{ticker} Live Chart | Multi-Forecast Engine with Inline Matrix Customizer",
                xaxis_title="Date/Time", template="plotly_dark",
                paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
                xaxis_rangeslider_visible=False, height=600, font=dict(color="#8a99ad"),
                margin=dict(t=30, b=10, l=10, r=50),
                yaxis=dict(title="Price", side="right", showgrid=True, gridcolor="rgba(42, 46, 57, 0.4)", ticks="outside")
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- EDITABLE SIGNAL TABLE ---
            st.markdown("---")
            st.write("### 📊 Live Actionable Signals & Custom Risk Matrix Editor")
            st.info("💡 **How to see Position on Chart**: Look at the index number of any row in the table below, then input that number into the **'Active Trade Visualizer'** box inside the left Sidebar! You can also adjust its candle distance using the slider.")
            
            if trade_table_data:
                df_to_show = df_base.drop(columns=["raw_idx"], errors="ignore")
                
                if "df_editable" not in st.session_state or st.session_state.get("current_ticker") != ticker:
                    df_to_show["Account Balance ($)"] = 1000.0
                    df_to_show["Risk (%)"] = 1.0
                    st.session_state.df_editable = df_to_show.copy()
                    st.session_state.current_ticker = ticker
                
                edited_df = st.data_editor(
                    st.session_state.df_editable,
                    hide_index=False, 
                    use_container_width=True,
                    disabled=["Type", "Signal Date", "Entry", "Stop Loss (SL)", "Take Profit (TP)", "Side"], 
                    column_order=["Type", "Signal Date", "Entry", "Stop Loss (SL)", "Take Profit (TP)", "Account Balance ($)", "Risk (%)"]
                )
                
                st.session_state.df_editable = edited_df

                computed_rows = []
                for _, row in edited_df.iterrows():
                    entry = row["Entry"]
                    sl = row["Stop Loss (SL)"]
                    tp = row["Take Profit (TP)"]
                    bal = row["Account Balance ($)"]
                    r_pct = row["Risk (%)"]
                    
                    allowed_risk_usd = bal * (r_pct / 100.0)
                    price_diff_sl = abs(entry - sl)
                    price_diff_tp = abs(tp - entry)
                    
                    if price_diff_sl > 0:
                        position_size = allowed_risk_usd / price_diff_sl
                        total_position_value = position_size * entry
                        margin_required = total_position_value / leverage
                        expected_loss = price_diff_sl * position_size
                        expected_profit = price_diff_tp * position_size
                    else:
                        margin_required, position_size, expected_loss, expected_profit = 0, 0, 0, 0
                    
                    computed_rows.append({
                        "Type": row["Type"],
                        "Size (Units)": round(position_size, 4),
                        "Margin Required ($)": round(margin_required, 2),
                        "If Profit (TP Hit)": f"+${round(expected_profit, 2)}",
                        "If Loss (SL Hit)": f"-${round(expected_loss, 2)}"
                    })
                    
                df_final_display = pd.DataFrame(computed_rows)
                st.markdown("#### 🎯 Execution Plan Outputs (Calculated Live)")
                st.dataframe(df_final_display, use_container_width=True, hide_index=True)
            else:
                st.info("⏳ Scanning Matrix... No valid unmitigated entry conditions met on the immediate horizon.")

            # --- USER FEEDBACK SYSTEM (PERMANENT STORAGE VIA SQLITE) ---
            st.markdown("---")
            st.write("### 💬 Trader Feedback & Suggestions Hub")
            
            with st.form("feedback_form", clear_on_submit=True):
                user_name = st.text_input("Your Name / Alias:", placeholder="e.g., Anonymous Trader")
                feedback_text = st.text_area("Your Feedback / Feature Request:", placeholder="Write your thoughts or suggestion here...")
                submit_btn = st.form_submit_button("Submit Feedback")
                
                if submit_btn:
                    if feedback_text.strip() != "":
                        display_name = user_name.strip() if user_name.strip() != "" else "Anonymous Trader"
                        
                        # Database Insert Execution
                        conn = sqlite3.connect('users.db')
                        c = conn.cursor()
                        c.execute('INSERT INTO feedbacks (user_name, feedback_text) VALUES (?, ?)', (display_name, feedback_text.strip()))
                        conn.commit()
                        conn.close()
                        
                        st.success("Thank you! Your feedback has been saved permanently to the database.")
                        st.rerun()
                    else:
                        st.warning("Please write something before submitting.")
            
            st.markdown("#### Recent Community Feedback")
            
            # Fetch permanent rows from database
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('SELECT user_name, feedback_text FROM feedbacks ORDER BY id DESC')
            all_feedbacks = c.fetchall()
            conn.close()
            
            if all_feedbacks:
                for fb in all_feedbacks:
                    st.markdown(f"> **👤 {fb[0]}:** {fb[1]}")
            else:
                # Fallback placeholders when database table has 0 logs
                st.markdown("> **👤 AlphaTrader:** The live position size updater inside the table is incredibly fast. Love it!")
                st.markdown("> **👤 CryptoWhale:** Can you add an option for Trailing Stop Losses next?")

        except Exception as e:
            st.error(f"Something went wrong while compiling charts: {e}")
