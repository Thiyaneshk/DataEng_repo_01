"""
Index Manager Page (04_Index_Manager.py)
View and sync stock market index constituents.
"""

import streamlit as st
from app.core.etl.indices import get_index_details, get_index_constituents, sync_all_indices
from app.db.connection import get_connection
from sqlalchemy import text
import pandas as pd


def show():
    """Render index manager page."""
    
    st.title("📈 Index Manager")
    st.markdown("Manage stock market indices and constituents")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Indices", "Sync"])
    
    # TAB 1: View Indices
    with tab1:
        st.markdown("### Available Indices")
        
        try:
            conn = get_connection()
            query = text("SELECT index_symbol, index_name, market, constituent_count, last_synced_at FROM indices ORDER BY market, index_symbol")
            result = conn.execute(query)
            
            indices_data = []
            for row in result:
                indices_data.append({
                    "Symbol": row[0],
                    "Name": row[1],
                    "Market": row[2],
                    "Constituents": row[3],
                    "Last Synced": row[4].strftime("%Y-%m-%d %H:%M") if row[4] else "Never"
                })
            
            if indices_data:
                df = pd.DataFrame(indices_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No indices found. Run migration first!")
        
        except Exception as e:
            st.error(f"Failed to load indices: {e}")
        
        st.markdown("---")
        
        # View constituents
        st.markdown("### View Constituents")
        
        try:
            conn = get_connection()
            index_symbols = [row[0] for row in conn.execute(text("SELECT index_symbol FROM indices ORDER BY index_symbol")).fetchall()]
            
            if index_symbols:
                selected_index = st.selectbox("Select Index", index_symbols)
                
                constituents = get_index_constituents(selected_index, limit=500)
                
                if constituents:
                    df = pd.DataFrame(constituents)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.info(f"Showing {len(constituents)} constituents")
                else:
                    st.info("No constituents yet. Run sync to populate.")
            else:
                st.warning("No indices available")
        
        except Exception as e:
            st.error(f"Failed to load constituents: {e}")
    
    # TAB 2: Sync
    with tab2:
        st.markdown("### Sync Indices")
        st.info("Manual trigger to fetch and load index constituents from data sources.")
        
        if st.button("🔄 Sync All Indices", use_container_width=True, key="sync_indices_manager"):
            with st.spinner("Syncing all indices... This may take a minute."):
                try:
                    results = sync_all_indices()
                    
                    st.success("✓ Sync complete!")
                    
                    # Show results
                    sync_summary = []
                    for idx_symbol, result in results.items():
                        if isinstance(result, dict) and result.get('status') != 'error':
                            sync_summary.append({
                                "Index": idx_symbol,
                                "Inserted": result.get('inserted', 0),
                                "Updated": result.get('updated', 0),
                                "Status": "✓ Success" if result.get('status') == 'success' else "⚠️ Partial"
                            })
                    
                    if sync_summary:
                        df = pd.DataFrame(sync_summary)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    st.json(results)
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Sync failed: {e}")
        
        st.markdown("---")
        st.markdown("### Sync Notes")
        st.markdown("""
        - **US Indices** (SPY, QQQ, IWM): Uses yfinance, limited details
        - **India Indices** (NIFTY50, NIFTY_IT): Uses seeded data, manual updates only
        - **Canada Indices** (TSX60): Uses yfinance
        
        Manual edits: Use DB directly or create CSV import feature in future.
        """)
