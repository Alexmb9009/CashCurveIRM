import streamlit as st
import yfinance as yf
import pandas as pd

# ------------------ Page Setup ------------------
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("📈 CashCurve")
st.caption("Visualize your income. Understand your risk. Stay ahead.")

# ------------------ User Inputs ------------------
ticker = st.text_input("Enter stock ticker:", value="AAPL").upper()
shares = st.number_input("How many shares do you own?", min_value=0.0, step=1.0)
refresh = st.button("🔄 Refresh Data")

# ------------------ Data Pull ------------------
@st.cache_data(ttl=120)
def load_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")
    return stock, info, hist

# ------------------ Dividend Math ------------------
def get_dividends(info, shares):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    yield_pct = info.get("dividendYield", 0.0) or 0.0

    if rate == 0.0 and yield_pct > 0:
        rate = price * yield_pct
    if yield_pct == 0.0 and rate > 0 and price > 0:
        yield_pct = rate / price

    annual_income = rate * shares
    return {
        "Share Price ($)": round(price, 2),
        "Dividend/Share ($/yr)": round(rate, 2),
        "Dividend Yield (%)": round(yield_pct * 100, 2),
        "Annual Income ($)": round(annual_income, 2),
        "Monthly Income ($)": round(annual_income / 12, 2),
        "Weekly Income ($)": round(annual_income / 52, 2),
        "Daily Income ($)": round(annual_income / 365, 2),
    }

# ------------------ Risk Assessment ------------------
def get_risk(info):
    return {
        "Beta (Market Volatility)": round(info.get("beta", 0.0), 2),
        "52-Week High ($)": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low ($)": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2),
    }

# ------------------ Momentum Analysis ------------------
def get_momentum(history):
    close = history["Close"].dropna()
    if len(close) < 50:
        return {}

    rsi = compute_rsi(close)
    ma_50 = close.rolling(50).mean().iloc[-1]
    ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    current_price = close.iloc[-1]

    momentum = {
        "Current Price ($)": round(current_price, 2),
        "50-Day MA ($)": round(ma_50, 2),
        "RSI (14)": round(rsi, 2),
    }
    if ma_200:
        momentum["200-Day MA ($)"] = round(ma_200, 2)

    if rsi > 70:
        momentum["Trend"] = "🔴 Overbought"
    elif rsi < 30:
        momentum["Trend"] = "🟢 Oversold"
    else:
        momentum["Trend"] = "⚪ Neutral"

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

# ------------------ Main Display ------------------
if ticker and shares > 0:
    stock, info, history = load_data(ticker)

    # Dividend Section
    st.subheader("💵 Dividend Breakdown")
    div_data = get_dividends(info, shares)
    st.dataframe(pd.DataFrame(div_data.items(), columns=["Metric", "Value"]), use_container_width=True)

    # Risk Section
    st.subheader("⚠️ Risk Overview")
    risk_data = get_risk(info)
    st.dataframe(pd.DataFrame(risk_data.items(), columns=["Metric", "Value"]), use_container_width=True)

    # Momentum Section
    st.subheader("📊 Momentum Metrics")
    momentum_data = get_momentum(history)
    st.dataframe(pd.DataFrame(momentum_data.items(), columns=["Indicator", "Value"]), use_container_width=True)

    # Summary
    st.markdown("---")
    st.markdown(
        f"📌 {ticker} pays you **${div_data['Monthly Income ($)']:.2f}/mo** "
        f"and **${div_data['Daily Income ($)']:.2f}/day** for **{int(shares)} shares owned**."
    )
else:
    st.info("Enter a valid stock ticker and number of shares to begin.")
