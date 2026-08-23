import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Institutional Crypto Analysis", layout="wide")
st.title("🛡️ Institutional Grade Crypto Trading Dashboard")

# Sidebar Controls
st.sidebar.header("Trading Parameters")
symbol = st.sidebar.selectbox("Select Crypto Pair", ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"])
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "4h"])

# Fetch Data from Delta Exchange API
url = f"https://api.delta.exchange/v2/history/candles?resolution={timeframe}&symbol={symbol}"
res = requests.get(url).json()

if "result" in res and len(res["result"]) > 0:
    df = pd.DataFrame(res["result"])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.sort_values('time').reset_index(drop=True)

    # Pure Pandas Math Calculations
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()

    # RSI Calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD Calculation
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # Bollinger Bands Calculation
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['STD20'] = df['close'].rolling(window=20).std()
    df['BBU'] = df['MA20'] + (df['STD20'] * 2)
    df['BBL'] = df['MA20'] - (df['STD20'] * 2)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${last['close']:.2f}")
    col2.metric("RSI (14)", f"{last['RSI']:.2f}" if not pd.isna(last['RSI']) else "N/A")
    col3.metric("EMA 200 (Major Trend)", f"${last['EMA_200']:.2f}")

    # Confluence Rules
    is_bullish_trend = last['close'] > last['EMA_200'] and last['EMA_20'] > last['EMA_50']
    is_bearish_trend = last['close'] < last['EMA_200'] and last['EMA_20'] < last['EMA_50']

    macd_bullish_cross = prev['MACD'] <= prev['MACD_Signal'] and last['MACD'] > last['MACD_Signal']
    macd_bearish_cross = prev['MACD'] >= prev['MACD_Signal'] and last['MACD'] < last['MACD_Signal']

    st.subheader("🎯 Trade Signal")
    
    if is_bullish_trend and macd_bullish_cross and last['RSI'] < 65:
        st.success(f"🟢 STRONG BUY SIGNAL DETECTED!\n\n• Entry: ${last['close']:.2f}")
    elif is_bearish_trend and macd_bearish_cross and last['RSI'] > 35:
        st.error(f"🔴 STRONG SHORT/SELL SIGNAL DETECTED!\n\n• Entry: ${last['close']:.2f}")
    else:
        st.warning("⚪ NO HIGH-CONFIDENCE ENTRY (Wait / Low Confluence)")

    # Interactive Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Candles"))
    fig.add_trace(go.Scatter(x=df['time'], y=df['EMA_20'], line=dict(color='yellow', width=1), name="EMA 20"))
    fig.add_trace(go.Scatter(x=df['time'], y=df['EMA_50'], line=dict(color='orange', width=1), name="EMA 50"))
    fig.add_trace(go.Scatter(x=df['time'], y=df['EMA_200'], line=dict(color='purple', width=2), name="EMA 200 Trend"))
    fig.add_trace(go.Scatter(x=df['time'], y=df['BBU'], line=dict(color='gray', width=1, dash='dash'), name="Upper BB"))
    fig.add_trace(go.Scatter(x=df['time'], y=df['BBL'], line=dict(color='gray', width=1, dash='dash'), name="Lower BB"))

    fig.update_layout(template="plotly_dark", height=600, title=f"Technical Chart - {symbol} ({timeframe})")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("API response error. Please wait a moment.")
