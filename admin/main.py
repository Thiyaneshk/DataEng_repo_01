"""
Phase 5.4: Admin Dashboard (Separate Streamlit App)
Port: 8502

Main entry point for admin-only features:
- Password authentication (admin/admin for MVP)
- Ticker and holdings management
- Index constituent management
- Pipeline health monitoring

Configuration:
- Runs on port 8502 in docker-compose
- Shares Postgres database with main app
- Uses session state for authentication
"""

import streamlit as st
from pathlib import Path

# Page configuration
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


def require_admin_password():
    """
    Simple password gate for admin app.
    
    Stores authentication in st.session_state so user only enters password once per session.
    For MVP: hardcoded "admin/admin"
    Future: Load from environment variable or secure password DB
    """
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        # Login page
        st.title("🔐 Admin Dashboard")
        st.markdown("---")
        
        with st.form("login_form"):
            st.markdown("### Access Required")
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••")
            submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            # Verify credentials (MVP: hardcoded)
            if username == "admin" and password == "admin":
                st.session_state.admin_authenticated = True
                st.success("✓ Authentication successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")
                st.info("MVP credentials: username=`admin`, password=`admin`")
        
        st.stop()  # Block all page content


def logout():
    """Clear authentication and return to login."""
    st.session_state.admin_authenticated = False
    st.rerun()


def main():
    """Main admin dashboard entry point."""
    
    # Require authentication first
    require_admin_password()
    
    # Sidebar: Navigation + Logout
    with st.sidebar:
        st.markdown("### 🔐 Admin Control Panel")
        st.markdown("---")
        
        # Navigation links
        page = st.radio(
            "Select Section",
            [
                "📊 Dashboard",
                "📝 Ticker Manager",
                "💰 Holdings Manager", 
                "📈 Index Manager",
                "❤️ Pipeline Health"
            ],
            index=0
        )
        
        st.markdown("---")
        
        # User info
        st.markdown(f"**Logged in as:** admin")
        
        # Logout button
        if st.button("🔓 Logout", use_container_width=True):
            logout()
    
    # Route pages based on selection
    if page == "📊 Dashboard":
        from pages import dashboard
        dashboard.show()
    
    elif page == "📝 Ticker Manager":
        from pages import ticker_manager
        ticker_manager.show()
    
    elif page == "💰 Holdings Manager":
        from pages import holdings_manager
        holdings_manager.show()
    
    elif page == "📈 Index Manager":
        from pages import index_manager
        index_manager.show()
    
    elif page == "❤️ Pipeline Health":
        from pages import pipeline_health
        pipeline_health.show()


if __name__ == "__main__":
    main()
