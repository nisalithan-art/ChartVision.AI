import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import find_peaks
from supabase import create_client, Client

st.set_page_config(page_title="Pro Trader AI-Less Tool", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0b0e14; color: #ecf0f1; }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .stButton>button { background-color: #00ffcc; color: #0b0e14; font-weight: bold; width: 100%; border-radius: 5px; }
    .stButton>button:hover { background-color: #00cc99; color: #ffffff; }
    .feedback-box { background-color: #11151c; padding: 20px; border-radius: 10px; border: 1px solid #232a36; margin-top: 30px; }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ""
    
if not st.session_state['logged_in']:
    st.title("🔒 ChartVision.AI - Secure Login")
    st.subheader("Please Login or Sign Up to access the Pro Trading Tool")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up (Create Free Account)"])
    
    with tab1:
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_password_input")
        if st.button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = login_email
                st.success("Successfully Logged In! Redirecting...")
                st.rerun()
            except Exception as e:
                st.error(f"Login Failed: {e}")
                
    with tab2:
        signup_email = st.text_input("Enter Your Email Address", key="signup_email_input")
        signup_password = st.text_input("Create a Strong Password (Min 6 chars)", type="password", key="signup_password_input")
        if st.button("Create Account"):
            try:
                res = supabase.auth.sign_up({"email": signup_email, "password": signup_password})
                st.success("Account Created Successfully! You can now switch to the Login tab and log in.")
            except Exception as e:
                st.error(f"Sign Up Failed: {e}")

else:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state['user_email']}**")
    if st.sidebar.button("🚪 Log Out"):
        supabase.auth.sign_out()
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = ""
        st.rerun()

    st.title("📈 Pro Trader Automated Chart Pattern & S&R Tool")
    st.subheader("Pure Maths & Code - Premium Dark Edition")

    ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, EURUSD=X, AAPL):", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Select Timeframe:", ["1d", "1h", "15m", "5m"])
    period = st.sidebar.selectbox("Select Period (Data Range):", ["3mo", "1mo", "7d", "1d"])

    @st.cache_data
    def load_data(symbol, p, tf):
        df = yf.download(symbol, period=p, interval=tf)
        return df

    try:
        data = load_data(ticker, period, timeframe)
        
        if data.empty:
            st.error("No data found! Please check the Ticker symbol.")
        else:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col for col in data.columns]
            else:
                data.columns = [col if isinstance(col, tuple) else col for col in data.columns]
                
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values

            peaks, _ = find_peaks(high_prices, distance=10, prominence=np.std(high_prices)*0.2)
            troughs, _ = find_peaks(-low_prices, distance=10, prominence=np.std(low_prices)*0.2)

            fig = go.Figure(data=[go.Candlestick(
                x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
                increasing_line_color='#00ff66', decreasing_line_color='#ff3366', name="Candlesticks"
            )])

            for peak in peaks:
                fig.add_shape(type="line", x0=data.index, y0=high_prices[peak], x1=data.index[-1], y1=high_prices[peak],
                              line=dict(color="#ff3366", width=1.5, dash="dash"))

            for trough in troughs:
                fig.add_shape(type="line", x0=data.index, y0=low_prices[trough], x1=data.index[-1], y1=low_prices[trough],
                              line=dict(color="#00ff66", width=1.5, dash="dash"))

            fig.update_layout(
                title=f"{ticker} Live Chart with Auto S&R", yaxis_title="Price", xaxis_title="Date/Time",
                template="plotly_dark", paper_bgcolor='#11151c', plot_bgcolor='#11151c',
                xaxis_rangeslider_visible=False, height=650, font=dict(color="#8a99ad")
            )

            st.plotly_chart(fig, use_container_width=True)

            st.write("### 🔍 Detected Chart Patterns (Maths Engine)")
            detected_patterns = []
            for i in range(len(peaks)-1):
                p1, p2 = high_prices[peaks[i]], high_prices[peaks[i+1]]
                if abs(p1 - p2) / p1 < 0.005:
                    detected_patterns.append(f"⚠️ Potential **Double Top** detected near price {round(p1, 2)}")

            for i in range(len(troughs)-1):
                t1, t2 = low_prices[troughs[i]], low_prices[troughs[i+1]]
                if abs(t1 - t2) / t1 < 0.005:
                    detected_patterns.append(f"✅ Potential **Double Bottom** detected near price {round(t1, 2)}")

            if detected_patterns:
                for pattern in detected_patterns: st.info(pattern)
            else:
                st.success("No clear patterns detected at this moment. Market is moving smoothly.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")

    st.write("---")
    st.markdown('<div class="feedback-box">', unsafe_allow_html=True)
    st.write("### 💬 Share Your Feedback / Suggestions")
    st.write("Please let us know your valuable thoughts, suggestions, or any issues you found with this tool!")
    
    rating = st.slider("Rate this tool (Stars):", 1, 5, 5)
    comment = st.text_area("Write your feedback here...", placeholder="Type your review here...")
    
    if st.button("🚀 Submit Feedback"):
        if comment.strip():
            try:
                feedback_data = {
                    "email": st.session_state['user_email'],
                    "rating": rating,
                    "comment": comment
                }
                supabase.table("feedback").insert(feedback_data).execute()
                st.success("Thank you so much for your feedback! 🔥 It has been saved successfully.")
            except Exception as e:
                st.error(f"Could not save feedback: {e}")
        else:
            st.warning("Please enter some text before submitting!")
    st.markdown('</div>', unsafe_allow_html=True)
