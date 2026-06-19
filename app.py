import streamlit as st
import pandas as pd
import yfinance as yf
import json
from supabase import create_client, Client

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
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
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
    st.sidebar.write("### 🛠️ Proprietary Core Algorithmic Indicators")
    show_sr = st.sidebar.toggle("🎯 Auto-Snap S&R Lines", value=True)
    show_ob = st.sidebar.toggle("🛡️ Smart Money Order Blocks", value=True)
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("🎨 Custom Chart Styling Panel", expanded=False):
        c_bull = st.color_picker("Bullish Candle", value="#26a69a")
        c_bear = st.color_picker("Bearish Candle", value="#ef5350")
        c_res = st.color_picker("Resistance Vectors", value="#ef5350")
        c_sup = st.color_picker("Support Vectors", value="#26a69a")

    try:
        data = yf.download(ticker.strip(), period=period, interval=timeframe, progress=False)
        
        if data is not None and not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            df_clean = pd.DataFrame({
                'open': data['Open'],
                'high': data['High'],
                'low': data['Low'],
                'close': data['Close']
            }).dropna()

            df_clean['time'] = df_clean.index.astype('int64') // 10**9
            chart_records = df_clean[['time', 'open', 'high', 'low', 'close']].to_dict(orient='records')
            js_candles = json.dumps(chart_records)

            sr_data = {"res": 0.0, "sup": 0.0, "show": False}
            if show_sr and len(df_clean) > 20:
                sr_data["res"] = float(df_clean['high'].tail(50).max())
                sr_data["sup"] = float(df_clean['low'].tail(50).min())
                sr_data["show"] = True

            ob_data = {"top": 0.0, "bottom": 0.0, "show": False}
            if show_ob and len(df_clean) > 30:
                for i in range(len(df_clean) - 3, len(df_clean) - 30, -1):
                    if df_clean['close'].iloc[i] < df_clean['open'].iloc[i]:
                        if df_clean['close'].iloc[i+1] > df_clean['open'].iloc[i+1]:
                            ob_data["top"] = float(df_clean['high'].iloc[i])
                            ob_data["bottom"] = float(df_clean['low'].iloc[i])
                            ob_data["show"] = True
                            break

            st.markdown(f"<h2 style='margin:0 0 10px 0; font-weight:600; color:#ffffff;'>📊 {ticker} Custom In-House Terminal</h2>", unsafe_allow_html=True)

            custom_terminal_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background-color: #131722; overflow: hidden; }}
                    #custom_canvas {{ width: 100%; height: 680px; background-color: #131722; }}
                </style>
                <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
            </head>
            <body>
                <div id="custom_canvas"></div>
                <script>
                    const container = document.getElementById('custom_canvas');
                    const chart = LightweightCharts.createChart(container, {{
                        width: container.clientWidth,
                        height: 680,
                        layout: {{
                            background: {{ type: 'solid', color: '#131722' }},
                            textColor: '#d1d4dc',
                            fontSize: 12
                        }},
                        grid: {{
                            vertLines: {{ color: '#1f222e' }},
                            horzLines: {{ color: '#1f222e' }}
                        }},
                        crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                        priceScale: {{ borderColor: '#2a2e39' }},
                        timeScale: {{ borderColor: '#2a2e39', timeVisible: true }}
                    }});

                    const candleSeries = chart.addCandlestickSeries({{
                        upColor: '{c_bull}', downColor: '{c_bear}',
                        borderUpColor: '{c_bull}', borderDownColor: '{c_bear}',
                        wickUpColor: '{c_bull}', wickDownColor: '{c_bear}'
                    }});

                    const data = {js_candles};
                    candleSeries.setData(data);

                    const srInfo = {json.dumps(sr_data)};
                    if (srInfo.show) {{
                        candleSeries.createPriceLine({{ price: srInfo.res, color: '{c_res}', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'Resistance' }});
                        candleSeries.createPriceLine({{ price: srInfo.sup, color: '{c_sup}', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'Support' }});
                    }}

                    const obInfo = {json.dumps(ob_data)};
                    if (obInfo.show) {{
                        candleSeries.createPriceLine({{ price: obInfo.top, color: '#00ffcc', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true, title: 'OB Top' }});
                        candleSeries.createPriceLine({{ price: obInfo.bottom, color: '#00ffcc', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true, title: 'OB Bottom' }});
                    }}

                    window.addEventListener('resize', () => {{
                        chart.resize(container.clientWidth, 680);
                    }});
                </script>
            </body>
            </html>
            """
            import streamlit.components.v1 as components
            components.html(custom_terminal_html, height=690, scrolling=False)

    except Exception as e:
        st.error(f"Data Core Connection Failure: {e}")
