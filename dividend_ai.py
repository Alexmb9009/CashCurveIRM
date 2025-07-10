import streamlit as st
import yfinance as yf
import pandas as pd

# --- Setup ---
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Show what your money can grow into — with optional dividend reinvestment and historical CAGR.")

# --- Inputs ---
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

# --- Calculate 2-Year CAGR ---
def calculate_cagr(hist):
    close = hist["Close"].dropna()
    if len(close) < 2:
        return 0.0
    start_price = close.iloc[0]
    end_price = close.iloc[-1]
    years = (close.index[-1] - close.index[0]).days / 365
    if years == 0 or start_price == 0:
        return 0.0
    cagr = (end_price / start_price) ** (1 / years) - 1
    return round(cagr * 100, 2)

# --- Main Forecast ---
def compute_forecast(info, hist, amount, term, drip):
    price = info.get("regularMarketPrice", 0.0)
    dividend_rate = info.get("dividendRate", 0.0) or 0.0
    dividend_yield = info.get("dividendYield", 0.0) or 0.0
    if dividend_rate == 0 and dividend_yield > 0 and price > 0:
        dividend_rate = price * dividend_yield

    shares = amount / price if price > 0 else 0
    annual_dividend = shares * dividend_rate
    total_dividend_income = 0

    # CAGR from history
    growth_rate = calculate_cagr(hist)
    annual_growth_factor = 1 + (growth_rate / 100)

    if drip:
        # Compound dividends each year
        for _ in range(term):
            shares += (shares * dividend_rate) / price
        future_price = price * (annual_growth_factor ** term)
        future_value = shares * future_price
        total_dividend_income = (shares * dividend_rate) * term  # for display
    else:
        # Dividends not reinvested
        future_price = price * (annual_growth_factor ** term)
        future_value = shares * future_price
        total_dividend_income = annual_dividend * term

    return {
        "Current Price": round(price, 2),
        "Estimated Shares": round(shares, 4),
        "Dividend/Share ($/yr)": round(dividend_rate, 2),
        "Dividend Yield (%)": round(dividend_yield * 100, 2),
        "Annual Dividend Income ($)": round(annual_dividend, 2),
        "Growth Rate (2Y CAGR)": round(growth_rate, 2),
        "Future Price Estimate": round(future_price, 2),
        "Total Dividends Over Term": round(total_dividend_income, 2),
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
    results = compute_forecast(info, hist, amount_invested, term_years, drip_enabled)

    st.subheader("📘 Forecast Equations")
    st.markdown(f"**Shares =** ${amount_invested} ÷ ${results['Current Price']} = `{results['Estimated Shares']}`")
    st.markdown(f"**Annual Dividends =** `{results['Estimated Shares']}` × ${results['Dividend/Share ($/yr)']} = `${results['Annual Dividend Income ($)']}`")
    st.markdown(f"**Growth Rate (CAGR) =** `{results['Growth Rate (2Y CAGR)']}%`")
    st.markdown(f"**Future Price =** ${results['Current Price']} × (1 + `{results['Growth Rate (2Y CAGR)']/100}`)^`{term_years}` = `${results['Future Price Estimate']}`")
    st.markdown(f"**Projected Asset Value =** `{results['Estimated Shares']}` × `${results['Future Price Estimate']}` = `${results['Projected Asset Value']}`")
    st.markdown(f"**Total Dividends Received =** `${results['Total Dividends Over Term']}`")

    st.subheader("🧾 Summary Table")
    df = pd.DataFrame(list(results.items()), columns=["Metric", "Value"])
    st.dataframe(df, use_container_width=True)

    st.subheader("🛡️ Risk Metrics")
    risk_data = {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0) * 100, 2)
    }
    st.table(pd.DataFrame.from_dict(risk_data, orient="index", columns=["Value"]))

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
        st.write("Not enough data for momentum metrics.")
else:
    st.info("Enter a stock ticker, investment amount, and term held to begin.")
