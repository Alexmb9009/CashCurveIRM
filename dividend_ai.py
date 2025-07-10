import streamlit as st
import yfinance as yf
import pandas as pd
from yfinance import utils

# --- PAGE SETUP ---
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income and growth over time — investment-based insights.")

# --- COMPANY SEARCH UTILITY ---
def resolve_to_ticker(user_input):
    user_input = user_input.strip()
    if not user_input:
        return None

    if len(user_input) <= 5 and user_input.isalpha():
        return user_input.upper()  # assume it's already a ticker

    # Try to search by company name using yfinance
    matches = utils.get_yf_rich_summary(user_input)
    if matches and "symbol" in matches:
        return matches["symbol"]
    return None

# --- USER INPUT ---
user_input = st.text_input("Enter Stock Ticker or Company Name", value="Apple")
ticker = resolve_to_ticker(user_input)

if not ticker:
    st.warning("Please enter a valid stock ticker or company name.")
    st.stop()

amount_invested = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term_years = st.number_input("Term Held (Years)", min_value=1, step=1)
drip_enabled = st.toggle("Enable Dividend Reinvestment (DRIP)", value=False)

# --- DATA FETCH ---
@st.cache_data(ttl=120)
def get_data(tkr):
    stock = yf.Ticker(tkr)
    info = stock.info
    hist = stock.history(period="2y")
    return info, hist

# --- CAGR ---
def calculate_cagr(hist):
    close = hist["Close"].dropna()
    if len(close) < 2:
        return 0.0, 0.0, 0.0
    start = close.iloc[0]
    end = close.iloc[-1]
    years = (close.index[-1] - close.index[0]).days / 365
    if start <= 0 or years <= 0:
        return 0.0, start, end
    cagr = ((end / start) ** (1 / years)) - 1
    return round(cagr * 100, 2), round(start, 2), round(end, 2)

# --- FORECAST ---
def compute_forecast(info, hist, amount, term, drip, growth_rate):
    price = info.get("regularMarketPrice", 0.0)
    if price <= 0:
        raise ValueError("Could not retrieve valid stock price. Please check the ticker or company name.")

    div_rate = info.get("dividendRate", 0.0) or 0.0
    dy = info.get("dividendYield", 0.0) or 0.0
    if div_rate == 0 and dy > 0:
        div_rate = price * dy

    shares = amount / price
    annual_div = shares * div_rate
    growth_factor = 1 + (growth_rate / 100)

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
        "Dividend/Share ($/yr)": round(div_rate, 2),
        "Dividend Yield (%)": round(dy * 100, 2),
        "Estimated Shares": round(shares, 4),
        "Annual Dividend Income ($)": round(annual_div, 2),
        "Growth Rate Used (%)": round(growth_rate, 2),
        "Future Price Estimate": round(future_price, 2),
        "Total Dividends Over Term": round(total_div, 2),
        "Projected Asset Value": round(future_value, 2)
    }

# --- DISPLAY ---
try:
    info, hist = get_data(ticker)
    cagr, start_price, end_price = calculate_cagr(hist)

    st.subheader("📈 Projected Growth Rate")
    st.markdown(f"**Auto-calculated CAGR (2-year):** {cagr}%")
    use_override = st.toggle("Override with my own growth %", value=False)
    growth_rate = st.number_input("Enter your own projected annual growth rate (%)", value=cagr, step=0.1) if use_override else cagr

    forecast = compute_forecast(info, hist, amount_invested, term_years, drip_enabled, growth_rate)

    st.subheader("📊 Projected Stock Price Growth")
    st.markdown(f"- **Price 2 Years Ago:** ${start_price}")
    st.markdown(f"- **Current Price:** ${end_price}")
    st.markdown(f"- **Growth Rate Used:** {growth_rate}%")
    st.markdown(f"- **Projected Price in {term_years} Years:** ${forecast['Future Price Estimate']}")

    st.subheader("📘 Forecast Breakdown")
    st.markdown(f"**Shares =** ${amount_invested} ÷ ${forecast['Current Price']} = {forecast['Estimated Shares']}")
    st.markdown(f"**Annual Dividends =** {forecast['Estimated Shares']} × ${forecast['Dividend/Share ($/yr)']} = ${forecast['Annual Dividend Income ($)']}")

    # --- Stylish Projected Asset Value ---
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #eef2f3, #d0e1f9);
                    padding: 20px 25px;
                    border-radius: 12px;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06); 
                    margin: 20px 0;">
            <h4 style="color: #0A2342; margin-bottom: 10px;">💰 Projected Asset Value</h4>
            <p style="font-size: 26px; font-weight: 700; color: #0A2342; margin: 0;">
                ${forecast['Projected Asset Value']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"**Total Dividends Over {term_years} Years =** ${forecast['Total Dividends Over Term']}")

    st.subheader("🧾 Summary")
    st.dataframe(pd.DataFrame(forecast.items(), columns=["Metric", "Value"]), use_container_width=True)

except ValueError as e:
    st.error(str(e))
except Exception as e:
    st.error("An unexpected error occurred. Please check the input and try again.")
