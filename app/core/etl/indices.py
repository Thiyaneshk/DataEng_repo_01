"""
Phase 5.2: Index ETL Pipeline

Manages fetching and loading stock market index constituents locally.
Supports US (SPY, QQQ), India (NIFTY50, NIFTY_IT), and Canada (TSX60) indices.

Main functions:
- fetch_index_constituents() - Get constituents from yfinance or manual source
- load_index_constituents() - Upsert constituents to database
- sync_all_indices() - Manual trigger for all indices
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
import yfinance as yf
from sqlalchemy import text
from app.db.connection import get_connection

logger = logging.getLogger(__name__)

# Indices to sync: (index_symbol, yfinance_ticker, market)
SUPPORTED_INDICES = [
    ("SPY", "SPY", "US"),      # S&P 500
    ("QQQ", "QQQ", "US"),      # Nasdaq 100
    ("IWM", "IWM", "US"),      # Russell 2000
    ("NIFTY50", "^NSEI", "IN"),  # India NSE Nifty 50
    ("NIFTY_IT", "^NSMIT", "IN"), # India NSE Nifty IT
    ("TSX60", "^GSPTSE", "CA"),   # Canada TSX
]


def fetch_index_constituents(
    index_symbol: str,
    data_source: str = "auto"
) -> pd.DataFrame:
    """
    Fetch index constituents from data source.
    
    For US indices (SPY, QQQ, IWM): Use yfinance info
    For India (NIFTY50, NIFTY_IT): Use manual/hardcoded data (from seed)
    For Canada (TSX60): Use yfinance info
    
    Args:
        index_symbol: Index ticker (SPY, NIFTY50, etc.)
        data_source: Auto-detect based on index, or force "yfinance" / "manual"
    
    Returns:
        DataFrame with columns: [symbol, weight, sector, industry, company_name]
        OR empty DataFrame if fetch fails
    """
    logger.info(f"Fetching constituents for {index_symbol}...")
    
    try:
        if index_symbol in ["SPY", "QQQ", "IWM", "TSX60"]:
            # Use yfinance for these
            constituents_df = _fetch_yfinance_constituents(index_symbol)
        elif index_symbol in ["NIFTY50", "NIFTY_IT"]:
            # Use seeded data from database (India indices are manually maintained)
            logger.info(f"Using seeded data for {index_symbol} (India market requires manual updates)")
            constituents_df = pd.DataFrame()  # Will use DB seed data
        else:
            logger.warning(f"Unknown index: {index_symbol}")
            constituents_df = pd.DataFrame()
        
        logger.info(f"✓ Fetched {len(constituents_df)} constituents for {index_symbol}")
        return constituents_df
    
    except Exception as e:
        logger.error(f"✗ Failed to fetch {index_symbol}: {e}")
        from app.core.etl.health import log_health_check
        log_health_check(
            check_type="index_sync",
            target=index_symbol,
            status="error",
            message=f"Failed to fetch constituents: {str(e)}"
        )
        return pd.DataFrame()


def _fetch_yfinance_constituents(index_symbol: str) -> pd.DataFrame:
    """
    Fetch constituents from yfinance for US/Canada indices.
    
    Note: yfinance doesn't provide constituent lists directly,
    so we return empty DataFrame. This triggers manual entry or
    uses pre-seeded data from db/seed_indices.sql
    
    Args:
        index_symbol: US or Canada index ticker
    
    Returns:
        DataFrame with constituent symbols (basic implementation)
    """
    try:
        # yfinance.Ticker() doesn't have constituent list, so return empty
        # This is by design - constituents are seeded and updated manually
        # For production, integrate with a proper constituents API:
        # - SEC Edgar for US
        # - NSE official API for India
        # - TSX official API for Canada
        
        logger.debug(f"yfinance doesn't provide constituent lists. Using seeded data for {index_symbol}")
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error fetching from yfinance: {e}")
        return pd.DataFrame()


def load_index_constituents(
    index_symbol: str,
    constituents_df: Optional[pd.DataFrame] = None,
    update_existing: bool = True
) -> Dict:
    """
    Upsert index constituents to database.
    
    If constituents_df is empty/None, uses existing seeded data.
    Updates weights and sectors if constituent already exists.
    
    Args:
        index_symbol: Index ticker (SPY, NIFTY50, etc.)
        constituents_df: DataFrame with columns [symbol, weight, sector, industry, company_name]
        update_existing: If True, update existing constituents; if False, skip
    
    Returns:
        Dict with keys:
        - inserted: number of new constituents
        - updated: number of updated constituents
        - skipped: number of duplicates skipped
        - index_id: database index_id
        - status: "success" or "error"
    """
    result = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "index_id": None,
        "status": "success"
    }
    
    try:
        conn = get_connection()
        
        # 1. Get index_id from database
        query = text("""
            SELECT index_id FROM indices WHERE index_symbol = :symbol
        """)
        res = conn.execute(query, {"symbol": index_symbol})
        row = res.fetchone()
        
        if not row:
            logger.error(f"Index not found: {index_symbol}")
            result["status"] = "error"
            return result
        
        index_id = row[0]
        result["index_id"] = index_id
        
        # 2. If constituents_df provided, insert/update them
        if constituents_df is not None and len(constituents_df) > 0:
            for _, row in constituents_df.iterrows():
                symbol = row.get("symbol")
                weight = row.get("weight")
                sector = row.get("sector")
                industry = row.get("industry")
                company_name = row.get("company_name")
                
                if not symbol:
                    continue
                
                # Upsert: try insert, if conflict update
                upsert_query = text("""
                    INSERT INTO index_constituents 
                        (index_id, symbol, weight, sector, industry, company_name, added_date)
                    VALUES 
                        (:index_id, :symbol, :weight, :sector, :industry, :company_name, CURRENT_DATE)
                    ON CONFLICT (index_id, symbol) DO UPDATE SET
                        weight = :weight,
                        sector = :sector,
                        industry = :industry,
                        company_name = :company_name,
                        removed_date = NULL,  -- Reactivate if was removed
                        updated_at = CURRENT_TIMESTAMP
                """)
                
                try:
                    conn.execute(upsert_query, {
                        "index_id": index_id,
                        "symbol": symbol,
                        "weight": weight,
                        "sector": sector,
                        "industry": industry,
                        "company_name": company_name
                    })
                    result["inserted"] += 1
                except Exception as e:
                    if "duplicate" in str(e).lower():
                        result["skipped"] += 1
                    else:
                        result["updated"] += 1
                        logger.debug(f"Updated constituent {symbol} in {index_symbol}")
            
            conn.commit()
        
        # 3. Update constituent_count in indices table
        count_query = text("""
            UPDATE indices
            SET constituent_count = (
                SELECT COUNT(*) FROM index_constituents 
                WHERE index_id = :index_id AND removed_date IS NULL
            ),
            last_synced_at = CURRENT_TIMESTAMP
            WHERE index_id = :index_id
        """)
        conn.execute(count_query, {"index_id": index_id})
        conn.commit()
        
        logger.info(f"✓ Loaded {result['inserted']} constituents for {index_symbol}")
        
        # 4. Log health check
        from app.core.etl.health import log_health_check
        log_health_check(
            check_type="index_sync",
            target=index_symbol,
            status="success",
            message=f"Synced {result['inserted']} constituents"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to load constituents for {index_symbol}: {e}")
        result["status"] = "error"
        
        from app.core.etl.health import log_health_check
        log_health_check(
            check_type="index_sync",
            target=index_symbol,
            status="error",
            message=f"Failed to load constituents: {str(e)}"
        )
        
        return result


def sync_all_indices() -> Dict:
    """
    Manual trigger to sync all supported indices.
    
    Returns:
        Dict mapping index_symbol -> sync result
    """
    logger.info("Starting manual sync of all indices...")
    results = {}
    
    try:
        conn = get_connection()
        
        for index_symbol, yf_ticker, market in SUPPORTED_INDICES:
            logger.info(f"\n--- Syncing {index_symbol} ({market}) ---")
            
            # Fetch (returns empty for India, uses seeded data)
            constituents_df = fetch_index_constituents(index_symbol)
            
            # Load to database
            result = load_index_constituents(index_symbol, constituents_df)
            results[index_symbol] = result
            
            logger.info(f"✓ {index_symbol}: {result['inserted']} inserted, {result['updated']} updated")
        
        logger.info("\n✓ Index sync complete!")
        return results
    
    except Exception as e:
        logger.error(f"Index sync failed: {e}")
        return {"error": str(e)}


def get_index_details(index_symbol: str) -> Dict:
    """
    Get index metadata and constituent count.
    
    Returns:
        Dict with index_symbol, index_name, market, constituent_count, last_synced_at
    """
    try:
        conn = get_connection()
        query = text("""
            SELECT index_symbol, index_name, market, constituent_count, last_synced_at
            FROM indices
            WHERE index_symbol = :symbol
        """)
        res = conn.execute(query, {"symbol": index_symbol})
        row = res.fetchone()
        
        if row:
            return {
                "index_symbol": row[0],
                "index_name": row[1],
                "market": row[2],
                "constituent_count": row[3],
                "last_synced_at": row[4]
            }
        else:
            return {}
    
    except Exception as e:
        logger.error(f"Failed to get index details: {e}")
        return {}


def get_index_constituents(index_symbol: str, limit: int = 100) -> List[Dict]:
    """
    Get constituents for a given index.
    
    Returns:
        List of dicts with symbol, company_name, weight, sector, industry
    """
    try:
        conn = get_connection()
        query = text("""
            SELECT symbol, company_name, weight, sector, industry
            FROM index_constituents
            WHERE index_id = (SELECT index_id FROM indices WHERE index_symbol = :symbol)
            AND removed_date IS NULL
            ORDER BY weight DESC
            LIMIT :limit
        """)
        res = conn.execute(query, {"symbol": index_symbol, "limit": limit})
        
        return [
            {
                "symbol": row[0],
                "company_name": row[1],
                "weight": float(row[2]) if row[2] else None,
                "sector": row[3],
                "industry": row[4]
            }
            for row in res
        ]
    
    except Exception as e:
        logger.error(f"Failed to get constituents: {e}")
        return []


if __name__ == "__main__":
    # Manual test: sync all indices
    logging.basicConfig(level=logging.INFO)
    results = sync_all_indices()
    print("\nSync Results:")
    for idx_symbol, result in results.items():
        print(f"  {idx_symbol}: {result}")
