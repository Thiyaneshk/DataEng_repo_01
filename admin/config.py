"""
Admin application configuration and shared utilities.
"""

import os
from typing import Optional
from pathlib import Path

# Django-like settings for admin app
class AdminConfig:
    """Admin app configuration settings."""
    
    # Security
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # Should be in .env for production
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    
    # Database
    DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/app.duckdb")
    POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/stock_ml")
    
    # App settings
    APP_NAME = os.getenv("APP_NAME", "Stock ML Admin")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def get_duckdb_path(cls) -> Path:
        """Get the DuckDB database path."""
        return Path(cls.DUCKDB_PATH)
    
    @classmethod
    def get_postgres_url(cls) -> str:
        """Get the PostgreSQL connection URL."""
        return cls.POSTGRES_URL


# Streamlit configuration helper
def configure_streamlit_admin():
    """Configure Streamlit for admin app."""
    import streamlit as st
    
    st.set_page_config(
        page_title="Stock ML Admin",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .admin-header { font-size: 28px; font-weight: bold; color: #1f77b4; }
        .admin-subheader { font-size: 18px; color: #555; margin-bottom: 20px; }
        .success-box { padding: 10px; border-radius: 5px; background-color: #d4edda; border: 1px solid #c3e6cb; }
        .error-box { padding: 10px; border-radius: 5px; background-color: #f8d7da; border: 1px solid #f5c6cb; }
        .warning-box { padding: 10px; border-radius: 5px; background-color: #fff3cd; border: 1px solid #ffeaa7; }
    </style>
    """, unsafe_allow_html=True)
