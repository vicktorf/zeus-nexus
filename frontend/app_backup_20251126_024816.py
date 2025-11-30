"""
Zeus Nexus AI - Main Application
Multi-LLM AI Agent Platform with Collapsible Sidebar
"""
import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional

# Import page modules
from pages_llm_setup import show_llm_setup_page
from pages_agent_config import show_agent_configuration_page
from pages_system_settings import show_system_settings_page

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="⚡ Zeus Nexus AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .agent-card {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #667eea;
        margin: 0.5rem 0;
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
    }
    
    /* Sidebar toggle button enhancement */
    button[kind="header"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Zeus Core API configuration
ZEUS_API_URL = "https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "selected_llm" not in st.session_state:
    st.session_state.selected_llm = "gpt-4"
if "agents" not in st.session_state:
    st.session_state.agents = []
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

# Sidebar with collapsible menu
with st.sidebar:
    # Header with collapse toggle
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("## ⚡ Zeus Nexus")
    with col2:
        if st.button("☰", key="sidebar_toggle", help="Toggle sidebar"):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
    
    st.markdown("---")
    
    if not st.session_state.sidebar_collapsed:
        # Navigation menu
        st.markdown("### 🧭 Navigation")
        
        # Chat option
        if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.current_page == "chat" else "secondary"):
            st.session_state.current_page = "chat"
            st.rerun()
        
        # Settings menu
        st.markdown("**⚙️ Settings**")
        
        if st.button("  🤖 LLM Setup", use_container_width=True, type="primary" if st.session_state.current_page == "llm_setup" else "secondary"):
            st.session_state.current_page = "llm_setup"
            st.rerun()
        
        if st.button("  🎭 Agent Config", use_container_width=True, type="primary" if st.session_state.current_page == "agent_config" else "secondary"):
            st.session_state.current_page = "agent_config"
            st.rerun()
        
        if st.button("  ⚙️ System", use_container_width=True, type="primary" if st.session_state.current_page == "system_settings" else "secondary"):
            st.session_state.current_page = "system_settings"
            st.rerun()
        
        st.markdown("---")
        
        # Chat-specific controls (only show when on chat page)
        if st.session_state.current_page == "chat":
            st.markdown("### 🤖 Chat Configuration")
            
            # LLM Model Selector - Fetch from backend
            st.markdown("**Select LLM Model:**")
            
            # Load available models
            if not st.session_state.available_models:
                with st.spinner("Loading models..."):
                    try:
                        response = requests.get(f"{ZEUS_API_URL}/llm/models", timeout=5)
                        if response.status_code == 200:
                            all_models = response.json()
                            # Filter only configured models
                            st.session_state.available_models = [
                                model for model in all_models 
                                if model.get("api_key_configured", False)
                            ]
                        else:
                            st.error("❌ Failed to load models")
                            st.session_state.available_models = []
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.available_models = []
            
            if st.session_state.available_models:
                # Create model options with provider info
                model_options = {
                    f"{model['model']} ({model['provider'].upper()})": model['model']
                    for model in st.session_state.available_models
                }
                
                # Find current selection
                current_display = None
                for display, model_id in model_options.items():
                    if model_id == st.session_state.selected_llm:
                        current_display = display
                        break
                
                if not current_display and model_options:
                    # Default to first available model
                    current_display = list(model_options.keys())[0]
                    st.session_state.selected_llm = model_options[current_display]
                
                selected_display = st.selectbox(
                    "Model:",
                    list(model_options.keys()),
                    index=list(model_options.keys()).index(current_display) if current_display else 0,
                    label_visibility="collapsed"
                )
                st.session_state.selected_llm = model_options[selected_display]
                
                # Show model info
                selected_model_info = next(
                    (m for m in st.session_state.available_models if m['model'] == st.session_state.selected_llm),
                    None
                )
                if selected_model_info:
                    with st.expander("ℹ️ Model Info"):
                        st.caption(f"**Context:** {selected_model_info['context_length']:,} tokens")
                        st.caption(f"**Cost In:** ${selected_model_info['cost_per_1k_input']}/1k")
                        st.caption(f"**Cost Out:** ${selected_model_info['cost_per_1k_output']}/1k")
            else:
                st.warning("⚠️ No models configured")
                if st.button("🔧 Configure LLMs"):
                    st.session_state.current_page = "llm_setup"
                    st.rerun()
            
            st.markdown("---")
            
            # Session controls
            st.markdown("**Session:**")
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.session_id = None
                st.rerun()
    
    # Compact mode (sidebar collapsed)
    else:
        st.markdown("🧭")
        if st.button("💬", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
        if st.button("🤖", use_container_width=True):
            st.session_state.current_page = "llm_setup"
            st.rerun()
        if st.button("🎭", use_container_width=True):
            st.session_state.current_page = "agent_config"
            st.rerun()
        if st.button("⚙️", use_container_width=True):
            st.session_state.current_page = "system_settings"
            st.rerun()

# Main content area - Route to appropriate page
if st.session_state.current_page == "llm_setup":
    show_llm_setup_page()

elif st.session_state.current_page == "agent_config":
    show_agent_configuration_page()

elif st.session_state.current_page == "system_settings":
    show_system_settings_page()

else:  # Default: Chat page
    st.markdown('<div class="main-header">⚡ Zeus Nexus AI Pantheon</div>', unsafe_allow_html=True)
    
    # Info cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💬 Messages", len(st.session_state.messages))
    with col2:
        st.metric("🤖 Active Agents", len(st.session_state.agents) if st.session_state.agents else 7)
    with col3:
        model_name = st.session_state.selected_llm.split('-')[0].upper() if st.session_state.selected_llm else "N/A"
        st.metric("🧠 LLM Model", model_name)
    with col4:
        session_status = "Active" if st.session_state.session_id else "New"
        st.metric("📡 Session", session_status)
    
    st.markdown("---")
    
    # Chat container
    st.markdown("### 💬 Chat with Zeus")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show metadata for assistant messages
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("📊 Response Metadata"):
                    st.json(message["metadata"])
    
    # Chat input
    if prompt := st.chat_input("Ask Zeus anything..."):
        # Check if LLM is configured
        if not st.session_state.available_models:
            st.error("⚠️ No LLM models configured. Please configure LLM providers first.")
            if st.button("🔧 Go to LLM Setup"):
                st.session_state.current_page = "llm_setup"
                st.rerun()
        else:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Send to Zeus Core API
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                
                with st.spinner("Zeus is thinking..."):
                    try:
                        payload = {
                            "message": prompt,
                            "llm_model": st.session_state.selected_llm
                        }
                        
                        if st.session_state.session_id:
                            payload["session_id"] = st.session_state.session_id
                        
                        response = requests.post(
                            f"{ZEUS_API_URL}/chat",
                            json=payload,
                            headers={"Content-Type": "application/json"},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Update session ID
                            st.session_state.session_id = data.get("session_id")
                            
                            # Display response
                            response_text = data.get("response", "No response")
                            message_placeholder.markdown(response_text)
                            
                            # Display metadata
                            metadata = {
                                "agent": data.get("agent"),
                                "session_id": data.get("session_id"),
                                "timestamp": data.get("timestamp"),
                                "metadata": data.get("metadata", {})
                            }
                            
                            with metadata_placeholder.expander("📊 Response Metadata"):
                                st.json(metadata)
                            
                            # Add assistant message to chat
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_text,
                                "metadata": metadata
                            })
                            
                        else:
                            error_msg = f"❌ Error: {response.status_code} - {response.text}"
                            message_placeholder.error(error_msg)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_msg
                            })
                            
                    except requests.exceptions.Timeout:
                        error_msg = "❌ Request timeout. Zeus might be busy."
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>⚡ <strong>Zeus Nexus AI Pantheon</strong> - Powered by OpenShift & LangChain</p>
        <p style='font-size: 0.8rem;'>🔗 API: <code>zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com</code></p>
    </div>
    """,
    unsafe_allow_html=True
)
