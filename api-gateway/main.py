"""
Zeus Nexus API Gateway
Unified entry point for all agent and tool service requests
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import redis.asyncio as redis
from typing import Optional, Dict, Any
import json
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zeus Nexus API Gateway",
    description="Unified API Gateway for Zeus Nexus MCP Architecture",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Registry - Dynamic service discovery
SERVICE_REGISTRY = {
    "zeus-core": "http://zeus-core.ac-agentic.svc.cluster.local:8000",
    "athena": "http://athena.ac-agentic.svc.cluster.local:8001",
    "mcp-registry": "http://mcp-registry.ac-agentic.svc.cluster.local:8080",
    "tool-jira": "http://tool-service-jira.ac-agentic.svc.cluster.local:8002",
    "tool-github": "http://tool-service-github.ac-agentic.svc.cluster.local:8003",
    "auth": "http://auth-service.ac-agentic.svc.cluster.local:8090",
}

# Redis for caching & rate limiting
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url(
        "redis://redis.ac-agentic.svc.cluster.local:6379",
        encoding="utf-8",
        decode_responses=True
    )
    logger.info("✅ API Gateway initialized")

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

# Rate Limiting Middleware
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
    
    async def __call__(self, request: Request):
        if not redis_client:
            return
        
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Increment counter
        current = await redis_client.incr(key)
        
        if current == 1:
            await redis_client.expire(key, 60)  # 1 minute window
        
        if current > self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

rate_limiter = RateLimiter(requests_per_minute=100)

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"📨 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(duration)
    response.headers["X-Gateway-Version"] = "1.0.0"
    
    return response

# Health Check
@app.get("/health")
async def health():
    """Gateway health check"""
    service_health = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICE_REGISTRY.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=2.0)
                service_health[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                service_health[service_name] = "unreachable"
    
    return {
        "gateway": "healthy",
        "services": service_health,
        "timestamp": datetime.utcnow().isoformat()
    }

# Service Discovery
@app.get("/api/services")
async def list_services():
    """List all registered services"""
    return {
        "services": [
            {
                "name": name,
                "endpoint": url,
                "type": "agent" if name in ["zeus-core", "athena"] else "tool-service"
            }
            for name, url in SERVICE_REGISTRY.items()
        ]
    }

# Proxy to Zeus Core
@app.api_route("/api/zeus/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_zeus(path: str, request: Request, _: None = Depends(rate_limiter)):
    """Proxy requests to Zeus Core"""
    return await proxy_request("zeus-core", path, request)

# Proxy to Agents
@app.api_route("/api/agent/{agent_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_agent(agent_name: str, path: str, request: Request, _: None = Depends(rate_limiter)):
    """Proxy requests to specific agent"""
    if agent_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    return await proxy_request(agent_name, path, request)

# Proxy to Tool Services
@app.api_route("/api/tool/{tool_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_tool(tool_name: str, path: str, request: Request, _: None = Depends(rate_limiter)):
    """Proxy requests to tool services"""
    service_key = f"tool-{tool_name}"
    if service_key not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool service '{tool_name}' not found")
    
    return await proxy_request(service_key, path, request)

# MCP Registry Proxy
@app.api_route("/api/mcp/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_mcp(path: str, request: Request):
    """Proxy requests to MCP Registry"""
    return await proxy_request("mcp-registry", path, request)

# Generic Proxy Function
async def proxy_request(service_name: str, path: str, request: Request) -> JSONResponse:
    """Generic proxy function with caching and error handling"""
    target_url = f"{SERVICE_REGISTRY[service_name]}/{path}"
    
    # Check cache for GET requests
    if request.method == "GET" and redis_client:
        cache_key = f"cache:{service_name}:{path}:{request.url.query}"
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"💾 Cache hit: {cache_key}")
            return JSONResponse(content=json.loads(cached))
    
    # Forward request
    async with httpx.AsyncClient() as client:
        try:
            # Prepare request
            headers = dict(request.headers)
            headers.pop("host", None)  # Remove host header
            
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # Make request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
                timeout=30.0
            )
            
            # Cache successful GET responses
            if request.method == "GET" and response.status_code == 200 and redis_client:
                cache_key = f"cache:{service_name}:{path}:{request.url.query}"
                await redis_client.setex(cache_key, 300, response.text)  # 5 min cache
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
        
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout: {target_url}")
            raise HTTPException(status_code=504, detail="Service timeout")
        
        except httpx.ConnectError:
            logger.error(f"🔌 Connection failed: {target_url}")
            raise HTTPException(status_code=503, detail=f"Service '{service_name}' unavailable")
        
        except Exception as e:
            logger.error(f"❌ Error proxying to {service_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Circuit Breaker Pattern (Simple Implementation)
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures: Dict[str, int] = {}
        self.opened_at: Dict[str, float] = {}
    
    def is_open(self, service: str) -> bool:
        if service not in self.opened_at:
            return False
        
        if time.time() - self.opened_at[service] > self.timeout:
            # Reset after timeout
            self.failures[service] = 0
            del self.opened_at[service]
            return False
        
        return True
    
    def record_failure(self, service: str):
        self.failures[service] = self.failures.get(service, 0) + 1
        if self.failures[service] >= self.failure_threshold:
            self.opened_at[service] = time.time()
            logger.warning(f"🔥 Circuit breaker opened for {service}")
    
    def record_success(self, service: str):
        self.failures[service] = 0

circuit_breaker = CircuitBreaker()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
