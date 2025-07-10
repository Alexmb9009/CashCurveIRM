import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Page setup
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("See live price + realistic growth projections based on historical & analyst data.")

# User inputs
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term = st.number_input("Term Held (Years)", min_value=1, step=1)
drip = st.toggle("Enable Dividend Reinvestment (DRIP)", value=False)

# Fetch data
@st.cache_data(ttl=120)
def load_data(tkr):
    st.session_state.load_time = datetime.now()
    stock = yf.Ticker(tkr)
    return stock.info, stock.history(period="2y")

info, hist = load_data(ticker) if ticker else ({}, pd.DataFrame())

# Compute live price
current_price = info.get("regularMarketPrice", 0.0)
if ticker:
    st.subheader("Live Price")
    st.write(f"${current_price:.2f}")

# Compute historical CAGR
def get_cagr(hist):
    close = hist["Close"].dropna()
    if len(close) < 2: return 0.0
    start, end = close.iloc[0], close.iloc[-1]
    years = (close.index[-1] - close.index[0]).days / 365
    return round(((end / start)**(1/years) - 1)*100, 2)

cagr = get_cagr(hist)

# Scrape any recent analyst growth estimate (demo via NVDA Reuters mention)
def scrape_estimate(tkr):
    url = f"https://finance.yahoo.com/quote/{tkr}"
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        info_div = soup.find("td", attrs={"data-test":"ONE_YEAR_TARGET_PRICE-value"})
        return float(info_div.text.replace(",", "")) if info_div else None
    except:
        return None

estimated = scrape_estimate(ticker)
if estimated:
    est_pct = round((estimated/current_price - 1)*100, 2)
else:
    est_pct = None

# Let user pick which growth rate to use
growth_options = {"Historical CAGR": cagr}
if est_pct:
    growth_options[f"Analyst Estimate (~{est_pct}%)"] = est_pct

growth_label = st.selectbox("Projected Annual Growth Rate", growth_options.keys())
growth = growth_options[growth_label]

# Compute forecast
def compute(amount, term, drip, price, div_rate, CAGR):
    shares = amount / price if price else 0
    annual_div = shares * div_rate
    growth_factor = 1 + (CAGR / 100)
    for _ in range(term):
        if drip:
            shares += (shares * div_rate) / price
    future_price = price * (growth_factor ** term)
    future_value = shares * future_price
    total_div = annual_div * term
    return shares, annual_div, total_div, future_price, future_value

div_rate = info.get("dividendRate", 0.0) or price * (info.get("dividendYield", 0.0) or 0)
s, a_div, t_div, f_price, f_value = compute(amount, term, drip, current_price, div_rate, growth)

# Display forecast
st.subheader("📘 Forecast Breakdown")
st.markdown(f"- Estimated Shares: {s:.4f}")
st.markdown(f"- Annual Dividends: ${a_div:.2f}")
st.markdown(f"- Projected Price in {term} yrs (at {growth}%): ${f_price:.2f}")
st.markdown(f"- Projected Asset Value: ${f_value:.2f}")
st.markdown(f"- Total Dividends Over Term: ${t_div:.2f}")

# Summary table
df = pd.DataFrame({
    "Metric": ["Current Price", "Growth Rate %", "Projected Price", "Asset Value", "Total Dividends"],
    "Value": [round(current_price, 2), growth, round(f_price,2), round(f_value,2), round(t_div,2)]
})
st.dataframe(df, use_container_width=True)

# Risk & momentum...
