# 📖 User & Admin Guide

This guide explains how to use the Equity Data Platform for both administrators and users.

## 🛡️ Admin Port (8502 or via Navigation)
The Admin role focuses on data ingestion, pipeline health, and watchlist management.

### 1. Data Management
- **Recent Refresh**: Use "Recent (Period)" to pull the latest 5 days of data for your watchlist.
- **Historical Backfill**: Use "Historical (Backfill)" to pull large chunks of data (e.g., 2024-01-01 to today).
- **dbt Transformations**: After loading data, click "Run dbt Transformations" to calculate RSI, EMA, and Bollinger Bands.
- **Observability**: Check "Recent ETL Runs" to see if your data loads were successful.

### 2. Portfolio Manager
- **Quick Import**: Select a global index (S&P 500, Nifty 50, TSX 60) and click "Import" to quickly populate your watchlist with major stocks.
- **Manual Entry**: Add stocks manually. Set `Quantity > 0` for holdings or `Quantity = 0` for watchlist only.
- **Maintenance**: Use "Quick Edit" to update notes or tags, or "Remove Stock" to clean up your list.

---

## 📈 User Port (8501 or via Navigation)
The User role focuses on analysis and visualization.

### 1. Home Dashboard
- Overview of your current holdings and portfolio value.
- Quick links to market analysis.

### 2. Stock Overview
- View raw price action for any symbol in the database.
- Interactive candlestick charts with automatic weekend removal for a clean view.

### 3. Technical Analysis
- Deep dive into technical indicators:
  - **EMAs**: 20, 50, and 200-period trends.
  - **RSI**: Momentum oscillator to find overbought/oversold levels.
  - **Bollinger Bands**: Volatility bands with a custom "Position" indicator.
- **Analysis Summary**: Automated insights based on technical rules.

### 4. AI Analyst (Local RAG)
- Chat with a local AI about your stocks.
- The AI uses the technical indicators calculated by dbt to give you context-aware answers.

---

## 🛠️ Step-by-Step Learning Flow
1. **Setup**: Ensure `.env` has `POSTGRES_URL` set.
2. **Populate**: Go to **Portfolio Manager** and import the S&P 500 constituents.
3. **Ingest**: Go to **Data Management**, select "Recent", and click "Refresh Market Data".
4. **Transform**: Click "Run dbt Transformations" (Check "Install Deps" if it's your first time).
5. **Analyze**: Head to **Technical Analysis** to see the calculated indicators on a chart.
6. **Chat**: Use the **AI Analyst** to ask: "What is the current trend for AAPL based on the RSI and EMA?"
