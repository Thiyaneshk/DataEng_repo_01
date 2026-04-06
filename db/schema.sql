-- ============================================================================
-- Data Warehouse Schema for Stock ML Platform
-- Database: stock_ml
-- Purpose: Persistent storage for app data, raw prices, and dbt transformations
-- Created: 2026-04-06
-- ============================================================================

-- MIGRATION HISTORY:
-- 2026-04-06: Phase 4 - Added core tables (user_stocks, prices) + dbt marts
-- 2026-04-06: Phase 5 - Added indices management (indices, index_constituents, health_checks)
--
-- To apply Phase 5 migrations, run:
--   psql -d stock_ml -f db/indices_schema.sql
--   psql -d stock_ml -f db/seed_indices.sql

-- ============================================================================
-- Layer 1: Application Tables (User Data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_stocks (
    symbol TEXT PRIMARY KEY,
    quantity DOUBLE PRECISION DEFAULT 0,
    avg_cost DOUBLE PRECISION,
    tags TEXT,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE user_stocks IS 'Unified table for watchlist (quantity=0) and holdings (quantity>0)';
COMMENT ON COLUMN user_stocks.symbol IS 'Stock ticker symbol (uppercase)';
COMMENT ON COLUMN user_stocks.quantity IS 'Number of shares held (0 for watchlist items)';
COMMENT ON COLUMN user_stocks.avg_cost IS 'Average purchase price per share';
COMMENT ON COLUMN user_stocks.tags IS 'User-defined tags (comma-separated)';
COMMENT ON COLUMN user_stocks.note IS 'Optional user notes';

-- ============================================================================
-- Layer 2: Raw Data (ETL Landing Zone)
-- ============================================================================

CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT,
    source_load_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    load_batch_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, datetime)
);

CREATE INDEX idx_prices_symbol_datetime ON prices(symbol, datetime DESC);
CREATE INDEX idx_prices_symbol ON prices(symbol);

COMMENT ON TABLE prices IS 'Raw market price data from yfinance ETL';
COMMENT ON COLUMN prices.symbol IS 'Stock ticker symbol';
COMMENT ON COLUMN prices.datetime IS 'Bar timestamp (5-minute intervals)';
COMMENT ON COLUMN prices.close IS 'Closing price for the period';
COMMENT ON COLUMN prices.source_load_ts IS 'When the ETL loaded this data';
COMMENT ON COLUMN prices.load_batch_id IS 'Batch ID for tracking ETL runs';

-- ============================================================================
-- Layer 3: Marts (dbt Outputs - Business-Ready)
-- ============================================================================

CREATE TABLE IF NOT EXISTS portfolio_summary (
    symbol TEXT PRIMARY KEY,
    quantity DOUBLE PRECISION,
    avg_cost DOUBLE PRECISION,
    current_price DOUBLE PRECISION,
    market_value DOUBLE PRECISION,
    gain_loss DOUBLE PRECISION,
    gain_loss_pct DOUBLE PRECISION,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE portfolio_summary IS 'Daily portfolio snapshot - dbt marts output';
COMMENT ON COLUMN portfolio_summary.symbol IS 'Stock ticker';
COMMENT ON COLUMN portfolio_summary.quantity IS 'Current shares held';
COMMENT ON COLUMN portfolio_summary.market_value IS 'Current position value (quantity * current_price)';
COMMENT ON COLUMN portfolio_summary.gain_loss IS 'Profit/loss in dollars';
COMMENT ON COLUMN portfolio_summary.gain_loss_pct IS 'Profit/loss as percentage';

-- ============================================================================
-- Setup and Initialization
-- ============================================================================

-- Insert sample watchlist items
INSERT INTO user_stocks (symbol, quantity, avg_cost, tags, note)
VALUES 
    ('AAPL', 0, NULL, 'tech', 'Tech leader - monitoring'),
    ('MSFT', 0, NULL, 'tech', 'Enterprise software'),
    ('GOOGL', 0, NULL, 'tech', 'Search and advertising')
ON CONFLICT (symbol) DO NOTHING;

-- Insert sample holdings
INSERT INTO user_stocks (symbol, quantity, avg_cost, tags, note)
VALUES 
    ('TSLA', 5, 250.00, 'ev', 'Electric vehicles'),
    ('SPY', 10, 400.00, 'etf', 'S&P 500 tracking')
ON CONFLICT (symbol) DO UPDATE SET 
    quantity = EXCLUDED.quantity,
    avg_cost = EXCLUDED.avg_cost;

-- ============================================================================
-- Utility: Refresh Updated Timestamp on Insert/Update
-- ============================================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_stocks_timestamp
BEFORE UPDATE ON user_stocks
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- Documentation and References
-- ============================================================================

/*
USAGE:

1. Create all tables:
   psql -U postgres -d stock_ml -f db/schema.sql

2. View table structure:
   \d user_stocks
   \d prices
   \d portfolio_summary

3. Add a stock to watchlist:
   INSERT INTO user_stocks (symbol, quantity, tags, note) 
   VALUES ('NVDA', 0, 'ai', 'AI chip leader');

4. Update a holding:
   UPDATE user_stocks SET quantity = 20, avg_cost = 85.50 
   WHERE symbol = 'TSLA';

5. View portfolio:
   SELECT * FROM portfolio_summary ORDER BY market_value DESC;

6. View price data:
   SELECT symbol, datetime, close 
   FROM prices 
   WHERE symbol = 'AAPL' 
   ORDER BY datetime DESC LIMIT 10;
*/
