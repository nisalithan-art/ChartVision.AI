import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

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
            st.caption("🎨 Interactive Mode: TradingView Zooming & Panning enabled.")
            
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

            current_price = float(close_series.iloc[-1])
            prev_price = float(close_series.iloc[-2])
            price_change = ((current_price - prev_price) / prev_price) * 100
            current_vol = float(volume_series.iloc[-1])

            lookback = min(len(close_series), 60)
            r2 = float(high_series.iloc[-lookback:].quantile(0.92))
            r1 = float(high_series.iloc[-lookback:].quantile(0.78))
            pivot = float(close_series.iloc[-lookback:].quantile(0.50))
            s1 = float(low_series.iloc[-lookback:].quantile(0.22))
            s2 = float(low_series.iloc[-lookback:].quantile(0.08))

            df_tv = pd.DataFrame({
                'time': close_series.index.astype(np.int64) // 10**9,
                'open': open_series.values,
                'high': high_series.values,
                'low': low_series.values,
                'close': close_series.values
            })

            chart_options = {
                "width": 900,
                "height": 620,
                "layout": {
                    "background": {"type": "solid", "color": "#131722"},
                    "textColor": "#d1d4dc",
                },
                "grid": {
                    "vertLines": {"color": "#2a2e39"},
                    "horzLines": {"color": "#2a2e39"},
                },
                "rightPriceScale": {
                    "borderColor": "#2a2e39",
                },
                "timeScale": {
                    "borderColor": "#2a2e39",
                    "timeVisible": True,
                    "secondsVisible": False
                },
            }

            series_list = [
                {
                    "type": "Candlestick",
                    "data": df_tv.to_dict(orient="records"),
                    "options": {
                        "upColor": cbull,
                        "downColor": cbear,
                        "borderUpColor": cbull,
                        "borderDownColor": cbear,
                        "wickUpColor": cbull,
                        "wickDownColor": cbear,
                    }
                }
            ]

            if s_sr:
                series_list["options"]["priceLines"] = [
                    {"price": r2, "color": cres, "lineStyle": 1, "axisLabelVisible": True, "title": "R2"},
                    {"price": r1, "color": cres, "lineStyle": 0, "axisLabelVisible": True, "title": "R1"},
                    {"price": pivot, "color": "rgba(255, 153, 0, 0.4)", "lineStyle": 2, "axisLabelVisible": True, "title": "Pivot"},
                    {"price": s1, "color": csup, "lineStyle": 0, "axisLabelVisible": True, "title": "S1"},
                    {"price": s2, "color": csup, "lineStyle": 1, "axisLabelVisible": True, "title": "S2"},
                ]

            delta = close_series.diff()
            gain = (delta.where(delta > 0, 0)).ewm(span=14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            current_rsi = float(rsi.iloc[-1])

            with chart_placeholder.container():
                renderLightweightCharts(charts=[{"otions": chart_options, "series": series_list}], key="tv_lightweight_canvas")

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
