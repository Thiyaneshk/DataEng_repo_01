from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
import pandas as pd
from sqlalchemy import text
from app.db.connection import get_connection
from app.config import get_config

app = FastAPI(
    title="Equity Market Data API",
    description="API for accessing market prices and technical indicators.",
    version="0.1.0"
)

# --- Dependency ---
def get_db():
    with get_connection() as conn:
        yield conn

@app.get("/")
def read_root():
    return {"message": "Welcome to the Equity Market Data API", "docs": "/docs"}

@app.get("/stocks")
def list_stocks(db=Depends(get_db)):
    """List all symbols currently in the database."""
    query = text("SELECT DISTINCT symbol FROM raw_prices_5m ORDER BY symbol")
    result = db.execute(query).fetchall()
    return {"symbols": [r[0] for r in result]}

@app.get("/prices/{symbol}")
def get_prices(symbol: str, limit: int = 100, db=Depends(get_db)):
    """Fetch recent prices for a specific symbol."""
    query = text("SELECT * FROM raw_prices_5m WHERE symbol = :sym ORDER BY datetime DESC LIMIT :limit")
    df = pd.read_sql(query, db, params={"sym": symbol.upper(), "limit": limit})
    if df.empty:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return df.to_dict(orient="records")

@app.get("/indicators/{symbol}")
def get_indicators(symbol: str, db=Depends(get_db)):
    """Fetch dbt-calculated indicators for a specific symbol."""
    try:
        query = text("SELECT * FROM fct_equity_features_1d WHERE symbol = :sym ORDER BY trade_date DESC LIMIT 50")
        df = pd.read_sql(query, db, params={"sym": symbol.upper()})
        if df.empty:
            raise HTTPException(status_code=404, detail="Indicators not found for this symbol")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# To run:
# uv run uvicorn api.main:app --reload
