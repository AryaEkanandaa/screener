"""
Database Layer — db.py
Koneksi dan query PostgreSQL.
Semua fungsi di sini hanya melakukan SELECT (read-only).
INSERT dilakukan oleh etl.py.
"""

import os
import psycopg2
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Membuat koneksi ke PostgreSQL menggunakan kredensial dari .env"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "stock_screener"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def init_tables():
    """Membuat tabel jika belum ada (dipanggil oleh etl.py)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume BIGINT,
            source VARCHAR(20) NOT NULL,
            UNIQUE(ticker, date, source)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_indicators (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            ma5 FLOAT,
            ma20 FLOAT,
            ma50 FLOAT,
            bb_upper FLOAT,
            bb_middle FLOAT,
            bb_lower FLOAT,
            UNIQUE(ticker, date)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


# ──────────────────────────────────────────────
#  INSERT functions (dipakai oleh etl.py saja)
# ──────────────────────────────────────────────

def insert_prices(df: pd.DataFrame, source: str):
    """
    INSERT data harga OHLCV ke tabel stock_prices.
    ON CONFLICT DO NOTHING agar tidak duplikat.
    """
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute(
            """
            INSERT INTO stock_prices (ticker, date, open, high, low, close, volume, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date, source) DO NOTHING
            """,
            (
                row["ticker"],
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                int(row["volume"]) if pd.notna(row["volume"]) else None,
                source,
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


def insert_indicators(df: pd.DataFrame):
    """
    INSERT indikator teknikal (MA & BB) ke tabel stock_indicators.
    ON CONFLICT DO NOTHING agar tidak duplikat.
    """
    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute(
            """
            INSERT INTO stock_indicators (ticker, date, ma5, ma20, ma50,
                                          bb_upper, bb_middle, bb_lower)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO NOTHING
            """,
            (
                row["ticker"],
                row["date"],
                row.get("ma5"),
                row.get("ma20"),
                row.get("ma50"),
                row.get("bb_upper"),
                row.get("bb_middle"),
                row.get("bb_lower"),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


# ──────────────────────────────────────────────
#  SELECT functions (dipakai oleh connector.py)
# ──────────────────────────────────────────────

def get_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    SELECT data harga OHLCV dari stock_prices.
    Mengambil data dari source 'yahoo' sebagai prioritas utama.
    """
    conn = get_connection()
    query = """
        SELECT ticker, date, open, high, low, close, volume, source
        FROM stock_prices
        WHERE ticker = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn, params=(ticker, start, end))
    conn.close()

    # Jika ada data duplikat dari dua source, prioritaskan Yahoo
    if not df.empty:
        df = df.sort_values(["date", "source"])
        df = df.drop_duplicates(subset=["ticker", "date"], keep="first")
        df = df.sort_values("date").reset_index(drop=True)

    return df


def get_indicators(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    SELECT indikator teknikal dari stock_indicators.
    """
    conn = get_connection()
    query = """
        SELECT ticker, date, ma5, ma20, ma50,
               bb_upper, bb_middle, bb_lower
        FROM stock_indicators
        WHERE ticker = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn, params=(ticker, start, end))
    conn.close()
    return df
