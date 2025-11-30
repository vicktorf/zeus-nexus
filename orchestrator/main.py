"""
ZEUS Master Agent - Orchestrator Layer
Central coordinator for all satellite agents and reasoning engine
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import httpx
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZEUS Master Agent",
    version="2.0.0",
    description="Central Orchestrator for Zeus Nexus Agentic Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class AgentType(str, Enum):
    ATHENA = "athena"          # Project Management / Jira
    HEPHAESTUS = "hephaestus"  # Cloud Architecture
    APOLLO = "apollo"          # Consultant
    HERMES = "hermes"          # Sales
    VULCAN = "vulcan"          # Platform Engineering
    ARES = "ares"              # Security

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Models
class AgentCapability(BaseModel):
    name: str
    description: str
    tools: List[str]
    confidence_level: float = Field(ge=0.0, le=1.0)

class SatelliteAgent(BaseModel):
    name: str
    agent_type: AgentType
    endpoint: str
    capabilities: List[AgentCapability]
    health_status: str = "unknown"
    last_health_check: Optional[datetime] = None
    load_factor: float = 0.0  # Current load 0-1

class UserRequest(BaseModel):
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    query: str
    context: Optional[Dict[str, Any]] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    require_agents: Optional[List[AgentType]] = None

class TaskExecution(BaseModel):
    task_id: str
    request_id: str
    agent_type: AgentType
    agent_endpoint: str
    status: TaskStatus
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None

class ReasoningPlan(BaseModel):
    plan_id: str
    user_request: UserRequest
    selected_agents: List[AgentType]
    execution_sequence: List[Dict[str, Any]]
    reasoning: str
    confidence: float

# Agent Registry - Service Discovery
AGENT_REGISTRY: Dict[AgentType, SatelliteAgent] = {}

# In-memory task tracking (in production, use Redis/database)
active_tasks: Dict[str, TaskExecution] = {}
reasoning_plans: Dict[str, ReasoningPlan] = {}

def initialize_agent_registry():
    """Initialize the satellite agent registry"""
    agents = [
        SatelliteAgent(
            name="Athena",
            agent_type=AgentType.ATHENA,
            endpoint="http://athena.ac-agentic.svc.cluster.local:8001",
            capabilities=[
                AgentCapability(
                    name="project_management",
                    description="Jira integration, project planning, task management",
                    tools=["jira", "confluence", "project_planning"],
                    confidence_level=0.95
                ),
                AgentCapability(
                    name="documentation",
                    description="Technical documentation and knowledge management",
                    tools=["confluence", "wiki", "documentation"],
                    confidence_level=0.85
                )
            ]
        ),
        SatelliteAgent(
            name="Hephaestus",
            agent_type=AgentType.HEPHAESTUS,
            endpoint="http://hephaestus.ac-agentic.svc.cluster.local:8002",
            capabilities=[
                AgentCapability(
                    name="cloud_architecture",
                    description="OpenShift, Kubernetes, cloud infrastructure design",
                    tools=["openshift", "kubernetes", "helm", "terraform"],
                    confidence_level=0.92
                ),
                AgentCapability(
                    name="infrastructure_automation",
                    description="Infrastructure as Code, CI/CD pipelines",
                    tools=["terraform", "ansible", "jenkins", "argocd"],
                    confidence_level=0.88
                )
            ]
        ),
        SatelliteAgent(
            name="Apollo",
            agent_type=AgentType.APOLLO,
            endpoint="http://apollo.ac-agentic.svc.cluster.local:8003",
            capabilities=[
                AgentCapability(
                    name="business_consulting",
                    description="Business analysis, strategy consulting, solution architecture",
                    tools=["analysis", "reporting", "strategy"],
                    confidence_level=0.90
                )
            ]
        ),
        SatelliteAgent(
            name="Hermes",
            agent_type=AgentType.HERMES,
            endpoint="http://hermes.ac-agentic.svc.cluster.local:8004",
            capabilities=[
                AgentCapability(
                    name="sales_automation",
                    description="CRM integration, sales pipeline management",
                    tools=["crm", "sales_pipeline", "lead_management"],
                    confidence_level=0.87
                )
            ]
        ),
        SatelliteAgent(
            name="Vulcan",
            agent_type=AgentType.VULCAN,
            endpoint="http://vulcan.ac-agentic.svc.cluster.local:8005",
            capabilities=[
                AgentCapability(
                    name="platform_engineering",
                    description="DevOps, platform automation, monitoring",
                    tools=["grafana", "prometheus", "devops", "monitoring"],
                    confidence_level=0.91
                )
            ]
        ),
        SatelliteAgent(
            name="Ares",
            agent_type=AgentType.ARES,
            endpoint="http://ares.ac-agentic.svc.cluster.local:8006",
            capabilities=[
                AgentCapability(
                    name="security_management",
                    description="Security scanning, compliance, vulnerability assessment",
                    tools=["owasp", "security_scan", "compliance", "vulnerability"],
                    confidence_level=0.89
                )
            ]
        )
    ]
    
    for agent in agents:
        AGENT_REGISTRY[agent.agent_type] = agent

async def analyze_user_intent(request: UserRequest) -> ReasoningPlan:
    """
    Reasoning engine to analyze user intent and create execution plan
    """
    query = request.query.lower()
    plan_id = str(uuid.uuid4())
    
    # Intent analysis keywords
    intent_keywords = {
        AgentType.ATHENA: ["jira", "project", "task", "issue", "confluence", "documentation", "ticket"],
        AgentType.HEPHAESTUS: ["openshift", "kubernetes", "deploy", "infrastructure", "cloud", "cluster"],
        AgentType.APOLLO: ["analyze", "strategy", "business", "consulting", "recommendation", "solution"],
        AgentType.HERMES: ["sales", "crm", "lead", "customer", "pipeline", "opportunity"],
        AgentType.VULCAN: ["monitor", "grafana", "devops", "platform", "automation", "pipeline"],
        AgentType.ARES: ["security", "scan", "vulnerability", "compliance", "owasp", "audit"]
    }
    
    # Score agents based on keyword matching
    agent_scores = {}
    for agent_type, keywords in intent_keywords.items():
        score = sum(1 for keyword in keywords if keyword in query)
        if score > 0:
            agent_scores[agent_type] = score
    
    # Select top agents or use user specified agents
    if request.require_agents:
        selected_agents = request.require_agents
    else:
        # Select agents with highest scores
        if agent_scores:
            selected_agents = [agent for agent, _ in sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[:2]]
        else:
            # Default to Apollo for general queries
            selected_agents = [AgentType.APOLLO]
    
    # Create execution sequence
    execution_sequence = []
    for i, agent_type in enumerate(selected_agents):
        execution_sequence.append({
            "step": i + 1,
            "agent_type": agent_type,
            "action": "process_request",
            "depends_on": execution_sequence[i-1]["step"] if i > 0 else None
        })
    
    reasoning = f"Analyzed query: '{request.query}'. Selected agents: {[a.value for a in selected_agents]} based on keyword matching and intent analysis."
    confidence = max(agent_scores.values()) / len(intent_keywords) if agent_scores else 0.5
    
    plan = ReasoningPlan(
        plan_id=plan_id,
        user_request=request,
        selected_agents=selected_agents,
        execution_sequence=execution_sequence,
        reasoning=reasoning,
        confidence=confidence
    )
    
    reasoning_plans[plan_id] = plan
    return plan

async def execute_agent_task(agent_type: AgentType, task_data: Dict[str, Any]) -> TaskExecution:
    """Execute task on specific satellite agent"""
    
    task_id = str(uuid.uuid4())
    agent = AGENT_REGISTRY.get(agent_type)
    
    if not agent:
        raise HTTPException(status_code=404, f"Agent {agent_type} not found in registry")
    
    task = TaskExecution(
        task_id=task_id,
        request_id=task_data.get("request_id", ""),
        agent_type=agent_type,
        agent_endpoint=agent.endpoint,
        status=TaskStatus.PROCESSING,
        input_data=task_data,
        started_at=datetime.utcnow()
    )
    
    active_tasks[task_id] = task
    
    try:
        # Make HTTP request to satellite agent
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{agent.endpoint}/process",
                json=task_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                task.status = TaskStatus.COMPLETED
                task.output_data = result
            else:
                task.status = TaskStatus.FAILED
                task.error = f"HTTP {response.status_code}: {response.text}"
                
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error = str(e)
        logger.error(f"Task {task_id} failed: {e}")
    
    task.completed_at = datetime.utcnow()
    if task.started_at:
        task.execution_time_ms = int((task.completed_at - task.started_at).total_seconds() * 1000)
    
    return task

# API Endpoints
@app.get("/health")
async def health():
    """Health check for Zeus master agent"""
    return {
        "status": "healthy",
        "service": "zeus-master",
        "timestamp": datetime.utcnow().isoformat(),
        "registered_agents": len(AGENT_REGISTRY),
        "active_tasks": len(active_tasks)
    }

@app.post("/process")
async def process_user_request(request: UserRequest, background_tasks: BackgroundTasks):
    """
    Main entry point for user requests
    Analyzes intent and routes to appropriate agents
    """
    try:
        # Create reasoning plan
        plan = await analyze_user_intent(request)
        
        # Execute tasks based on plan
        results = {}
        for step in plan.execution_sequence:
            agent_type = AgentType(step["agent_type"])
            
            task_data = {
                "request_id": request.request_id,
                "query": request.query,
                "context": request.context,
                "step": step["step"]
            }
            
            task = await execute_agent_task(agent_type, task_data)
            results[agent_type.value] = {
                "task_id": task.task_id,
                "status": task.status.value,
                "output": task.output_data,
                "error": task.error,
                "execution_time_ms": task.execution_time_ms
            }
        
        return {
            "request_id": request.request_id,
            "plan_id": plan.plan_id,
            "reasoning": plan.reasoning,
            "confidence": plan.confidence,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process request {request.request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all registered satellite agents"""
    return {
        "agents": [agent.dict() for agent in AGENT_REGISTRY.values()],
        "total_count": len(AGENT_REGISTRY)
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of specific task"""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.dict()

@app.get("/plans/{plan_id}")
async def get_reasoning_plan(plan_id: str):
    """Get reasoning plan details"""
    plan = reasoning_plans.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan.dict()

@app.on_event("startup")
async def startup():
    """Initialize Zeus Master Agent"""
    logger.info("Starting Zeus Master Agent...")
    initialize_agent_registry()
    logger.info(f"Initialized {len(AGENT_REGISTRY)} satellite agents")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)