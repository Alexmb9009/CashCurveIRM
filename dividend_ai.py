import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- Page Setup ---
st.set_page_config(page_title="CashCurve", layout="centered")

# --- Display Logo ---
st.image("cashcurve_logo.png", width=220)
st.title("CashCurve")
st.caption("Visualize what your money becomes — with growth, dividends, and smart reinvestment.")

# --- User Inputs ---
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount_invested = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term_years = st.number_input("Term Held (Years)", min_value=1, step=1)
drip_enabled = st.toggle("Enable Dividend Reinvestment (DRIP)", value=False)

# --- Pull Data ---
@st.cache_data(ttl=120)
def get_data(tkr):
    stock = yf.Ticker(tkr)
    info = stock.info
    hist = stock.history(period="2y")
    return info, hist

# --- Calculate CAGR ---
def calculate_cagr(hist):
    close = hist["Close"].dropna()
    if len(close) < 2:
        return 0.0
    start = close.iloc[0]
    end = close.iloc[-1]
    years = (close.index[-1] - close.index[0]).days / 365
    if years == 0 or start == 0:
        return 0.0
    return round(((end / start) ** (1 / years) - 1) * 100, 2)

# --- Forecast Logic ---
def compute_forecast(info, hist, amount, term, drip):
    price = info.get("regularMarketPrice", 0.0)
    div_rate = info.get("dividendRate", 0.0) or 0.0
    dy = info.get("dividendYield", 0.0) or 0.0
    if div_rate == 0 and dy > 0 and price > 0:
        div_rate = price * dy

    shares = amount / price if price > 0 else 0
    annual_div = shares * div_rate
    growth = calculate_cagr(hist)
    growth_factor = 1 + (growth / 100)
    total_div = 0

    if drip:
        for _ in range(term):
            shares += (shares * div_rate) / price
        future_price = price * (growth_factor ** term)
        future_value = shares * future_price
        total_div = (shares * div_rate) * term
    else:
        future_price = price * (growth_factor ** term)
        future_value = shares * future_price
        total_div = annual_div * term

    return {
        "Current Price": round(price, 2),
        "Estimated Shares": round(shares, 4),
        "Dividend/Share ($/yr)": round(div_rate, 2),
        "Dividend Yield (%)": round(dy * 100, 2),
        "Annual Dividend Income ($)": round(annual_div, 2),
        "Growth Rate (2Y CAGR)": round(growth, 2),
        "Future Price Estimate": round(future_price, 2),
        "Total Dividends Over Term": round(total_div, 2),
        "Projected Asset Value": round(future_value, 2)
    }

# --- RSI Calculation ---
def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return (100 - (100 / (1 + rs))).iloc[-1] if not rs.empty else 0

# --- App Logic ---
if ticker and amount_invested > 0 and term_years > 0:
    info, hist = get_data(ticker)
    forecast = compute_forecast(info, hist, amount_invested, term_years, drip_enabled)

    # --- Live Price Chart ---
    st.subheader("📊 Live Price Chart")
    st.line_chart(hist["Close"], use_container_width=True)

    # --- Forecast Equations ---
    st.subheader("📘 Forecast Equations")
    st.markdown(f"**Shares =** `${amount_invested} ÷ {forecast['Current Price']} = {forecast['Estimated Shares']}`")
    st.markdown(f"**Annual Dividends =** `{forecast['Estimated Shares']} × {forecast['Dividend/Share ($/yr)']} = {forecast['Annual Dividend Income ($)']}`")
    st.markdown(f"**Growth Rate (CAGR) =** `{forecast['Growth Rate (2Y CAGR)']}%`")
    st.markdown(f"**Future Price =** `{forecast['Current Price']} × (1 + CAGR)^{term_years} = {forecast['Future Price Estimate']}`")
    st.markdown(f"**Future Value =** `{forecast['Estimated Shares']} × {forecast['Future Price Estimate']} = {forecast['Projected Asset Value']}`")
    st.markdown(f"**Total Dividends Over {term_years} Years =** `{forecast['Total Dividends Over Term']}`")

    # --- Summary Table ---
    st.subheader("🧾 Summary Table")
    df = pd.DataFrame(forecast.items(), columns=["Metric", "Value"])
    st.dataframe(df, use_container_width=True)

    # --- Risk Analysis ---
    st.subheader("🛡️ Risk Metrics")
    risk = {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2)
    }
    st.table(pd.DataFrame.from_dict(risk, orient="index", columns=["Value"]))

    # --- Momentum Indicators ---
    st.subheader("📈 Momentum Indicators")
    close = hist["Close"].dropna()
    if len(close) >= 50:
        ma_50 = close.rolling(50).mean().iloc[-1]
        ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
        rsi = compute_rsi(close)
        trend = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        momentum = {
            "Current Price": round(close.iloc[-1], 2),
            "50-Day MA": round(ma_50, 2),
            "RSI (14)": round(rsi, 2),
            "Trend": trend
        }
        if ma_200:
            momentum["200-Day MA"] = round(ma_200, 2)
        st.table(pd.DataFrame.from_dict(momentum, orient="index", columns=["Value"]))
    else:
        st.write("Not enough price history to show trend indicators.")
else:
    st.info("Enter a stock ticker, dollar amount invested, and time held to view your CashCurve forecast.")
