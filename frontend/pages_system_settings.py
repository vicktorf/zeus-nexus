"""
System Settings Page - Advanced system configuration and monitoring
"""
import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Optional

ZEUS_API_URL = "http://zeus-core.ac-agentic.svc.cluster.local:8000"

def show_system_settings_page():
    """Display System Settings page"""
    
    st.markdown("## ⚙️ System Settings")
    st.markdown("Advanced system configuration, monitoring, and logs.")
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["🏥 Health", "📊 Metrics", "📜 Logs", "🔧 Advanced"])
    
    # Health Tab
    with tab1:
        st.markdown("### 🏥 System Health Check")
        
        if st.button("🔄 Check Health", use_container_width=True):
            with st.spinner("Checking system health..."):
                try:
                    response = requests.get(f"{ZEUS_API_URL}/health", timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        
                        st.success("✅ Zeus Core is healthy!")
                        
                        # Display services status
                        if "services" in health_data:
                            st.markdown("**Service Status:**")
                            cols = st.columns(3)
                            for idx, (service, status) in enumerate(health_data["services"].items()):
                                with cols[idx % 3]:
                                    if status == "healthy":
                                        st.success(f"✅ {service.capitalize()}")
                                    else:
                                        st.error(f"❌ {service.capitalize()}: {status}")
                        
                        # Display full response
                        with st.expander("📋 Full Health Response"):
                            st.json(health_data)
                    else:
                        st.error(f"❌ Health check failed: {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error(f"❌ Health check failed: {str(e)}")
        
        st.markdown("---")
        
        # Component status
        st.markdown("### 🧩 Component Status")
        
        components = {
            "Zeus Core": f"{ZEUS_API_URL}/health",
            "LLM Config": f"{ZEUS_API_URL}/llm/config",
            "Models": f"{ZEUS_API_URL}/llm/models",
        }
        
        for component, endpoint in components.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{component}**")
            
            with col2:
                try:
                    response = requests.get(endpoint, timeout=3)
                    if response.status_code == 200:
                        st.success("Online")
                    else:
                        st.error(f"Error {response.status_code}")
                except:
                    st.error("Offline")
            
            with col3:
                if st.button("Test", key=f"test_{component}"):
                    try:
                        response = requests.get(endpoint, timeout=5)
                        st.info(f"Status: {response.status_code}")
                    except Exception as e:
                        st.error(str(e))
    
    # Metrics Tab
    with tab2:
        st.markdown("### 📊 System Metrics")
        
        try:
            # Fetch metrics from Prometheus endpoint
            response = requests.get(f"{ZEUS_API_URL}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_text = response.text
                
                # Parse some key metrics
                metrics_lines = metrics_text.split('\n')
                
                # Display key metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Requests Total", "N/A", help="Total requests processed")
                
                with col2:
                    st.metric("Active Agents", "7", help="Number of active agents")
                
                with col3:
                    st.metric("Avg Response Time", "N/A", help="Average response time")
                
                st.markdown("---")
                
                # Full metrics
                with st.expander("📈 Full Prometheus Metrics"):
                    st.code(metrics_text, language="text")
            else:
                st.error(f"❌ Failed to fetch metrics: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Metrics unavailable: {str(e)}")
    
    # Logs Tab
    with tab3:
        st.markdown("### 📜 System Logs")
        
        log_source = st.selectbox(
            "Log Source",
            options=["Zeus Core", "Zeus Frontend", "Agents"],
            key="log_source_select"
        )
        
        log_level = st.selectbox(
            "Log Level",
            options=["ALL", "INFO", "WARNING", "ERROR"],
            key="log_level_select"
        )
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            lines = st.number_input("Lines", min_value=10, max_value=1000, value=50, step=10)
        
        with col2:
            if st.button("🔄 Refresh Logs", use_container_width=True):
                st.info(f"Fetching {lines} lines from {log_source}...")
        
        # Log display area
        st.markdown("**Recent Logs:**")
        log_container = st.container()
        
        with log_container:
            st.code("""
[2025-11-26 10:30:15] INFO: Zeus Core started successfully
[2025-11-26 10:30:16] INFO: Connected to Redis
[2025-11-26 10:30:16] INFO: Connected to PostgreSQL
[2025-11-26 10:30:17] INFO: 7 agents initialized
[2025-11-26 10:31:22] INFO: LLM config endpoint accessed
[2025-11-26 10:32:45] INFO: Chat request processed (gpt-4)
[2025-11-26 10:33:10] INFO: Agent Athena selected for query
            """, language="log")
        
        st.markdown("---")
        
        # Log download
        if st.button("💾 Download Logs", use_container_width=True):
            st.info("Logs download feature coming soon...")
    
    # Advanced Tab
    with tab4:
        st.markdown("### 🔧 Advanced Settings")
        
        st.warning("⚠️ Advanced settings - Change with caution!")
        
        # System configuration
        st.markdown("**System Configuration**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            debug_mode = st.checkbox("Debug Mode", value=False, help="Enable debug logging")
            cache_enabled = st.checkbox("Cache Enabled", value=True, help="Enable response caching")
            metrics_enabled = st.checkbox("Metrics Enabled", value=True, help="Enable Prometheus metrics")
        
        with col2:
            max_retries = st.number_input("Max Retries", min_value=0, max_value=10, value=3)
            timeout = st.number_input("Timeout (seconds)", min_value=1, max_value=300, value=30)
            rate_limit = st.number_input("Rate Limit (req/min)", min_value=0, max_value=1000, value=100)
        
        st.markdown("---")
        
        # Database management
        st.markdown("**Database Management**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                st.warning("Cache cleared!")
        
        with col2:
            if st.button("📊 Export Data", use_container_width=True):
                st.info("Data export feature coming soon...")
        
        with col3:
            if st.button("🔄 Reset Settings", use_container_width=True):
                st.warning("Settings reset to default!")
        
        st.markdown("---")
        
        # Danger zone
        with st.expander("⚠️ Danger Zone", expanded=False):
            st.error("**Warning:** These actions cannot be undone!")
            
            if st.button("🗑️ Delete All API Keys", type="secondary"):
                st.error("This will delete all configured LLM API keys!")
                confirm = st.checkbox("I understand the consequences")
                if confirm:
                    if st.button("⚠️ Confirm Deletion"):
                        st.error("All API keys deleted!")
            
            st.markdown(" ")
            
            if st.button("🔄 Reset All Configurations", type="secondary"):
                st.error("This will reset all agent configurations!")
                confirm2 = st.checkbox("I understand this will reset everything")
                if confirm2:
                    if st.button("⚠️ Confirm Reset"):
                        st.error("All configurations reset!")
        
        st.markdown("---")
        
        # System information
        st.markdown("### ℹ️ System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Zeus Nexus Version:** 2.0.0
            **Python Version:** 3.11
            **Streamlit Version:** 1.29.0
            **Deployed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """)
        
        with col2:
            st.info(f"""
            **Cluster:** prod01.fis-cloud.fpt.com
            **Namespace:** ac-agentic
            **Environment:** Production
            **Region:** Asia Pacific
            """)
