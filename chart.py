"""
Slice B — Chart Output (chart.py)
Candlestick chart dengan overlay MA dan Bollinger Bands menggunakan Plotly.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_chart(df_prices: pd.DataFrame, df_indicators: pd.DataFrame, metrics: list[str], ticker: str):
    """
    Render candlestick chart dengan overlay indikator teknikal.

    Parameters:
        df_prices     : DataFrame harga OHLCV
        df_indicators : DataFrame indikator (MA & BB)
        metrics       : list metrik yang dipilih user
        ticker        : simbol saham untuk judul chart
    """
    if df_prices.empty:
        st.warning(f"⚠️ Tidak ada data harga untuk **{ticker}**. Pastikan ETL sudah dijalankan.")
        return

    # Pastikan kolom date bertipe datetime
    df_prices["date"] = pd.to_datetime(df_prices["date"])
    if not df_indicators.empty:
        df_indicators["date"] = pd.to_datetime(df_indicators["date"])

    # Buat candlestick chart
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_prices["date"],
        open=df_prices["open"],
        high=df_prices["high"],
        low=df_prices["low"],
        close=df_prices["close"],
        name="OHLC",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ))

    # Overlay Moving Average jika dipilih
    if "MA (Moving Average)" in metrics and not df_indicators.empty:
        ma_colors = {"ma5": "#FFD700", "ma20": "#00BFFF", "ma50": "#FF69B4"}
        ma_labels = {"ma5": "MA 5", "ma20": "MA 20", "ma50": "MA 50"}

        for col, color in ma_colors.items():
            if col in df_indicators.columns:
                fig.add_trace(go.Scatter(
                    x=df_indicators["date"],
                    y=df_indicators[col],
                    mode="lines",
                    name=ma_labels[col],
                    line=dict(color=color, width=1.5),
                ))

    # Overlay Bollinger Bands jika dipilih
    if "BB (Bollinger Bands)" in metrics and not df_indicators.empty:
        if "bb_upper" in df_indicators.columns:
            fig.add_trace(go.Scatter(
                x=df_indicators["date"],
                y=df_indicators["bb_upper"],
                mode="lines",
                name="BB Upper",
                line=dict(color="#ab47bc", width=1, dash="dash"),
            ))
        if "bb_middle" in df_indicators.columns:
            fig.add_trace(go.Scatter(
                x=df_indicators["date"],
                y=df_indicators["bb_middle"],
                mode="lines",
                name="BB Middle",
                line=dict(color="#ab47bc", width=1.5),
            ))
        if "bb_lower" in df_indicators.columns:
            fig.add_trace(go.Scatter(
                x=df_indicators["date"],
                y=df_indicators["bb_lower"],
                mode="lines",
                name="BB Lower",
                line=dict(color="#ab47bc", width=1, dash="dash"),
                fill="tonexty",
                fillcolor="rgba(171, 71, 188, 0.08)",
            ))

    # Layout styling
    fig.update_layout(
        title=dict(
            text=f"📈 {ticker} — Stock Chart",
            font=dict(size=20),
        ),
        yaxis_title="Harga (IDR)",
        xaxis_title="Tanggal",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=60, r=30, t=80, b=50),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tampilkan ringkasan data
    _render_summary(df_prices, df_indicators, ticker)


def _render_summary(df_prices: pd.DataFrame, df_indicators: pd.DataFrame, ticker: str):
    """Tampilkan ringkasan statistik di bawah chart."""
    st.markdown(f"### 📋 Ringkasan Data — {ticker}")

    if df_prices.empty:
        return

    latest = df_prices.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Open", f"{latest['open']:,.0f}")
    col2.metric("High", f"{latest['high']:,.0f}")
    col3.metric("Low", f"{latest['low']:,.0f}")
    col4.metric("Close", f"{latest['close']:,.0f}")

    if len(df_prices) >= 2:
        prev_close = df_prices.iloc[-2]["close"]
        change = latest["close"] - prev_close
        pct = (change / prev_close) * 100 if prev_close else 0
        st.markdown(
            f"**Perubahan terakhir:** {'🟢' if change >= 0 else '🔴'} "
            f"{change:+,.0f} ({pct:+.2f}%)"
        )

    # Tabel data harga
    with st.expander("📊 Lihat Data Harga (Tabel)", expanded=False):
        display_df = df_prices[["date", "open", "high", "low", "close", "volume"]].copy()
        display_df = display_df.sort_values("date", ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Tabel indikator
    if not df_indicators.empty:
        with st.expander("📐 Lihat Data Indikator (Tabel)", expanded=False):
            ind_cols = ["date"]
            for c in ["ma5", "ma20", "ma50", "bb_upper", "bb_middle", "bb_lower"]:
                if c in df_indicators.columns:
                    ind_cols.append(c)
            display_ind = df_indicators[ind_cols].copy()
            display_ind = display_ind.sort_values("date", ascending=False)
            st.dataframe(display_ind, use_container_width=True, hide_index=True)
