"""
LLM Pool Service - Multi-LLM Router and Load Balancer
Manages OpenAI, Claude, and Local LLM instances with intelligent routing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
import httpx
import json
import logging
import asyncio
import time
from datetime import datetime
from enum import Enum
import os
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Pool Service",
    version="1.0.0",
    description="Multi-LLM Router and Load Balancer for Zeus Nexus Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class LLMProvider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"

class LLMModel(str, Enum):
    # OpenAI models
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    
    # Claude models
    CLAUDE3_OPUS = "claude-3-opus-20240229"
    CLAUDE3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE3_HAIKU = "claude-3-haiku-20240307"
    
    # Local models
    LLAMA2 = "llama2-7b"
    CODELLAMA = "codellama-13b"
    MISTRAL = "mistral-7b"

# Models
class LLMRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None
    agent: Optional[str] = None
    model: Optional[LLMModel] = None
    provider: Optional[LLMProvider] = None
    max_tokens: int = 1000
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False

class LLMResponse(BaseModel):
    response: str
    model_used: str
    provider_used: str
    tokens_used: int
    cost_usd: Optional[float] = None
    response_time_ms: int
    timestamp: str

@dataclass
class LLMProvider_Config:
    name: str
    provider_type: LLMProvider
    endpoint: str
    api_key: Optional[str]
    models: List[str]
    cost_per_token: Dict[str, float]  # input/output costs
    max_requests_per_minute: int
    current_requests: int = 0
    last_reset: float = 0
    health_status: str = "unknown"
    average_response_time: float = 0.0

# Provider configurations
LLM_PROVIDERS: Dict[str, LLMProvider_Config] = {}

def initialize_providers():
    """Initialize LLM provider configurations"""
    global LLM_PROVIDERS
    
    # OpenAI Configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        LLM_PROVIDERS["openai"] = LLMProvider_Config(
            name="OpenAI",
            provider_type=LLMProvider.OPENAI,
            endpoint="https://api.openai.com/v1/chat/completions",
            api_key=openai_key,
            models=[LLMModel.GPT4, LLMModel.GPT4_TURBO, LLMModel.GPT35_TURBO],
            cost_per_token={
                "gpt-4": {"input": 0.00003, "output": 0.00006},
                "gpt-4-turbo-preview": {"input": 0.00001, "output": 0.00003},
                "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015}
            },
            max_requests_per_minute=60
        )
    
    # Claude Configuration
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    if claude_key:
        LLM_PROVIDERS["claude"] = LLMProvider_Config(
            name="Anthropic Claude",
            provider_type=LLMProvider.CLAUDE,
            endpoint="https://api.anthropic.com/v1/messages",
            api_key=claude_key,
            models=[LLMModel.CLAUDE3_OPUS, LLMModel.CLAUDE3_SONNET, LLMModel.CLAUDE3_HAIKU],
            cost_per_token={
                "claude-3-opus-20240229": {"input": 0.000015, "output": 0.000075},
                "claude-3-sonnet-20240229": {"input": 0.000003, "output": 0.000015},
                "claude-3-haiku-20240307": {"input": 0.00000025, "output": 0.00000125}
            },
            max_requests_per_minute=50
        )
    
    # Local LLM Configuration
    local_endpoint = os.getenv("LOCAL_LLM_ENDPOINT", "http://ollama.ac-agentic.svc.cluster.local:11434")
    LLM_PROVIDERS["local"] = LLMProvider_Config(
        name="Local LLM",
        provider_type=LLMProvider.LOCAL,
        endpoint=f"{local_endpoint}/api/generate",
        api_key=None,
        models=[LLMModel.LLAMA2, LLMModel.CODELLAMA, LLMModel.MISTRAL],
        cost_per_token={
            "llama2-7b": {"input": 0.0, "output": 0.0},
            "codellama-13b": {"input": 0.0, "output": 0.0},
            "mistral-7b": {"input": 0.0, "output": 0.0}
        },
        max_requests_per_minute=100
    )

def select_optimal_provider(request: LLMRequest) -> LLMProvider_Config:
    """Select the best available LLM provider based on request and current load"""
    
    # If specific provider requested, use it
    if request.provider:
        provider_key = request.provider.value
        if provider_key in LLM_PROVIDERS and LLM_PROVIDERS[provider_key].health_status == "healthy":
            return LLM_PROVIDERS[provider_key]
    
    # If specific model requested, find provider that supports it
    if request.model:
        for provider in LLM_PROVIDERS.values():
            if request.model in provider.models and provider.health_status == "healthy":
                return provider
    
    # Intelligent routing based on request characteristics
    prompt_length = len(request.prompt)
    
    # For complex reasoning tasks, prefer GPT-4 or Claude Opus
    if any(keyword in request.prompt.lower() for keyword in [
        "analyze", "strategy", "complex", "architecture", "reasoning"
    ]):
        for provider_key in ["openai", "claude"]:
            if provider_key in LLM_PROVIDERS:
                provider = LLM_PROVIDERS[provider_key]
                if provider.health_status == "healthy" and provider.current_requests < provider.max_requests_per_minute * 0.8:
                    return provider
    
    # For code-related tasks, prefer CodeLlama if available, otherwise GPT-4
    if any(keyword in request.prompt.lower() for keyword in [
        "code", "programming", "debug", "function", "api"
    ]):
        if "local" in LLM_PROVIDERS and "codellama" in request.prompt.lower():
            return LLM_PROVIDERS["local"]
        if "openai" in LLM_PROVIDERS:
            return LLM_PROVIDERS["openai"]
    
    # For simple tasks or high load, prefer faster/cheaper models
    if prompt_length < 500 or request.max_tokens < 500:
        # Try local first (free), then cheaper cloud models
        if "local" in LLM_PROVIDERS and LLM_PROVIDERS["local"].health_status == "healthy":
            return LLM_PROVIDERS["local"]
        if "openai" in LLM_PROVIDERS:
            return LLM_PROVIDERS["openai"]  # Can use GPT-3.5-turbo
    
    # Fallback: find any healthy provider
    for provider in LLM_PROVIDERS.values():
        if provider.health_status == "healthy":
            return provider
    
    raise HTTPException(status_code=503, detail="No healthy LLM providers available")

async def call_openai(provider: LLMProvider_Config, request: LLMRequest) -> Dict[str, Any]:
    """Call OpenAI API"""
    
    model = request.model or LLMModel.GPT35_TURBO
    
    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": request.prompt}
        ],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            provider.endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result["choices"][0]["message"]["content"],
                "tokens_used": result["usage"]["total_tokens"],
                "model_used": model
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

async def call_claude(provider: LLMProvider_Config, request: LLMRequest) -> Dict[str, Any]:
    """Call Claude API"""
    
    model = request.model or LLMModel.CLAUDE3_HAIKU
    
    headers = {
        "x-api-key": provider.api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "max_tokens": request.max_tokens,
        "messages": [
            {"role": "user", "content": request.prompt}
        ],
        "temperature": request.temperature
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            provider.endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result["content"][0]["text"],
                "tokens_used": result["usage"]["input_tokens"] + result["usage"]["output_tokens"],
                "model_used": model
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

async def call_local_llm(provider: LLMProvider_Config, request: LLMRequest) -> Dict[str, Any]:
    """Call Local LLM (Ollama)"""
    
    model = request.model or LLMModel.LLAMA2
    
    payload = {
        "model": model.replace("-", ":"),  # Convert to Ollama format
        "prompt": request.prompt,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            provider.endpoint,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result.get("response", ""),
                "tokens_used": len(request.prompt.split()) + len(result.get("response", "").split()),
                "model_used": model
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

def calculate_cost(provider: LLMProvider_Config, model: str, tokens_used: int) -> float:
    """Calculate cost based on tokens used"""
    
    if model in provider.cost_per_token:
        # Simplified: assume 75% input, 25% output tokens
        input_tokens = int(tokens_used * 0.75)
        output_tokens = int(tokens_used * 0.25)
        
        cost_info = provider.cost_per_token[model]
        total_cost = (input_tokens * cost_info["input"]) + (output_tokens * cost_info["output"])
        return round(total_cost, 6)
    
    return 0.0

# API Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    provider_status = {}
    
    for name, provider in LLM_PROVIDERS.items():
        provider_status[name] = {
            "status": provider.health_status,
            "models": provider.models,
            "current_load": f"{provider.current_requests}/{provider.max_requests_per_minute}",
            "avg_response_time": f"{provider.average_response_time:.2f}ms"
        }
    
    return {
        "status": "healthy",
        "service": "llm-pool",
        "providers": provider_status,
        "total_providers": len(LLM_PROVIDERS),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/generate")
async def generate_response(request: LLMRequest) -> LLMResponse:
    """Generate response using optimal LLM provider"""
    
    start_time = time.time()
    
    try:
        # Select optimal provider
        provider = select_optimal_provider(request)
        
        # Update request count (simple rate limiting)
        current_time = time.time()
        if current_time - provider.last_reset > 60:  # Reset every minute
            provider.current_requests = 0
            provider.last_reset = current_time
        
        if provider.current_requests >= provider.max_requests_per_minute:
            raise HTTPException(status_code=429, detail=f"Rate limit exceeded for {provider.name}")
        
        provider.current_requests += 1
        
        # Call appropriate LLM
        if provider.provider_type == LLMProvider.OPENAI:
            result = await call_openai(provider, request)
        elif provider.provider_type == LLMProvider.CLAUDE:
            result = await call_claude(provider, request)
        elif provider.provider_type == LLMProvider.LOCAL:
            result = await call_local_llm(provider, request)
        else:
            raise HTTPException(status_code=500, detail="Unsupported provider type")
        
        # Calculate metrics
        response_time = int((time.time() - start_time) * 1000)
        cost = calculate_cost(provider, result["model_used"], result["tokens_used"])
        
        # Update provider stats
        if provider.average_response_time == 0:
            provider.average_response_time = response_time
        else:
            provider.average_response_time = (provider.average_response_time * 0.8) + (response_time * 0.2)
        
        provider.health_status = "healthy"
        
        return LLMResponse(
            response=result["response"],
            model_used=result["model_used"],
            provider_used=provider.name,
            tokens_used=result["tokens_used"],
            cost_usd=cost,
            response_time_ms=response_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        
        # Update provider health if it was a provider-specific error
        if 'provider' in locals():
            provider.health_status = "unhealthy"
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/providers")
async def list_providers():
    """List all configured LLM providers"""
    
    providers_info = []
    for name, provider in LLM_PROVIDERS.items():
        providers_info.append({
            "name": provider.name,
            "type": provider.provider_type.value,
            "models": provider.models,
            "health_status": provider.health_status,
            "max_requests_per_minute": provider.max_requests_per_minute,
            "current_requests": provider.current_requests,
            "average_response_time": f"{provider.average_response_time:.2f}ms"
        })
    
    return {
        "providers": providers_info,
        "total_count": len(providers_info)
    }

@app.get("/models")
async def list_models():
    """List all available models"""
    
    all_models = []
    for provider in LLM_PROVIDERS.values():
        for model in provider.models:
            all_models.append({
                "model": model,
                "provider": provider.name,
                "provider_type": provider.provider_type.value,
                "cost_per_1k_tokens": provider.cost_per_token.get(model, {"input": 0, "output": 0})
            })
    
    return {
        "models": all_models,
        "total_count": len(all_models)
    }

@app.on_event("startup")
async def startup():
    """Initialize LLM providers on startup"""
    logger.info("Starting LLM Pool Service...")
    initialize_providers()
    
    # Health check all providers
    for provider in LLM_PROVIDERS.values():
        provider.health_status = "healthy"  # Simplified for now
    
    logger.info(f"Initialized {len(LLM_PROVIDERS)} LLM providers")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)