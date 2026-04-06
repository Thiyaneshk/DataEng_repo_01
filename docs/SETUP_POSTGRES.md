# Setup Guide: Postgres + ETL + dbt

## What We've Configured

Your Stock ML platform now uses **Postgres** as the persistent backend with:

✅ **App Data Layer**: `user_stocks` (watchlist + holdings)  
✅ **Raw Data Layer**: `prices` (market data from yfinance)  
✅ **Mart Layer**: `portfolio_summary` (dbt transformations)  
✅ **ETL Pipeline**: Loads prices automatically  
✅ **dbt Integration**: Transforms raw → marts  
✅ **DBeaver IDE**: Full DB access & management  

---

## Quick Start

### 1. View Data in DBeaver

1. **Open DBeaver** (already installed)
2. **New Connection** → PostgreSQL:
   - Host: `localhost`
   - Port: `5432`
   - Database: `stock_ml`
   - User: `postgres`
   - Password: `postgres`
3. Click **Test Connection** → OK

### 2. Load Sample Data

```bash
docker exec de_template-streamlit-1 python << 'EOF'
from app.db.utils import add_to_watchlist, update_holding

# Add to watchlist
add_to_watchlist('AAPL', tags='tech')
add_to_watchlist('MSFT', tags='tech')
add_to_watchlist('GOOGL', tags='tech')

# Add to holdings
update_holding('TSLA', quantity=10, avg_cost=250)
update_holding('SPY', quantity=20, avg_cost=400)

print("✓ Sample data loaded")
EOF
```

### 3. Run ETL to Load Prices

```bash
docker exec de_template-streamlit-1 python << 'EOF'
from app.core.etl.prices import load_prices_5m

count = load_prices_5m(symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'SPY'], period='5d')
print(f"✓ Loaded {count} price records")
EOF
```

### 4. Transform Data with dbt

```bash
docker exec de_template-streamlit-1 bash -c "cd /app/dbt && dbt run --target postgres"
```

### 5. Query Results in DBeaver

In DBeaver SQL editor:

```sql
-- See all holdings with current prices
SELECT 
    us.symbol,
    us.quantity,
    us.avg_cost,
    ROUND(p.close, 2) as current_price,
    ROUND(us.quantity * p.close, 2) as market_value
FROM user_stocks us
LEFT JOIN (
    SELECT DISTINCT ON (symbol) symbol, close, datetime
    FROM prices
    ORDER BY symbol, datetime DESC
) p ON us.symbol = p.symbol
WHERE us.quantity > 0
ORDER BY market_value DESC;
```

---

## File Structure (New & Updated)

```
├── db/
│   └── schema.sql                    # ✨ NEW: DDL for all tables
├── docs/
│   └── DATABASE.md                   # ✨ NEW: Complete database docs
├── Dockerfile                        # ✏️ UPDATED: Added dbt-postgres
├── docker-compose.yml                # ✏️ UPDATED: Using stock_ml database
├── dbt/
│   └── profiles.yml                  # ✏️ UPDATED: Postgres as default target
├── app/
│   ├── core/etl/
│   │   └── prices.py                 # ✏️ UPDATED: Postgres ETL loader
│   └── db/
│       └── utils.py                  # ✏️ UPDATED: Postgres support
└── .env.example                      # ✏️ UPDATED: POSTGRES_URL docs
```

---

## Key Files & References

| File | Purpose |
|------|---------|
| `db/schema.sql` | All DDL statements - version controlled |
| `docs/DATABASE.md` | Full schema documentation with examples |
| `app/core/etl/prices.py` | ETL pipeline that loads prices → Postgres |
| `app/db/utils.py` | CRUD helpers for user_stocks |
| `dbt/profiles.yml` | dbt configuration (now Postgres) |
| `dbt/models/` | dbt transformation queries |

---

##Architecture

```
┌─────────────────────────────────────────┐
│  Streamlit App (http://localhost:8501)  │
├─────────────────────────────────────────┤
│  App Layer (user_stocks CRUD)           │
├─────────────────────────────────────────┤
│  ETL Pipeline (prices.py)               │
├─────────────────────────────────────────┤
│  PostgreSQL Database (stock_ml)         │
│  ├── user_stocks (app data)             │
│  ├── prices (raw 5min data)             │
│  └── portfolio_summary (dbt marts)      │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│  DBeaver (Mac): http://localhost:5432   │
│  - Query execution                      │
│  - Data visualization                   │
│  - Stored procedures                    │
│  - Schema management                    │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│  dbt (Transformations)                  │
│  - staging (raw_prices_5m)              │
│  - marts (portfolio_summary)            │
└─────────────────────────────────────────┘
```

---

## Next Steps

1. **Create stored procedures** in DBeaver for portfolio calculations
2. **Add more dbt models** for technical indicators
3. **Set up Airflow DAG** to schedule ETL  
4. **Add data validation tests** in dbt

---

## Troubleshooting

**Q: Port 5432 still not connecting?**  
A: Run `docker ps` and check if postgres container is running.

**Q: ETL says "invalid length of startup packet"?**  
A: This was fixed. Rebuild with: `docker-compose up -d --build`

**Q: dbt can't find postgres target?**  
A: Added dbt-postgres to Dockerfile. Rebuild: `docker-compose down && docker-compose up -d --build`

**Q: How do I backup the database?**  
A: `docker exec de_template-postgres-1 pg_dump -U postgres stock_ml > backup.sql`

---

## Documentation Going Forward

For every new feature, save:
1. **DDL** → Add to `db/schema.sql`
2. **Docs** → Update `docs/DATABASE.md`
3. **Examples** → Include in this guide

Version control these files!

---

**Your database setup is now complete and documented! 🎉**
