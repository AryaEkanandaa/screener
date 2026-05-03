"""
ETL Layer — etl.py
Fetch data dari Yahoo Finance dan STOOQ, hitung indikator teknikal,
lalu simpan ke PostgreSQL.

Semua kalkulasi MA dan BB dilakukan di sini (pre-calculated).
"""

import sys
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
import db


def fetch_yahoo(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch data OHLCV dari Yahoo Finance via yfinance."""
    print(f"[Yahoo] Fetching {ticker} dari {start} s/d {end} ...")
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            print(f"[Yahoo] Tidak ada data untuk {ticker}")
            return pd.DataFrame()

        # Handle multi-level columns dari yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        df["ticker"] = ticker
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Ambil kolom yang dibutuhkan saja
        cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
        df = df[[c for c in cols if c in df.columns]]

        print(f"[Yahoo] Berhasil fetch {len(df)} baris untuk {ticker}")
        return df

    except Exception as e:
        print(f"[Yahoo] Error fetching {ticker}: {e}")
        return pd.DataFrame()


def fetch_stooq(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Fetch data OHLCV dari STOOQ via pandas_datareader."""
    print(f"[STOOQ] Fetching {ticker} dari {start} s/d {end} ...")
    try:
        df = pdr.DataReader(ticker, "stooq", start=start, end=end)
        if df.empty:
            print(f"[STOOQ] Tidak ada data untuk {ticker}")
            return pd.DataFrame()

        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        df["ticker"] = ticker
        df["date"] = pd.to_datetime(df["date"]).dt.date

        cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
        df = df[[c for c in cols if c in df.columns]]

        df = df.sort_values("date").reset_index(drop=True)
        print(f"[STOOQ] Berhasil fetch {len(df)} baris untuk {ticker}")
        return df

    except Exception as e:
        print(f"[STOOQ] Error fetching {ticker}: {e}")
        return pd.DataFrame()


def calculate_indicators(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Hitung indikator teknikal: MA5, MA20, MA50, Bollinger Bands.
    Kalkulasi dilakukan di pandas sebelum INSERT ke DB.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.sort_values("date").reset_index(drop=True)

    # Moving Averages
    df["ma5"] = df["close"].rolling(window=5).mean()
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["ma50"] = df["close"].rolling(window=50).mean()

    # Bollinger Bands (window=20, std=2)
    df["bb_middle"] = df["close"].rolling(window=20).mean()
    rolling_std = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_middle"] + (rolling_std * 2)
    df["bb_lower"] = df["bb_middle"] - (rolling_std * 2)

    # Siapkan DataFrame indikator
    indicators = df[["date", "ma5", "ma20", "ma50",
                      "bb_upper", "bb_middle", "bb_lower"]].copy()
    indicators["ticker"] = ticker

    return indicators


def merge_sources(df_yahoo: pd.DataFrame, df_stooq: pd.DataFrame) -> pd.DataFrame:
    """
    Gabungkan data dari kedua source.
    Prioritaskan Yahoo, fallback ke STOOQ jika Yahoo tidak ada data pada tanggal tertentu.
    """
    if df_yahoo.empty and df_stooq.empty:
        return pd.DataFrame()
    if df_yahoo.empty:
        return df_stooq
    if df_stooq.empty:
        return df_yahoo

    # Gabungkan berdasarkan tanggal, prioritaskan Yahoo
    merged = pd.concat([df_yahoo, df_stooq], ignore_index=True)
    merged = merged.sort_values(["date"]).reset_index(drop=True)
    merged = merged.drop_duplicates(subset=["ticker", "date"], keep="first")
    return merged


def run_etl(ticker: str, period_months: int = 12):
    """
    Jalankan pipeline ETL lengkap untuk satu ticker:
    1. Fetch dari Yahoo & STOOQ
    2. Gabungkan data
    3. Hitung indikator teknikal
    4. INSERT ke PostgreSQL
    """
    # Inisialisasi tabel
    db.init_tables()

    # Hitung rentang tanggal
    # Tambah 60 hari ekstra untuk kalkulasi MA50 (butuh 50 data point sebelumnya)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=period_months * 30 + 60)).strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"ETL Pipeline untuk {ticker}")
    print(f"Periode: {start_date} s/d {end_date}")
    print(f"{'='*60}")

    # 1. Fetch dari kedua source
    df_yahoo = fetch_yahoo(ticker, start_date, end_date)
    df_stooq = fetch_stooq(ticker, start_date, end_date)

    # 2. INSERT harga mentah ke DB (masing-masing source)
    if not df_yahoo.empty:
        db.insert_prices(df_yahoo, source="yahoo")
        print(f"[DB] Inserted {len(df_yahoo)} baris harga dari Yahoo")

    if not df_stooq.empty:
        db.insert_prices(df_stooq, source="stooq")
        print(f"[DB] Inserted {len(df_stooq)} baris harga dari STOOQ")

    # 3. Gabungkan untuk kalkulasi indikator
    df_merged = merge_sources(df_yahoo, df_stooq)

    if df_merged.empty:
        print(f"[WARNING] Tidak ada data untuk {ticker}, skip kalkulasi indikator.")
        return

    # 4. Hitung indikator teknikal (pre-calculated)
    df_indicators = calculate_indicators(df_merged, ticker)

    # 5. INSERT indikator ke DB
    if not df_indicators.empty:
        db.insert_indicators(df_indicators)
        print(f"[DB] Inserted {len(df_indicators)} baris indikator")

    print(f"\n[DONE] ETL selesai untuk {ticker}\n")


def main():
    """
    Entry point ETL. Jalankan dengan:
        python etl.py BBCA.JK TLKM.JK
    atau tanpa argumen untuk ticker default.
    """
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        # Ticker default untuk demo
        tickers = ["BBCA.JK", "TLKM.JK"]

    print("=" * 60)
    print("Stock Screener — ETL Pipeline")
    print(f"Tickers: {', '.join(tickers)}")
    print("=" * 60)

    for ticker in tickers:
        run_etl(ticker, period_months=12)

    print("\n✅ Semua ETL pipeline selesai!")


if __name__ == "__main__":
    main()
