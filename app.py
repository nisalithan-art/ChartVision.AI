import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

st.set_page_config(
    page_title="ChartVision.AI Premium Pro Terminal", 
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
    [data-testid="stSidebar"] {
        background-color: #1c2030 !important;
        border-right: 1px solid #2a2e39 !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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
    tradingview_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            html, body {
                margin: 0;
                padding: 0;
                height: 100%;
                width: 100%;
                background-color: #131722;
                overflow: hidden;
            }
            #tv_terminal_container {
                height: 100vh;
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div id="tv_terminal_container"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
            new TradingView.widget({
                "width": "100%",
                "height": "100%",
                "symbol": "BITSTAMP:BTCUSD",
                "interval": "60",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "container_id": "tv_terminal_container",
                "watchlist": [
                    "BITSTAMP:BTCUSD",
                    "BITSTAMP:ETHUSD",
                    "COINBASE:BTCUSD",
                    "BINANCE:BTCUSDT"
                ],
                "details": true,
                "hotlist": true,
                "calendar": true,
                "studies": [
                    "STD;RSI"
                ]
            });
        </script>
    </body>
    </html>
    """
    
    components.html(tradingview_html, height=850, scrolling=False)
