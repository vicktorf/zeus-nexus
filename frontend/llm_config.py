"""
LLM Backend Configuration and Management
Supports multiple LLM providers: OpenAI, Anthropic, Google AI
"""

import os
from typing import Dict, List, Optional
from enum import Enum

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class LLMConfig:
    """LLM model configuration"""
    
    MODELS = {
        # OpenAI Models
        "gpt-4": {
            "provider": LLMProvider.OPENAI,
            "name": "GPT-4",
            "description": "Most capable OpenAI model, best for complex tasks",
            "context_length": 8192,
            "cost_per_1k_tokens": {"input": 0.03, "output": 0.06}
        },
        "gpt-4-turbo": {
            "provider": LLMProvider.OPENAI,
            "name": "GPT-4 Turbo",
            "description": "Faster GPT-4 with 128K context window",
            "context_length": 128000,
            "cost_per_1k_tokens": {"input": 0.01, "output": 0.03}
        },
        "gpt-4o": {
            "provider": LLMProvider.OPENAI,
            "name": "GPT-4o",
            "description": "Optimized GPT-4 with better performance",
            "context_length": 128000,
            "cost_per_1k_tokens": {"input": 0.005, "output": 0.015}
        },
        "gpt-3.5-turbo": {
            "provider": LLMProvider.OPENAI,
            "name": "GPT-3.5 Turbo",
            "description": "Fast and cost-effective for simple tasks",
            "context_length": 16384,
            "cost_per_1k_tokens": {"input": 0.0005, "output": 0.0015}
        },
        
        # Anthropic Models
        "claude-3-opus": {
            "provider": LLMProvider.ANTHROPIC,
            "name": "Claude 3 Opus",
            "description": "Most capable Claude model, excels at complex tasks",
            "context_length": 200000,
            "cost_per_1k_tokens": {"input": 0.015, "output": 0.075}
        },
        "claude-3-sonnet": {
            "provider": LLMProvider.ANTHROPIC,
            "name": "Claude 3 Sonnet",
            "description": "Balanced performance and cost",
            "context_length": 200000,
            "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
        },
        "claude-3-haiku": {
            "provider": LLMProvider.ANTHROPIC,
            "name": "Claude 3 Haiku",
            "description": "Fastest Claude model, ideal for quick responses",
            "context_length": 200000,
            "cost_per_1k_tokens": {"input": 0.00025, "output": 0.00125}
        },
        "claude-3.5-sonnet": {
            "provider": LLMProvider.ANTHROPIC,
            "name": "Claude 3.5 Sonnet",
            "description": "Latest Claude model with improved reasoning",
            "context_length": 200000,
            "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
        },
        
        # Google AI Models
        "gemini-pro": {
            "provider": LLMProvider.GOOGLE,
            "name": "Gemini Pro",
            "description": "Google's advanced AI model",
            "context_length": 32000,
            "cost_per_1k_tokens": {"input": 0.0005, "output": 0.0015}
        },
        "gemini-1.5-pro": {
            "provider": LLMProvider.GOOGLE,
            "name": "Gemini 1.5 Pro",
            "description": "Enhanced Gemini with 1M context window",
            "context_length": 1000000,
            "cost_per_1k_tokens": {"input": 0.00125, "output": 0.005}
        },
        "gemini-1.5-flash": {
            "provider": LLMProvider.GOOGLE,
            "name": "Gemini 1.5 Flash",
            "description": "Fast and efficient Gemini model",
            "context_length": 1000000,
            "cost_per_1k_tokens": {"input": 0.000125, "output": 0.0005}
        }
    }
    
    @classmethod
    def get_models_by_provider(cls, provider: LLMProvider) -> List[str]:
        """Get all models for a specific provider"""
        return [
            model_id for model_id, config in cls.MODELS.items()
            if config["provider"] == provider
        ]
    
    @classmethod
    def get_model_info(cls, model_id: str) -> Optional[Dict]:
        """Get information about a specific model"""
        return cls.MODELS.get(model_id)
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """Get list of all available models"""
        return list(cls.MODELS.keys())
    
    @classmethod
    def get_provider_api_key_name(cls, provider: LLMProvider) -> str:
        """Get environment variable name for provider API key"""
        provider_key_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.GOOGLE: "GOOGLE_AI_API_KEY"
        }
        return provider_key_map[provider]


class LLMBackendManager:
    """Manages LLM backend connections and API keys"""
    
    def __init__(self):
        self.api_keys = {}
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment variables or Kubernetes secrets"""
        for provider in LLMProvider:
            key_name = LLMConfig.get_provider_api_key_name(provider)
            api_key = os.environ.get(key_name)
            if api_key:
                self.api_keys[provider] = api_key
    
    def is_provider_configured(self, provider: LLMProvider) -> bool:
        """Check if a provider is configured with API key"""
        return provider in self.api_keys and bool(self.api_keys[provider])
    
    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for a provider"""
        return self.api_keys.get(provider)
    
    def set_api_key(self, provider: LLMProvider, api_key: str):
        """Set API key for a provider"""
        self.api_keys[provider] = api_key
    
    def get_available_models(self) -> List[str]:
        """Get list of models that are available (have API keys configured)"""
        available_models = []
        for model_id, config in LLMConfig.MODELS.items():
            provider = config["provider"]
            if self.is_provider_configured(provider):
                available_models.append(model_id)
        return available_models
    
    def validate_model_selection(self, model_id: str) -> tuple[bool, str]:
        """Validate if a model can be used"""
        model_info = LLMConfig.get_model_info(model_id)
        if not model_info:
            return False, f"Unknown model: {model_id}"
        
        provider = model_info["provider"]
        if not self.is_provider_configured(provider):
            key_name = LLMConfig.get_provider_api_key_name(provider)
            return False, f"Provider {provider.value} not configured. Missing {key_name}"
        
        return True, "OK"


def get_llm_display_name(model_id: str) -> str:
    """Get display name for a model"""
    model_info = LLMConfig.get_model_info(model_id)
    if model_info:
        return f"{model_info['name']} ({model_info['provider'].value})"
    return model_id


def format_cost_estimate(model_id: str, input_tokens: int, output_tokens: int) -> str:
    """Calculate and format cost estimate for a model"""
    model_info = LLMConfig.get_model_info(model_id)
    if not model_info:
        return "N/A"
    
    costs = model_info["cost_per_1k_tokens"]
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    total_cost = input_cost + output_cost
    
    return f"${total_cost:.6f}"
