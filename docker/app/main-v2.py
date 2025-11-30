import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import redis.asyncio as redis
import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

# Metrics
request_count = Counter('zeus_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('zeus_request_duration_seconds', 'Request duration')
active_agents = Gauge('zeus_active_agents', 'Number of active agents')
llm_requests = Counter('zeus_llm_requests_total', 'Total LLM requests', ['provider', 'model'])

app = FastAPI(
    title="Zeus Nexus Core", 
    version="1.0.0", 
    description="AI Pantheon Command Center - Zeus Core API with Multi-LLM Support"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Provider Configuration
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    agent_preference: Optional[str] = None
    llm_model: Optional[str] = "gpt-4"  # Default model
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    confidence: float
    execution_time: float

class TaskRequest(BaseModel):
    task_type: str
    agent_name: str
    input_data: Dict[str, Any]
    llm_model: Optional[str] = "gpt-4"

class AgentStatus(BaseModel):
    name: str
    status: str
    endpoint: str
    last_health_check: Optional[str]

class LLMConfigModel(BaseModel):
    model: str
    provider: str
    api_key_configured: bool
    context_length: int
    cost_per_1k_input: float
    cost_per_1k_output: float

# Global connections
redis_client = None
db_pool = None

# LLM Model Registry
LLM_MODELS = {
    "gpt-4": {
        "provider": LLMProvider.OPENAI,
        "context_length": 8192,
        "cost": {"input": 0.03, "output": 0.06}
    },
    "gpt-4-turbo": {
        "provider": LLMProvider.OPENAI,
        "context_length": 128000,
        "cost": {"input": 0.01, "output": 0.03}
    },
    "gpt-4o": {
        "provider": LLMProvider.OPENAI,
        "context_length": 128000,
        "cost": {"input": 0.005, "output": 0.015}
    },
    "gpt-3.5-turbo": {
        "provider": LLMProvider.OPENAI,
        "context_length": 16384,
        "cost": {"input": 0.0005, "output": 0.0015}
    },
    "claude-3-opus": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.015, "output": 0.075}
    },
    "claude-3-sonnet": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.003, "output": 0.015}
    },
    "claude-3-haiku": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.00025, "output": 0.00125}
    },
    "claude-3.5-sonnet": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.003, "output": 0.015}
    },
    "gemini-pro": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 32000,
        "cost": {"input": 0.0005, "output": 0.0015}
    },
    "gemini-1.5-pro": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 1000000,
        "cost": {"input": 0.00125, "output": 0.005}
    },
    "gemini-1.5-flash": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 1000000,
        "cost": {"input": 0.000125, "output": 0.0005}
    }
}

def get_llm_api_key(provider: LLMProvider) -> Optional[str]:
    """Get API key for LLM provider"""
    key_map = {
        LLMProvider.OPENAI: os.getenv('OPENAI_API_KEY'),
        LLMProvider.ANTHROPIC: os.getenv('ANTHROPIC_API_KEY'),
        LLMProvider.GOOGLE: os.getenv('GOOGLE_AI_API_KEY')
    }
    return key_map.get(provider)

def is_llm_configured(model_id: str) -> bool:
    """Check if LLM model is configured with API key"""
    model_config = LLM_MODELS.get(model_id)
    if not model_config:
        return False
    provider = model_config["provider"]
    return bool(get_llm_api_key(provider))

async def init_connections():
    """Initialize database connections"""
    global redis_client, db_pool
    
    try:
        # Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://redis.ac-agentic.svc.cluster.local:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        # PostgreSQL connection pool
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://zeus:zeus123@postgresql.ac-agentic.svc.cluster.local:5432/zeus')
        db_pool = await asyncpg.create_pool(postgres_url, min_size=2, max_size=10)
        
        print("✅ Zeus Nexus Core initialized successfully!")
        print(f"   - Redis: {redis_url}")
        print(f"   - PostgreSQL: Connected")
        
        # Check LLM configurations
        print("\n🤖 LLM Providers Status:")
        for provider in LLMProvider:
            api_key = get_llm_api_key(provider)
            status = "✅ Configured" if api_key else "❌ Not Configured"
            print(f"   - {provider.value}: {status}")
        
    except Exception as e:
        print(f"❌ Failed to initialize connections: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    await init_connections()
    active_agents.set(7)  # 7 agents in total

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    global redis_client, db_pool
    
    if redis_client:
        await redis_client.close()
    
    if db_pool:
        await db_pool.close()

@app.get("/")
async def root():
    """Root endpoint"""
    request_count.labels(method="GET", endpoint="/").inc()
    return {
        "message": "⚡ Zeus Nexus Core API",
        "version": "1.0.0",
        "status": "active",
        "description": "AI Pantheon Command Center with Multi-LLM Support",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "agents": "/agents",
            "chat": "/chat",
            "llm_models": "/llm/models",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    request_count.labels(method="GET", endpoint="/health").inc()
    
    services = {
        "redis": "healthy",
        "postgresql": "healthy"
    }
    
    try:
        # Test Redis
        await redis_client.ping()
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
    
    try:
        # Test PostgreSQL
        async with db_pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
    except Exception as e:
        services["postgresql"] = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }

@app.get("/llm/models", response_model=List[LLMConfigModel])
async def list_llm_models():
    """List all available LLM models and their configuration status"""
    request_count.labels(method="GET", endpoint="/llm/models").inc()
    
    models = []
    for model_id, config in LLM_MODELS.items():
        provider = config["provider"]
        api_key_configured = bool(get_llm_api_key(provider))
        
        models.append(LLMConfigModel(
            model=model_id,
            provider=provider.value,
            api_key_configured=api_key_configured,
            context_length=config["context_length"],
            cost_per_1k_input=config["cost"]["input"],
            cost_per_1k_output=config["cost"]["output"]
        ))
    
    return models

@app.get("/agents")
async def list_agents():
    """List all registered AI agents"""
    request_count.labels(method="GET", endpoint="/agents").inc()
    
    try:
        async with db_pool.acquire() as conn:
            agents = await conn.fetch("""
                SELECT name, status, endpoint, last_health_check
                FROM agents
                ORDER BY name
            """)
            
            return [dict(agent) for agent in agents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat endpoint with agent routing and LLM model selection"""
    request_count.labels(method="POST", endpoint="/chat").inc()
    
    try:
        # Validate LLM model
        llm_model = message.llm_model or "gpt-4"
        if llm_model not in LLM_MODELS:
            raise HTTPException(status_code=400, detail=f"Unknown LLM model: {llm_model}")
        
        if not is_llm_configured(llm_model):
            provider = LLM_MODELS[llm_model]["provider"].value
            raise HTTPException(
                status_code=503, 
                detail=f"LLM provider '{provider}' not configured. Please set API key."
            )
        
        # Track LLM usage
        provider = LLM_MODELS[llm_model]["provider"].value
        llm_requests.labels(provider=provider, model=llm_model).inc()
        
        # Generate session ID if not provided
        session_id = message.session_id or str(uuid.uuid4())
        
        # Agent routing logic based on keywords
        agent_map = {
            "project": "athena", "jira": "athena", "confluence": "athena", "pm": "athena",
            "monitor": "ares", "grafana": "ares", "alert": "ares", "devops": "ares", "incident": "ares",
            "sales": "apollo", "revenue": "apollo", "forecast": "apollo", "crm": "apollo",
            "docs": "clio", "report": "clio", "documentation": "clio", "wiki": "clio",
            "cloud": "hephaestus", "terraform": "hephaestus", "aws": "hephaestus", "infrastructure": "hephaestus",
            "notion": "hermes", "customer": "hermes", "contact": "hermes",
            "learn": "mnemosyne", "knowledge": "mnemosyne", "training": "mnemosyne", "analytics": "mnemosyne"
        }
        
        # Determine agent
        selected_agent = message.agent_preference
        if not selected_agent:
            message_lower = message.message.lower()
            for keyword, agent in agent_map.items():
                if keyword in message_lower:
                    selected_agent = agent
                    break
        
        if not selected_agent:
            selected_agent = "athena"  # Default to Athena (Project Manager)
        
        # Get agent info from database
        async with db_pool.acquire() as conn:
            agent_info = await conn.fetchrow("""
                SELECT name, endpoint, status
                FROM agents
                WHERE name = $1
            """, selected_agent)
            
            if not agent_info:
                raise HTTPException(status_code=404, detail=f"Agent '{selected_agent}' not found")
            
            if agent_info['status'] != 'active':
                raise HTTPException(status_code=503, detail=f"Agent '{selected_agent}' is not active")
            
            # Store conversation in PostgreSQL
            conversation_id = await conn.fetchval("""
                INSERT INTO conversations (session_id, agent_name, message, user_id, llm_model, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, session_id, selected_agent, message.message, message.user_id, llm_model, datetime.utcnow())
            
            # Mock response (in production, this would call the actual agent with LLM)
            response_text = f"Hello! I'm {selected_agent.capitalize()}, and I received your message: '{message.message}'. "
            response_text += f"I'm using {llm_model} to process your request. I'm ready to help!"
            
            # Update conversation with response
            await conn.execute("""
                UPDATE conversations
                SET response = $1, llm_provider = $2, updated_at = $3
                WHERE id = $4
            """, response_text, provider, datetime.utcnow(), conversation_id)
            
            # Cache in Redis (24 hours TTL)
            cache_key = f"chat:{session_id}:{selected_agent}"
            await redis_client.setex(
                cache_key,
                86400,  # 24 hours
                json.dumps({
                    "message": message.message,
                    "response": response_text,
                    "agent": selected_agent,
                    "llm_model": llm_model,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            # Get agent capabilities
            capabilities_raw = await conn.fetchval("SELECT capabilities FROM agents WHERE name = $1", selected_agent)
            capabilities = json.loads(capabilities_raw) if capabilities_raw else []
            
            return {
                "session_id": session_id,
                "agent": selected_agent,
                "response": response_text,
                "llm_model": llm_model,
                "llm_provider": provider,
                "metadata": {
                    "agent_endpoint": agent_info['endpoint'],
                    "agent_capabilities": capabilities,
                    "temperature": message.temperature,
                    "max_tokens": message.max_tokens
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/tasks")
async def create_task(task: TaskRequest):
    """Create a new task for an agent"""
    request_count.labels(method="POST", endpoint="/tasks").inc()
    
    task_id = str(uuid.uuid4())
    
    try:
        # Validate LLM model
        llm_model = task.llm_model or "gpt-4"
        if llm_model not in LLM_MODELS:
            raise HTTPException(status_code=400, detail=f"Unknown LLM model: {llm_model}")
        
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tasks (task_id, task_type, agent_name, status, input_data, llm_model, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, task_id, task.task_type, task.agent_name, "pending", 
               json.dumps(task.input_data), llm_model, datetime.utcnow())
        
        return {
            "task_id": task_id,
            "status": "pending",
            "agent": task.agent_name,
            "llm_model": llm_model,
            "message": "Task created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
