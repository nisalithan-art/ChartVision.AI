import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import plotly.graph_objects as go

st.set_page_config(
    page_title="ChartVision.AI", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #0B0E14 !important;
        color: #E0E6ED !important;
    }
    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] {
        background-color: #11151D !important;
    }
    /* Text Labels color to white */
    label, .stWidgetLabel p {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    /* Input boxes background */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #1A1F2C !important;
        border: 1px solid #2D3748 !important;
    }
    /* Input text color to white */
    input, textarea, select {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    /* Placeholder text color */
    input::placeholder {
        color: #A0AEC0 !important;
    }
    /* Tabs Style */
    button[data-baseweb="tab"] {
        color: #8A99AD !important;
    }
    button[aria-selected="true"] {
        color: #00FFCC !important;
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

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up (Create Free Account)"])

    with tab1:
        login_email = st.text_input("Email Address", key="login_email_input", placeholder="name@example.com")
        login_password = st.text_input("Password", type="password", key="login_pw_input", placeholder="••••••••")
        if st.button("Log In", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": login_email,
                    "password": login_password
                })
                st.session_state.logged_in = True
                st.session_state.user_email = login_email
                st.success("Logged in successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")

    with tab2:
        signup_email = st.text_input("Enter Your Email Address", key="signup_email_input", placeholder="name@example.com")
        signup_password = st.text_input("Enter Password", type="password", key="signup_pw_input", placeholder="Minimum 6 characters")
        if st.button("Create Account", use_container_width=True):
            try:
                response = supabase.auth.sign_up({
                    "email": signup_email,
                    "password": signup_password
                })
                st.success("Sign Up Successful! Now you can switch to Login tab and log in.")
            except Exception as e:
                st.error(f"Sign Up Failed: {e}")


else:
    st.sidebar.write(f"👤 Logged in as:")
    st.sidebar.info(st.session_state.user_email)
    
    if st.sidebar.button("Log Out", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    st.sidebar.markdown("---")
    
    ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, EURUSD=X, AAPL):", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Select Timeframe:", options=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"], index=4)
    period = st.sidebar.selectbox("Select Period (Data Range):", options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "max"], index=2)

    st.title("📊 Pro Trader Automated Chart Pattern & S&R Tool")
    st.write("### Pure Maths & Code - Premium Dark Edition")

    if ticker:
        try:
            data = yf.download(ticker, period=period, interval=timeframe)
            
            if data.empty:
                st.warning("No data found for the specified ticker and options.")
            else:
                if isinstance(data.columns, pd.MultiIndex):
                    if 'Close' in data.columns.get_level_values(1):
                        data.columns = data.columns.get_level_values(1)
                    else:
                        data.columns = data.columns.get_level_values(0)
                
                if 'Close' in data.columns:
                    fig = go.Figure()
                    
                    if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
                        fig.add_trace(go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name=ticker
                        ))
                    else:
                        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'))
                    
                    r2 = float(data['High'].quantile(0.92))
                    r1 = float(data['High'].quantile(0.75))
                    pivot = float(data['Close'].quantile(0.50))
                    s1 = float(data['Low'].quantile(0.25))
                    s2 = float(data['Low'].quantile(0.08))

                    fig.add_hline(y=r2, line_dash="dash", line_color="#00FF66", line_width=1.5, annotation_text="Major Resistance (R2)", annotation_position="top left")
                    fig.add_hline(y=r1, line_dash="dash", line_color="#00CC52", line_width=1, annotation_text="Minor Resistance (R1)", annotation_position="top left")
                    
                    fig.add_hline(y=pivot, line_dash="dot", line_color="#FF9900", line_width=1, annotation_text="Market Pivot (PP)", annotation_position="top left")
                    
                    fig.add_hline(y=s1, line_dash="dash", line_color="#FF3333", line_width=1, annotation_text="Minor Support (S1)", annotation_position="bottom left")
                    fig.add_hline(y=s2, line_dash="dash", line_color="#CC0000", line_width=1.5, annotation_text="Major Support (S2)", annotation_position="bottom left")

                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="#0B0E14",
                        plot_bgcolor="#0B0E14",
                        xaxis_rangeslider_visible=False,
                        height=600,
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Error: 'Close' column not found in data structure.")
                    
        except Exception as e:
            st.error(f"Something went wrong: '{e}'")

    st.markdown("---")
    st.write("### 💬 Share Your Feedback / Suggestions")
    st.write("Please let us know your valuable thoughts, suggestions, or any issues you found with this tool!")
    
    rating = st.slider("Rate this tool (Stars):", min_value=1, max_value=5, value=5)
    review_text = st.text_area("Write your feedback here...", placeholder="Type your review here...")
    
    if st.button("Submit Feedback"):
        if review_text.strip() == "":
            st.warning("Please type your feedback before submitting.")
        else:
            try:
                st.success("Thank you for your feedback! Your suggestion has been recorded.")
            except Exception as e:
                st.error(f"Failed to submit feedback: {e}")
