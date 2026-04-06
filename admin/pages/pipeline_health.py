"""
Pipeline Health Page (05_Pipeline_Health.py)
Monitor data freshness, API errors, and system health.
"""

import streamlit as st
from app.core.etl.health import report_health_status, check_data_freshness, check_api_errors
import pandas as pd


def show():
    """Render pipeline health page."""
    
    st.title("❤️ Pipeline Health")
    st.markdown("System health monitoring and diagnostics")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["Health Report", "Data Freshness", "API Errors"])
    
    # TAB 1: Health Report
    with tab1:
        st.markdown("### System Health Report")
        
        with st.spinner("Loading health report..."):
            try:
                report = report_health_status()
                
                # Main health score
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Health Score",
                        f"{report.get('health_score', 0)}/100",
                        f"Status: {report.get('health_level', 'Unknown')}"
                    )
                
                with col2:
                    st.metric(
                        report.get('health_level', '🔴 Error'),
                        "",
                        f"Last updated: {report.get('timestamp', 'Unknown')}"
                    )
                
                st.markdown("---")
                
                # Data Freshness
                st.markdown("### Data Freshness")
                data_fresh = report.get('data_freshness', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✓ Fresh Data", data_fresh.get('symbols_ok', 0))
                with col2:
                    st.metric("⚠️ Aging Data", data_fresh.get('symbols_warning', 0))
                with col3:
                    st.metric("❌ Stale Data", data_fresh.get('symbols_error', 0))
                
                st.markdown("---")
                
                # API Health
                st.markdown("### API Health")
                api_health = report.get('api_health', {})
                st.metric(f"API Errors (24h): {api_health.get('total_errors_24h', 0)}")
                
                if api_health.get('by_target'):
                    st.write("**Errors by Target:**")
                    st.json(api_health['by_target'])
                
                if api_health.get('most_recent_error'):
                    st.write("**Most Recent Error:**")
                    error = api_health['most_recent_error']
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Type:** {error.get('check_type')}")
                    col2.write(f"**Target:** {error.get('target')}")
                    col3.write(f"**Status:** {error.get('status')}")
                    st.text(f"Message: {error.get('message')}")
                
                st.markdown("---")
                
                # Recommendations
                if report.get('recommendations'):
                    st.markdown("### 💡 Recommendations")
                    for rec in report['recommendations']:
                        st.info(rec)
            
            except Exception as e:
                st.error(f"Failed to load health report: {e}")
    
    # TAB 2: Data Freshness
    with tab2:
        st.markdown("### Data Freshness Check")
        
        if st.button("🔍 Run Freshness Check", use_container_width=True, key="run_freshness"):
            with st.spinner("Checking data freshness for all symbols..."):
                try:
                    freshness = check_data_freshness()
                    
                    if freshness:
                        df_data = []
                        for symbol, details in freshness.items():
                            df_data.append({
                                "Symbol": symbol,
                                "Status": details.get('status', 'unknown'),
                                "Last Update": details.get('last_update'),
                                "Lag (hours)": f"{details.get('lag_hours', 0):.1f}" if details.get('lag_hours') else "N/A",
                                "Message": details.get('message', '')
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Summary
                        col1, col2, col3 = st.columns(3)
                        col1.metric("✓ Fresh", len([d for d in df_data if d['Status'] in ['success', 'warning']]))
                        col2.metric("⚠️ Aging", len([d for d in df_data if d['Status'] == 'warning']))
                        col3.metric("❌ Stale", len([d for d in df_data if d['Status'] == 'error']))
                    else:
                        st.info("No symbols with data yet")
                
                except Exception as e:
                    st.error(f"Freshness check failed: {e}")
    
    # TAB 3: API Errors
    with tab3:
        st.markdown("### API Error Log")
        
        # Lookback period selector
        lookback = st.slider("Show errors from last (hours)", 1, 168, 24)
        
        if st.button("📋 Check API Errors", use_container_width=True, key="run_api_errors"):
            with st.spinner(f"Checking API errors from last {lookback}h..."):
                try:
                    errors = check_api_errors(lookback_hours=lookback)
                    
                    st.metric(f"Total Errors ({lookback}h)", errors.get('total_errors_24h', 0))
                    
                    if errors.get('by_target'):
                        st.markdown("**Errors by Target:**")
                        for target, count in errors['by_target'].items():
                            col1, col2 = st.columns([3, 1])
                            col1.write(target)
                            col2.metric(count, "errors")
                    
                    if errors.get('most_recent'):
                        st.markdown("**Recent Errors:**")
                        for error in errors['most_recent'][:5]:
                            with st.expander(f"{error['check_type']} - {error['target']} - {error['checked_at']}"):
                                st.write(f"**Status:** {error['status']}")
                                st.write(f"**Message:** {error['message']}")
                
                except Exception as e:
                    st.error(f"Error check failed: {e}")
