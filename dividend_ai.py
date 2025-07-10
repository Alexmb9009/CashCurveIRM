import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="CashCurve", layout="centered")

# --- Load Logo ---
st.image("cashcurve_logo.png", width=200)
st.title("CashCurve")
st.caption("Visualize what your money becomes — with real growth and optional reinvestment.")

# --- User Inputs ---
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount_invested = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term_years = st.number_input("Term Held (Years)", min_value=1, step=1)
drip_enabled = st.toggle("Enable Dividend Reinvestment (DRIP)", value=False)

# --- Get Data ---
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

# --- Forecast Function ---
def compute_forecast(info, hist, amount, term, drip):
    price = info.get("regularMarketPrice", 0.0)
    div_rate = info.get("dividendRate", 0.0) or 0.0
    dy = info.get("dividendYield", 0.0) or 0.0
    if div_rate == 0 and dy > 0 and price > 0:
        div_rate = price * dy

    shares = amount / price if price > 0 else 0
    annual_div = shares * div_rate
    total_div = 0

    growth = calculate_cagr(hist)
    growth_factor = 1 + (growth / 100)

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

# --- RSI ---
def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return (100 - (100 / (1 + rs))).iloc[-1] if not rs.empty else 0

# --- Main Display ---
if ticker and amount_invested > 0 and term_years > 0:
    info, hist = get_data(ticker)

    #
