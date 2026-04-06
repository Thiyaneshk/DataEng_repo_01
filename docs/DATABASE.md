# Database Schema & Architecture

## Overview

This document describes the Postgres database schema for the Stock ML platform.

**Database**: `stock_ml`  
**Environment**: Docker Compose (Postgres 15)  
**Connection**: `postgresql://postgres:postgres@postgres:5432/stock_ml`

---

## Schema Layers

### Layer 1: Application Tables (User Data)

#### `user_stocks`
Unified table for watchlist items and portfolio holdings.

```sql
SELECT * FROM user_stocks;
-- symbol | quantity | avg_cost | tags | note | created_at | updated_at
```

**Use cases:**
- Add to watchlist: `INSERT INTO user_stocks (symbol, quantity, tags) VALUES ('AAPL', 0, 'tech')`
- Update holdings: `UPDATE user_stocks SET quantity = 100, avg_cost = 150.50 WHERE symbol = 'AAPL'`
- Get all stocks: `SELECT symbol, quantity FROM user_stocks`

---

### Layer 2: Raw Data (ETL Landing)

#### `prices`
Market price data from yfinance ETL (5-minute intervals).

```sql
SELECT symbol, datetime, open, high, low, close, volume 
FROM prices 
WHERE symbol = 'AAPL' 
ORDER BY datetime DESC LIMIT 10;
```

**Indexes:**
- `idx_prices_symbol_datetime` (for analytics queries)
- `idx_prices_symbol` (for ETL filters)

**ETL Loading:**
```python
from app.core.etl.prices import load_prices_5m
count = load_prices_5m(symbols=['AAPL', 'MSFT'], period='5d')
print(f'Loaded {count} records')
```

---

### Layer 3: Marts (dbt Outputs)

#### `portfolio_summary`
Aggregated daily portfolio snapshot (updated by dbt).

```sql
SELECT symbol, quantity, current_price, market_value, gain_loss_pct 
FROM portfolio_summary 
ORDER BY market_value DESC;
```

**dbt model:**
```sql
-- dbt/models/marts/portfolio_summary.sql
SELECT 
    us.symbol,
    us.quantity,
    ROUND(p.close, 2) as current_price,
    ROUND(us.quantity * p.close, 2) as market_value,
    ROUND((us.quantity * p.close - us.quantity * us.avg_cost) / (us.quantity * us.avg_cost) * 100, 2) as gain_loss_pct
FROM user_stocks us
LEFT JOIN (
    SELECT symbol, datetime, close,
           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY datetime DESC) as rn
    FROM prices
) p ON us.symbol = p.symbol AND p.rn = 1
WHERE us.quantity > 0;
```

---

## Setup Instructions

### 1. Create Database & Schema

```bash
# From your Mac host
psql postgresql://postgres:postgres@localhost:5432/postgres

-- Create database
CREATE DATABASE stock_ml;

-- Apply schema
\c stock_ml
\i db/schema.sql
```

Or using Docker:
```bash
# Apply schema inside container
docker exec de_template-streamlit-1 psql -U postgres -d stock_ml -f /app/db/schema.sql
```

### 2. Load Sample Data

```bash
docker exec de_template-streamlit-1 python << 'EOF'
from app.db.utils import add_to_watchlist, update_holding
add_to_watchlist('AAPL', tags='tech')
add_to_watchlist('MSFT', tags='tech')
update_holding('TSLA', quantity=5, avg_cost=250)
print("✓ Sample data loaded")
EOF
```

### 3. Load Price Data

```bash
docker exec de_template-streamlit-1 python << 'EOF'
from app.core.etl.prices import load_prices_5m
count = load_prices_5m(symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA'], period='5d')
print(f"✓ Loaded {count} price records")
EOF
```

### 4. Run dbt Transformations

```bash
docker exec de_template-streamlit-1 bash -c "cd /app/dbt && dbt run --target postgres"
```

---

## Common Queries

### Get portfolio value
```sql
SELECT 
    SUM(quantity * (SELECT close FROM prices p WHERE p.symbol = ps.symbol ORDER BY datetime DESC LIMIT 1)) as total_value
FROM portfolio_summary ps;
```

### Price history for a stock
```sql
SELECT symbol, datetime, open, high, low, close, volume
FROM prices
WHERE symbol = 'AAPL'
  AND datetime >= NOW() - INTERVAL '30 days'
ORDER BY datetime DESC;
```

### Holdings profit/loss
```sql
SELECT 
    us.symbol,
    us.quantity,
    us.avg_cost,
    p.close,
    ROUND(us.quantity * (p.close - us.avg_cost), 2) as gain_loss
FROM user_stocks us
LEFT JOIN (
    SELECT DISTINCT ON (symbol) symbol, close
    FROM prices
    ORDER BY symbol, datetime DESC
) p ON us.symbol = p.symbol
WHERE us.quantity > 0
ORDER BY gain_loss DESC;
```

---

## Stored Procedures (Examples)

### Calculate portfolio metrics
```sql
CREATE OR REPLACE FUNCTION get_portfolio_metrics()
RETURNS TABLE (
    total_value NUMERIC,
    total_gain_loss NUMERIC,
    position_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ROUND(SUM(quantity * close)::NUMERIC, 2),
        ROUND(SUM(quantity * (close - avg_cost))::NUMERIC, 2),
        COUNT(*)::INT
    FROM user_stocks us
    LEFT JOIN (
        SELECT DISTINCT ON (symbol) symbol, close
        FROM prices
        ORDER BY symbol, datetime DESC
    ) p ON us.symbol = p.symbol
    WHERE us.quantity > 0;
END;
$$ LANGUAGE plpgsql;

-- Usage:
SELECT * FROM get_portfolio_metrics();
```

---

## dbt Configuration

**File**: `dbt/profiles.yml`
```yaml
default:
  target: postgres
  outputs:
    postgres:
      type: postgres
      host: postgres
      user: postgres
      password: postgres
      dbname: stock_ml
      port: 5432
      schema: public
```

**Run dbt:**
```bash
dbt run --target postgres          # Run all models
dbt run --select portfolio_summary # Run specific model
dbt test                           # Run tests
dbt docs generate                  # Generate documentation
```

---

## Monitoring & Maintenance

### Table sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_catalog.pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Recent price data count
```sql
SELECT symbol, COUNT(*) as record_count, MAX(datetime) as latest
FROM prices
GROUP BY symbol
ORDER BY latest DESC;
```

### User stocks count
```sql
SELECT COUNT(*) as total, SUM(CASE WHEN quantity > 0 THEN 1 ELSE 0 END) as holdings
FROM user_stocks;
```

---

## Troubleshooting

**Connection issues?**
```bash
# Test connection from Mac
psql postgresql://postgres:postgres@localhost:5432/stock_ml -c "SELECT version();"

# From Docker
docker exec de_template-postgres-1 psql -U postgres -c "SELECT version();"
```

**ETL fails?**
```bash
docker logs de_template-streamlit-1 | grep -i "price\|etl\|error"
```

**dbt issues?**
```bash
docker exec de_template-streamlit-1 bash -c "cd /app/dbt && dbt debug"
```

---

## References

- Schema file: `db/schema.sql`
- ETL code: `app/core/etl/prices.py`
- dbt models: `dbt/models/`
- App utilities: `app/db/utils.py`
