"""
Slice A — Form Input (form.py)
Komponen form untuk input parameter screener saham.
"""

import streamlit as st


def render_form():
    """
    Render form input dan return parameter yang dipilih user.

    Returns:
        tuple: (ticker, period, metrics, submitted)
    """
    st.sidebar.markdown("## 📊 Parameter Screener")
    st.sidebar.markdown("---")

    # Input ticker saham
    ticker = st.sidebar.text_input(
        "🏷️ Ticker Saham",
        value="BBCA.JK",
        placeholder="Contoh: BBCA.JK, TLKM.JK",
        help="Masukkan simbol ticker saham. Gunakan suffix .JK untuk saham Indonesia.",
    )

    # Selectbox periode
    period = st.sidebar.selectbox(
        "📅 Periode Analisis",
        options=["1 Bulan", "3 Bulan", "6 Bulan", "1 Tahun"],
        index=3,
        help="Pilih rentang waktu data yang ingin dianalisis.",
    )

    # Multiselect metrik
    metrics = st.sidebar.multiselect(
        "📈 Metrik Teknikal",
        options=["MA (Moving Average)", "BB (Bollinger Bands)"],
        default=["MA (Moving Average)"],
        help="Pilih indikator teknikal yang ingin ditampilkan pada chart.",
    )

    st.sidebar.markdown("---")

    # Tombol Analisis
    submitted = st.sidebar.button(
        "🔍 Analisis",
        use_container_width=True,
        type="primary",
    )

    # Info tambahan
    st.sidebar.markdown("---")
    st.sidebar.caption("💡 Jalankan `etl.py` terlebih dahulu untuk mengisi data ke database.")

    return ticker.strip().upper(), period, metrics, submitted
