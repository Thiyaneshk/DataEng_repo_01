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
