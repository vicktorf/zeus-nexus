"""
LLM Setup Page - Configure LLM providers with API keys
"""
import streamlit as st
import requests
from typing import Dict, Optional

ZEUS_API_URL = "http://zeus-core.ac-agentic.svc.cluster.local:8000"

def show_llm_setup_page():
    """Display LLM Setup page with provider selection, API key input, test and save"""
    
    st.markdown("## 🤖 LLM Provider Setup")
    st.markdown("Configure API keys for different LLM providers to enable AI models.")
    st.markdown("---")
    
    # Load saved settings from database on first load
    if "settings_loaded" not in st.session_state:
        with st.spinner("Loading saved settings from database..."):
            try:
                settings_response = requests.get(
                    f"{ZEUS_API_URL}/user/settings",
                    params={"user_id": "default_user"},
                    timeout=5
                )
                
                if settings_response.status_code == 200:
                    saved_settings = settings_response.json()
                    if saved_settings.get("exists"):
                        # Load API keys into runtime
                        api_keys = saved_settings.get("api_keys", {})
                        for provider, key in api_keys.items():
                            runtime_update = {f"{provider}_api_key": key}
                            requests.post(
                                f"{ZEUS_API_URL}/llm/config",
                                json=runtime_update,
                                headers={"Content-Type": "application/json"},
                                timeout=5
                            )
                        st.session_state.settings_loaded = True
                        st.toast("✅ Loaded saved settings from database", icon="💾")
            except Exception as e:
                st.warning(f"Could not load saved settings: {str(e)}")
                st.session_state.settings_loaded = True
    
    # Fetch current configuration
    with st.spinner("Loading current configuration..."):
        try:
            response = requests.get(f"{ZEUS_API_URL}/llm/config", timeout=5)
            if response.status_code == 200:
                config_data = response.json()
                providers = config_data.get("providers", {})
            else:
                st.error(f"❌ Failed to load configuration: {response.status_code}")
                providers = {}
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            providers = {}
    
    # Display current status cards
    st.markdown("### 📊 Current Provider Status")
    cols = st.columns(3)
    
    provider_info = {
        "openai": {
            "icon": "🤖",
            "name": "OpenAI",
            "models": ["GPT-4", "GPT-4 Turbo", "GPT-4o", "GPT-3.5 Turbo"],
            "url": "https://platform.openai.com/api-keys"
        },
        "anthropic": {
            "icon": "🧠",
            "name": "Anthropic",
            "models": ["Claude 3 Opus", "Claude 3.5 Sonnet", "Claude 3 Sonnet", "Claude 3 Haiku"],
            "url": "https://console.anthropic.com/settings/keys"
        },
        "google": {
            "icon": "🔍",
            "name": "Google AI",
            "models": ["Gemini Pro", "Gemini 1.5 Pro", "Gemini 1.5 Flash"],
            "url": "https://makersuite.google.com/app/apikey"
        }
    }
    
    for idx, (provider_key, info) in enumerate(provider_info.items()):
        with cols[idx]:
            provider_data = providers.get(provider_key, {})
            configured = provider_data.get("configured", False)
            
            st.markdown(f"""
            <div style='padding: 1rem; border-radius: 10px; border: 2px solid {"#4CAF50" if configured else "#FFA726"}; 
                        background: {"rgba(76, 175, 80, 0.1)" if configured else "rgba(255, 167, 38, 0.1)"}; text-align: center;'>
                <h2 style='margin: 0;'>{info['icon']}</h2>
                <h4 style='margin: 0.5rem 0;'>{info['name']}</h4>
                <p style='margin: 0; color: {"#4CAF50" if configured else "#FFA726"}; font-weight: bold;'>
                    {"✅ Configured" if configured else "❌ Not Configured"}
                </p>
                {f"<p style='font-size: 0.8rem; margin: 0.5rem 0;'>{len(info['models'])} models available</p>" if configured else ""}
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # LLM Provider Selection
    st.markdown("### 🔧 Configure Provider")
    
    selected_provider = st.selectbox(
        "Select Provider to Configure:",
        options=list(provider_info.keys()),
        format_func=lambda x: f"{provider_info[x]['icon']} {provider_info[x]['name']}",
        key="provider_select"
    )
    
    provider = provider_info[selected_provider]
    
    # Provider configuration form
    with st.container():
        st.markdown(f"""
        <div style='padding: 1.5rem; border-radius: 10px; border: 2px solid #667eea; background: rgba(102, 126, 234, 0.05);'>
            <h4>{provider['icon']} {provider['name']} Configuration</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(" ")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Available Models:** {', '.join(provider['models'])}")
            st.markdown(f"**Get API Key:** [{provider['url']}]({provider['url']})")
        
        with col2:
            current_status = providers.get(selected_provider, {})
            if current_status.get("configured"):
                st.success("✅ Currently Configured")
                if current_status.get("key_preview"):
                    st.caption(f"Key: `{current_status['key_preview']}`")
            else:
                st.warning("⚠️ Not Configured")
        
        st.markdown("---")
        
        # API Key Input
        api_key_placeholder = {
            "openai": "sk-proj-...",
            "anthropic": "sk-ant-...",
            "google": "AIza..."
        }
        
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder=api_key_placeholder[selected_provider],
            help=f"Enter your {provider['name']} API key",
            key=f"api_key_{selected_provider}"
        )
        
        # Action buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        
        with col1:
            test_button = st.button("🧪 Test Connection", use_container_width=True, type="secondary")
        
        with col2:
            save_button = st.button("💾 Save", use_container_width=True, type="primary")
        
        with col3:
            delete_button = st.button("🗑️ Delete", use_container_width=True, type="secondary")
        
        # Handle Test Connection
        if test_button:
            if not api_key:
                st.error("⚠️ Please enter an API key first")
            else:
                with st.spinner(f"Testing {provider['name']} connection..."):
                    try:
                        # Save temporarily to test
                        update_data = {f"{selected_provider}_api_key": api_key}
                        
                        response = requests.post(
                            f"{ZEUS_API_URL}/llm/config",
                            json=update_data,
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            # Fetch models to verify
                            models_response = requests.get(f"{ZEUS_API_URL}/llm/models", timeout=5)
                            if models_response.status_code == 200:
                                models = models_response.json()
                                provider_models = [m for m in models if m["provider"] == selected_provider and m["api_key_configured"]]
                                
                                if provider_models:
                                    st.success(f"✅ Connection successful! {len(provider_models)} models available")
                                    with st.expander("📋 Available Models"):
                                        for model in provider_models:
                                            st.write(f"- **{model['model']}** ({model['context_length']:,} tokens)")
                                else:
                                    st.warning("⚠️ API key saved but no models found")
                            else:
                                st.error("❌ Failed to verify models")
                        else:
                            st.error(f"❌ Connection failed: {response.status_code}")
                            st.code(response.text)
                    except Exception as e:
                        st.error(f"❌ Test failed: {str(e)}")
        
        # Handle Save
        if save_button:
            if not api_key:
                st.error("⚠️ Please enter an API key")
            else:
                with st.spinner(f"Saving {provider['name']} configuration..."):
                    try:
                        # First, get current settings from database
                        settings_response = requests.get(
                            f"{ZEUS_API_URL}/user/settings",
                            params={"user_id": "default_user"},
                            timeout=10
                        )
                        
                        if settings_response.status_code == 200:
                            current_settings = settings_response.json()
                            api_keys = current_settings.get("api_keys", {}) if current_settings.get("exists") else {}
                        else:
                            api_keys = {}
                        
                        # Update API key for selected provider
                        api_keys[selected_provider] = api_key
                        
                        # Prepare settings data
                        settings_data = {
                            "llm_provider": selected_provider,
                            "llm_model": provider["models"][0].lower().replace(" ", "-"),  # Default to first model
                            "api_keys": api_keys,
                            "last_chat_provider": selected_provider,
                            "last_chat_model": provider["models"][0].lower().replace(" ", "-")
                        }
                        
                        # Save to database
                        response = requests.post(
                            f"{ZEUS_API_URL}/user/settings",
                            json=settings_data,
                            params={"user_id": "default_user"},
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            # Also update runtime config for immediate use
                            runtime_update = {f"{selected_provider}_api_key": api_key}
                            requests.post(
                                f"{ZEUS_API_URL}/llm/config",
                                json=runtime_update,
                                headers={"Content-Type": "application/json"},
                                timeout=10
                            )
                            
                            st.success(f"✅ {provider['name']} API key saved to database!")
                            st.info("💾 Settings will persist across pod restarts")
                            
                            # Clear cached models
                            if "available_models" in st.session_state:
                                st.session_state.available_models = []
                            
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to save: {response.status_code}")
                            st.code(response.text)
                    except Exception as e:
                        st.error(f"❌ Save failed: {str(e)}")
        
        # Handle Delete
        if delete_button:
            with st.spinner(f"Deleting {provider['name']} configuration..."):
                try:
                    response = requests.delete(
                        f"{ZEUS_API_URL}/llm/config/{selected_provider}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success(f"✅ {provider['name']} API key deleted")
                        
                        # Clear cached models
                        if "available_models" in st.session_state:
                            st.session_state.available_models = []
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Delete failed: {str(e)}")
    
    st.markdown("---")
    
    # All Available Models
    st.markdown("### 🎯 All Available Models")
    
    with st.spinner("Loading models..."):
        try:
            response = requests.get(f"{ZEUS_API_URL}/llm/models", timeout=5)
            if response.status_code == 200:
                all_models = response.json()
                
                # Group by provider
                for provider_key, info in provider_info.items():
                    provider_models = [m for m in all_models if m["provider"] == provider_key]
                    configured_count = sum(1 for m in provider_models if m["api_key_configured"])
                    
                    with st.expander(
                        f"{info['icon']} **{info['name']}** - {configured_count}/{len(provider_models)} configured",
                        expanded=configured_count > 0
                    ):
                        if not provider_models:
                            st.info("No models available for this provider")
                        else:
                            for model in provider_models:
                                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                                
                                with col1:
                                    status_icon = "✅" if model["api_key_configured"] else "❌"
                                    st.markdown(f"{status_icon} **{model['model']}**")
                                
                                with col2:
                                    st.caption(f"{model['context_length']:,}")
                                
                                with col3:
                                    st.caption(f"${model['cost_per_1k_input']}")
                                
                                with col4:
                                    st.caption(f"${model['cost_per_1k_output']}")
                                
                                with col5:
                                    if model["api_key_configured"]:
                                        st.success("Ready")
                                    else:
                                        st.error("Disabled")
            else:
                st.error(f"❌ Failed to load models: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
