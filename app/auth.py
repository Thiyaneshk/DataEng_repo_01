"""Authentication helpers (Google/Gmail OAuth).

Learning goals:
- See how auth plugs into the app lifecycle.
- Use st.session_state to track login status.
- Implement a "Dev Mode" bypass to unblock UI development.
"""


from typing import Optional, Dict
import streamlit as st
import os
try:
    from streamlit_oauth import OAuth2Component
except ImportError:
    OAuth2Component = None

def require_login() -> Optional[Dict]:
    """
    Ensures the user is logged in.

    If logged in, returns the user dict.
    If not logged in, shows a login UI and stops the app.

    Features:
    - Real OAuth (skeleton) if secrets present.
    - Dev Mode Bypass if secrets missing.
    """

    # 1. Check if already logged in via session state
    if "user" in st.session_state:
        return st.session_state["user"]

    # 2. Check for secrets
    try:
        auth_secrets = st.secrets.get("google_auth")
    except Exception:
        auth_secrets = None

    st.title("🔐 Authentication")

    if not auth_secrets or OAuth2Component is None:
        st.warning("Google OAuth secrets missing or streamlit-oauth not installed.")
        st.info("To unblock your page development, you can use **Dev Mode** below.")
        if st.button("🚀 Dev Login (Bypass Auth)", type="primary", use_container_width=True):
            user = {
                "name": "Dev User",
                "email": "dev@example.com",
                "avatar": "🛠️"
            }
            st.session_state["user"] = user
            st.success("Logged in as Dev User!")
            st.rerun()
        st.stop()

    # 3. Real Google OAuth2 Flow

    oauth2 = OAuth2Component(
        auth_secrets["client_id"],
        auth_secrets["client_secret"],
        auth_secrets.get("redirect_uri", "http://localhost:8501")
    )

    result = oauth2.authorize_button(
        name="Login with Google",
        icon="https://developers.google.com/identity/images/g-logo.png",
        redirect_uri=auth_secrets.get("redirect_uri", "http://localhost:8501"),
        key="google_oauth_login",
        scope="openid email profile"
    )

    if result and "token" in result:
        import requests
        token = result["token"]
        userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
        headers = {"Authorization": f"Bearer {token['access_token']}"}
        resp = requests.get(userinfo_endpoint, headers=headers)
        if resp.status_code == 200:
            info = resp.json()
            user = {
                "name": info.get("name", info.get("email", "Google User")),
                "email": info.get("email", "user@gmail.com"),
                "avatar": info.get("picture", "📧")
            }
            st.session_state["user"] = user
            st.success(f"Logged in as {user['name']}!")
            st.rerun()
        else:
            st.error("Failed to fetch user info from Google.")
    else:
        st.info("Please log in with Google to continue.")
        st.stop()
    return None

def logout():
    """Clear session state and logout."""
    if "user" in st.session_state:
        del st.session_state["user"]
    st.rerun()
