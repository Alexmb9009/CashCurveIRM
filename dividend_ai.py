import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="CashCurve | Visualize Your Income Over Time", layout="centered")

st.title("📊 CashCurve")
st.caption("**Visualize your income over time. AI-powered insights for passive income investors.**")
st.markdown("---")

# --- User Input
st.subheader("🔍 Search a Company")
user_input = st.text_input("Enter ticker symbol or company name", placeholder="e.g. AAPL or Apple Inc.")

# --- Function to fetch stock data
def fetch_data(query):
    try:
        ticker_obj = yf.Ticker(query)
        info = ticker_obj.info
        if not info.get("symbol"):
            all_tickers = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
            match = all_tickers[all_tickers['Security'].str.lower().str.contains(query.lower())]
            if not match.empty:
                symbol = match.iloc[0]['Symbol']
                ticker_obj = yf.Ticker(symbol)
                info = ticker_obj.info
        return info
    except:
        return None

# --- Display Stock Info
def display(info):
    st.subheader(f"📈 {info.get('shortName', '')} ({info.get('symbol')})")

    price = info.get("currentPrice")
    prev_close = info.get("previousClose")
    dividend_yield = info.get("dividendYield", 0) * 100
    payout_ratio = info.get("payoutRatio", 0) * 100
    sector = info.get("sector", "N/A")

    # Basic Metrics
    st.metric("💵 Price", f"${price:.2f}" if price else "N/A", f"{((price - prev_close) / prev_close) * 100:.2f}%" if prev_close else "")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Dividend Yield:** {dividend_yield:.2f}%")
        st.write(f"**Payout Ratio:** {payout_ratio:.2f}%")
    with col2:
        st.write(f"**Sector:** {sector}")
        st.write("**Risk Level:** 🟢 Low Risk (based on payout ratio & stability)")

    st.markdown("---")

    # Income Simulation
    st.subheader("💸 Income Simulation")
    invest_amount = st.number_input("Investment Amount ($)", value=1000, step=100)
    term_years = st.number_input("Investment Term (Years)", value=10, step=1)

    if dividend_yield > 0 and price:
        shares = invest_amount / price
        annual_income = invest_amount * (dividend_yield / 100)
        monthly_income = annual_income / 12
        weekly_income = annual_income / 52
        daily_income = annual_income / 365
        total_income = annual_income * term_years
        total_asset_value = invest_amount + total_income

        st.markdown(f"**📊 Income from ${invest_amount:,.2f} over {term_years} years**")
        st.write(f"- Daily: ${daily_income:,.2f}")
        st.write(f"- Weekly: ${weekly_income:,.2f}")
        st.write(f"- Monthly: ${monthly_income:,.2f}")
        st.write(f"- Annual: ${annual_income:,.2f}")
        st.success(f"**Total Passive Income: ${total_income:,.2f}**")
        st.info(f"**Total Asset Value (with no reinvestment): ${total_asset_value:,.2f}**")
    else:
        st.warning("⚠️ This stock does not currently pay a dividend.")

    st.markdown(f"[🔗 Trade on Robinhood](https://robinhood.com/stocks/{info.get('symbol')})")

# --- Main Execution
if user_input:
    result = fetch_data(user_input)
    if result:
        display(result)
    else:
        st.error("Stock not found. Please try a different name or ticker.")

