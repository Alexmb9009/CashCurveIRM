import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="CashCurve – AI Investment Risk Advisor", layout="wide")

st.title("📊 CashCurve")
st.caption("Visualize your income over time — AI-powered investment insights.")
st.divider()

# --- Search Bar ---
query = st.text_input("🔍 Search by Company Name or Ticker (e.g., AAPL or Apple)", value="AAPL").strip().upper()

def find_ticker(q):
    try:
        if len(q) <= 5:
            return q
        search = yf.Ticker(q)
        return search.ticker
    except:
        return None

ticker = find_ticker(query)

if ticker:
    stock = yf.Ticker(ticker)
    info = stock.info

    price = info.get("regularMarketPrice", 0)
    prev_close = info.get("previousClose", 0)
    change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0

    raw_yield = info.get("dividendYield", 0)
    payout_ratio = info.get("payoutRatio", 0)
    sector = info.get("sector", "N/A")

    # ---- CAP unrealistic yield ----
    dividend_yield = min(raw_yield or 0, 0.20)  # max 20% realistic cap

    st.subheader(f"{info.get('shortName', 'Unknown')} ({ticker})")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric("💵 Price", f"${price:.2f}", f"{change_pct:.2f}%")
        st.write(f"**Dividend Yield:** {round(raw_yield * 100 if raw_yield else 0, 2)}%")
        st.write(f"**Payout Ratio:** {round(payout_ratio * 100 if payout_ratio else 0, 2)}%")
    with col2:
        st.write(f"**Sector:** {sector}")
        risk_level = "🟢 Low Risk" if payout_ratio < 0.6 else "🟠 Medium Risk" if payout_ratio < 0.85 else "🔴 High Risk"
        st.write(f"**Risk Level:** {risk_level}")
        momentum = "📈 Rising" if change_pct > 1 else "📉 Falling" if change_pct < -1 else "⏸ Stable"
        st.write(f"**Momentum:** {momentum}")

    if raw_yield and raw_yield > 0.20:
        st.warning("⚠️ Yield exceeds 20%. Display capped for accurate projections.")

    st.divider()

    # --- Income Simulation ---
    st.subheader("💸 Income Simulation")

    investment_amount = st.number_input("Investment Amount ($)", min_value=100, max_value=1_000_000, value=10_000, step=100)
    term_years = st.number_input("Investment Term (Years)", min_value=1, max_value=30, value=5)

    annual_income = investment_amount * dividend_yield
    monthly_income = annual_income / 12
    weekly_income = annual_income / 52
    daily_income = annual_income / 365
    total_income = annual_income * term_years

    st.markdown(f"📊 **Income from ${investment_amount:,.2f} over {term_years} years**")
    st.write(f"- Daily: ${daily_income:,.2f}")
    st.write(f"- Weekly: ${weekly_income:,.2f}")
    st.write(f"- Monthly: ${monthly_income:,.2f}")
    st.write(f"- Annual: ${annual_income:,.2f}")
    st.success(f"✅ Total Passive Income: ${total_income:,.2f}")

    total_asset = investment_amount + total_income
    st.markdown(f"💼 **Estimated Total Asset Value: ${total_asset:,.2f}**")

    # --- Link to Trade ---
    st.markdown(f"[🔗 Trade on Robinhood](https://robinhood.com/stocks/{ticker.lower()})")

else:
    st.info("Enter a valid stock name or ticker to begin.")
