/**
 * PHASE 5: Indices Management Schema
 * 
 * Three new tables for managing market indices and their constituents locally.
 * Enables admin panel to CRUD tickers and track index compositions without
 * repeated yfinance fetches.
 * 
 * Tables:
 * 1. indices - Master index definitions (SPY, QQQ, NIFTY50, etc.)
 * 2. index_constituents - Constituent stocks + weights/sectors
 * 3. health_checks - Pipeline health logs (freshness, API errors, sync status)
 */

-- ============================================================================
-- TABLE 1: indices
-- ============================================================================
-- Master definitions of stock market indices
-- Example: SPY = S&P 500 ETF, NIFTY50 = India's top 50 stocks, TSX60 = Canada
CREATE TABLE IF NOT EXISTS indices (
    index_id SERIAL PRIMARY KEY,
    index_symbol VARCHAR(20) NOT NULL UNIQUE,      -- e.g., "SPY", "NIFTY50"
    index_name VARCHAR(200) NOT NULL,               -- e.g., "S&P 500 ETF Trust"
    market VARCHAR(10) NOT NULL,                    -- e.g., "US", "IN", "CA"
    description TEXT,                               -- e.g., "Tracks S&P 500 stocks"
    source VARCHAR(50),                             -- e.g., "yfinance", "nse.co.in", "manual"
    constituent_count INT DEFAULT 0,                -- Number of stocks in index
    last_synced_at TIMESTAMP,                       -- Last time we updated constituents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_indices_market ON indices(market);
CREATE INDEX idx_indices_symbol ON indices(index_symbol);
CREATE INDEX idx_indices_last_synced ON indices(last_synced_at DESC);

-- Table comment
COMMENT ON TABLE indices IS 'Master index definitions (SPY, NIFTY50, TSX indices, etc.)';
COMMENT ON COLUMN indices.index_symbol IS 'Ticker symbol: SPY, QQQ, NIFTY50, TSX60';
COMMENT ON COLUMN indices.market IS 'Market: US, IN (India), CA (Canada)';
COMMENT ON COLUMN indices.constituent_count IS 'Denormalized count for dashboard display';

-- ============================================================================
-- TABLE 2: index_constituents
-- ============================================================================
-- Stocks that make up each index with their properties
-- Example: SPY has 500 constituents (Apple, Microsoft, etc.)
CREATE TABLE IF NOT EXISTS index_constituents (
    constituent_id SERIAL PRIMARY KEY,
    index_id INT NOT NULL REFERENCES indices(index_id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,                    -- e.g., "AAPL", "MSFT"
    weight NUMERIC(6, 4),                           -- Index weight %: 7.1234
    sector VARCHAR(50),                             -- e.g., "Technology", "Healthcare"
    industry VARCHAR(100),                          -- e.g., "Software", "Biotechnology"
    company_name VARCHAR(255),                      -- e.g., "Apple Inc."
    added_date DATE DEFAULT CURRENT_DATE,           -- When constituent was added
    removed_date DATE,                              -- NULL = still in index
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(index_id, symbol)                        -- One row per (index, symbol) pair
);

-- Indexes for common queries
CREATE INDEX idx_constituents_index_id ON index_constituents(index_id);
CREATE INDEX idx_constituents_symbol ON index_constituents(symbol);
CREATE INDEX idx_constituents_sector ON index_constituents(sector);
CREATE INDEX idx_constituents_active ON index_constituents(index_id) WHERE removed_date IS NULL;

-- Table comment
COMMENT ON TABLE index_constituents IS 'Constituent stocks of each index: SPY has AAPL, MSFT, etc.';
COMMENT ON COLUMN index_constituents.weight IS 'Index weight in percent (e.g., 7.1234 for 7.1234%)';
COMMENT ON COLUMN index_constituents.removed_date IS 'NULL = active, DATE = removed from index';

-- ============================================================================
-- TABLE 3: health_checks
-- ============================================================================
-- Pipeline health monitoring: data freshness, API errors, sync status
CREATE TABLE IF NOT EXISTS health_checks (
    health_check_id SERIAL PRIMARY KEY,
    check_type VARCHAR(50) NOT NULL,                -- e.g., "data_freshness", "api_error", "index_sync"
    target VARCHAR(100),                            -- e.g., "AAPL", "SPY", "yfinance_api"
    status VARCHAR(20) NOT NULL,                    -- "success", "warning", "error"
    message TEXT,                                   -- e.g., "Data stale, last update 2h ago"
    metadata JSONB,                                 -- Additional context: {"last_update": "2026-04-06T10:30:00Z", "lag_hours": 2}
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl_days INT DEFAULT 30                         -- Retention policy: keep 30 days
);

-- Indexes for common queries
CREATE INDEX idx_health_check_type ON health_checks(check_type);
CREATE INDEX idx_health_target ON health_checks(target);
CREATE INDEX idx_health_status ON health_checks(status);
CREATE INDEX idx_health_checked_at ON health_checks(checked_at DESC);
CREATE INDEX idx_health_metadata ON health_checks USING gin(metadata);

-- Table comment
COMMENT ON TABLE health_checks IS 'Pipeline health logs: data freshness, API errors, sync status';
COMMENT ON COLUMN health_checks.check_type IS 'Type: data_freshness, api_error, index_sync, etl_error';
COMMENT ON COLUMN health_checks.status IS 'Severity: success, warning, error';
COMMENT ON COLUMN health_checks.metadata IS 'JSON: {last_update, lag_hours, error_msg, rows_affected}';

-- ============================================================================
-- HELPER FUNCTION: Get active constituents for an index
-- ============================================================================
CREATE OR REPLACE FUNCTION get_index_constituents(p_index_symbol VARCHAR)
RETURNS TABLE (
    symbol VARCHAR,
    company_name VARCHAR,
    weight NUMERIC,
    sector VARCHAR,
    industry VARCHAR,
    added_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT ic.symbol, ic.company_name, ic.weight, ic.sector, ic.industry, ic.added_date
    FROM index_constituents ic
    JOIN indices i ON ic.index_id = i.index_id
    WHERE i.index_symbol = p_index_symbol AND ic.removed_date IS NULL
    ORDER BY ic.weight DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- HELPER FUNCTION: Log a health check
-- ============================================================================
CREATE OR REPLACE FUNCTION log_health_check(
    p_check_type VARCHAR,
    p_target VARCHAR,
    p_status VARCHAR,
    p_message TEXT,
    p_metadata JSONB DEFAULT NULL
)
RETURNS INT AS $$
DECLARE
    v_health_check_id INT;
BEGIN
    INSERT INTO health_checks (check_type, target, status, message, metadata)
    VALUES (p_check_type, p_target, p_status, p_message, p_metadata)
    RETURNING health_check_id INTO v_health_check_id;
    
    RETURN v_health_check_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- HELPER VIEW: Latest health status per check type
-- ============================================================================
CREATE OR REPLACE VIEW v_latest_health_checks AS
SELECT DISTINCT ON (check_type, target)
    check_type,
    target,
    status,
    message,
    checked_at
FROM health_checks
ORDER BY check_type, target, checked_at DESC;

COMMENT ON VIEW v_latest_health_checks IS 'Latest health status per check type for dashboard display';
