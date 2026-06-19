import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="ChartVision.AI", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    .stApp {
        background-color: #0B0E14 !important;
        color: #E0E6ED !important;
    }
    [data-testid="stSidebar"] {
        background-color: #11151D !important;
    }
    label, .stWidgetLabel p {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #1A1F2C !important;
        border: 1px solid #2D3748 !important;
    }
    input, textarea, select {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .analysis-card {
        background-color: #11151D;
        border: 1px solid #1A1F2C;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    div[data-testid="stMetric"] {
        background-color: #11151D !important;
        border: 1px solid #1A1F2C !important;
        padding: 15px !important;
        border-radius: 8px !important;
    }
    
    /* --- STOP STREAMLIT REFRESH FLASHING --- */
    div[data-fragment-id] {
        opacity: 1 !important;
        filter: none !important;
    }
    [data-testid="stElementLoadingIndicator"], .stSpinner {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)


def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Supabase Connection Error: {e}")
    st.stop()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""


if not st.session_state.logged_in:
    st.title("🔒 ChartVision.AI - Secure Login")
    st.write("### Please Login or Sign Up to access the Pro Trading Tool")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_pw_input")
        if st.button("Log In", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                st.session_state.logged_in = True
                st.session_state.user_email = login_email
                st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")

    with tab2:
        signup_email = st.text_input("Enter Your Email Address", key="signup_email_input")
        signup_password = st.text_input("Enter Password", type="password", key="signup_pw_input")
        if st.button("Create Account", use_container_width=True):
            try:
                response = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                st.success("Sign Up Successful! Go to Login tab.")
            except Exception as e:
                st.error(f"Sign Up Failed: {e}")

else:
    st.sidebar.write(f"👤 Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Log Out", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    st.sidebar.markdown("---")
    
    ticker = st.sidebar.text_input("Enter Ticker:", value="BTC-USD", key="ticker_input_field")
    timeframe = st.sidebar.selectbox("Select Timeframe:", options=["1m", "5m", "15m", "30m", "1h", "1d"], index=3, key="tf_select_field") 
    period = st.sidebar.selectbox("Select Period:", options=["1d", "5d", "1mo", "3mo", "1y", "max"], index=2, key="pr_select_field")
    
    st.sidebar.markdown("---")
    st.sidebar.write("### 🛠️ Smart Money & Chart Tools")
    show_sr = st.sidebar.toggle("🎯 Auto-Snap S&R Lines", value=False)
    show_trendlines = st.sidebar.toggle("📈 Auto-Trendlines & Breakouts", value=False)
    show_ob = st.sidebar.toggle("🛡️ Unmitigated Order Blocks (OB)", value=False)
    show_fvg = st.sidebar.toggle("🕳️ Unfilled Fair Value Gaps (FVG)", value=False)
    
    st.sidebar.markdown("---")
    live_mode = st.sidebar.toggle("🔴 Live Market Update (Auto-Refresh)", value=True)
    refresh_rate = 10 if live_mode else None

    st.title("📊 ChartVision.AI - Smart Money Concepts Dashboard")
    st.write("### Toggle advanced institutional metrics and automated trend breakout markers from the sidebar.")

    live_ui_placeholder = st.empty()

    @st.fragment(run_every=refresh_rate)
    def render_smart_dashboard(tk, tf, pr, s_sr, s_tl, s_ob, s_fvg):
        if not tk.strip():
            return

        try:
            data = yf.download(tk.strip(), period=pr, interval=tf, progress=False)
            if data.empty:
                return

            def extract_ticker_series(df, col_name):
                if col_name in df.columns:
                    series_data = df[col_name]
                    return series_data.iloc[:, 0] if isinstance(series_data, pd.DataFrame) else series_data
                if isinstance(df.columns, pd.MultiIndex):
                    for col in df.columns:
                        if col_name in col:
                            series_data = df[col]
                            return series_data.iloc[:, 0] if isinstance(series_data, pd.DataFrame) else series_data
                return pd.Series(dtype=float)

            close_series = extract_ticker_series(data, 'Close').dropna()
            high_series = extract_ticker_series(data, 'High').dropna()
            low_series = extract_ticker_series(data, 'Low').dropna()
            open_series = extract_ticker_series(data, 'Open').dropna()

            if len(close_series) < 20:
                return

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=close_series.index, open=open_series, high=high_series, low=low_series, close=close_series, name=tk
            ))

            lookback = min(len(close_series), 60)
            r2 = float(high_series.iloc[-lookback:].quantile(0.92))
            r1 = float(high_series.iloc[-lookback:].quantile(0.78))
            pivot = float(close_series.iloc[-lookback:].quantile(0.50))
            s1 = float(low_series.iloc[-lookback:].quantile(0.22))
            s2 = float(low_series.iloc[-lookback:].quantile(0.08))

            if s_sr:
                fig.add_hline(y=r2, line_dash="dash", line_color="#00FF66", line_width=1.5, annotation_text=" R2 (Major Resistance)")
                fig.add_hline(y=r1, line_dash="solid", line_color="#00CC52", line_width=1, annotation_text=" R1 (Minor Resistance)")
                fig.add_hline(y=pivot, line_dash="dot", line_color="#FF9900", line_width=1, annotation_text=" PP (Pivot)")
                fig.add_hline(y=s1, line_dash="solid", line_color="#FF3333", line_width=1, annotation_text=" S1 (Minor Support)")
                fig.add_hline(y=s2, line_dash="dash", line_color="#CC0000", line_width=1.5, annotation_text=" S2 (Major Support Floor)")

            if s_tl:
                window = 10
                high_peaks = high_series[(high_series == high_series.rolling(window=window, center=True).max())].dropna()
                low_troughs = low_series[(low_series == low_series.rolling(window=window, center=True).min())].dropna()

                breakout_buys = []
                breakout_sells = []

                if len(high_peaks) >= 2:
                    p1_idx, p2_idx = high_peaks.index[-2], high_peaks.index[-1]
                    p1_val, p2_val = high_peaks.iloc[-2], high_peaks.iloc[-1]
                    
                    # Formulate trendline line formula: y = mx + c
                    x_vals = np.arange(len(close_series))
                    idx_map = {date: i for i, date in enumerate(close_series.index)}
                    
                    x1, x2 = idx_map[p1_idx], idx_map[p2_idx]
                    m = (p2_val - p1_val) / (x2 - x1)
                    c = p1_val - m * x1
                    
                    res_trend = m * x_vals + c
                    
                    fig.add_trace(go.Scatter(x=close_series.index[max(x1, 0):], y=res_trend[max(x1, 0):], line=dict(color="#FF00CC", width=1.5, dash="dash"), name="Resistance Trend"))

                    for i in range(x2 + 1, len(close_series)):
                        if close_series.iloc[i] > res_trend[i] and close_series.iloc[i-1] <= res_trend[i-1]:
                            breakout_buys.append(close_series.index[i])

                if len(low_troughs) >= 2:
                    t1_idx, t2_idx = low_troughs.index[-2], low_troughs.index[-1]
                    t1_val, t2_val = low_troughs.iloc[-2], low_troughs.iloc[-1]
                    
                    idx_map = {date: i for i, date in enumerate(close_series.index)}
                    x_vals = np.arange(len(close_series))
                    
                    x1, x2 = idx_map[t1_idx], idx_map[t2_idx]
                    m = (t2_val - t1_val) / (x2 - x1)
                    c = t1_val - m * x1
                    
                    sup_trend = m * x_vals + c
                    
                    fig.add_trace(go.Scatter(x=close_series.index[max(x1, 0):], y=sup_trend[max(x1, 0):], line=dict(color="#00FFFF", width=1.5, dash="dash"), name="Support Trend"))

                    for i in range(x2 + 1, len(close_series)):
                        if close_series.iloc[i] < sup_trend[i] and close_series.iloc[i-1] >= sup_trend[i-1]:
                            breakout_sells.append(close_series.index[i])

                if breakout_buys:
                    fig.add_trace(go.Scatter(x=breakout_buys, y=high_series.loc[breakout_buys] * 1.002, mode="markers", marker=dict(symbol="triangle-down", size=14, color="#00FF66"), name="Bullish Breakout"))
                if breakout_sells:
                    fig.add_trace(go.Scatter(x=breakout_sells, y=low_series.loc[breakout_sells] * 0.998, mode="markers", marker=dict(symbol="triangle-up", size=14, color="#FF3333"), name="Bearish Breakdown"))

            if s_ob:
                bullish_obs = []
                bearish_obs = []

                for i in range(len(close_series) - 3, max(1, len(close_series) - 50), -1):
                    if close_series.iloc[i] > open_series.iloc[i] and (close_series.iloc[i] - open_series.iloc[i]) > (high_series.iloc[i] - low_series.iloc[i]) * 0.5:
                        if close_series.iloc[i-1] < open_series.iloc[i-1]:
                            ob_low = low_series.iloc[i-1]
                            ob_high = high_series.iloc[i-1]

                            subsequent_lows = low_series.iloc[i:]
                            if not (subsequent_lows < ob_low).any():
                                bullish_obs.append((close_series.index[i-1], ob_low, ob_high))
                                if len(bullish_obs) >= 3: break # Limit to top 3 latest fresh zones

                for i in range(len(close_series) - 3, max(1, len(close_series) - 50), -1):
                    if close_series.iloc[i] < open_series.iloc[i] and (open_series.iloc[i] - close_series.iloc[i]) > (high_series.iloc[i] - low_series.iloc[i]) * 0.5:
                        if close_series.iloc[i-1] > open_series.iloc[i-1]:
                            ob_low = low_series.iloc[i-1]
                            ob_high = high_series.iloc[i-1]

                            subsequent_highs = high_series.iloc[i:]
                            if not (subsequent_highs > ob_high).any():
                                bearish_obs.append((close_series.index[i-1], ob_low, ob_high))
                                if len(bearish_obs) >= 3: break

                for ob in bullish_obs:
                    fig.add_shape(type="rect", x0=ob[0], y0=ob[1], x1=close_series.index[-1], y1=ob[2], fillcolor="rgba(0, 255, 102, 0.08)", line=dict(color="rgba(0, 255, 102, 0.3)", width=1))
                for ob in bearish_obs:
                    fig.add_shape(type="rect", x0=ob[0], y0=ob[1], x1=close_series.index[-1], y1=ob[2], fillcolor="rgba(255, 51, 51, 0.08)", line=dict(color="rgba(255, 51, 51, 0.3)", width=1))

            if s_fvg:
                for i in range(len(close_series) - 3):
                    if high_series.iloc[i] < low_series.iloc[i+2] and close_series.iloc[i+1] > open_series.iloc[i+1]:
                        gap_bottom = high_series.iloc[i]
                        gap_top = low_series.iloc[i+2]

                        future_lows = low_series.iloc[i+2:]
                        if not (future_lows <= gap_bottom).any():
                            fig.add_shape(type="rect", x0=close_series.index[i+1], y0=gap_bottom, x1=close_series.index[-1], y1=gap_top, fillcolor="rgba(0, 255, 204, 0.05)", line=dict(width=0))

                    if low_series.iloc[i] > high_series.iloc[i+2] and close_series.iloc[i+1] < open_series.iloc[i+1]:
                        gap_top = low_series.iloc[i]
                        gap_bottom = high_series.iloc[i+2]

                        future_highs = high_series.iloc[i+2:]
                        if not (future_highs >= gap_top).any():
                            fig.add_shape(type="rect", x0=close_series.index[i+1], y0=gap_bottom, x1=close_series.index[-1], y1=gap_top, fillcolor="rgba(255, 153, 0, 0.05)", line=dict(width=0))

            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#0B0E14", plot_bgcolor="#0B0E14",
                xaxis_rangeslider_visible=False, height=650, margin=dict(l=20, r=20, t=20, b=20),
                uirevision=tk
            )

            current_price = float(close_series.iloc[-1])
            prev_price = float(close_series.iloc[-2])
            price_change = ((current_price - prev_price) / prev_price) * 100

            with live_ui_placeholder.container():
                st.plotly_chart(fig, use_container_width=True, key="smc_dashboard_chart_canvas", config={'displaylogo': False, 'scrollZoom': True})

                st.markdown("---")
                st.write("## 🏛️ Smart Money Technical Matrix Data")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(label=f"Live {tk} Price", value=f"{current_price:,.2f}", delta=f"{price_change:+.2f}%")
                with col2:
                    st.metric(label="Structural Pivot Target", value=f"{pivot:,.2f}")
                with col3:
                    st.metric(label="Institutional Resistance (R1)", value=f"{r1:,.2f}")
                with col4:
                    st.metric(label="Institutional Support (S1)", value=f"{s1:,.2f}")
                
        except Exception as e:
            pass

    render_smart_dashboard(ticker, timeframe, period, show_sr, show_trendlines, show_ob, show_fvg)
