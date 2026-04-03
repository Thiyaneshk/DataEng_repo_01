# DE Template — Scaffolding Requirements & Status

> This file documents the original scaffolding requirements and what has been implemented.
> Keep this updated as features are built out — it helps AI agents understand project state.

---

## Original Requirements

### 1. Template Project
| Requirement | Status | Notes |
|---|---|---|
| Streamlit app | ✅ Done | `app/main.py` — entry point with page config |
| Gmail / Google OAuth hook | 🟡 Done (Mock/Dev) | `app/auth.py` unblocked with Dev Mode bypass |
| Config + secrets in TOML | ✅ Done | `.streamlit/config.toml` + `secrets.example.toml` |
| Clean folder structure | ✅ Done | `app/`, `scripts/`, `tests/`, `data/`, `dbt/`, `airflow/` |
| Best practices (linting, formatting, editorconfig) | ✅ Done | `ruff.toml`, `.editorconfig`, `pytest.ini` |

### 2. Multi-Run Story
| Requirement | Status | Notes |
|---|---|---|
| CLI to load/refresh DB | ✅ Done | `scripts/refresh_data.py` — real yfinance ETL |
| Streamlit run with `uv` (no Docker) for office laptop | ✅ Done | `uv run streamlit run app/main.py` |
| Same project runnable via Docker on Mac | ✅ Done | `Dockerfile` (bug-fixed: `uv.lock` copy) |

### 3. Data Stack Direction
| Requirement | Status | Notes |
|---|---|---|
| Start with DuckDB | ✅ Done | `app/db/connection.py` — context-manager connection |
| Later move to local Postgres | ⬜ Not started | TODO in `connection.py` (commented-out code) |
| Learn dbt first | ✅ Done | `dbt/profiles.yml` and `stg_prices.sql` created |
| Learn Airflow | 🟡 Skeleton | Empty placeholder DAG |
| yfinance as data source | ✅ Done | `app/core/etl/prices.py` — fetches OHLCV for AAPL, RELIANCE.NS, RY.TO |
| RAG + local LLM, vector search, ML | ⬜ Not started | `app/core/rag/` — empty `__init__.py` |

### 4. Quality & Tooling
| Requirement | Status | Notes |
|---|---|---|
| Cross-platform (Windows + Mac) | ✅ Done | uv + Docker |
| Git initialized | ✅ Done | Clean first commit |
| Linting config | ✅ Done | Ruff with F, E, W, I rules |
| Test config | ✅ Done | pytest with 7 passing tests |
| CI/CD pipeline | ❌ Missing | No `.github/workflows/` yet |

---

## Project Structure (Current)

```
de_template/
├── app/
│   ├── __init__.py
│   ├── main.py              # Streamlit entry point
│   ├── auth.py              # OAuth placeholder (st.stop())
│   ├── config.py            # AppConfig dataclass with env vars
│   ├── core/
│   │   ├── etl/
│   │   │   └── prices.py    # ✅ Real yfinance ETL
│   │   └── rag/
│   │       └── __init__.py  # ⬜ Empty placeholder
│   └── db/
│       └── connection.py    # DuckDB context manager
├── airflow/
│   ├── README.md
│   └── dags/
│       └── example_placeholder_dag.py  # 🟡 Empty stub
├── dbt/
│   ├── README.md
│   └── dbt_project.yml      # 🟡 Skeleton only
├── scripts/
│   └── refresh_data.py      # ✅ CLI: yfinance → DuckDB
├── tests/
│   ├── test_smoke.py         # ✅ Basic smoke test
│   └── test_etl.py           # ✅ 6 ETL tests (fetch + DuckDB)
├── data/
│   └── .gitkeep              # DB files gitignored
├── .streamlit/
│   ├── config.toml
│   └── secrets.example.toml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── ruff.toml
├── pytest.ini
├── .editorconfig
├── .gitignore
├── .dockerignore
└── README.md
```

---

## Build Roadmap

| Step | Description | Status |
|---|---|---|
| **Step 1** | Real ETL with yfinance | ✅ Complete |
| **Step 2** | dbt on top of DuckDB | ✅ Complete |
| **Step 3** | Indicators in Python (RSI, SuperTrend) | 🔄 In Progress |
| **Step 4** | Indicators in dbt SQL | ⬜ Planned |
| **Step 5** | Airflow skeleton DAG | ⬜ Planned |
| **Step 6** | Google OAuth implementation | ⬜ Planned |
| **Step 7** | Postgres migration path | ⬜ Planned |
| **Step 8** | RAG + vector search | ⬜ Planned |
| **Step 9** | CI/CD pipeline | ⬜ Planned |
