"""
OAuth Authentication Module for Zeus Nexus
Supports Google OAuth2 for user authentication
"""

import streamlit as st
import jwt
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import secrets

class OAuthManager:
    """Manages OAuth authentication and session tokens"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.jwt_secret = secrets.token_urlsafe(32)
        
    def get_authorization_url(self) -> str:
        """Generate Google OAuth2 authorization URL"""
        state = secrets.token_urlsafe(16)
        st.session_state.oauth_state = state
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    def create_session_token(self, user_info: Dict) -> str:
        """Create JWT session token for authenticated user"""
        payload = {
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "sub": user_info.get("sub"),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    def verify_session_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT session token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_avatar(self, email: str) -> str:
        """Generate Gravatar URL from email"""
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=100"


def init_oauth():
    """Initialize OAuth configuration from environment/secrets"""
    if "oauth_manager" not in st.session_state:
        # Try to get from environment or use defaults for development
        client_id = st.secrets.get("GOOGLE_CLIENT_ID", "your-client-id.apps.googleusercontent.com")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET", "your-client-secret")
        redirect_uri = st.secrets.get("OAUTH_REDIRECT_URI", "https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com")
        
        st.session_state.oauth_manager = OAuthManager(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )


def check_authentication() -> bool:
    """Check if user is authenticated"""
    if "auth_token" in st.session_state:
        oauth_manager = st.session_state.get("oauth_manager")
        if oauth_manager:
            user_info = oauth_manager.verify_session_token(st.session_state.auth_token)
            if user_info:
                st.session_state.user_info = user_info
                return True
    return False


def show_login_page():
    """Display login page with OAuth button"""
    st.markdown("""
    <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
        }
        .login-title {
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        .login-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 3rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">⚡ Zeus Nexus AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">AI Pantheon Command Center</div>', unsafe_allow_html=True)
        
        st.markdown("### 🔐 Sign in to continue")
        
        if st.button("🔑 Sign in with Google", use_container_width=True, type="primary"):
            oauth_manager = st.session_state.get("oauth_manager")
            if oauth_manager:
                auth_url = oauth_manager.get_authorization_url()
                st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Demo mode (for testing without OAuth)
        with st.expander("🧪 Demo Mode (No Auth)"):
            st.warning("Demo mode bypasses authentication. Use only for testing!")
            if st.button("Enter Demo Mode", use_container_width=True):
                # Create demo user
                demo_user = {
                    "email": "demo@zeus-nexus.local",
                    "name": "Demo User",
                    "picture": "https://www.gravatar.com/avatar/demo?d=identicon&s=100",
                    "sub": "demo-user-id"
                }
                oauth_manager = st.session_state.get("oauth_manager")
                if oauth_manager:
                    token = oauth_manager.create_session_token(demo_user)
                    st.session_state.auth_token = token
                    st.session_state.user_info = demo_user
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


def show_user_sidebar():
    """Display user info and logout in sidebar"""
    if check_authentication():
        user_info = st.session_state.get("user_info", {})
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Profile")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                picture_url = user_info.get("picture", "")
                if picture_url:
                    st.image(picture_url, width=60)
            with col2:
                st.markdown(f"**{user_info.get('name', 'User')}**")
                st.markdown(f"_{user_info.get('email', '')}_")
            
            if st.button("🚪 Logout", use_container_width=True):
                # Clear session
                if "auth_token" in st.session_state:
                    del st.session_state.auth_token
                if "user_info" in st.session_state:
                    del st.session_state.user_info
                if "messages" in st.session_state:
                    del st.session_state.messages
                st.rerun()
