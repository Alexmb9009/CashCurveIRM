import streamlit as st
import requests

API_KEY = "H0CM17PePAJ_6ny8pFIqgxwOfXYhD9Tp"

# ---------------------- Functions ---------------------- #

def get_stock_info(ticker):
    try:
        # Get current price
        price_url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={API_KEY}"
        r = requests.get(price_url)
        r.raise_for_status()
        price_data = r.json()['results'][0]
        price = price_data['c']
        prev_close = price_data['c']  # You can refine this to get actual close if needed

        # Get fundamentals
        fund_url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey={API_KEY}"
        f = requests.get(fund_url).json()
        name = f['results'].get('name', ticker)
        sector = f['results'].get('sic_description', 'Unknown')

        # Get dividend yield (safe)
        div_url = f"https://api.polygon.io/v3/reference/dividends?ticker={ticker}&apiKey={API_KEY}&limit=1"
        d = requests.get(div_url).json()
        if d.get('results'):
            dividend_raw = d['results'][0]
            dividend_amt = float(dividend_raw.get('cash_amount', 0))
            frequency = dividend_raw.get('frequency', "")
            frequency_str = str(frequency).lower()
            dividend_annual = dividend_amt * 4 if "quarter" in frequency_str else dividend_amt
            yield_percent = dividend_annual / price if price else 0
        else:
            dividend_annual = 0
            yield_percent = 0

        # Cap high yields
        if yield_percent > 0.2:
            yield_percent = 0.2
            yield_warning = True
        else:
            yield_warning = False

        payout_ratio = 0.5  # Polygon doesn’t provide this directly — assume a safe 50%

        return {
            "name": name,
            "price": price,
            "prev_close": prev_close,
            "dividend_yield": yield_percent,
            "payout_ratio": payout_ratio,
            "sector": sector,
            "yield_warning": yield_warning
        }

    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return None


def simulate_income(price, yield_pct, amount, term_months):
    annual_return = amount * yield_pct
    monthly_return = annual_return / 12
    daily = monthly_return / 30.44
    weekly = monthly_return / 4.35
    annual = annual_return
    total_income = monthly_return * term_months
    asset_value = amount + total_income
    return daily, weekly, monthly_return, annual, total_income, asset_value

# ---------------------- UI ---------------------- #

st.set_page_config(page_title="CashCurve – AI Investment Risk Advisor", layout="centered")

st.title("💸 CashCurve")
st.caption("Visualize your income over time. Powered by AI + Polygon.io")

ticker_input = st.text_input("🔍 Search a company by ticker (e.g., AAPL)", value="AAPL").upper()

if ticker_input:
    data = get_stock_info(ticker_input)

    if data:
        st.header(f"{data['name']} ({ticker_input})")
        st.metric("💵 Price", f"${data['price']:.2f}")
        st.write(f"Dividend Yield: {data['dividend_yield'] * 100:.2f}%")
        if data['yield_warning']:
            st.warning("⚠️ Yield is unusually high. Displaying capped value for realistic return.")
        st.write(f"Payout Ratio (estimated): {data['payout_ratio'] * 100:.1f}%")
        st.write(f"Sector: {data['sector']}")

        st.subheader("📊 Income from Investment")

        invest_amt = st.number_input("💰 Investment Amount ($)", value=1000, min_value=10, max_value=1_000_000, step=100)
        term = st.number_input("📆 Investment Term (months)", value=12, min_value=1, max_value=360, step=1)

        daily, weekly, monthly, annual, total_income, asset_value = simulate_income(
            data['price'], data['dividend_yield'], invest_amt, term)

        st.write(f"**Daily Income:** ${daily:.2f}")
        st.write(f"**Weekly Income:** ${weekly:.2f}")
        st.write(f"**Monthly Income:** ${monthly:.2f}")
        st.write(f"**Annual Income:** ${annual:.2f}")
        st.success(f"📈 Total Income over {term} months: ${total_income:.2f}")
        st.info(f"💼 Projected Asset Value: ${asset_value:.2f}")

        robinhood_url = f"https://robinhood.com/stocks/{ticker_input}"
        st.markdown(f"[🔗 View on Robinhood]({robinhood_url})")

st.markdown("---")
st.caption("Built with ❤️ using Polygon.io and Streamlit | [GitHub](https://github.com/Alexmb9009/CashCurveIRM)")
