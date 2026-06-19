import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="ChartVision.AI Premium Terminal", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #131722 !important;
        color: #d1d4dc !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1c2030 !important;
        border-right: 1px solid #2a2e39 !important;
    }
    label, .stWidgetLabel p {
        color: #848e9c !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="color-picker"] {
        background-color: #1e222d !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px !important;
    }
    .tv-panel {
        background-color: #1c2030;
        border: 1px solid #2a2e39;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .tv-stat-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #2a2e39;
        font-size: 13px;
    }
    .tv-stat-label {
        color: #787b86;
    }
    .tv-stat-value {
        color: #d1d4dc;
        font-weight: bold;
    }
    
    /* --- PREVENT REFRESH FLICKERING --- */
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

def hex_to_rgba(hex_str, opacity=0.1):
    hex_str = hex_str.lstrip('#')
    lv = len(hex_str)
    if lv == 6:
        rgb = tuple(int(hex_str[i:i + 2], 16) for i in range(0, 6, 2))
    else:
        rgb = (38, 166, 154)
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.title("🔒 ChartVision.AI - Secure Login")
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
                st.success("Sign Up Successful!")
            except Exception as e:
                st.error(f"Sign Up Failed: {e}")

else:
    st.sidebar.markdown(f"🟢 **Premium Active**<br><small style='color:#787b86;'>{st.session_state.user_email}</small>", unsafe_allow_html=True)
    if st.sidebar.button("Sign Out Terminal", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    st.sidebar.markdown("---")
    ticker = st.sidebar.text_input("Symbol:", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Interval:", options=["1m", "5m", "15m", "30m", "1h", "1d"], index=4) 
    period = st.sidebar.selectbox("Range:", options=["1d", "5d", "1mo", "3mo", "1y", "max"], index=2)
    
    st.sidebar.markdown("---")
    st.sidebar.write("### 🛠️ Chart Tools Activation")
    show_sr = st.sidebar.toggle("🎯 Auto-Snap S&R Lines", value=True)
    show_trendlines = st.sidebar.toggle("📈 Auto-Trendlines & Breakouts", value=True)
    show_ob = st.sidebar.toggle("🛡️ Smart Money Order Blocks", value=True)
    show_fvg = st.sidebar.toggle("🕳️ Fair Value Gaps (FVG)", value=False)
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("🎨 Chart Style Settings (Custom Colors)"):
        c_bull = st.color_picker("Bullish Candle Color", value="#26a69a")
        c_bear = st.color_picker("Bearish Candle Color", value="#ef5350")
        c_res = st.color_picker("Resistance Geometry Line", value="#ef5350")
        c_sup = st.color_picker("Support Geometry Line", value="#26a69a")
        c_ob_bull = st.color_picker("Bullish Order Block Base", value="#26a69a")
        c_ob_bear = st.color_picker("Bearish Order Block Base", value="#ef5350")

    st.sidebar.markdown("---")
    live_mode = st.sidebar.toggle("🔴 Live Streaming Updates", value=True)

    refresh_rate = 2 if live_mode else None

    chart_col, side_panel_col = st.columns([3.8, 1.2])

    with chart_col:
        st.markdown(f"<h2 style='margin:0; font-weight:600; color:#ffffff;'>📊 {ticker} Live Terminal Space</h2>", unsafe_allow_html=True)
        if live_mode:
            st.caption("⚡ Turbo Live Stream Engine Active (2s updates). Turn off to freeze custom drawing state.")
        else:
            st.caption("🎨 Interactive Mode: Grab edges to extend custom geometric structures manually.")
            
        chart_placeholder = st.empty()

    with side_panel_col:
        st.markdown("<h3 style='margin:0; font-weight:600; color:#ffffff;'>Watchlist & Stats</h3>", unsafe_allow_html=True)
        panel_placeholder = st.empty()

    @st.fragment(run_every=refresh_rate)
    def update_terminal_matrix(tk, tf, pr, s_sr, s_tl, s_ob, s_fvg, cbull, cbear, cres, csup, cob_bull, cob_bear):
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
            volume_series = extract_ticker_series(data, 'Volume').dropna()

            if len(close_series) < 20:
                return

            fig = go.Figure()
            
            fig.add_trace(go.Candlestick(
                x=close_series.index, open=open_series, high=high_series, low=low_series, close=close_series,
                name=tk, increasing_line_color=cbull, decreasing_line_color=cbear,
                increasing_fillcolor=cbull, decreasing_fillcolor=cbear
            ))

            current_price = float(close_series.iloc[-1])
            prev_price = float(close_series.iloc[-2])
            price_change = ((current_price - prev_price) / prev_price) * 100
            current_vol = float(volume_series.iloc[-1])

            active_color = cbull if current_price >= open_series.iloc[-1] else cbear
            fig.add_hline(
                y=current_price, 
                line_color=active_color, 
                line_width=1.2, 
                line_dash="dash",
                annotation_text=f" {current_price:,.2f} ",
                annotation_position="right",
                annotation_font=dict(color="#ffffff", size=11, family="Courier New"),
                annotation_bgcolor=active_color
            )

            lookback = min(len(close_series), 60)
            r2 = float(high_series.iloc[-lookback:].quantile(0.92))
            r1 = float(high_series.iloc[-lookback:].quantile(0.78))
            pivot = float(close_series.iloc[-lookback:].quantile(0.50))
            s1 = float(low_series.iloc[-lookback:].quantile(0.22))
            s2 = float(low_series.iloc[-lookback:].quantile(0.08))

            if s_sr:
                fig.add_hline(y=r2, line_dash="dash", line_color=cres, line_width=1, annotation_text="R2")
                fig.add_hline(y=r1, line_dash="solid", line_color=cres, line_width=0.8, annotation_text="R1")
                fig.add_hline(y=pivot, line_dash="dot", line_color="rgba(255, 153, 0, 0.4)", line_width=1)
                fig.add_hline(y=s1, line_dash="solid", line_color=csup, line_width=0.8, annotation_text="S1")
                fig.add_hline(y=s2, line_dash="dash", line_color=csup, line_width=1, annotation_text="S2")

            if s_tl:
                window = 10
                high_peaks = high_series[(high_series == high_series.rolling(window=window, center=True).max())].dropna()
                low_troughs = low_series[(low_series == low_series.rolling(window=window, center=True).min())].dropna()
                breakout_buys = []
                breakout_sells = []

                if len(high_peaks) >= 2:
                    p1_idx, p2_idx = high_peaks.index[-2], high_peaks.index[-1]
                    x_vals = np.arange(len(close_series))
                    idx_map = {date: i for i, date in enumerate(close_series.index)}
                    x1, x2 = idx_map[p1_idx], idx_map[p2_idx]
                    m = (high_peaks.iloc[-1] - high_peaks.iloc[-2]) / (x2 - x1)
                    c = high_peaks.iloc[-2] - m * x1
                    res_trend = m * x_vals + c
                    fig.add_trace(go.Scatter(x=close_series.index[max(x1, 0):], y=res_trend[max(x1, 0):], line=dict(color=cres, width=1.2, dash="dash"), name="Trend Resistance"))
                    
                    for i in range(x2 + 1, len(close_series)):
                        if close_series.iloc[i] > res_trend[i] and close_series.iloc[i-1] <= res_trend[i-1]:
                            breakout_buys.append(close_series.index[i])

                if len(low_troughs) >= 2:
                    t1_idx, t2_idx = low_troughs.index[-2], low_troughs.index[-1]
                    idx_map = {date: i for i, date in enumerate(close_series.index)}
                    x_vals = np.arange(len(close_series))
                    x1, x2 = idx_map[t1_idx], idx_map[t2_idx]
                    m = (low_troughs.iloc[-1] - low_troughs.iloc[-2]) / (x2 - x1)
                    c = low_troughs.iloc[-2] - m * x1
                    sup_trend = m * x_vals + c
                    fig.add_trace(go.Scatter(x=close_series.index[max(x1, 0):], y=sup_trend[max(x1, 0):], line=dict(color=csup, width=1.2, dash="dash"), name="Trend Support"))

                    for i in range(x2 + 1, len(close_series)):
                        if close_series.iloc[i] < sup_trend[i] and close_series.iloc[i-1] >= sup_trend[i-1]:
                            breakout_sells.append(close_series.index[i])

                if breakout_buys:
                    fig.add_trace(go.Scatter(x=breakout_buys, y=high_series.loc[breakout_buys] * 1.002, mode="markers", marker=dict(symbol="triangle-down", size=12, color=cbull), showlegend=False))
                if breakout_sells:
                    fig.add_trace(go.Scatter(x=breakout_sells, y=low_series.loc[breakout_sells] * 0.998, mode="markers", marker=dict(symbol="triangle-up", size=12, color=cbear), showlegend=False))

            if s_ob:
                bullish_obs = []
                bearish_obs = []
                for i in range(len(close_series) - 3, max(1, len(close_series) - 50), -1):
                    if close_series.iloc[i] > open_series.iloc[i] and (close_series.iloc[i] - open_series.iloc[i]) > (high_series.iloc[i] - low_series.iloc[i]) * 0.5:
                        if close_series.iloc[i-1] < open_series.iloc[i-1]:
                            ob_l, ob_h = low_series.iloc[i-1], high_series.iloc[i-1]
                            if not (low_series.iloc[i:] < ob_l).any():
                                bullish_obs.append((close_series.index[i-1], ob_l, ob_h))
                                if len(bullish_obs) >= 2: break

                for ob in bullish_obs:
                    fig.add_shape(type="rect", x0=ob[0], y0=ob[1], x1=close_series.index[-1], y1=ob[2], fillcolor=hex_to_rgba(cob_bull, 0.08), line=dict(color=cob_bull, width=1))

            time_delta = close_series.index[-1] - close_series.index[-2] if len(close_series) > 1 else pd.Timedelta(minutes=1)
            future_padding_end = close_series.index[-1] + (time_delta * 8) # Adds 8 bars worth of blank timeline space to the right
            start_visible_view = close_series.index[-min(len(close_series), 45)]

            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722",
                xaxis_rangeslider_visible=False, height=620, margin=dict(l=10, r=10, t=10, b=10),
                uirevision=tk,
                xaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", range=[start_visible_view, future_padding_end]),
                yaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", side="right")
            )

            delta = close_series.diff()
            gain = (delta.where(delta > 0, 0)).ewm(span=14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            current_rsi = float(rsi.iloc[-1])

            with chart_placeholder.container():
                st.plotly_chart(fig, use_container_width=True, key="tv_custom_canvas", config={'editable': True, 'displaylogo': False, 'scrollZoom': True})

            with panel_placeholder.container():
                st.markdown(f"""
                <div class="tv-panel">
                    <div style="font-size:16px; font-weight:bold; margin-bottom:10px; color:#ffffff;">{tk} Live Feed</div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Last Price</span><span class="tv-stat-value" style="color:{cbull if price_change >=0 else cbear};">{current_price:,.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Change %</span><span class="tv-stat-value" style="color:{cbull if price_change >=0 else cbear};">{price_change:+.2f}%</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Volume (Bar)</span><span class="tv-stat-value">{current_vol:,.0f}</span></div>
                </div>
                
                <div class="tv-panel">
                    <div style="font-size:14px; font-weight:bold; margin-bottom:10px; color:#ffffff;">Key Matrix Stats</div>
                    <div class="tv-stat-row"><span class="tv-stat-label">RSI (14)</span><span class="tv-stat-value">{current_rsi:.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Pivot Point</span><span class="tv-stat-value">{pivot:,.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Resistance R1</span><span class="tv-stat-value" style="color:{cbull};">{r1:,.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Support S1</span><span class="tv-stat-value" style="color:{cbear};">{s1:,.2f}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            pass

    update_terminal_matrix(ticker, timeframe, period, show_sr, show_trendlines, show_ob, show_fvg, c_bull, c_bear, c_res, c_sup, c_ob_bull, c_ob_bear)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💬 Submit Developer Bug Report / Feature Request Desk"):
        with st.form("tv_feedback_form", clear_on_submit=True):
            user_msg = st.text_area("Request Additional Terminal Feature Modifications:")
            if st.form_submit_button("Send to Database Master Line"):
                if user_msg.strip():
                    try:
                        supabase.table("feedback").insert({"email": st.session_state.user_email, "message": user_msg.strip()}).execute()
                        st.success("Matrix Logged! Your terminal feature request has been securely transmitted.")
                    except Exception as e:
                        st.error(f"Transmission failed: {e}")
