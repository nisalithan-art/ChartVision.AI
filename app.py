import streamlit as st
import pandas as pd
import numpy as np
import json
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from supabase import create_client, Client
except ImportError:
    Client = None

st.set_page_config(
    page_title="ChartVision.AI Ultimate Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #131722 !important;
        color: #d1d4dc !important;
    }
    .top-bar-box {
        background-color: #1c2030;
        border-bottom: 1px solid #2a2e39;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .vertical-toolbar {
        background-color: #1c2030;
        border-right: 1px solid #2a2e39;
        padding: 10px;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        border-radius: 4px;
    }
    div[data-baseweb="select"], div[data-baseweb="input"] {
        background-color: #1e222d !important;
        border: 1px solid #2a2e39 !important;
        border-radius: 4px !important;
    }
    .stButton>button {
        background-color: #1e222d !important;
        color: #d1d4dc !important;
        border: 1px solid #2a2e39 !important;
        width: 100% !important;
        padding: 10px 5px !important;
    }
    .stButton>button:hover {
        border-color: #00ffcc !important;
        color: #00ffcc !important;
    }
    .delete-btn>div>button {
        border-color: #ef5350 !important;
        color: #ef5350 !important;
    }
    .analysis-box {
        background-color: #1e222d;
        border: 1px solid #00ffcc;
        border-radius: 8px;
        padding: 20px;
        margin-top: 15px;
    }
    html, body, [data-testid="stCanvasBlockContainer"] {
        background-color: #131722 !important;
    }
    </style>
""", unsafe_allow_html=True)

def init_supabase():
    if Client is not None and "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return None

try:
    supabase = init_supabase()
except Exception:
    supabase = None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'active_tool' not in st.session_state:
    st.session_state.active_tool = "Crosshair"

if not st.session_state.logged_in and supabase is not None:
    st.markdown("<h2 style='text-align: center; color: #ffffff;'>🔒 ChartVision.AI Secure Gateway</h2>", unsafe_allow_html=True)
    col_l, col_main, col_r = st.columns()
    with col_main:
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
        with tab1:
            login_email = st.text_input("Email Address", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_pw")
            if st.button("Log In Securely", use_container_width=True):
                try:
                    response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication Failed: {e}")
        with tab2:
            signup_email = st.text_input("Enter Email Address", key="signup_email")
            signup_password = st.text_input("Enter Password", type="password", key="signup_pw")
            if st.button("Register Account", use_container_width=True):
                try:
                    response = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                    st.success("Registration Successful!")
                except Exception as e:
                    st.error(f"Registration Failed: {e}")

else:
    with st.container():
        top_col1, top_col2, top_col3, top_col4, top_col5 = st.columns()
        
        with top_col1:
            coin_choose = st.selectbox("Coin Choose:", ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"])
        with top_col2:
            st.markdown(f"<p style='margin-top:4px; font-size:12px; color:#848e9c;'>Coin Name</p><h4 style='margin:0; color:#00ffcc;'>{coin_choose}</h4>", unsafe_allow_html=True)
        with top_col3:
            time_frame = st.selectbox("Time Frame:", ["1m", "5m", "15m", "1h", "1d"], index=0)
        with top_col4:
            indicator = st.selectbox("Indicator:", ["None Overlay", "Local S&R Edge Scanner (Upload Snapshot)", "Moving Average (EMA 20/50)"])
        with top_col5:
            choose_key = st.text_input("Choose Key:", value="Default_Core_Key", type="password")

    st.markdown("<hr style='margin:5px 0 15px 0; border-color:#2a2e39;'>", unsafe_allow_html=True)

    body_col_tools, body_col_chart = st.columns()

    with body_col_tools:
        st.markdown("<p style='font-size:11px; color:#848e9c; text-align:center; margin-bottom:10px;'>Tools</p>", unsafe_allow_html=True)
        if st.button("🖱️\n\nPoint"): st.session_state.active_tool = "Crosshair"
        if st.button("📈\n\nTrend"): st.session_state.active_tool = "Trendlines"
        if st.button("🤖\n\nAuto"): st.session_state.active_tool = "Auto"
        if st.button("🎯\n\nS & R"): st.session_state.active_tool = "S&R"
        if st.button("🧩\n\nPattrn"): st.session_state.active_tool = "Chart Pattern"
        
        for _ in range(5): st.write("")
        
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button("🗑️\n\nDel"):
            st.session_state.active_tool = "Crosshair"
            st.toast("Layout vectors flushed.")
        st.markdown('</div>', unsafe_allow_html=True)

    symbol_map = {
        "BTC-USD": "BTCUSDT", "ETH-USD": "ETHUSDT", 
        "SOL-USD": "SOLUSDT", "BNB-USD": "BNBUSDT", "XRP-USD": "XRPUSDT"
    }
    binance_symbol = symbol_map.get(coin_choose, "BTCUSDT")

    with body_col_chart:
        if indicator == "Local S&R Edge Scanner (Upload Snapshot)" and cv2 is not None:
            st.subheader("📷 Local Snapshot Edge Detector Canvas")
            uploaded_file = st.file_uploader("Upload static screenshot:", type=["png", "jpg", "jpeg"])
            if uploaded_file is not None:
                file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                img_bgr = cv2.imdecode(file_bytes, 1)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                row_sums = np.sum(edges, axis=1)
                h, w = gray.shape
                res_y = np.argmax(row_sums[int(h*0.2):int(h*0.5)]) + int(h*0.2)
                sup_y = np.argmax(row_sums[int(h*0.5):int(h*0.8)]) + int(h*0.5)
                cv2.line(img_bgr, (0, res_y), (w, res_y), (0, 0, 255), 3)
                cv2.line(img_bgr, (0, sup_y), (w, sup_y), (0, 255, 0), 3)
                st.image(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), use_container_width=True)
        else:
            st.markdown(f"<span style='color:#848e9c;'>Active Tool:</span> <b style='color:#00ffcc;'>{st.session_state.active_tool} Mode</b>", unsafe_allow_html=True)
            
            live_terminal_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/lightweight-charts/4.1.1/lightweight-charts.standalone.production.js"></script>
                <style>
                    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background-color: #131722 !important; overflow: hidden; }}
                    #chart_container {{ width: 100%; height: 620px; background-color: #131722; }}
                </style>
            </head>
            <body style="background-color: #131722;">
                <div id="chart_container"></div>
                <script>
                    const container = document.getElementById('chart_container');
                    const chart = LightweightCharts.createChart(container, {{
                        width: container.clientWidth,
                        height: 620,
                        layout: {{ background: {{ type: 'solid', color: '#131722' }}, textColor: '#d1d4dc', fontSize: 12 }},
                        grid: {{ vertLines: {{ color: '#1f222e' }}, horzLines: {{ color: '#1f222e' }} }},
                        priceScale: {{ borderColor: '#2a2e39' }},
                        timeScale: {{ borderColor: '#2a2e39', timeVisible: true }}
                    }});

                    const candleSeries = chart.addCandlestickSeries({{
                        upColor: '#26a69a', downColor: '#ef5350',
                        borderUpColor: '#26a69a', borderDownColor: '#ef5350',
                        wickUpColor: '#26a69a', wickDownColor: '#ef5350'
                    }});

                    const symbol = "{binance_symbol}";
                    const interval = "{time_frame}";

                    fetch(`https://api.binance.com/api/v3/klines?symbol=${{symbol}}&interval=${{interval}}&limit=500`)
                        .then(res => res.json())
                        .then(data => {{
                            const historicalData = data.map(d => ({{
                                time: d / 1000,
                                open: parseFloat(d),
                                high: parseFloat(d),
                                low: parseFloat(d),
                                close: parseFloat(d)
                            }}));
                            candleSeries.setData(historicalData);

                            const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${{symbol.toLowerCase()}}@kline_${{interval}}`);
                            ws.onmessage = (event) => {{
                                const message = JSON.parse(event.data);
                                const kline = message.k;
                                candleSeries.update({{
                                    time: kline.t / 1000,
                                    open: parseFloat(kline.o),
                                    high: parseFloat(kline.h),
                                    low: parseFloat(kline.l),
                                    close: parseFloat(kline.c)
                                }});
                            }};
                        }}).catch(err => console.error("Data Hub Connectivity Error: ", err));

                    window.addEventListener('resize', () => {{
                        chart.resize(container.clientWidth, 620);
                    }});
                </script>
            </body>
            </html>
            """
            import streamlit.components.v1 as components
            components.html(live_terminal_html, height=630, scrolling=False)
