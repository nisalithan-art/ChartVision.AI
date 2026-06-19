import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import plotly.graph_objects as go

st.set_page_config(
    page_title="ChartVision.AI Premium Pro Terminal", 
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
    div[data-baseweb="input"], div[data-baseweb="select"] {
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
    div[data-fragment-id] {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    [data-testid="stElementLoadingIndicator"], .stSpinner, [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }
    .js-plotly-plot .plotly .modebar {
        background-color: #1c2030 !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px !important;
        padding: 4px !important;
    }
    .js-plotly-plot .plotly .modebar-btn path {
        fill: #848e9c !important;
    }
    .js-plotly-plot .plotly .modebar-btn:hover path {
        fill: #26a69a !important;
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
    st.sidebar.write("### 🛠️ Core Algorithmic Indicators")
    show_sr = st.sidebar.toggle("🎯 Auto-Snap S&R Lines", value=True)
    show_trendlines = st.sidebar.toggle("📈 Auto-Trendlines & Breakouts", value=True)
    show_ob = st.sidebar.toggle("🛡️ Smart Money Order Blocks", value=True)
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("🎨 Custom Chart Styling Panel", expanded=False):
        c_bull = st.color_picker("Bullish Candle", value="#26a69a")
        c_bear = st.color_picker("Bearish Candle", value="#ef5350")
        c_res = st.color_picker("Resistance Vectors", value="#ef5350")
        c_sup = st.color_picker("Support Vectors", value="#26a69a")
        c_ob_bull = st.color_picker("Bullish OB Block Area", value="#00ffcc")
        c_ob_bear = st.color_picker("Bearish OB Block Area", value="#ff3366")

    st.sidebar.markdown("---")
    live_mode = st.sidebar.toggle("🔴 Streaming Engine Active", value=True)
    refresh_rate = 5 if live_mode else None

    @st.fragment(run_every=refresh_rate)
    def render_isolated_terminal(tk, tf, pr, s_sr, s_tl, s_ob, cbull, cbear, cres, csup, cob_bull, cob_bear):
        if not tk.strip():
            return

        chart_col, side_panel_col = st.columns([3.9, 1.1])

        try:
            data = yf.download(tk.strip(), period=pr, interval=tf, progress=False)
            if data is None or data.empty:
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

            if len(close_series) < 15:
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
                y=current_price, line_color=active_color, line_width=1.5, line_dash="dash",
                annotation_text=f" {current_price:,.2f} ", annotation_position="right",
                annotation_font=dict(color="#ffffff", size=11, family="Courier New", weight="bold"),
                annotation_bgcolor=active_color
            )

            lookback = min(len(close_series), 60)
            r1 = float(high_series.iloc[-lookback:].quantile(0.85))
            pivot = float(close_series.iloc[-lookback:].quantile(0.50))
            s1 = float(low_series.iloc[-lookback:].quantile(0.15))

            if s_sr:
                fig.add_hline(y=r1, line_dash="solid", line_color=cres, line_width=1, annotation_text="Resistance")
                fig.add_hline(y=pivot, line_dash="dot", line_color="rgba(255,153,0,0.3)", line_width=1)
                fig.add_hline(y=s1, line_dash="solid", line_color=csup, line_width=1, annotation_text="Support")

            if s_ob:
                ob_lookback = min(len(close_series), 60)
                for i in range(len(close_series) - 3, len(close_series) - ob_lookback, -1):
                    if close_series.iloc[i] < open_series.iloc[i]:
                        if close_series.iloc[i+1] > open_series.iloc[i+1] and close_series.iloc[i+2] > open_series.iloc[i+2]:
                            ob_low, ob_high = float(low_series.iloc[i]), float(high_series.iloc[i])
                            if not (low_series.iloc[i+1:] < ob_low).any():
                                fig.add_shape(type="rect", x0=close_series.index[i], y0=ob_low, x1=close_series.index[-1], y1=ob_high,
                                              fillcolor=hex_to_rgba(cob_bull, 0.1), line=dict(color=cob_bull, width=1, dash="dot"))
                                break
                for i in range(len(close_series) - 3, len(close_series) - ob_lookback, -1):
                    if close_series.iloc[i] > open_series.iloc[i]:
                        if close_series.iloc[i+1] < open_series.iloc[i+1] and close_series.iloc[i+2] < open_series.iloc[i+2]:
                            ob_low, ob_high = float(low_series.iloc[i]), float(high_series.iloc[i])
                            if not (high_series.iloc[i+1:] > ob_high).any():
                                fig.add_shape(type="rect", x0=close_series.index[i], y0=ob_low, x1=close_series.index[-1], y1=ob_high,
                                              fillcolor=hex_to_rgba(cob_bear, 0.1), line=dict(color=cob_bear, width=1, dash="dot"))
                                break

            time_delta = close_series.index[-1] - close_series.index[-2] if len(close_series) > 1 else pd.Timedelta(minutes=1)
            future_padding = close_series.index[-1] + (time_delta * 8)
            start_view = close_series.index[-min(len(close_series), 50)]

            fig.update_layout(
                template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722",
                xaxis_rangeslider_visible=False, height=650, margin=dict(l=10, r=10, t=10, b=10),
                uirevision=tk, 
                xaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", range=[start_view, future_padding]),
                yaxis=dict(gridcolor="#2a2e39", linecolor="#2a2e39", side="right"),
                newshape=dict(line_color="#26a69a", line_width=2, fillcolor="rgba(38, 166, 154, 0.1)")
            )

            delta = close_series.diff()
            gain = (delta.where(delta > 0, 0)).ewm(span=14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / (loss + 1e-10))))
            current_rsi = float(rsi.iloc[-1])

            with chart_col:
                st.markdown(f"<h2 style='margin:0; font-weight:600; color:#ffffff;'>📊 {tk} Custom Engine Workspace</h2>", unsafe_allow_html=True)
                st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    key="native_tv_canvas_core", 
                    config={
                        'scrollZoom': True,
                        'displaylogo': False,
                        'modeBarButtonsToAdd': [
                            'drawline',
                            'drawrect',
                            'drawcircle',
                            'eraseshape'
                        ],
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'zoom2d', 'pan2d'],
                        'displayModeBar': True
                    }
                )

            with side_panel_col:
                st.markdown("<h3 style='margin:0; font-weight:600; color:#ffffff;'>Market Tracker</h3>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="tv-panel">
                    <div style="font-size:15px; font-weight:bold; margin-bottom:10px; color:#ffffff;">Asset Status</div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Price Matrix</span><span class="tv-stat-value" style="color:{cbull if price_change >=0 else cbear};">{current_price:,.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Session Net %</span><span class="tv-stat-value" style="color:{cbull if price_change >=0 else cbear};">{price_change:+.2f}%</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Bar Volume</span><span class="tv-stat-value">{current_vol:,.0f}</span></div>
                </div>
                <div class="tv-panel">
                    <div style="font-size:14px; font-weight:bold; margin-bottom:10px; color:#ffffff;">Oscillators</div>
                    <div class="tv-stat-row"><span class="tv-stat-label">RSI (14)</span><span class="tv-stat-value">{current_rsi:.2f}</span></div>
                    <div class="tv-stat-row"><span class="tv-stat-label">Pivot Track</span><span class="tv-stat-value">{pivot:,.2f}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Render Matrix Failure: {e}")

    render_isolated_terminal(ticker, timeframe, period, show_sr, show_trendlines, show_ob, c_bull, c_bear, c_res, c_sup, c_ob_bull, c_ob_bear)
