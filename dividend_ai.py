import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="CashCurve: Visualize Your Income", layout="centered")

# --- HEADER ---
st.title("📈 CashCurve Dividend & Risk Tracker")
st.caption("Visualize your income, risk, and momentum — updated live")

# --- USER INPUT ---
ticker = st.text_input("Enter a stock ticker:", value="AAPL").upper()
shares = st.number_input("Number of shares owned:", min_value=0.0, step=1.0)

refresh = st.button("🔄 Refresh Data")

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=60)
def fetch_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="6mo")

    return stock, info, hist

def calculate_dividends(info, shares):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    yield_pct = info.get("dividendYield", 0.0) or 0.0

    if rate == 0.0 and yield_pct > 0 and price > 0:
        rate = price * yield_pct
    if yield_pct == 0.0 and rate > 0 and price > 0:
        yield_pct = rate / price

    annual = rate * shares
    return {
        "Price": round(price, 2),
        "Dividend Rate ($/share)": round(rate, 2),
        "Dividend Yield (%)": round(yield_pct * 100, 2),
        "Annual Income ($)": round(annual, 2),
        "Monthly Income ($)": round(annual / 12, 2),
        "Weekly Income ($)": round(annual / 52, 2),
        "Daily Income ($)": round(annual / 365, 2)
    }

def calculate_risk(info):
    return {
        "Beta": round(info.get("beta", 0.0), 2),
        "Volatility (1Y)": round(info.get("52WeekChange", 0.0) * 100, 2),
        "52W High": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52W Low": round(info.get("fiftyTwoWeekLow", 0.0), 2),
    }

def calculate_momentum(hist):
    df = hist["Close"].dropna()
    if len(df) < 50:
        return {}

    rsi = compute_rsi(df)
    ma_50 = df.rolling(window=50).mean().iloc[-1]
    ma_200 = df.rolling(window=200).mean().iloc[-1] if len(df) >= 200 else None
    price = df.iloc[-1]

    momentum = {
        "Current Price": round(price, 2),
        "50-Day MA": round(ma_50, 2),
        "RSI (14)": round(rsi, 2)
    }
    if ma_200:
        momentum["200-Day MA"] = round(ma_200, 2)

    # Momentum prediction (basic)
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

# --- MAIN EXECUTION ---
if ticker and shares > 0:
    stock, info, hist = fetch_data(ticker)

    st.subheader(f"📊 {ticker} Dividend Breakdown")
    dividends = calculate_dividends(info, shares)
    st.dataframe(pd.DataFrame(dividends.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.subheader("⚠️ Risk Metrics")
    risk = calculate_risk(info)
    st.dataframe(pd.DataFrame(risk.items(), columns=["Metric", "Value"]), use_container_width=True)

    st.subheader("📈 Momentum Indicators")
    momentum = calculate_momentum(hist)
    st.dataframe(pd.DataFrame(momentum.items(), columns=["Indicator", "Value"]), use_container_width=True)

    # Summary line
    st.markdown("---")
    st.markdown(f"💵 **{ticker} pays ${dividends['Monthly Income ($)']:.2f}/mo "
                f"and ${dividends['Daily Income ($)']:.2f}/day for {int(shares)} shares owned.**")

else:
    st.info("Enter a valid stock ticker and number of shares above to get started.")
