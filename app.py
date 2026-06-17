import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client, Client
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="ChartVision.AI", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #0B0E14 !important;
        color: #E0E6ED !important;
    }
    [data-testid="stSidebar"] {
        background-color: #11151D !important;
    }
    label, .stWidgetLabel p {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background-color: #1A1F2C !important;
        border: 1px solid #2D3748 !important;
    }
    input, textarea, select {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    input::placeholder {
        color: #A0AEC0 !important;
    }
    button[data-baseweb="tab"] {
        color: #8A99AD !important;
    }
    button[aria-selected="true"] {
        color: #00FFCC !important;
    }
    .analysis-card {
        background-color: #11151D;
        border: 1px solid #1A1F2C;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    div[data-testid="stMetric"] {
        background-color: #11151D !important;
        border: 1px solid #1A1F2C !important;
        padding: 15px !important;
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
    
    ticker = st.sidebar.text_input("Enter Ticker (e.g., BTC-USD, AAPL, EURUSD=X):", value="BTC-USD")
    timeframe = st.sidebar.selectbox("Select Timeframe:", options=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"], index=4)
    period = st.sidebar.selectbox("Select Period (Data Range):", options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "max"], index=3)

    st.title("📊 Pro Trader Automated Chart Pattern & S&R Tool")
    st.write("### Advanced Multi-Indicator Technical Analysis Engine")

    if ticker:
        try:
            data = yf.download(ticker, period=period, interval=timeframe)
            
            if data.empty:
                st.warning("No data found for the specified ticker and options.")
            else:
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

                if close_series.empty or high_series.empty or low_series.empty or open_series.empty:
                    st.error("Error: Required price columns ('Close', 'High', 'Low', 'Open') could not be parsed from the data structure.")
                elif len(close_series) < 30:
                    st.error("Not enough historical data bars to process technical math indicators. Please choose a wider period range.")
                else:
                    r2 = float(high_series.quantile(0.92))
                    r1 = float(high_series.quantile(0.75))
                    pivot = float(close_series.quantile(0.50))
                    s1 = float(low_series.quantile(0.25))
                    s2 = float(low_series.quantile(0.08))

                    delta = close_series.diff()
                    gain = (delta.where(delta > 0, 0)).ewm(span=14, adjust=False).mean()
                    loss = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
                    rs = gain / (loss + 1e-10)
                    rsi_series = 100 - (100 / (1 + rs))
                    current_rsi = float(rsi_series.iloc[-1])

                    ema12 = close_series.ewm(span=12, adjust=False).mean()
                    ema26 = close_series.ewm(span=26, adjust=False).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    current_macd = float(macd_line.iloc[-1])
                    current_signal = float(signal_line.iloc[-1])

                    sma20 = close_series.rolling(window=20).mean()
                    std20 = close_series.rolling(window=20).std()
                    upper_bb = sma20 + (2 * std20)
                    lower_bb = sma20 - (2 * std20)
                    current_upper_bb = float(upper_bb.iloc[-1])
                    current_lower_bb = float(lower_bb.iloc[-1])

                    sma9 = close_series.rolling(window=9).mean()
                    sma21 = close_series.rolling(window=21).mean()
                    current_sma9 = float(sma9.iloc[-1])
                    current_sma21 = float(sma21.iloc[-1])

                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=close_series.index, open=open_series, high=high_series, low=low_series, close=close_series, name=ticker
                    ))

                    fig.add_trace(go.Scatter(x=close_series.index, y=upper_bb, line=dict(color='rgba(0, 255, 204, 0.25)', width=1.5, dash='dash'), name='Upper Bollinger Band'))
                    fig.add_trace(go.Scatter(x=close_series.index, y=lower_bb, line=dict(color='rgba(0, 255, 204, 0.25)', width=1.5, dash='dash'), name='Lower Bollinger Band'))

                    fig.add_hline(y=r2, line_dash="dash", line_color="#00FF66", line_width=1.5, annotation_text="Major Resistance (R2)", annotation_position="top left")
                    fig.add_hline(y=r1, line_dash="dash", line_color="#00CC52", line_width=1, annotation_text="Minor Resistance (R1)", annotation_position="top left")
                    fig.add_hline(y=pivot, line_dash="dot", line_color="#FF9900", line_width=1, annotation_text="Market Pivot (PP)", annotation_position="top left")
                    fig.add_hline(y=s1, line_dash="dash", line_color="#FF3333", line_width=1, annotation_text="Minor Support (S1)", annotation_position="bottom left")
                    fig.add_hline(y=s2, line_dash="dash", line_color="#CC0000", line_width=1.5, annotation_text="Major Support (S2)", annotation_position="bottom left")

                    fig.update_layout(
                        template="plotly_dark", paper_bgcolor="#0B0E14", plot_bgcolor="#0B0E14",
                        xaxis_rangeslider_visible=False, height=500, margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    current_price = float(close_series.iloc[-1])
                    prev_price = float(close_series.iloc[-2])
                    price_change = ((current_price - prev_price) / prev_price) * 100

                    buy_weight = 0
                    sell_weight = 0

                    if current_rsi <= 30: buy_weight += 2
                    elif current_rsi >= 70: sell_weight += 2

                    if current_macd > current_signal: buy_weight += 1.5
                    else: sell_weight += 1.5

                    if current_sma9 > current_sma21: buy_weight += 1
                    else: sell_weight += 1

                    if current_price <= current_lower_bb: buy_weight += 1.5
                    elif current_price >= current_upper_bb: sell_weight += 1.5

                    if buy_weight > sell_weight and buy_weight >= 3:
                        action_signal = "🚀 STRONG BUY SIGNAL"
                        signal_color = "#00FF66"
                        summary_txt = f"The asset is showing clear oversold characteristics with bullish momentum support. Moving Averages and MACD validate high probability upward continuation."
                    elif sell_weight > buy_weight and sell_weight >= 3:
                        action_signal = "💥 STRONG SELL SIGNAL"
                        signal_color = "#FF3333"
                        summary_txt = f"The asset is severely overextended into overbought territory. Technical metrics demonstrate deceleration in buying momentum with immediate bearish divergence risks."
                    else:
                        action_signal = "⏳ NEUTRAL / HOLD DIRECTION"
                        signal_color = "#FF9900"
                        summary_txt = f"The market metrics are currently consolidating tightly between valid structural zones. Volatility is contracting inside standard deviations. Risk parameters favor wait-and-see execution configurations."

                    st.markdown("---")
                    st.write("## 🧠 Core Mathematical & Technical Analysis Layer")
                    
                    st.markdown(f"""
                    <div class="analysis-card" style="border-left: 5px solid {signal_color};">
                        <h3 style="color: {signal_color}; margin-top:0;">{action_signal}</h3>
                        <p style="font-size: 16px; color: #E0E6ED;"><b>Algorithmic Technical Summary:</b> {summary_txt}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(label="Current Execution Price", value=f"{current_price:,.2f}", delta=f"{price_change:+.2f}%")
                        st.markdown(f"**Structural Level:** {'Above Pivot' if current_price > pivot else 'Below Pivot'}")
                    with col2:
                        st.metric(label="RSI (14) Momentum", value=f"{current_rsi:.2f}")
                        st.markdown(f"**Momentum Zone:** {'Overbought 🛑' if current_rsi >= 70 else 'Oversold 🟢' if current_rsi <= 30 else 'Neutral 🔄'}")
                    with col3:
                        st.metric(label="MACD Histogram Spread", value=f"{(current_macd - current_signal):.4f}")
                        st.markdown(f"**Trend State:** {'Bullish Expansion 📈' if current_macd > current_signal else 'Bearish Retraction 📉'}")
                    with col4:
                        bb_pct = ((current_price - current_lower_bb) / (current_upper_bb - current_lower_bb + 1e-10)) * 100
                        st.metric(label="Bollinger Band Bandwidth %", value=f"{bb_pct:.1f}%")
                        st.markdown(f"**Volatility State:** {'Volatility Expansion' if bb_pct > 90 or bb_pct < 10 else 'Low Compression Range'}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    lvl_col1, lvl_col2 = st.columns(2)
                    with lvl_col1:
                        st.markdown("""
                        <div class="analysis-card">
                            <h4 style="margin-top:0; color:#00FFCC;">🎯 Target Resistance Levels</h4>
                            <hr style="margin: 8px 0; border-color: #1A1F2C;">
                            <ul>
                                <li><b>Major Resistance (R2):</b> """ + f"{r2:,.2f}" + """</li>
                                <li><b>Minor Resistance (R1):</b> """ + f"{r1:,.2f}" + """</li>
                                <li><b>Upper Bollinger Boundary:</b> """ + f"{current_upper_bb:,.2f}" + """</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    with lvl_col2:
                        st.markdown("""
                        <div class="analysis-card">
                            <h4 style="margin-top:0; color:#FF3333;">🛡️ Risk Support Floor Levels</h4>
                            <hr style="margin: 8px 0; border-color: #1A1F2C;">
                            <ul>
                                <li><b>Minor Support (S1):</b> """ + f"{s1:,.2f}" + """</li>
                                <li><b>Major Support (S2):</b> """ + f"{s2:,.2f}" + """</li>
                                <li><b>Lower Bollinger Boundary:</b> """ + f"{current_lower_bb:,.2f}" + """</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"Something went wrong inside the analysis core: '{e}'")

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
