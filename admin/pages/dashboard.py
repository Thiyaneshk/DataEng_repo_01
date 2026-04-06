"""
Admin Dashboard Page (01_Dashboard.py)
Shows system overview, recent activities, and quick actions.
"""

import streamlit as st
from datetime import datetime
from app.db.connection import get_connection
from sqlalchemy import text


def show():
    """Render dashboard page."""
    
    st.title("📊 Admin Dashboard")
    st.markdown("System overview and quick actions")
    st.markdown("---")
    
    # 1. Health Status Overview
    with st.spinner("Loading health status..."):
        try:
            from app.core.etl.health import report_health_status
            health_report = report_health_status()
        except Exception as e:
            st.error(f"Failed to load health report: {e}")
            health_report = {"health_score": 0, "health_level": "🔴 Error"}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "System Health Score",
            f"{health_report.get('health_score', 0)}/100",
            "Overall pipeline health"
        )
    
    with col2:
        st.markdown(f"### {health_report.get('health_level', '🔴 Error')}")
    
    with col3:
        data_freshness = health_report.get('data_freshness', {})
        st.metric(
            "Data Points",
            data_freshness.get('symbols_ok', 0),
            f"{data_freshness.get('total', 0)} total"
        )
    
    with col4:
        api_health = health_report.get('api_health', {})
        st.metric(
            "API Errors (24h)",
            api_health.get('total_errors_24h', 0),
            "last 24 hours"
        )
    
    st.markdown("---")
    
    # 2. Recent Activities
    st.markdown("### 📋 Recent Activities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Latest Health Checks")
        try:
            conn = get_connection()
            query = text("""
                SELECT DISTINCT ON (check_type, target)
                    check_type, target, status, message, checked_at
                FROM health_checks
                ORDER BY check_type, target, checked_at DESC
                LIMIT 10
            """)
            result = conn.execute(query)
            
            checks = []
            for row in result:
                checks.append({
                    "Type": row[0],
                    "Target": row[1],
                    "Status": row[2],
                    "Message": row[3],
                    "Time": row[4].strftime("%H:%M:%S") if row[4] else "N/A"
                })
            
            if checks:
                import pandas as pd
                df = pd.DataFrame(checks)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No health checks yet")
        
        except Exception as e:
            st.error(f"Failed to load health checks: {e}")
    
    with col2:
        st.markdown("#### Database Stats")
        try:
            conn = get_connection()
            
            stats = {}
            
            # Count user stocks
            query = text("SELECT COUNT(*) FROM user_stocks")
            stats['user_stocks'] = conn.execute(query).fetchone()[0]
            
            # Count prices
            query = text("SELECT COUNT(*) FROM prices")
            stats['prices'] = conn.execute(query).fetchone()[0]
            
            # Count indices
            query = text("SELECT COUNT(*) FROM indices")
            stats['indices'] = conn.execute(query).fetchone()[0]
            
            # Count constituents
            query = text("SELECT COUNT(*) FROM index_constituents")
            stats['constituents'] = conn.execute(query).fetchone()[0]
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Watchlist/Holdings", stats['user_stocks'])
                st.metric("Indices", stats['indices'])
            with col_b:
                st.metric("Price Records", f"{stats['prices']:,}")
                st.metric("Constituents", f"{stats['constituents']:,}")
        
        except Exception as e:
            st.error(f"Failed to load stats: {e}")
    
    st.markdown("---")
    
    # 3. Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Sync All Indices", use_container_width=True, key="sync_indices"):
            with st.spinner("Syncing indices..."):
                try:
                    from app.core.etl.indices import sync_all_indices
                    results = sync_all_indices()
                    st.success("✓ Index sync complete!")
                    st.json(results)
                except Exception as e:
                    st.error(f"Sync failed: {e}")
    
    with col2:
        if st.button("📊 Refresh Health Check", use_container_width=True, key="refresh_health"):
            with st.spinner("Running health checks..."):
                try:
                    from app.core.etl.health import check_data_freshness, check_api_errors
                    freshness = check_data_freshness()
                    errors = check_api_errors()
                    st.success("✓ Health check complete!")
                    
                    if freshness:
                        st.write("**Data Freshness:**")
                        st.json({k: v['status'] for k, v in freshness.items()})
                    
                    if errors.get('total_errors', 0) > 0:
                        st.warning(f"**API Errors:** {errors['total_errors']}")
                    else:
                        st.success("✓ No recent API errors")
                
                except Exception as e:
                    st.error(f"Health check failed: {e}")
    
    with col3:
        if st.button("🗑️ Clear Old Logs", use_container_width=True, key="clear_logs"):
            with st.spinner("Clearing old health check logs..."):
                try:
                    conn = get_connection()
                    query = text("""
                        DELETE FROM health_checks
                        WHERE checked_at < NOW() - INTERVAL '30 DAYS'
                    """)
                    result = conn.execute(query)
                    conn.commit()
                    st.success(f"✓ Cleared old logs")
                except Exception as e:
                    st.error(f"Failed to clear logs: {e}")
    
    st.markdown("---")
    
    # 4. System Recommendations
    if health_report.get('recommendations'):
        st.markdown("### 💡 Recommendations")
        for rec in health_report['recommendations']:
            st.info(rec)
