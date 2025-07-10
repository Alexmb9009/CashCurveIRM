import streamlit as st
import requests

API_KEY = "H0CM17PePAJ_6ny8pFIqgxwOfXYhD9Tp"

# ---------------------- Core Functions ---------------------- #

def get_stock_info(ticker):
    try:
        # Price data
        price_url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={API_KEY}"
        price_data = requests.get(price_url).json()['results'][0]
        price = price_data['c']
        prev_close = price_data['c']

        # Company data
        meta_url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={API_KEY}"
        meta = requests.get(meta_url).json()
        name = meta['results'].get('name', ticker)
        sector = meta['results'].get('sic_description', 'Unknown')

        # Dividend data
        div_url = f"https://api.polygon.io/v3/reference/dividends?ticker={ticker}&apiKey={API_KEY}&limit=1"
        d = requests.get(div_url).json()
        if d.get('results'):
            div = d['results'][0]
            dividend_amt = float(div.get('cash_amount', 0))
            freq = str(div.get('frequency', "")).lower()
            dividend_annual = dividend_amt * 4 if "quarter" in freq else dividend_amt
            yield_percent = dividend_annual / price if price else 0
        else:
            dividend_annual = 0
            yield_percent = 0

        # Yield warning if too high
        yield_warning = False
        if yield_percent > 0.2:
            yield_percent = 0.2
            yield_warning = True

        return {
            "name": name,
            "price": price,
            "prev_close": prev_close,
            "dividend_yield": yield_percent,
            "dividend_annual": dividend_annual,
            "sector": sector,
            "yield_warning": yield_warning
        }

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None


def simulate_income(price, yield_pct, amount, term_years):
    annual_income = amount * yield_pct
    monthly = annual_income / 12
    weekly = annual_income / 52
    daily = annual_income / 365
    total_income = annual_income * term_years
    final_asset = amount + total_income
    return daily, weekly, monthly, annual_income, total_income, final_asset

# ---------------------- UI ---------------------- #

st.set_page_config(page_title="CashCurve – AI Investment Risk Advisor", layout="centered")

st.title("💸 CashCurve")
st.caption("Visualize your income over time. Powered by AI + Polygon.io")

ticker = st.text_input("🔍 Search a company by ticker (e.g., AAPL)", value="AAPL").upper()

if ticker:
    stock = get_stock_info(ticker)

    if stock:
        st.header(f"{stock['name']} ({ticker})")
        st.metric("💵 Price", f"${stock['price']:.2f}")
        st.write(f"Dividend Yield: {stock['dividend_yield'] * 100:.2f}%")
        if stock['yield_warning']:
            st.warning("⚠️ Yield capped at 20% for realistic return projections.")
        st.write(f"Sector: {stock['sector']}")

        st.subheader("📊 Income from Investment")

        invest_amt = st.number_input("💰 Investment Amount ($)", value=1000, min_value=10, max_value=1_000_000, step=100)
        term_years = st.number_input("📆 Investment Term (years)", value=1, min_value=1, max_value=30, step=1)

        daily, weekly, monthly, annual, total_income, final_value = simulate_income(
            stock['price'], stock['dividend_yield'], invest_amt, term_years)

        st.write(f"**Daily Income:** ${daily:.2f}")
        st.write(f"**Weekly Income:** ${weekly:.2f}")
        st.write(f"**Monthly Income:** ${monthly:.2f}")
        st.write(f"**Annual Income:** ${annual:.2f}")
        st.success(f"💰 Total Income over {term_years} years: ${total_income:.2f}")
        st.info(f"📈 Projected Asset Value: ${final_value:.2f}")

        robinhood_url = f"https://robinhood.com/stocks/{ticker}"
        st.markdown(f"[🔗 View on Robinhood]({robinhood_url})")

st.markdown("---")
st.caption("Built with ❤️ using Polygon.io and Streamlit | [GitHub](https://github.com/Alexmb9009/CashCurveIRM)")
