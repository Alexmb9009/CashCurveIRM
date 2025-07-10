import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

# Streamlit setup
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income & growth over time — with realistic forecasts.")

# Inputs
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term = st.number_input("Term Held (Years)", min_value=1, step=1)
growth_pct = st.number_input("Estimated Annual Growth Rate (%)", min_value=0.0, step=0.1, value=5.0)
refresh = st.button("Refresh Data")

# Fetch data
@st.cache_data(ttl=120)
def get_data(tkr):
    st.session_state.t = datetime.now()
    stock = yf.Ticker(tkr)
    info = stock.info
    hist = stock.history(period="2y")
    return info, hist

# Compute forecast
def compute_forecast(info, hist, amount, term, growth_pct):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    dy = info.get("dividendYield", 0.0) or 0.0
    if rate == 0 and dy > 0 and price: rate = price * dy
    shares = amount / price if price else 0
    annual_div = shares * rate
    total_div = annual_div * term
    future_price = price * ((1 + growth_pct / 100) ** term)
    future_value = shares * future_price
    return dict(
        price=price, rate=rate, dy=dy*100,
        shares=shares, annual_div=annual_div,
        total_div=total_div, future_price=future_price,
        future_value=future_value
    )

# Basic news sentiment
def get_sentiment(tkr):
    # Placeholder – future: news sentiment integration
    return f"News sentiment unavailable. Coming soon..."

# Display
if ticker and amount > 0 and term > 0:
    info, hist = get_data(ticker)
    fc = compute_forecast(info, hist, amount, term, growth_pct)

    st.subheader("📘 Forecast Math")
    st.markdown(f"$\\text{{Shares}} = \\frac{{{amount:.2f}}}{{{fc['price']:.2f}}} = {fc['shares']:.4f}$")
    st.markdown(f"$\\text{{Annual Dividend}} = {fc['shares']:.4f} * {fc['rate']:.2f} = {fc['annual_div']:.2f}$")
    st.markdown(f"$\\text{{Total Dividends over {term} yrs}} = {fc['annual_div']:.2f} * {term} = {fc['total_div']:.2f}$")
    st.markdown(f"$\\text{{Future Price}} = {fc['price']:.2f} * (1 + {growth_pct/100:.4f})^{{{term}}} ≈ {fc['future_price']:.2f}$")
    st.markdown(f"$\\text{{Future Asset Value}} = {fc['shares']:.4f} * {fc['future_price']:.2f} = {fc['future_value']:.2f}$")

    st.subheader("🧾 Summary Table")
    df = pd.DataFrame({
        "Metric": [
            "Current Share Price ($)",
            "Dividend / Share ($/yr)",
            "Dividend Yield (%)",
            "Estimated Shares",
            "Annual Dividends ($)",
            f"Total Dividends ({term} yrs)",
            f"Future Price ({term} yrs)",
            f"Future Asset Value"
        ],
        "Value": [
            round(fc['price'], 2),
            round(fc['rate'], 2),
            round(fc['dy'], 2),
            round(fc['shares'], 4),
            round(fc['annual_div'], 2),
            round(fc['total_div'], 2),
            round(fc['future_price'], 2),
            round(fc['future_value'], 2)
        ]
    })
    st.dataframe(df, use_container_width=True)

    st.subheader("🛡️ Risk Metrics")
    risk = {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0)*100, 2)
    }
    st.table(pd.DataFrame.from_dict(risk, orient="index", columns=["Value"]))

    st.subheader("📈 Momentum Indicators")
    close = hist["Close"].dropna()
    if len(close) >= 50:
        def rsi(ts, period=14):
            d = ts.diff().dropna()
            g = d.where(d>0,0); l = -d.where(d<0,0)
            rs = g.rolling(period).mean()/l.rolling(period).mean()
            return (100 - 100/(1+rs)).iloc[-1]
        data = {
            "Current Price": round(close.iloc[-1], 2),
            "50-Day MA": round(close.rolling(50).mean().iloc[-1], 2),
            "200-Day MA": round(close.rolling(200).mean().iloc[-1], 2) if len(close)>=200 else None,
            "RSI (14)": round(rsi(close), 2)
        }
        data["Trend"] = ("Overbought" if data["RSI (14)"]>70 else "Oversold" if data["RSI (14)"]<30 else "Neutral")
        st.table(pd.DataFrame.from_dict(data, orient="index", columns=["Value"]))
    else:
        st.write("Not enough history for momentum metrics.")

    st.subheader("📰 Market Sentiment")
    st.write(get_sentiment(ticker))

else:
    st.info("Enter ticker, investment amount, term, and growth rate to see forecasts.")
