# DE Template — Progress Log

> This file tracks all changes made to this project, including what was changed, why, and verification results.
> **For AI agents:** Read this file first to understand project history before making changes.

---

## Phase 0/3: Unified Holdings & Watchlist Management ✅
**Date:** 2026-04-04
**Status:** Complete

### What Was Done
1. **Unified Database Schema** in `app/db/utils.py`:
   - Replaced separate `watchlist` and `holdings` tables with single `user_stocks` table containing: `symbol` (PK), `quantity`, `avg_cost`, `tags`, `note`, `updated_at`
   - Added automatic migration logic to preserve existing watchlist/holdings data from legacy tables
   - Maintained backward compatibility with legacy functions (`get_watchlist()`, `add_to_watchlist()`, etc.)
   - Added new functions: `get_all_stocks()`, `add_or_update_stock()`, `remove_stock()`

2. **Redesigned Admin UI** in `app/views/05_Admin_Watchlist.py`:
   - Combined watchlist and holdings management into single "Portfolio Manager" interface
   - Added quantity editing capability (quantity = 0 → watchlist, quantity > 0 → holding)
   - Implemented comprehensive CRUD operations with forms for adding/editing stocks
   - Added quick edit functionality for existing stocks
   - Included all metadata fields: symbol, quantity, avg_cost, tags, notes

3. **Updated Tests** in `tests/test_integration.py`:
   - Modified `test_db_init()` to check for new `user_stocks` table instead of legacy tables
   - Verified backward compatibility of CRUD operations

### Key Technical Decisions
- **Unified Schema:** Single table approach simplifies data management while preserving all functionality
- **Automatic Classification:** Stocks are dynamically classified as holdings/watchlist based on quantity
- **Migration Safety:** Legacy data is automatically migrated on first run, with error handling for missing tables

### Verification Results
- **Database Migration:** ✅ Legacy data preserved, new table created correctly
- **Backward Compatibility:** ✅ Legacy functions work with new schema
- **CRUD Operations:** ✅ Add/update/remove stocks functions correctly
- **UI Functionality:** ✅ Single interface handles both watchlist and holdings
- **Tests:** ✅ Updated tests pass, confirming schema and function changes

### User Experience Improvements
- **Seamless Management:** Users can now add stocks to watchlist and convert to holdings by simply editing quantity
- **Complete Metadata:** All stock information (tags, notes, costs) managed in one place
- **Real-time Updates:** Changes reflect immediately in the UI and database

---

## Auth & Navigation Fixes ✅
**Date:** 2026-04-04
**Status:** Complete

### Issues Fixed
1. **Logout Functionality**: Wired the logout button in `app/main.py` to actually call `auth.logout()` instead of showing a warning
2. **Admin Page Discovery**: Added "Admin" to `allowed_groups` in `app/main.py` so admin pages (05_Admin_Watchlist.py, 99_Admin_Platform_Setup.py) appear in navigation
3. **Auth Rerun Consistency**: Updated all `st.experimental_rerun()` calls to `st.rerun()` for compatibility with current Streamlit version

### Technical Details
- **Navigation Fix**: The page discovery logic was filtering out "Admin" group pages, preventing access to portfolio management features
- **Auth Flow**: Dev login and logout now properly refresh the app state using experimental_rerun
- **Session Management**: Logout correctly clears user session state and redirects to login

### Verification Results
- **Navigation**: Admin pages now appear in the sidebar navigation menu
- **Logout**: Clicking "Log out" properly clears session and returns to login screen
- **Login Flow**: Dev login successfully authenticates and grants access to all pages
- **Page Access**: Admin functionality is now accessible after authentication
- **Rerun Fix**: Corrected `st.experimental_rerun()` to `st.rerun()` for Streamlit compatibility
- **Ollama Integration**: Local LLM service running in Docker with model persistence
- **RAG System**: AI analyst provides context-aware analysis using stock data
- **Auto-detection**: Ollama client automatically detects Docker vs local environment

---

## Phase 4: Technical Analysis & AI RAG System ✅
**Date:** 2026-04-04
**Status:** Complete

### What Was Done
1. **Enhanced Technical Indicators** in `dbt/models/marts/fct_indicators_1d.sql`:
   - Added EMA 200 (long-term trend)
   - Implemented RSI 14 (momentum oscillator)
   - Added MACD with signal line and histogram (trend following)
   - Implemented Bollinger Bands with position indicator (volatility)
   - Added Stochastic Oscillator K%D (momentum)
   - All indicators calculated using proper window functions

2. **Created Technical Analysis Dashboard** (`app/views/07_Technical_Analysis.py`):
   - Interactive candlestick charts with overlaid EMAs and Bollinger Bands
   - Multi-panel visualization: Price/Volume/RSI/MACD
   - Key metrics display (latest close, returns, RSI, BB position)
   - Technical signals analysis and alerts
   - Date range filtering and symbol selection

3. **Updated Airflow DAG** (`airflow/dags/etl_prices_dag.py`):
   - Added dbt run for DuckDB target (indicators calculation)
   - Sequential execution: Load prices → Run dbt DuckDB → Run dbt Postgres
   - Maintains both local analytics and warehouse targets

4. **Implemented RAG AI Analyst** (`app/views/08_AI_Analyst.py`):
   - Integrated Ollama for local LLM inference
   - RAG system with stock data context retrieval
   - Chat interface for AI-powered market analysis
   - Model selection and management interface
   - Context-aware responses using technical indicators

5. **Added Ollama Docker Service**:
   - Ollama container for local LLM hosting
   - Automatic model initialization script
   - Volume persistence for downloaded models
   - Network integration with Streamlit app

### Key Technical Decisions
- **Comprehensive Indicator Suite**: Selected most widely used technical indicators for complete analysis
- **Multi-Panel Visualization**: Separated concerns (price, volume, oscillators, momentum) for clarity
- **Local LLM Priority**: Ollama chosen for privacy, cost-effectiveness, and offline capability
- **RAG Architecture**: Context retrieval from dbt models ensures data-driven AI responses

### Verification Results
- **Technical Indicators**: All indicators calculate correctly with proper window functions
- **Visualization**: Candlestick charts render with all overlays and multi-panel layout
- **Airflow Integration**: DAG successfully runs ETL → dbt DuckDB → dbt Postgres sequence
- **AI Analyst**: RAG system provides context-aware analysis using stock data
- **Ollama Setup**: Local LLM service runs in Docker with model persistence
- **Navigation**: New Analysis and AI pages accessible in sidebar

### Known Issues
- **AI Analyst Timeout**: Ollama requests timeout after 30 seconds for complex queries. Increased timeout to 120 seconds as temporary fix. Consider model optimization or streaming responses for better UX.

### User Experience Improvements
- **Advanced Analytics**: Professional-grade technical analysis with multiple indicators
- **Interactive Charts**: Zoom, pan, and overlay controls for detailed analysis
- **AI Insights**: Natural language queries answered with data-backed analysis
- **Local AI**: Privacy-preserving AI without external API dependencies
- **Automated Pipeline**: End-to-end data processing from raw prices to AI insights

---

## Phase 1 & 2: Postgres Analytics Stack & Global Indices ✅
**Date:** 2025-05-22
**Status:** Complete

### What Was Done
1.  **Postgres Infrastructure**:
    *   Updated `app/db/connection.py` to support Postgres as the primary database with SQLAlchemy.
    *   Refactored `app/core/etl/prices.py` with robust upsert logic using temporary tables.
    *   Implemented **Medallion Architecture**: Created a **Bronze Layer** (Parquet files in `data/bronze/`) to land raw API data before ingestion.
2.  **Global Market Expansion**:
    *   Added support and tracking for major indices: **S&P 500 (^GSPC)**, **TSX (^GSPTSE)**, and **Nifty 50 (^NSEI)**.
    *   Enhanced **Portfolio Manager** with a "Quick Import" feature for top index constituents.
3.  **Analytics & Visualization**:
    *   Developed `fct_equity_features_1d` dbt mart with RSI, EMA 20/50/200, and Bollinger Bands.
    *   Optimized Streamlit charts to **remove weekend/holiday gaps**, providing a clean, professional financial view.
4.  **Pipeline Observability**:
    *   Added an `etl_log` table to track every run (run_id, status, duration, rows).
    *   Created a monitoring dashboard in the Streamlit Admin page.
5.  **Documentation & Learning**:
    *   Created a comprehensive `docs/USER_ADMIN_GUIDE.md` for role-based operating instructions.

### Verification Results
*   **ETL**: ✅ Successfully loads multi-region indices into Postgres.
*   **dbt**: ✅ Financial indicators calculate correctly across all symbols.
*   **UI**: ✅ Charts are continuous (no weekend gaps) and show all technical overlays.

---

## AI Analyst Timeout Fix ✅
**Date:** 2026-04-04
**Status:** Complete

### Issue Identified
- Ollama API requests timing out after 30 seconds for complex stock analysis queries
- Error: `HTTPConnectionPool(host='ollama', port=11434): Read timed out. (read timeout=30)`

### Solution Implemented
- Increased request timeout from 30 to 120 seconds in `OllamaClient.generate()`
- Allows sufficient time for local LLM inference on complex financial analysis prompts

### Technical Details
- Local LLMs can be slower than cloud APIs, especially for detailed analysis
- 120-second timeout provides buffer for model loading and inference
- Future improvements: Implement streaming responses, model quantization, or smaller models

### Verification Results
- Timeout errors eliminated for standard queries
- AI analyst can now process multi-stock analysis requests
- Response quality maintained with increased processing time

---

## Step 2.5: Unblocking UI with Dev Auth ✅
**Date:** 2026-03-06
**Status:** Complete

### What Was Done
1. **Implemented Dev Auth Bypass** in `app/auth.py`:
   - Replaced `st.stop()` with logic that checks for `st.secrets["auth"]`.
   - Added a "🚀 Dev Login (Bypass Auth)" button that logs in as a mock user.
   - **Fix:** Wrapped `st.secrets` access in a try-except block to handle missing `secrets.toml` files (fixing the `StreamlitSecretNotFoundError`).
   - Added session state tracking for the user object.
   - Added a `logout()` helper.
2. **Cleaned up `.streamlit/config.toml`**: Removed invalid `google_auth` options that caused startup warnings.
3. **Created `app/pages` Directory** to support the new `discover_pages` logic in `main.py`.
4. **Added `01_Home_Dashboard.py`** as the first functional page.
5. **Verified Navigation:** The app now correctly discovers pages and handles the login state without hard-stopping or crashing.

---

## Step 2: dbt on top of DuckDB ✅
**Date:** 2026-03-06
**Status:** Complete

### What Was Done
1. **Added `dbt-duckdb>=1.9.0,<2.0.0`** to `pyproject.toml`.
2. **Created `dbt/profiles.yml`** — project-local profile for DuckDB.
3. **Created `dbt/models/sources.yml`** — defined `main.raw_prices` as a source.
4. **Created `dbt/models/staging/stg_prices.sql`** — staging model with cleanup and derived columns (`bar_range`, `bar_return_pct`).
5. **Created `dbt/models/staging/stg_prices.yml`** — schema tests (`not_null` on keys).
6. **Updated `.gitignore`** — added dbt artifacts (`target/`, `dbt_packages/`, `logs/`).

### Key Technical Decision
Set `schema: main` in `sources.yml` to explicitly point dbt at DuckDB's default schema, resolving a catalog error where dbt looked for `raw.raw_prices`.

### Verification Results
- **dbt debug:** ✅ Connection OK
- **dbt run:** ✅ `stg_prices` view created
- **dbt test:** ✅ 3/3 tests passed
- **Manual Query:** `SELECT * FROM stg_prices LIMIT 5` confirmed correct values and derived columns.

---

## Step 1: Real ETL with yfinance ✅
**Date:** 2026-03-06
**Status:** Complete

### What Was Done
1. **Added `yfinance>=0.2.40,<1.0.0`** to `pyproject.toml`
2. **Rewrote `app/core/etl/prices.py`** — full yfinance integration:
   - `fetch_prices(symbols, period, interval)` → calls `yf.download()`, returns tidy DataFrame
   - `load_prices(symbols, period, interval, conn)` → creates `raw_prices` table, inserts via DuckDB's DataFrame registration
   - Accepts optional `conn` parameter for testability (in-memory DuckDB)
   - Backwards-compatible `load_sample_prices()` alias preserved
3. **Updated `scripts/refresh_data.py`** — calls `load_prices()` with progress output and row counts
4. **Created `tests/test_etl.py`** — 6 real tests:
   - `test_returns_dataframe_with_expected_columns`
   - `test_returns_rows_for_valid_symbol`
   - `test_handles_invalid_symbol_gracefully`
   - `test_creates_raw_prices_table` (in-memory DuckDB)
   - `test_inserts_rows` (in-memory DuckDB)
   - `test_table_schema_matches` (in-memory DuckDB)

### Bug Fixes
- **Dockerfile:** Added `uv.lock` to `COPY` before `uv sync` (build was failing)
- **`.gitignore`:** Removed `uv.lock` from ignore list (should be tracked for reproducibility)

### Key Technical Decision
yfinance v0.2.66 **always** returns `MultiIndex` columns `(Ticker, Price)` even for single-ticker downloads. Fixed with `pd.DataFrame.xs(sym, axis=1, level=0, drop_level=True)` instead of naive column indexing.

### Verification Results
- **Tests:** 7/7 passed (3.61s)
- **CLI:** `uv run python -m scripts.refresh_data` → 1,155 rows loaded
  - AAPL: 390 rows
  - RELIANCE.NS: 375 rows
  - RY.TO: 390 rows
- **DuckDB schema:** `raw_prices(symbol TEXT, datetime TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume DOUBLE)`

### Default Configuration
- **Symbols:** `["AAPL", "RELIANCE.NS", "RY.TO"]` (US, India, Canada)
- **Period:** `5d` (5 trading days)
- **Interval:** `5m` (5-minute bars)

---

## Step 0: Initial Scaffold ✅
**Date:** 2026-03-06 (pre-existing)
**Status:** Complete (with known gaps)

### What Existed
- Project structure generated by `scaffold.py` (sourced from DeepSeek-v3)
- Streamlit app shell with auth placeholder
- DuckDB connection with context manager
- Config via `@dataclass` + env vars
- Docker, Ruff, pytest, editorconfig configured
- dbt/Airflow skeleton directories

### Known Issues (from initial review)
1. `scaffold.py` itself is incomplete (missing function bodies)
2. `auth.py` blocks entire UI with `st.stop()`
3. `AppConfig` reads env vars at class-definition time (stale values possible)
4. Relative DuckDB path is CWD-dependent
5. No CI/CD pipeline
