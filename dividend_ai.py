import streamlit as st
import yfinance as yf
import pandas as pd

# Streamlit page setup
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income and growth over time — investment-based insights.")

# User Inputs
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount_invested = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term_years = st.number_input("Term Held (Years)", min_value=1, step=1)
refresh = st.button("Refresh Data")

# Data pull with caching
@st.cache_data(ttl=120)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="6mo")
    return info, history

# Dividend logic
def compute_dividends(info, amount_invested):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    yield_pct = info.get("dividendYield", 0.0) or 0.0

    # Fallback logic
    if rate == 0.0 and yield_pct > 0 and price > 0:
        rate = price * yield_pct
    if yield_pct == 0.0 and rate > 0 and price > 0:
        yield_pct = rate / price

    shares = amount_invested / price if price > 0 else 0
    annual_income = rate * shares

    return {
        "Share Price ($)": round(price, 2),
        "Estimated Shares": round(shares, 4),
        "Dividend / Share ($/yr)": round(rate, 2),
        "Dividend Yield (%)": round(yield_pct * 100, 2),
        "Annual Dividend Income ($)": round(annual_income, 2),
        "Monthly Income ($)": round(annual_income / 12, 2),
        "Weekly Income ($)": round(annual_income / 52, 2),
        "Daily Income ($)": round(annual_income / 365, 2),
        "Total Dividends Over Term ($)": round(annual_income * term_years, 2),
        "Total Projected Asset Value ($)": round(price * shares, 2),
    }

# Risk metrics
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
    ma_50 = close.rolling(50).mean().iloc[-1]
    ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    current = close.iloc[-1]

    momentum = {
        "Current Price ($)": round(current, 2),
        "50-Day MA ($)": round(ma_50, 2),
        "RSI (14)": round(rsi, 2),
    }
    if ma_200:
        momentum["200-Day MA ($)"] = round(ma_200, 2)

    if rsi > 70:
        momentum["Trend"] = "Overbought"
    elif rsi < 30:
        momentum["Trend"] = "Oversold"
    else:
        momentum["Trend"] = "Neutral"

    return momentum

# RSI calculator
def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1] if not rsi.empty else 0

# Run app logic
if ticker and amount_invested > 0 and term_years > 0:
    info, history = get_data(ticker)

    # Dividend Forecast
    st.subheader("Dividend Income Forecast")
    dividends = compute_dividends(info, amount_invested)
    st.dataframe(pd.DataFrame(dividends.items(), columns=["Metric", "Value"]), use_container_width=True)

    # Risk Section
    st.subheader("Risk Analysis")
    risk = compute_risk(info)
    st.dataframe(pd.DataFrame(risk.items(), columns=["Metric", "Value"]), use_container_width=True)

    # Momentum Section
    st.subheader("Momentum Indicators")
    momentum = compute_momentum(history)
    st.dataframe(pd.DataFrame(momentum.items(), columns=["Indicator", "Value"]), use_container_width=True)

    # Summary
    st.markdown("---")
    st.markdown(
        f"Based on a **${amount_invested:,.2f}** investment in **{ticker}**, your estimated "
        f"**total dividends over {term_years} years** would be approximately "
        f"**${dividends['Total Dividends Over Term ($)']:.2f}**, and your "
        f"**projected asset value** would remain around "
        f"**${dividends['Total Projected Asset Value ($)']:.2f}** (assuming no price change)."
    )
else:
    st.info("Enter a stock ticker, investment amount, and term held (in years) to begin.")
