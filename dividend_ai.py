import streamlit as st
import yfinance as yf

st.set_page_config(page_title="📊 CashCurve", layout="centered")

st.markdown("# 💸 CashCurve")
st.caption("**Visualize your income over time.** — AI-powered investment breakdowns for fast, passive income.")

# --- User Input ---
ticker_input = st.text_input("🔍 Enter a stock ticker or company name").strip().upper()

# --- Get Stock Data ---
def fetch_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "name": info.get("shortName", ticker),
            "price": info.get("regularMarketPrice", 0.0),
            "prev_close": info.get("previousClose", 0.0),
            "yield": (info.get("dividendYield") or 0) * 100,
            "payout": (info.get("payoutRatio") or 0) * 100,
            "sector": info.get("sector", "Unknown"),
            "url": f"https://robinhood.com/stocks/{ticker}"
        }
    except:
        return None

def get_risk_level(yield_pct, payout):
    if yield_pct == 0:
        return "🔴 No Dividend"
    elif payout > 90:
        return "🔴 High Risk"
    elif payout > 70:
        return "🟡 Medium Risk"
    else:
        return "🟢 Low Risk"

def get_momentum(current, prev):
    if not current or not prev:
        return "⏸ Unknown"
    change = (current - prev) / prev * 100
    if change > 2:
        return "📈 Rising"
    elif change < -2:
        return "📉 Dropping"
    else:
        return "⏸ Stable"

# --- Display Result ---
if ticker_input:
    result = None
    if len(ticker_input) <= 5:
        result = fetch_info(ticker_input)
    else:
        # Try matching by name
        matches = ["AAPL", "MSFT", "KO", "T", "O", "PFE", "VZ", "XOM", "CVX"]
        for t in matches:
            data = fetch_info(t)
            if data and ticker_input.lower() in data['name'].lower():
                result = data
                break

    if result and result["price"]:
        st.subheader(f"{result['name']} ({result['ticker']})")
        st.metric("💵 Current Price", f"${result['price']:.2f}",
                  f"{((result['price'] - result['prev_close']) / result['prev_close']) * 100:.2f}%")

        st.markdown(f"- **Dividend Yield:** {result['yield']:.2f}%")
        st.markdown(f"- **Payout Ratio:** {result['payout']:.2f}%")
        st.markdown(f"- **Sector:** {result['sector']}")
        st.markdown(f"- **Risk Level:** {get_risk_level(result['yield'], result['payout'])}")
        st.markdown(f"- **Momentum:** {get_momentum(result['price'], result['prev_close'])}")

        # --- Passive Income Simulation ---
        st.markdown("### 📊 Investment Return Breakdown")
        amount = st.number_input("💰 Investment Amount ($)", min_value=100, max_value=1_000_000, value=1000)
        years = st.number_input("📅 Term (Years)", min_value=1, max_value=30, value=5)

        shares = amount / result['price']
        annual_income = amount * (result['yield'] / 100)
        monthly_income = annual_income / 12
        weekly_income = annual_income / 52
        daily_income = annual_income / 365
        total_income = annual_income * years
        final_value = (shares * result['price']) + total_income

        st.markdown(f"**From your ${amount:,.2f} investment:**")
        st.markdown(f"- 📈 **Estimated Shares:** {shares:.2f}")
        st.markdown(f"- 🗓️ **Daily Income:** ${daily_income:.2f}")
        st.markdown(f"- 🗓️ **Weekly Income:** ${weekly_income:.2f}")
        st.markdown(f"- 🗓️ **Monthly Income:** ${monthly_income:.2f}")
        st.markdown(f"- 🗓️ **Annual Income:** ${annual_income:.2f}")
        st.markdown(f"- ✅ **Total Passive Income over {years} yrs:** ${total_income:,.2f}")
        st.markdown(f"- 💼 **Projected Final Asset Value:** ${final_value:,.2f}")

        st.markdown(f"[🔗 View on Robinhood]({result['url']})")
        st.info("All values are estimates based on current market data and may vary over time.")
    else:
        st.warning("❌ Could not retrieve stock info. Please check the ticker or name.")

