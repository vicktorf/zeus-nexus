import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional
from settings_page import show_settings_page

# Page config
st.set_page_config(
    page_title="⚡ Zeus Nexus AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #667eea;
        margin: 0.5rem 0;
        background: rgba(102, 126, 234, 0.1);
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
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

# Sidebar
with st.sidebar:
    st.markdown("## 🎛️ Navigation")
    
    # Page selection
    page = st.radio(
        "Select Page:",
        ["💬 Chat", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if page == "💬 Chat":
        st.markdown("## ⚙️ Configuration")
        
        # LLM Model Selector - Fetch from backend
        st.markdown("### 🤖 LLM Model")
        
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
                "Select Model:",
                list(model_options.keys()),
                index=list(model_options.keys()).index(current_display) if current_display else 0
            )
            st.session_state.selected_llm = model_options[selected_display]
            
            # Show model info
            selected_model_info = next(
                (m for m in st.session_state.available_models if m['model'] == st.session_state.selected_llm),
                None
            )
            if selected_model_info:
                st.caption(f"📊 Context: {selected_model_info['context_length']:,} tokens")
                st.caption(f"💰 Cost: ${selected_model_info['cost_per_1k_input']}/1k in, ${selected_model_info['cost_per_1k_output']}/1k out")
        else:
            st.warning("⚠️ No LLM models configured. Please add API keys in Settings.")
            if st.button("🔧 Go to Settings"):
                st.session_state.page = "⚙️ Settings"
                st.rerun()
        
        # Zeus Core Health Check
        st.markdown("### 🏥 System Health")
    if st.button("Check Health", use_container_width=True):
        with st.spinner("Checking..."):
            try:
                response = requests.get(f"{ZEUS_API_URL}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    st.success("✅ Zeus Core: Healthy")
                    for service, status in health_data.get("services", {}).items():
                        if status == "healthy":
                            st.success(f"✅ {service.capitalize()}: {status}")
                        else:
                            st.error(f"❌ {service.capitalize()}: {status}")
                else:
                    st.error("❌ Zeus Core: Unhealthy")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Load Agents
    st.markdown("### 🎭 Available Agents")
    if st.button("Load Agents", use_container_width=True):
        with st.spinner("Loading agents..."):
            try:
                response = requests.get(f"{ZEUS_API_URL}/agents", timeout=5)
                if response.status_code == 200:
                    st.session_state.agents = response.json()
                    st.success(f"✅ Loaded {len(st.session_state.agents)} agents")
                else:
                    st.error("❌ Failed to load agents")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display agents
    if st.session_state.agents:
        for agent in st.session_state.agents:
            with st.expander(f"🤖 {agent['name'].capitalize()}", expanded=False):
                st.write(f"**Status:** {agent['status']}")
                st.write(f"**Endpoint:** {agent['endpoint']}")
    
    # Clear Chat
    st.markdown("---")
    if page == "💬 Chat" and st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# Main content - Conditional rendering based on selected page
if page == "⚙️ Settings":
    # Show Settings Page
    show_settings_page()
else:
    # Show Chat Page (default)
    st.markdown('<div class="main-header">⚡ Zeus Nexus AI Pantheon</div>', unsafe_allow_html=True)

    # Info cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💬 Messages", len(st.session_state.messages))
    with col2:
        st.metric("🤖 Active Agents", len(st.session_state.agents))
    with col3:
        st.metric("🧠 LLM Model", st.session_state.selected_llm.split('-')[0].upper() if st.session_state.selected_llm else "N/A")
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
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>⚡ <strong>Zeus Nexus AI Pantheon</strong> - Powered by OpenShift & LangChain</p>
        <p>🔗 API: <code>zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com</code></p>
    </div>
    """,
    unsafe_allow_html=True
)
