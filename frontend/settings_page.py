import streamlit as st
import requests
from typing import Dict, Any

ZEUS_API_URL = "http://zeus-core.ac-agentic.svc.cluster.local:8000"

def show_settings_page():
    """Display LLM Settings page"""
    st.markdown("## ⚙️ LLM Provider Settings")
    st.markdown("Configure API keys for different LLM providers to enable more models.")
    
    st.markdown("---")
    
    # Fetch current configuration
    with st.spinner("Loading current settings..."):
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
    
    # Display current status
    st.markdown("### 📊 Current Status")
    cols = st.columns(3)
    
    provider_icons = {
        "openai": "🤖",
        "anthropic": "🧠",
        "google": "🔍"
    }
    
    for idx, (provider_key, provider_data) in enumerate(providers.items()):
        with cols[idx]:
            icon = provider_icons.get(provider_key, "🔑")
            status = "✅ Configured" if provider_data.get("configured") else "❌ Not Configured"
            st.metric(
                f"{icon} {provider_key.capitalize()}", 
                status,
                delta=f"{provider_data.get('key_length', 0)} chars" if provider_data.get("configured") else None
            )
            if provider_data.get("key_preview"):
                st.caption(f"Key: `{provider_data['key_preview']}`")
    
    st.markdown("---")
    
    # Configuration Forms
    st.markdown("### 🔐 Update API Keys")
    
    with st.form("llm_config_form"):
        st.markdown("#### OpenAI")
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Get your API key from https://platform.openai.com/api-keys"
        )
        
        st.markdown("#### Anthropic (Claude)")
        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Get your API key from https://console.anthropic.com/settings/keys"
        )
        
        st.markdown("#### Google AI")
        google_key = st.text_input(
            "Google AI API Key",
            type="password",
            placeholder="AIza...",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_button = st.form_submit_button("💾 Save Configuration", use_container_width=True)
        with col2:
            clear_button = st.form_submit_button("🗑️ Clear All", use_container_width=True, type="secondary")
    
    # Handle form submission
    if submit_button:
        # Prepare update payload
        update_data = {}
        if openai_key:
            update_data["openai_api_key"] = openai_key
        if anthropic_key:
            update_data["anthropic_api_key"] = anthropic_key
        if google_key:
            update_data["google_api_key"] = google_key
        
        if not update_data:
            st.warning("⚠️ No API keys provided. Please enter at least one API key.")
        else:
            with st.spinner("Saving configuration..."):
                try:
                    response = requests.post(
                        f"{ZEUS_API_URL}/llm/config",
                        json=update_data,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Configuration updated successfully!")
                        st.info(f"Updated providers: {', '.join(result.get('updated_providers', []))}")
                        
                        # Refresh available models
                        if "available_models" in st.session_state:
                            st.session_state.available_models = []
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to update configuration: {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    if clear_button:
        st.warning("⚠️ Clear all API keys is not yet implemented. Use individual provider deletion if needed.")
    
    st.markdown("---")
    
    # Available Models based on configuration
    st.markdown("### 🤖 Available Models")
    
    with st.spinner("Loading available models..."):
        try:
            response = requests.get(f"{ZEUS_API_URL}/llm/models", timeout=5)
            if response.status_code == 200:
                all_models = response.json()
                
                # Group by provider
                models_by_provider = {}
                for model in all_models:
                    provider = model["provider"]
                    if provider not in models_by_provider:
                        models_by_provider[provider] = []
                    models_by_provider[provider].append(model)
                
                # Display grouped models
                for provider, models in models_by_provider.items():
                    with st.expander(f"{provider_icons.get(provider, '🔑')} **{provider.upper()}** - {len(models)} models", expanded=True):
                        for model in models:
                            col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
                            
                            with col1:
                                status_icon = "✅" if model["api_key_configured"] else "❌"
                                st.markdown(f"{status_icon} **{model['model']}**")
                            
                            with col2:
                                st.caption(f"{model['context_length']:,} tokens")
                            
                            with col3:
                                st.caption(f"💰 In: ${model['cost_per_1k_input']}/1k")
                            
                            with col4:
                                st.caption(f"📤 Out: ${model['cost_per_1k_output']}/1k")
            else:
                st.error(f"❌ Failed to load models: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error loading models: {str(e)}")
    
    st.markdown("---")
    
    # Help section
    with st.expander("❓ Help & Documentation"):
        st.markdown("""
        ### How to get API Keys:
        
        **OpenAI:**
        1. Visit https://platform.openai.com/api-keys
        2. Sign in or create an account
        3. Click "Create new secret key"
        4. Copy the key (starts with `sk-...`)
        
        **Anthropic (Claude):**
        1. Visit https://console.anthropic.com/settings/keys
        2. Sign in or create an account
        3. Click "Create Key"
        4. Copy the key (starts with `sk-ant-...`)
        
        **Google AI:**
        1. Visit https://makersuite.google.com/app/apikey
        2. Sign in with Google account
        3. Click "Create API Key"
        4. Copy the key (starts with `AIza...`)
        
        ### Security Notes:
        - API keys are stored in memory for the current session only
        - Keys are not persisted to disk
        - For production, use Kubernetes Secrets or secure vault
        - Never share your API keys publicly
        - Regularly rotate your API keys
        """)
