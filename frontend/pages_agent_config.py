"""
Agent Configuration Page - Configure agents with LLM and backend connections
"""
import streamlit as st
import requests
from typing import Dict, List, Optional

ZEUS_API_URL = "http://zeus-core.ac-agentic.svc.cluster.local:8000"

# Agent definitions
AGENTS = {
    "athena": {
        "name": "Athena",
        "icon": "🧠",
        "description": "Project Management & Jira",
        "capabilities": ["project_management", "jira", "confluence"],
        "default_backend": "http://athena.ac-agentic.svc.cluster.local:8001"
    },
    "ares": {
        "name": "Ares",
        "icon": "⚔️",
        "description": "DevOps & Monitoring",
        "capabilities": ["monitoring", "grafana", "alerts", "incident_response"],
        "default_backend": "http://ares.ac-agentic.svc.cluster.local:8002"
    },
    "hermes": {
        "name": "Hermes",
        "icon": "📨",
        "description": "Customer Success & Communication",
        "capabilities": ["customer_success", "notion", "contact_management"],
        "default_backend": "http://hermes.ac-agentic.svc.cluster.local:8003"
    },
    "hephaestus": {
        "name": "Hephaestus",
        "icon": "🔨",
        "description": "Infrastructure & Cloud",
        "capabilities": ["infrastructure", "terraform", "aws", "deployment"],
        "default_backend": "http://hephaestus.ac-agentic.svc.cluster.local:8004"
    },
    "apollo": {
        "name": "Apollo",
        "icon": "💰",
        "description": "Sales Intelligence & Revenue",
        "capabilities": ["sales_forecasting", "crm", "revenue_tracking"],
        "default_backend": "http://apollo.ac-agentic.svc.cluster.local:8005"
    },
    "mnemosyne": {
        "name": "Mnemosyne",
        "icon": "🧠",
        "description": "Knowledge & Learning",
        "capabilities": ["training", "analytics", "knowledge_base", "data_insights"],
        "default_backend": "http://mnemosyne.ac-agentic.svc.cluster.local:8006"
    },
    "clio": {
        "name": "Clio",
        "icon": "📚",
        "description": "Documentation & Reports",
        "capabilities": ["documentation", "reports", "wikis", "knowledge_management"],
        "default_backend": "http://clio.ac-agentic.svc.cluster.local:8007"
    }
}

def load_available_llms() -> List[Dict]:
    """Load available LLM models from backend"""
    try:
        response = requests.get(f"{ZEUS_API_URL}/llm/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            # Filter only configured models
            return [m for m in models if m.get("api_key_configured", False)]
        else:
            return []
    except Exception as e:
        st.error(f"❌ Failed to load LLMs: {str(e)}")
        return []

def load_agent_config() -> Dict:
    """Load agent configurations from backend or session state"""
    if "agent_configs" not in st.session_state:
        # Initialize with defaults
        st.session_state.agent_configs = {
            agent_id: {
                "enabled": False,
                "llm_model": None,
                "backend_url": agent_data["default_backend"],
                "custom_backend": False
            }
            for agent_id, agent_data in AGENTS.items()
        }
    
    return st.session_state.agent_configs

def save_agent_config(agent_id: str, config: Dict):
    """Save agent configuration"""
    if "agent_configs" not in st.session_state:
        st.session_state.agent_configs = {}
    
    st.session_state.agent_configs[agent_id] = config
    
    # TODO: Save to backend API when endpoint is available
    # try:
    #     response = requests.post(
    #         f"{ZEUS_API_URL}/agents/{agent_id}/config",
    #         json=config,
    #         headers={"Content-Type": "application/json"},
    #         timeout=10
    #     )
    #     return response.status_code == 200
    # except Exception as e:
    #     st.error(f"❌ Failed to save: {str(e)}")
    #     return False
    
    return True

def show_agent_configuration_page():
    """Display Agent Configuration page"""
    
    st.markdown("## 🎭 Agent Configuration")
    st.markdown("Configure AI agents with LLM models and backend connections.")
    st.markdown("---")
    
    # Load available LLMs
    available_llms = load_available_llms()
    
    if not available_llms:
        st.warning("⚠️ No LLM models configured. Please configure LLM providers first.")
        if st.button("🔧 Go to LLM Setup"):
            st.session_state.current_page = "llm_setup"
            st.rerun()
        return
    
    # Load agent configurations
    agent_configs = load_agent_config()
    
    # Summary cards
    st.markdown("### 📊 Agent Status Overview")
    cols = st.columns(4)
    
    enabled_count = sum(1 for config in agent_configs.values() if config.get("enabled", False))
    configured_count = sum(1 for config in agent_configs.values() if config.get("llm_model"))
    
    with cols[0]:
        st.metric("Total Agents", len(AGENTS))
    with cols[1]:
        st.metric("Enabled", enabled_count, delta=f"{enabled_count}/{len(AGENTS)}")
    with cols[2]:
        st.metric("Configured", configured_count, delta=f"{configured_count}/{len(AGENTS)}")
    with cols[3]:
        st.metric("Available LLMs", len(available_llms))
    
    st.markdown("---")
    
    # Agent configuration list
    st.markdown("### 🤖 Configure Agents")
    
    # Create LLM options for dropdown
    llm_options = {
        f"{model['model']} ({model['provider'].upper()})": model['model']
        for model in available_llms
    }
    llm_options_list = ["-- Select LLM --"] + list(llm_options.keys())
    
    for agent_id, agent_data in AGENTS.items():
        config = agent_configs.get(agent_id, {})
        
        with st.expander(
            f"{agent_data['icon']} **{agent_data['name']}** - {agent_data['description']}",
            expanded=config.get("enabled", False)
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Capabilities:** {', '.join(agent_data['capabilities'])}")
            
            with col2:
                enabled = st.checkbox(
                    "Enable Agent",
                    value=config.get("enabled", False),
                    key=f"enable_{agent_id}"
                )
            
            if enabled:
                st.markdown("---")
                
                # LLM Selection
                current_llm = config.get("llm_model")
                current_display = None
                
                if current_llm:
                    for display, model_id in llm_options.items():
                        if model_id == current_llm:
                            current_display = display
                            break
                
                default_index = 0
                if current_display and current_display in llm_options_list:
                    default_index = llm_options_list.index(current_display)
                
                selected_llm_display = st.selectbox(
                    "🤖 Select LLM Model",
                    options=llm_options_list,
                    index=default_index,
                    key=f"llm_{agent_id}",
                    help=f"Choose which LLM model {agent_data['name']} should use"
                )
                
                selected_llm = None
                if selected_llm_display != "-- Select LLM --":
                    selected_llm = llm_options[selected_llm_display]
                    
                    # Show model info
                    model_info = next((m for m in available_llms if m['model'] == selected_llm), None)
                    if model_info:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📊 Context: {model_info['context_length']:,} tokens")
                        with col2:
                            st.caption(f"💰 In: ${model_info['cost_per_1k_input']}/1k")
                        with col3:
                            st.caption(f"📤 Out: ${model_info['cost_per_1k_output']}/1k")
                
                st.markdown(" ")
                
                # Backend Configuration
                st.markdown("**🔌 Backend Connection**")
                
                use_custom = st.checkbox(
                    "Use custom backend URL",
                    value=config.get("custom_backend", False),
                    key=f"custom_{agent_id}"
                )
                
                if use_custom:
                    backend_url = st.text_input(
                        "Backend URL",
                        value=config.get("backend_url", agent_data["default_backend"]),
                        placeholder="http://agent.namespace.svc.cluster.local:8000",
                        key=f"backend_{agent_id}"
                    )
                else:
                    backend_url = agent_data["default_backend"]
                    st.info(f"Default: `{backend_url}`")
                
                st.markdown(" ")
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if st.button("💾 Save", key=f"save_{agent_id}", use_container_width=True):
                        if not selected_llm:
                            st.error("⚠️ Please select an LLM model")
                        else:
                            new_config = {
                                "enabled": enabled,
                                "llm_model": selected_llm,
                                "backend_url": backend_url,
                                "custom_backend": use_custom
                            }
                            
                            if save_agent_config(agent_id, new_config):
                                st.success(f"✅ {agent_data['name']} configuration saved!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to save {agent_data['name']} configuration")
                
                with col2:
                    if st.button("🧪 Test", key=f"test_{agent_id}", use_container_width=True):
                        if not selected_llm or not backend_url:
                            st.error("⚠️ Please configure LLM and backend first")
                        else:
                            with st.spinner(f"Testing {agent_data['name']} connection..."):
                                try:
                                    # Test backend health
                                    response = requests.get(f"{backend_url}/health", timeout=5)
                                    if response.status_code == 200:
                                        st.success(f"✅ {agent_data['name']} backend is healthy!")
                                    else:
                                        st.error(f"❌ Backend returned status {response.status_code}")
                                except Exception as e:
                                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.info(f"ℹ️ {agent_data['name']} is disabled. Enable to configure.")
    
    st.markdown("---")
    
    # Bulk operations
    st.markdown("### ⚡ Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Enable All Agents", use_container_width=True):
            for agent_id in AGENTS.keys():
                config = agent_configs.get(agent_id, {})
                config["enabled"] = True
                agent_configs[agent_id] = config
            st.success("All agents enabled!")
            st.rerun()
    
    with col2:
        if st.button("❌ Disable All Agents", use_container_width=True):
            for agent_id in AGENTS.keys():
                config = agent_configs.get(agent_id, {})
                config["enabled"] = False
                agent_configs[agent_id] = config
            st.success("All agents disabled!")
            st.rerun()
    
    with col3:
        # Select default LLM for all
        default_llm_display = st.selectbox(
            "Set LLM for all enabled agents",
            options=llm_options_list,
            key="bulk_llm_select"
        )
    
    if default_llm_display != "-- Select LLM --":
        if st.button("🔄 Apply LLM to All Enabled Agents", use_container_width=True):
            default_llm = llm_options[default_llm_display]
            count = 0
            for agent_id, config in agent_configs.items():
                if config.get("enabled", False):
                    config["llm_model"] = default_llm
                    agent_configs[agent_id] = config
                    count += 1
            st.success(f"✅ Applied {default_llm} to {count} enabled agents!")
            st.rerun()
    
    st.markdown("---")
    
    # Configuration summary
    with st.expander("📋 Configuration Summary", expanded=False):
        st.json(agent_configs)
