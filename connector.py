"""
Connector — connector.py
Jembatan antara Form Input (Slice A) dan Chart Output (Slice B).

Connector hanya melakukan SELECT query ke DB.
TIDAK ADA kalkulasi di sini.
"""

from datetime import datetime, timedelta
import pandas as pd
import db


def _resolve_period(period: str) -> tuple[str, str]:
    """
    Konversi label periode ke tanggal start dan end.
    Returns (start_date, end_date) dalam format 'YYYY-MM-DD'.
    """
    end = datetime.now()

    period_map = {
        "1 Bulan": 30,
        "3 Bulan": 90,
        "6 Bulan": 180,
        "1 Tahun": 365,
    }

    days = period_map.get(period, 365)
    start = end - timedelta(days=days)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def run_pipeline(ticker: str, period: str, metrics: list[str]):
    """
    Pipeline utama connector:
    1. Resolve periode ke tanggal
    2. SELECT data harga dari DB
    3. SELECT data indikator dari DB
    4. Return kedua DataFrame untuk dirender oleh chart.py

    Parameters:
        ticker  : simbol saham (contoh: 'BBCA.JK')
        period  : label periode ('1 Bulan', '3 Bulan', '6 Bulan', '1 Tahun')
        metrics : list metrik yang dipilih (['MA', 'BB'])

    Returns:
        (df_prices, df_indicators) : tuple of DataFrames
    """
    start, end = _resolve_period(period)

    # SELECT only — tidak ada kalkulasi
    df_prices = db.get_prices(ticker, start, end)
    df_indicators = db.get_indicators(ticker, start, end)

    return df_prices, df_indicators
