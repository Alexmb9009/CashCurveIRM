import streamlit as st
import yfinance as yf
import pandas as pd

# --- Streamlit Setup ---
st.set_page_config(page_title="CashCurve", layout="centered")
st.title("CashCurve")
st.caption("Visualize your income & growth — powered by historical performance.")

# --- Inputs ---
ticker = st.text_input("Stock Ticker", value="AAPL").upper()
amount = st.number_input("Amount Invested ($)", min_value=0.0, step=100.0)
term = st.number_input("Term Held (Years)", min_value=1, step=1)
refresh = st.button("Refresh Data")

# --- Pull Stock Data ---
@st.cache_data(ttl=120)
def get_data(tkr):
    stock = yf.Ticker(tkr)
    info = stock.info
    hist = stock.history(period="2y")
    return info, hist

# --- Calculate CAGR from price history ---
def calculate_cagr(hist, term):
    close = hist["Close"].dropna()
    if len(close) < 2:
        return 0.0
    initial = close.iloc[0]
    final = close.iloc[-1]
    years = (close.index[-1] - close.index[0]).days / 365
    if years == 0 or initial == 0:
        return 0.0
    cagr = (final / initial) ** (1 / years) - 1
    return round(cagr * 100, 2)

# --- Core Dividend & Forecast Logic ---
def compute_forecast(info, hist, amount, term):
    price = info.get("regularMarketPrice", 0.0)
    rate = info.get("dividendRate", 0.0) or 0.0
    dy = info.get("dividendYield", 0.0) or 0.0
    if rate == 0 and dy > 0 and price: rate = price * dy
    shares = amount / price if price else 0
    annual_div = shares * rate
    total_div = annual_div * term
    growth = calculate_cagr(hist, term)
    future_price = price * ((1 + growth / 100) ** term)
    future_value = shares * future_price
    return dict(
        price=price, rate=rate, dy=dy*100,
        shares=shares, annual_div=annual_div,
        total_div=total_div, growth=growth,
        future_price=future_price,
        future_value=future_value
    )

# --- RSI Helper ---
def compute_rsi(series, period=14):
    delta = series.diff().dropna()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return (100 - 100 / (1 + rs)).iloc[-1] if not rs.empty else 0

# --- Display Logic ---
if ticker and amount > 0 and term > 0:
    info, hist = get_data(ticker)
    fc = compute_forecast(info, hist, amount, term)

    st.subheader("📘 Forecast Math")
    st.markdown(f"$\\text{{Estimated Shares}} = \\frac{{{amount:.2f}}}{{{fc['price']:.2f}}} = {fc['shares']:.4f}$")
    st.markdown(f"$\\text{{Annual Dividend}} = {fc['shares']:.4f} * {fc['rate']:.2f} = {fc['annual_div']:.2f}$")
    st.markdown(f"$\\text{{Total Dividends}} = {fc['annual_div']:.2f} * {term} = {fc['total_div']:.2f}$")
    st.markdown(f"$\\text{{Historical Growth}} = {fc['growth']}\\% \\text{{ CAGR}}$")
    st.markdown(f"$\\text{{Future Price}} = {fc['price']:.2f} * (1 + {fc['growth']/100:.4f})^{term} = {fc['future_price']:.2f}$")
    st.markdown(f"$\\text{{Future Asset Value}} = {fc['shares']:.4f} * {fc['future_price']:.2f} = {fc['future_value']:.2f}$")

    st.subheader("🧾 Summary Table")
    summary_df = pd.DataFrame({
        "Metric": [
            "Current Share Price ($)",
            "Dividend / Share ($/yr)",
            "Dividend Yield (%)",
            "Estimated Shares",
            "Annual Dividends ($)",
            f"Total Dividends ({term} yrs)",
            f"Auto CAGR (2Y)",
            f"Future Price (est)",
            f"Future Asset Value"
        ],
        "Value": [
            round(fc['price'], 2),
            round(fc['rate'], 2),
            round(fc['dy'], 2),
            round(fc['shares'], 4),
            round(fc['annual_div'], 2),
            round(fc['total_div'], 2),
            f"{fc['growth']}%",
            round(fc['future_price'], 2),
            round(fc['future_value'], 2)
        ]
    })
    st.dataframe(summary_df, use_container_width=True)

    st.subheader("🛡️ Risk Metrics")
    risk = {
        "Beta": round(info.get("beta", 0.0), 2),
        "52-Week High": round(info.get("fiftyTwoWeekHigh", 0.0), 2),
        "52-Week Low": round(info.get("fiftyTwoWeekLow", 0.0), 2),
        "52-Week Change (%)": round(info.get("52WeekChange", 0.0)*100, 2)
    }
    st.table(pd.DataFrame.from_dict(risk, orient="index", columns=["Value"]))

    st.subheader("📈 Momentum Indicators")
    close = hist["Close"].dropna()
    if len(close) >= 50:
        ma_50 = close.rolling(50).mean().iloc[-1]
        ma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
        rsi = compute_rsi(close)
        momentum = {
            "Current Price": round(close.iloc[-1], 2),
            "50-Day MA": round(ma_50, 2),
            "RSI (14)": round(rsi, 2),
            "Trend": ("Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
        }
        if ma_200:
            momentum["200-Day MA"] = round(ma_200, 2)
        st.table(pd.DataFrame.from_dict(momentum, orient="index", columns=["Value"]))
    else:
        st.write("Not enough price history for momentum indicators.")
else:
    st.info("Enter a ticker, investment amount, and term to calculate projections.")
