import streamlit as st
import yfinance as yf
import pandas as pd

# Set up the Streamlit page
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income over time — with live data and real metrics.")

# User input
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
shares = st.number_input("Number of Shares Owned", min_value=0.0, step=1.0)
refresh = st.button("Refresh Data")

# Auto-fetch data (live every 2 mins)
@st.cache_data(ttl=120)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="6mo")
    return info, history

# Dividend math
def compute_dividends(info, shares):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    yield_pct = info.get("dividendYield", 0.0) or 0.0

    if rate == 0.0 and yield_pct > 0 and price > 0:
        rate = price * yield_pct
    if yield_pct == 0.0 and rate > 0 and price > 0:
        yield_pct = rate / price

    annual = rate * shares
    return {
        "Share Price ($)": round(price, 2),
        "Dividend / Share ($/yr)": round(rate, 2),
        "Dividend Yield (%)": round(yield_pct * 100, 2),
        "Annual Income ($)": round(annual, 2),
        "Monthly Income ($)": round(annual / 12, 2),
        "Weekly Income ($)": round(annual / 52, 2),
        "Daily Income ($)": round(annual / 365, 2),
    }

# Risk factors
def compute_risk(info):
    return {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High ($)": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low ($)": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2),
    }

# Momentum indicators
def compute_momentum(history):
    close = history["Close"].dropna()
    if len(close) < 50:
        return {}

    rsi = compute_rsi(close)
    ma_50 = close.rolling(window=50).mean().iloc[-1]
    ma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None
    current = close.iloc[-1]

    data = {
        "Current Price ($)": round(current, 2),
        "50-Day MA ($)": round(ma_50, 2),
        "RSI (14)": round(rsi, 2),
    }
    if ma_200:
        data["200-Day MA ($)"] = round(ma_200, 2)

    if rsi > 70:
        data["Trend"] = "Overbought"
    elif rsi < 30:
        data["Trend"] = "Oversold"
    else:
        data["Trend"] = "Neutral"

    return data

# RSI helper
def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 0

# Main logic
if ticker and shares > 0:
    info, history = get_data(ticker)

    st.subheader("Dividend Income Forecast")
    dividends = compute_dividends(info, shares)
    st.dataframe(pd.DataFrame(dividends.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.subheader("Risk Analysis")
    risk = compute_risk(info)
    st.dataframe(pd.DataFrame(risk.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.subheader("Momentum Indicators")
    momentum = compute_momentum(history)
    st.dataframe(pd.DataFrame(momentum.items(), columns=["Indicator", "Value"]), use_container_width=True)

    st.markdown("---")
    st.markdown(
        f"Based on current data, owning **{int(shares)} shares** of **{ticker}** earns approximately "
        f"**${dividends['Monthly Income ($)']:.2f} per month** or "
        f"**${dividends['Daily Income ($)']:.2f} per day**."
    )

else:
    st.info("Enter a valid stock ticker and share quantity to begin.")
