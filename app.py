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
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_pw_input")
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
        signup_email = st.text_input("Enter Your Email Address", key="signup_email_input")
        signup_password = st.text_input("Enter Password", type="password", key="signup_pw_input")
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
                    
                    max_price = float(data['Close'].max())
                    min_price = float(data['Close'].min())
                    avg_price = float(data['Close'].mean())
                    
                    fig.add_hline(y=max_price, line_dash="dash", line_color="green", annotation_text="Resistance")
                    fig.add_hline(y=min_price, line_dash="dash", line_color="red", annotation_text="Support")
                    fig.add_hline(y=avg_price, line_dash="dot", line_color="orange", annotation_text="Pivot")

                    fig.update_layout(
                        template="plotly_dark",
                        xaxis_rangeslider_visible=False,
                        height=550,
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
