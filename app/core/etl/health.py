"""
Phase 5.3: Health Check Pipeline

Monitors pipeline health:
- Data freshness (last price update timestamp)
- API errors (yfinance connection issues)
- Index sync status
- Overall system health

Main functions:
- check_data_freshness() - Check if price data is stale
- check_api_errors() - Check for recent API failures
- report_health_status() - Dashboard-friendly summary
- log_health_check() - Write health check to database
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from app.db.connection import get_connection

logger = logging.getLogger(__name__)

# Data freshness thresholds
FRESHNESS_WARNING_HOURS = 4   # Warn if no data for 4 hours
FRESHNESS_ERROR_HOURS = 24    # Error if no data for 24 hours (1 day)


def check_data_freshness(symbols: Optional[List[str]] = None) -> Dict:
    """
    Check if price data is fresh for each symbol.
    
    Queries the prices table to find last update timestamp.
    Compares to now: if stale, logs warning/error.
    
    Args:
        symbols: List of symbols to check (default: all from user_stocks)
    
    Returns:
        Dict mapping symbol -> {status, last_update, lag_hours}
    """
    logger.info("Checking data freshness...")
    results = {}
    
    try:
        conn = get_connection()
        
        # Get symbols if not provided
        if symbols is None:
            query = text("SELECT DISTINCT symbol FROM prices ORDER BY symbol")
            res = conn.execute(query)
            symbols = [row[0] for row in res]
        
        now = datetime.utcnow()
        
        for symbol in symbols:
            try:
                # Get last price record for this symbol
                query = text("""
                    SELECT MAX(datetime) as last_update
                    FROM prices
                    WHERE symbol = :symbol
                """)
                res = conn.execute(query, {"symbol": symbol})
                row = res.fetchone()
                
                if not row or row[0] is None:
                    status = "error"
                    lag_hours = None
                    message = f"No price data found for {symbol}"
                else:
                    last_update = row[0]
                    lag_hours = (now - last_update).total_seconds() / 3600
                    
                    if lag_hours > FRESHNESS_ERROR_HOURS:
                        status = "error"
                        message = f"Data stale: last update {lag_hours:.1f} hours ago"
                    elif lag_hours > FRESHNESS_WARNING_HOURS:
                        status = "warning"
                        message = f"Data aging: last update {lag_hours:.1f} hours ago"
                    else:
                        status = "success"
                        message = f"Data fresh: updated {lag_hours:.1f} hours ago"
                
                results[symbol] = {
                    "status": status,
                    "message": message,
                    "last_update": row[0] if row and row[0] else None,
                    "lag_hours": lag_hours
                }
                
                # Log this check
                log_health_check(
                    check_type="data_freshness",
                    target=symbol,
                    status=status,
                    message=message,
                    metadata={
                        "lag_hours": lag_hours,
                        "last_update": row[0].isoformat() if row and row[0] else None
                    }
                )
            
            except Exception as e:
                logger.error(f"Error checking freshness for {symbol}: {e}")
                results[symbol] = {
                    "status": "error",
                    "message": f"Check failed: {str(e)}",
                    "last_update": None,
                    "lag_hours": None
                }
        
        logger.info(f"✓ Freshness check complete: {len(results)} symbols")
        return results
    
    except Exception as e:
        logger.error(f"Data freshness check failed: {e}")
        log_health_check(
            check_type="data_freshness",
            target="all",
            status="error",
            message=f"Freshness check failed: {str(e)}"
        )
        return {}


def check_api_errors(lookback_hours: int = 24) -> Dict:
    """
    Check for recent API/ETL errors.
    
    Queries health_checks table for error status in recent logs.
    Summarizes by target (yfinance_api, index_sync, etc.).
    
    Args:
        lookback_hours: How far back to look (default 24 hours)
    
    Returns:
        Dict with:
        - total_errors: count of errors
        - by_target: {target -> count}
        - most_recent: list of most recent errors
    """
    logger.info(f"Checking API errors (last {lookback_hours}h)...")
    
    try:
        conn = get_connection()
        
        # Count errors by target
        query = text("""
            SELECT target, COUNT(*) as error_count
            FROM health_checks
            WHERE status = 'error'
            AND checked_at > NOW() - INTERVAL :hours HOUR
            GROUP BY target
            ORDER BY error_count DESC
        """)
        res = conn.execute(query, {"hours": lookback_hours})
        by_target = {row[0]: row[1] for row in res}
        
        total_errors = sum(by_target.values())
        
        # Get most recent errors
        recent_query = text("""
            SELECT check_type, target, status, message, checked_at
            FROM health_checks
            WHERE status = 'error'
            AND checked_at > NOW() - INTERVAL :hours HOUR
            ORDER BY checked_at DESC
            LIMIT 10
        """)
        res = conn.execute(recent_query, {"hours": lookback_hours})
        most_recent = [
            {
                "check_type": row[0],
                "target": row[1],
                "status": row[2],
                "message": row[3],
                "checked_at": row[4]
            }
            for row in res
        ]
        
        result = {
            "total_errors": total_errors,
            "by_target": by_target,
            "most_recent": most_recent,
            "lookback_hours": lookback_hours,
            "status": "success" if total_errors == 0 else "warning"
        }
        
        logger.info(f"✓ Found {total_errors} recent errors")
        return result
    
    except Exception as e:
        logger.error(f"API error check failed: {e}")
        return {
            "total_errors": -1,
            "status": "error",
            "message": str(e)
        }


def report_health_status() -> Dict:
    """
    Generate comprehensive health status for dashboard.
    
    Combines:
    - Data freshness summary
    - API error summary
    - Index sync status
    - Overall health score (0-100)
    
    Returns:
        Dict with dashboard-friendly summary
    """
    logger.info("Generating health status report...")
    
    try:
        conn = get_connection()
        
        # 1. Data freshness summary
        freshness = check_data_freshness()
        symbols_ok = sum(1 for r in freshness.values() if r.get("status") in ["success", "warning"])
        symbols_error = sum(1 for r in freshness.values() if r.get("status") == "error")
        
        # 2. API errors summary
        api_errors = check_api_errors(lookback_hours=24)
        
        # 3. Index sync status
        index_query = text("""
            SELECT index_symbol, last_synced_at
            FROM indices
            ORDER BY last_synced_at DESC
        """)
        res = conn.execute(index_query)
        latest_sync = res.fetchone()
        latest_sync_at = latest_sync[1] if latest_sync else None
        
        # 4. Calculate health score (0-100)
        health_score = 100
        
        # Deduct for stale data
        if symbols_error > 0:
            health_score -= min(30, symbols_error * 5)  # Up to -30 for stale data
        
        # Deduct for API errors
        if api_errors.get("total_errors", 0) > 0:
            health_score -= min(20, api_errors["total_errors"] * 2)  # Up to -20 for errors
        
        # Deduct if indices not synced recently
        if latest_sync_at:
            hours_since_sync = (datetime.utcnow() - latest_sync_at).total_seconds() / 3600
            if hours_since_sync > 168:  # More than 1 week
                health_score -= 10
        else:
            health_score -= 15  # No sync ever
        
        health_score = max(0, health_score)  # Floor at 0
        
        # Health level
        if health_score >= 90:
            health_level = "🟢 Excellent"
        elif health_score >= 70:
            health_level = "🟡 Good"
        elif health_score >= 50:
            health_level = "🟠 Fair"
        else:
            health_level = "🔴 Poor"
        
        report = {
            "health_score": health_score,
            "health_level": health_level,
            "timestamp": datetime.utcnow().isoformat(),
            "data_freshness": {
                "symbols_ok": symbols_ok,
                "symbols_warning": sum(1 for r in freshness.values() if r.get("status") == "warning"),
                "symbols_error": symbols_error,
                "total": len(freshness)
            },
            "api_health": {
                "total_errors_24h": api_errors.get("total_errors", 0),
                "by_target": api_errors.get("by_target", {}),
                "most_recent_error": api_errors.get("most_recent", [{}])[0] if api_errors.get("most_recent") else None
            },
            "index_sync": {
                "latest_sync_at": latest_sync_at.isoformat() if latest_sync_at else None,
                "indices_count": len(res.fetchall() + [latest_sync]) if latest_sync else 0
            },
            "recommendations": []
        }
        
        # Add recommendations
        if symbols_error > 0:
            report["recommendations"].append(f"⚠️  {symbols_error} symbols have stale data. Check ETL pipeline.")
        
        if api_errors.get("total_errors", 0) > 0:
            report["recommendations"].append(f"⚠️  {api_errors['total_errors']} API errors in last 24h. Review logs.")
        
        if not latest_sync_at:
            report["recommendations"].append("📋 Run index sync: from app.core.etl.indices import sync_all_indices; sync_all_indices()")
        
        logger.info(f"✓ Health status: {health_level} (score: {health_score})")
        return report
    
    except Exception as e:
        logger.error(f"Health report generation failed: {e}")
        return {
            "health_score": 0,
            "health_level": "🔴 Error",
            "error": str(e)
        }


def log_health_check(
    check_type: str,
    target: str,
    status: str,
    message: str,
    metadata: Optional[Dict] = None
) -> int:
    """
    Write health check to database.
    
    Args:
        check_type: Type of check (data_freshness, api_error, index_sync, etc.)
        target: What was checked (symbol, API name, etc.)
        status: success, warning, or error
        message: Human-readable message
        metadata: Optional JSON metadata (dict)
    
    Returns:
        health_check_id (database record ID)
    """
    try:
        conn = get_connection()
        
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        
        query = text("""
            INSERT INTO health_checks (check_type, target, status, message, metadata)
            VALUES (:check_type, :target, :status, :message, :metadata::jsonb)
            RETURNING health_check_id
        """)
        
        result = conn.execute(query, {
            "check_type": check_type,
            "target": target,
            "status": status,
            "message": message,
            "metadata": metadata_json
        })
        
        health_check_id = result.fetchone()[0]
        conn.commit()
        
        logger.debug(f"Logged health check: {check_type}/{target} = {status}")
        return health_check_id
    
    except Exception as e:
        logger.error(f"Failed to log health check: {e}")
        return -1


if __name__ == "__main__":
    # Manual test: generate health report
    logging.basicConfig(level=logging.INFO)
    report = report_health_status()
    
    import json
    print("\nHealth Report:")
    print(json.dumps(report, indent=2, default=str))
