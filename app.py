import streamlit as st
import streamlit.components.v1 as components
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
    iframe {
        border: none !important;
        border-radius: 8px !important;
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
    raw_ticker = st.sidebar.text_input("Symbol Tracker (e.g., BTCUSD, AAPL):", value="BTCUSD").upper().strip()

    tf_option = st.sidebar.selectbox("Default Interval:", options=["1 Minute", "5 Minutes", "15 Minutes", "1 Hour", "Daily"], index=3)
    tf_map = {"1 Minute": "1", "5 Minutes": "5", "15 Minutes": "15", "1 Hour": "60", "Daily": "D"}
    selected_tf = tf_map[tf_option]

    if "BTC" in raw_ticker or "ETH" in raw_ticker:
        tv_symbol = f"BITSTAMP:{raw_ticker.replace('-','')}"
    elif "-" in raw_ticker:
        tv_symbol = raw_ticker.replace("-", "")
    else:
        tv_symbol = raw_ticker

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Pro-Tip:** Use Mouse Scroll Wheel or Pinch Trackpad inside the chart to smoothly Zoom. Drag axes or background to Pan. Drawings are saved automatically!")

    st.markdown(f"<h2 style='margin-bottom:10px; font-weight:600; color:#ffffff;'>📊 TradingView Live Advanced Canvas</h2>", unsafe_allow_html=True)

    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:100%; width:100%; background-color:#131722;">
        <div id="tradingview_advanced_core" style="height:100%; width:100%;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "width": "100%",
            "height": "100%",
            "symbol": "{tv_symbol}",
            "interval": "{selected_tf}",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "enable_publishing": false,
            "hide_side_toolbar": false, 
            "allow_symbol_change": true,
            "save_image": true,
            "backgroundColor": "#131722",
            "gridColor": "#2a2e39",
            "container_id": "tradingview_advanced_core",
            "watchlist": [
                "BITSTAMP:BTCUSD",
                "BITSTAMP:ETHUSD",
                "FX:EURUSD",
                "FX:GBPUSD"
            ],
            "details": true,
            "hotlist": true,
            "calendar": true,
            "studies": [
                "STD;RSI",
                "STD;Average_True_Range"
            ]
        }});
        </script>
    </div>
    """

    # Render Native Component inside fluid block container safely (No Rerun Flicker)
    components.html(tradingview_html, height=700, scrolling=False)

    # --- Live Feedback Desk Area ---
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
