import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta
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

    # 1. Advanced Trend Indicators (EMA 20, 50, 200)
    df['EMA_20'] = ta.ema(df['close'], length=20)
    df['EMA_50'] = ta.ema(df['close'], length=50)
    df['EMA_200'] = ta.ema(df['close'], length=200)

    # 2. Momentum Indicators (RSI & MACD)
    df['RSI'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDs_12_26_9']

    # 3. Volatility & Bands (Bollinger Bands & ATR)
    bbands = ta.bbands(df['close'], length=20, std=2)
    df['BBL'] = bbands['BBL_20_2.0']
    df['BBU'] = bbands['BBU_20_2.0']
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Metrics Display
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${last['close']:.2f}")
    col2.metric("RSI (14)", f"{last['RSI']:.2f}")
    col3.metric("EMA 200 (Major Trend)", f"${last['EMA_200']:.2f}")
    col4.metric("Market Volatility (ATR)", f"${last['ATR']:.2f}")

    # Strict Institutional Math Logic
    is_bullish_trend = last['close'] > last['EMA_200'] and last['EMA_20'] > last['EMA_50']
    is_bearish_trend = last['close'] < last['EMA_200'] and last['EMA_20'] < last['EMA_50']

    macd_bullish_cross = prev['MACD'] <= prev['MACD_Signal'] and last['MACD'] > last['MACD_Signal']
    macd_bearish_cross = prev['MACD'] >= prev['MACD_Signal'] and last['MACD'] < last['MACD_Signal']

    # Signal Generation
    st.subheader("🎯 High-Probability Trade Signal")
    
    if is_bullish_trend and macd_bullish_cross and last['RSI'] < 65:
        sl = last['close'] - (1.5 * last['ATR'])
        tp = last['close'] + (3.0 * last['ATR'])
        st.success(f"🟢 STRONG BUY SIGNAL DETECTED!\n\n"
                   f"• Entry: ${last['close']:.2f}\n"
                   f"• Stop-Loss (SL): ${sl:.2f}\n"
                   f"• Take-Profit (TP): ${tp:.2f}\n"
                   f"• Risk-Reward: 1:2 Perfect Ratio")
    elif is_bearish_trend and macd_bearish_cross and last['RSI'] > 35:
        sl = last['close'] + (1.5 * last['ATR'])
        tp = last['close'] - (3.0 * last['ATR'])
        st.error(f"🔴 STRONG SHORT/SELL SIGNAL DETECTED!\n\n"
                 f"• Entry: ${last['close']:.2f}\n"
                 f"• Stop-Loss (SL): ${sl:.2f}\n"
                 f"• Take-Profit (TP): ${tp:.2f}\n"
                 f"• Risk-Reward: 1:2 Perfect Ratio")
    else:
        st.warning("⚪ NO HIGH-CONFIDENCE ENTRY (Market Consolidating / Low Confluence)")

    # Advanced Professional Candlestick Chart
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
    st.error("API response error. Please try again in a few seconds.")
