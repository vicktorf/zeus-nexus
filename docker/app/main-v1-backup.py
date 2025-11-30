import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import redis.asyncio as redis
import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

# Metrics
request_count = Counter('zeus_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('zeus_request_duration_seconds', 'Request duration')
active_agents = Gauge('zeus_active_agents', 'Number of active agents')

app = FastAPI(
    title="Zeus Nexus Core", 
    version="1.0.0", 
    description="AI Pantheon Command Center - Zeus Core API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    agent_preference: Optional[str] = None

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    confidence: float
    execution_time: float

class TaskRequest(BaseModel):
    task_type: str
    agent_name: str
    input_data: Dict[str, Any]

class AgentStatus(BaseModel):
    name: str
    status: str
    endpoint: str
    last_health_check: Optional[str]

# Global connections
redis_client = None
db_pool = None

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
    
    print("👋 Zeus Nexus Core shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "⚡ Zeus Nexus Core API",
        "version": "1.0.0",
        "status": "active",
        "description": "AI Pantheon Command Center",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "agents": "/agents",
            "chat": "/chat",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        health_status["services"]["postgresql"] = "healthy"
    except Exception as e:
        health_status["services"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    if health_status["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/agents", response_model=List[AgentStatus])
async def list_agents():
    """List all registered agents"""
    try:
        async with db_pool.acquire() as conn:
            agents = await conn.fetch("SELECT name, status, endpoint, last_health_check FROM agents ORDER BY name")
            return [
                {
                    "name": agent['name'],
                    "status": agent['status'],
                    "endpoint": agent['endpoint'],
                    "last_health_check": agent['last_health_check'].isoformat() if agent['last_health_check'] else None
                }
                for agent in agents
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agents: {str(e)}")

@app.get("/agents/{agent_name}/health")
async def check_agent_health(agent_name: str):
    """Check specific agent health"""
    try:
        async with db_pool.acquire() as conn:
            agent = await conn.fetchrow("SELECT * FROM agents WHERE name = $1", agent_name)
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check agent health
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{agent['endpoint']}/health")
                if response.status_code == 200:
                    return {
                        "agent": agent_name,
                        "status": "healthy",
                        "endpoint": agent['endpoint'],
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    return {
                        "agent": agent_name,
                        "status": "unhealthy",
                        "endpoint": agent['endpoint'],
                        "status_code": response.status_code
                    }
        except Exception as e:
            return {
                "agent": agent_name,
                "status": "error",
                "endpoint": agent['endpoint'],
                "error": str(e)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat endpoint with agent routing"""
    request_count.labels(method="POST", endpoint="/chat").inc()
    
    try:
        session_id = message.session_id or str(uuid.uuid4())
        
        # Simple agent routing logic based on keywords
        agent_map = {
            "project": "athena",
            "jira": "athena",
            "confluence": "athena",
            "monitor": "ares",
            "grafana": "ares",
            "alert": "ares",
            "sales": "apollo",
            "revenue": "apollo",
            "docs": "clio",
            "report": "clio",
            "cloud": "hephaestus",
            "terraform": "hephaestus",
            "openshift": "hephaestus",
            "crm": "hermes",
            "notion": "hermes",
            "learn": "mnemosyne",
            "knowledge": "mnemosyne"
        }
        
        # Determine agent based on message content or preference
        selected_agent = message.agent_preference
        if not selected_agent:
            message_lower = message.message.lower()
            for keyword, agent in agent_map.items():
                if keyword in message_lower:
                    selected_agent = agent
                    break
            else:
                selected_agent = "athena"  # default agent
        
        # Get agent endpoint from database
        async with db_pool.acquire() as conn:
            agent = await conn.fetchrow("SELECT * FROM agents WHERE name = $1", selected_agent)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {selected_agent} not found")
        
        # For now, return a simulated response since agents aren't deployed yet
        response_text = f"Hello! I'm {selected_agent.capitalize()}, and I received your message: '{message.message}'. I'm ready to help!"
        
        # Store conversation in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (session_id, user_id, agent_name, message, response, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, session_id, message.user_id, selected_agent, message.message, 
            response_text, json.dumps({"timestamp": datetime.utcnow().isoformat()}))
        
        # Store in Redis cache
        cache_key = f"session:{session_id}:last_message"
        await redis_client.setex(cache_key, 3600, json.dumps({
            "message": message.message,
            "agent": selected_agent,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return {
            "session_id": session_id,
            "agent": selected_agent,
            "response": response_text,
            "metadata": {
                "agent_endpoint": agent['endpoint'],
                "agent_capabilities": json.loads(agent['capabilities']) if agent['capabilities'] else []
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/tasks")
async def create_task(task: TaskRequest):
    """Create a new task for an agent"""
    try:
        task_id = str(uuid.uuid4())
        
        # Store task in database
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tasks (task_id, agent_name, task_type, status, input_data)
                VALUES ($1, $2, $3, $4, $5)
            """, task_id, task.agent_name, task.task_type, "pending", json.dumps(task.input_data))
        
        return {
            "task_id": task_id,
            "status": "created",
            "agent": task.agent_name,
            "task_type": task.task_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status"""
    try:
        async with db_pool.acquire() as conn:
            task = await conn.fetchrow("SELECT * FROM tasks WHERE task_id = $1", task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return {
                "task_id": task['task_id'],
                "agent_name": task['agent_name'],
                "task_type": task['task_type'],
                "status": task['status'],
                "input_data": json.loads(task['input_data']) if task['input_data'] else {},
                "output_data": json.loads(task['output_data']) if task['output_data'] else {},
                "error_message": task['error_message'],
                "created_at": task['created_at'].isoformat() if task['created_at'] else None,
                "completed_at": task['completed_at'].isoformat() if task['completed_at'] else None
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)