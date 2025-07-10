import streamlit as st
import yfinance as yf
import pandas as pd

# ---- Streamlit setup ----
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income and growth with math that makes sense.")

# ---- Inputs ----
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount_invested = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term_years = st.number_input("Term Held (Years)", min_value=1, step=1)
refresh = st.button("Refresh Data")

# ---- Data Pull ----
@st.cache_data(ttl=120)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")
    return info, hist

# ---- Core Dividend Logic ----
def compute_dividends(info, amount_invested, term_years):
    price = info.get("regularMarketPrice", 0.0)
    dividend_rate = info.get("dividendRate", 0.0) or 0.0
    dividend_yield = info.get("dividendYield", 0.0) or 0.0

    # Fill missing data
    if dividend_rate == 0.0 and dividend_yield > 0 and price > 0:
        dividend_rate = price * dividend_yield
    if dividend_yield == 0.0 and dividend_rate > 0 and price > 0:
        dividend_yield = dividend_rate / price

    shares = amount_invested / price if price > 0 else 0
    annual_dividend_income = shares * dividend_rate
    total_dividends = annual_dividend_income * term_years
    projected_asset_value = shares * price  # Flat price assumption

    return {
        "Share Price ($)": round(price, 2),
        "Dividend per Share ($/yr)": round(dividend_rate, 2),
        "Dividend Yield (%)": round(dividend_yield * 100, 2),
        "Estimated Shares =": round(shares, 4),
        "Annual Dividend Income =": round(annual_dividend_income, 2),
        f"Total Dividends Over {term_years} Years =": round(total_dividends, 2),
        f"Projected Asset Value =": round(projected_asset_value, 2),
    }

# ---- Risk Metrics ----
def compute_risk(info):
    return {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High ($)": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low ($)": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2),
    }

# ---- Momentum Indicators ----
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

def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 0

# ---- Display Logic ----
if ticker and amount_invested > 0 and term_years > 0:
    info, hist = get_data(ticker)

    st.subheader("📘 Dividend Income Forecast (Math View)")
    data = compute_dividends(info, amount_invested, term_years)
    for label, value in data.items():
        st.markdown(f"**{label}** ${value:,.2f}")

    st.subheader("🛡️ Risk Metrics")
    risk = compute_risk(info)
    st.dataframe(pd.DataFrame(risk.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.subheader("📈 Momentum Indicators")
    momentum = compute_momentum(hist)
    st.dataframe(pd.DataFrame(momentum.items(), columns=["Indicator", "Value"]), use_container_width=True)
else:
    st.info("Enter a stock ticker, investment amount, and term held (in years) to begin.")
