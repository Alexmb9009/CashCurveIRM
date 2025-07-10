import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# ----- PAGE CONFIG -----
st.set_page_config(
    page_title="🚀 CashCurve: Smarter Stock Insight",
    layout="centered"
)

# ----- HEADER -----
st.title("🚀 CashCurve")
st.caption("Visualize your income. Anticipate your risk. Predict your moves.")

# ----- USER INPUT -----
ticker = st.text_input("Enter Stock Ticker (Example: AAPL, KO, T):", value="AAPL").upper()
shares = st.number_input("Number of Shares Owned:", min_value=0.0, step=1.0)

refresh = st.button("🔁 Refresh Data")

# ----- CACHED DATA PULL -----
@st.cache_data(ttl=120)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")
    return stock, info, hist

# ----- CALCULATIONS -----
def calculate_dividends(info, shares):
    price = info.get("regularMarketPrice", 0.0)
    div_yield = info.get("dividendYield", 0.0) or 0.0
    div_rate = info.get("dividendRate", 0.0) or 0.0

    if div_rate == 0.0 and div_yield > 0:
        div_rate = price * div_yield
    if div_yield == 0.0 and div_rate > 0:
        div_yield = div_rate / price

    annual = div_rate * shares
    return {
        "Share Price ($)": round(price, 2),
        "Dividend per Share ($/yr)": round(div_rate, 2),
        "Dividend Yield (%)": round(div_yield * 100, 2),
        "Annual Income ($)": round(annual, 2),
        "Monthly Income ($)": round(annual / 12, 2),
        "Weekly Income ($)": round(annual / 52, 2),
        "Daily Income ($)": round(annual / 365, 2)
    }

def calculate_risk(info):
    return {
        "Beta (Market Volatility)": round(info.get("beta", 0.0), 2),
        "52-Week High ($)": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low ($)": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Price Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2)
    }

def calculate_momentum(hist):
    close = hist["Close"].dropna()
    if len(close) < 50:
        return {}

    rsi = compute_rsi(close)
    ma_50 = close.rolling(window=50).mean().iloc[-1]
    ma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None
    current = close.iloc[-1]

    momentum = {
        "Current Price ($)": round(current, 2),
        "50-Day MA ($)": round(ma_50, 2),
        "RSI (14)": round(rsi, 2)
    }
    if ma_200:
        momentum["200-Day MA ($)"] = round(ma_200, 2)

    if rsi > 70:
        momentum["Momentum Signal"] = "🔺 Overbought - watch for pullback"
    elif rsi < 30:
        momentum["Momentum Signal"] = "🔻 Oversold - possible breakout"
    else:
        momentum["Momentum Signal"] = "⚪ Neutral trend"

    return momentum

def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 0

# ----- SIMULATED NEWS SIGNAL (COMING SOON) -----
def predictive_spike_signal(info):
    headline_flag = "🧠 AI Prediction: No spike detected (News scan coming soon)"
    # Placeholder for real-time sentiment/NLP engine
    return {"Spike Alert": headline_flag}

# ----- MAIN OUTPUT -----
if ticker and shares > 0:
    stock, info, hist = get_stock_data(ticker)

    st.markdown("## 💵 Dividend Forecast")
    div_data = calculate_dividends(info, shares)
    st.dataframe(pd.DataFrame(div_data.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.markdown("## 🛡️ Risk Overview")
    risk_data = calculate_risk(info)
    st.dataframe(pd.DataFrame(risk_data.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.markdown("## ⚡ Momentum Metrics")
    momentum_data = calculate_momentum(hist)
    st.dataframe(pd.DataFrame(momentum_data.items(), columns=["Indicator", "Value"]), use_container_width=True)

    st.markdown("## 🔮 Predictive Intelligence")
    spike_data = predictive_spike_signal(info)
    st.dataframe(pd.DataFrame(spike_data.items(), columns=["Signal", "Status"]), use_container_width=True)

    st.markdown("---")
    st.markdown(
        f"📌 For {ticker}, owning **{int(shares)} shares** pays **${div_data['Monthly Income ($)']:.2f}/mo** "
        f"and **${div_data['Daily Income ($)']:.2f}/day** based on current dividend performance."
    )

else:
    st.info("Enter a valid stock ticker and number of shares to get started.")
