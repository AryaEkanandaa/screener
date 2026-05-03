-- ============================================================
-- Stock Screener Database Schema
-- Jalankan script ini di PostgreSQL untuk membuat tabel-tabel
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    source VARCHAR(20) NOT NULL,       -- 'yahoo' atau 'stooq'
    UNIQUE(ticker, date, source)
);

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

-- Index untuk mempercepat query
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date
    ON stock_prices(ticker, date);

CREATE INDEX IF NOT EXISTS idx_stock_indicators_ticker_date
    ON stock_indicators(ticker, date);
