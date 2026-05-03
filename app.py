"""
Application Layer — app.py
Entry point Streamlit.
Menghubungkan Slice A (form) → Connector → Slice B (chart).
"""

import streamlit as st
from form import render_form
from chart import render_chart
import connector

# ── Konfigurasi halaman ──
st.set_page_config(
    page_title="Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header ──
st.markdown(
    """
    <h1 style='text-align: center;'>📈 Stock Screener</h1>
    <p style='text-align: center; color: #888;'>
        Analisis saham dengan Moving Average &amp; Bollinger Bands
    </p>
    <hr>
    """,
    unsafe_allow_html=True,
)

# ── Slice A: Form Input ──
ticker, period, metrics, submitted = render_form()

# ── Main Content ──
if submitted:
    if not ticker:
        st.error("❌ Masukkan ticker saham terlebih dahulu!")
    else:
        with st.spinner(f"🔄 Mengambil data **{ticker}** ..."):
            try:
                # Connector: pipeline form → chart
                df_prices, df_indicators = connector.run_pipeline(
                    ticker=ticker,
                    period=period,
                    metrics=metrics,
                )

                # Slice B: Chart Output
                render_chart(df_prices, df_indicators, metrics, ticker)

            except Exception as e:
                st.error(f"❌ Terjadi error: {e}")
                st.info(
                    "💡 Pastikan:\n"
                    "1. PostgreSQL sudah berjalan\n"
                    "2. Database `stock_screener` sudah dibuat\n"
                    "3. File `.env` sudah dikonfigurasi\n"
                    "4. `etl.py` sudah dijalankan untuk ticker ini"
                )
else:
    # Tampilan awal sebelum user klik Analisis
    st.markdown(
        """
        <div style='text-align: center; padding: 80px 20px; color: #888;'>
            <h2>👈 Isi parameter di sidebar, lalu klik <b>Analisis</b></h2>
            <p>Pilih ticker saham, periode, dan metrik teknikal yang ingin ditampilkan.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
