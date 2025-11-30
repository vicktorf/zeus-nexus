"""
Hephaestus - Cloud Architecture AI Agent
Specializes in: OpenShift, Kubernetes, Infrastructure as Code, Cloud Architecture
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import httpx
import yaml
import json
import logging
from datetime import datetime
from kubernetes import client, config
import openshift.dynamic

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hephaestus Agent",
    version="2.0.0",
    description="Cloud Architecture AI - OpenShift & Kubernetes Specialist"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ProcessRequest(BaseModel):
    request_id: str
    query: str
    context: Optional[Dict[str, Any]] = None
    step: Optional[int] = None

class ArchitectureRequest(BaseModel):
    project_name: str
    requirements: Dict[str, Any]
    environment: str = "development"  # development, staging, production
    constraints: Optional[Dict[str, Any]] = None

class DeploymentRequest(BaseModel):
    namespace: str
    manifests: List[Dict[str, Any]]
    dry_run: bool = True

class InfrastructureAnalysis(BaseModel):
    cluster_info: Dict[str, Any]
    recommendations: List[str]
    resource_optimization: Dict[str, Any]

# Tool Hub Integration
class ToolHubClient:
    def __init__(self):
        self.openshift_service = "http://tool-openshift.ac-agentic.svc.cluster.local:8002"
        self.terraform_service = "http://tool-terraform.ac-agentic.svc.cluster.local:8003"
        self.helm_service = "http://tool-helm.ac-agentic.svc.cluster.local:8004"
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get OpenShift cluster information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.openshift_service}/cluster/info")
                if response.status_code == 200:
                    return response.json()
                return {"error": f"Failed to get cluster info: {response.status_code}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}
    
    async def deploy_resources(self, namespace: str, resources: List[Dict]) -> Dict[str, Any]:
        """Deploy resources to OpenShift"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "namespace": namespace,
                    "resources": resources
                }
                response = await client.post(
                    f"{self.openshift_service}/deploy",
                    json=payload
                )
                return response.json()
        except Exception as e:
            return {"error": f"Deployment failed: {str(e)}"}
    
    async def create_terraform_plan(self, infrastructure_spec: Dict) -> Dict[str, Any]:
        """Create Terraform plan for infrastructure"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.terraform_service}/plan",
                    json=infrastructure_spec
                )
                return response.json()
        except Exception as e:
            return {"error": f"Terraform planning failed: {str(e)}"}

# LLM Integration
async def call_llm_service(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM Pool service for reasoning"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://llm-pool.ac-agentic.svc.cluster.local:8000/generate",
                json={
                    "prompt": f"As a cloud architecture expert, analyze this request: {query}",
                    "context": context,
                    "agent": "hephaestus",
                    "max_tokens": 1000
                }
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"LLM service error: {response.status_code}"}
    except Exception as e:
        return {"error": f"LLM connection failed: {str(e)}"}

# Architecture Templates
ARCHITECTURE_TEMPLATES = {
    "microservices": {
        "description": "Microservices architecture with service mesh",
        "components": ["api-gateway", "services", "database", "cache", "monitoring"],
        "patterns": ["service-mesh", "circuit-breaker", "load-balancing"]
    },
    "serverless": {
        "description": "Serverless architecture with OpenShift Serverless",
        "components": ["knative-serving", "eventing", "functions"],
        "patterns": ["event-driven", "auto-scaling", "pay-per-use"]
    },
    "batch-processing": {
        "description": "Batch processing with OpenShift Jobs and CronJobs",
        "components": ["job-scheduler", "data-processing", "storage"],
        "patterns": ["batch-processing", "data-pipeline", "scheduled-tasks"]
    }
}

def generate_openshift_manifests(architecture_type: str, project_name: str, requirements: Dict) -> List[Dict]:
    """Generate OpenShift manifests based on architecture type"""
    
    if architecture_type == "microservices":
        return [
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": project_name}
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": f"{project_name}-api-gateway",
                    "namespace": project_name
                },
                "spec": {
                    "replicas": requirements.get("replicas", 2),
                    "selector": {"matchLabels": {"app": f"{project_name}-api-gateway"}},
                    "template": {
                        "metadata": {"labels": {"app": f"{project_name}-api-gateway"}},
                        "spec": {
                            "containers": [{
                                "name": "api-gateway",
                                "image": f"{project_name}/api-gateway:latest",
                                "ports": [{"containerPort": 8000}],
                                "resources": {
                                    "requests": {"memory": "256Mi", "cpu": "250m"},
                                    "limits": {"memory": "512Mi", "cpu": "500m"}
                                }
                            }]
                        }
                    }
                }
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": f"{project_name}-api-gateway-service",
                    "namespace": project_name
                },
                "spec": {
                    "selector": {"app": f"{project_name}-api-gateway"},
                    "ports": [{"port": 80, "targetPort": 8000}],
                    "type": "ClusterIP"
                }
            }
        ]
    
    return []

# API Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    tool_hub = ToolHubClient()
    cluster_info = await tool_hub.get_cluster_info()
    
    return {
        "status": "healthy",
        "agent": "hephaestus",
        "capabilities": [
            "cloud_architecture",
            "openshift_deployment", 
            "kubernetes_management",
            "infrastructure_automation",
            "terraform_planning"
        ],
        "cluster_status": "connected" if "error" not in cluster_info else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/process")
async def process_request(request: ProcessRequest):
    """Main processing endpoint for Zeus Master Agent"""
    
    try:
        query = request.query.lower()
        context = request.context or {}
        
        # Analyze request with LLM
        llm_response = await call_llm_service(request.query, context)
        
        tool_hub = ToolHubClient()
        result = {
            "agent": "hephaestus",
            "request_id": request.request_id,
            "analysis": llm_response.get("response", ""),
            "actions": []
        }
        
        # Architecture design request
        if any(keyword in query for keyword in ["architecture", "design", "infrastructure"]):
            cluster_info = await tool_hub.get_cluster_info()
            result["actions"].append({
                "type": "architecture_analysis",
                "cluster_info": cluster_info,
                "recommendations": [
                    "Use microservices pattern for scalability",
                    "Implement service mesh for communication security",
                    "Set up monitoring and observability stack",
                    "Configure auto-scaling based on metrics"
                ]
            })
        
        # Deployment request
        if any(keyword in query for keyword in ["deploy", "deployment", "install"]):
            # Extract project requirements from context
            project_name = context.get("project_name", "demo-project")
            requirements = context.get("requirements", {})
            
            # Generate manifests
            manifests = generate_openshift_manifests("microservices", project_name, requirements)
            
            result["actions"].append({
                "type": "deployment_plan",
                "manifests": manifests,
                "deployment_strategy": "rolling_update"
            })
        
        # Infrastructure optimization
        if any(keyword in query for keyword in ["optimize", "performance", "scaling"]):
            cluster_info = await tool_hub.get_cluster_info()
            result["actions"].append({
                "type": "infrastructure_optimization",
                "recommendations": [
                    "Enable horizontal pod autoscaling",
                    "Configure resource quotas and limits",
                    "Implement node affinity rules",
                    "Set up cluster monitoring"
                ],
                "cluster_analysis": cluster_info
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing request {request.request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/architecture/design")
async def design_architecture(request: ArchitectureRequest):
    """Design cloud architecture based on requirements"""
    
    try:
        # Get architecture template
        arch_type = request.requirements.get("type", "microservices")
        template = ARCHITECTURE_TEMPLATES.get(arch_type, ARCHITECTURE_TEMPLATES["microservices"])
        
        # Generate manifests
        manifests = generate_openshift_manifests(arch_type, request.project_name, request.requirements)
        
        # Create Terraform plan if needed
        tool_hub = ToolHubClient()
        terraform_plan = None
        if request.requirements.get("infrastructure", False):
            terraform_plan = await tool_hub.create_terraform_plan({
                "project": request.project_name,
                "environment": request.environment,
                "requirements": request.requirements
            })
        
        return {
            "project_name": request.project_name,
            "architecture_type": arch_type,
            "template": template,
            "manifests": manifests,
            "terraform_plan": terraform_plan,
            "estimated_resources": {
                "cpu": f"{len(manifests) * 0.5}",
                "memory": f"{len(manifests) * 512}Mi",
                "storage": "10Gi"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deploy")
async def deploy_infrastructure(request: DeploymentRequest):
    """Deploy infrastructure to OpenShift"""
    
    try:
        tool_hub = ToolHubClient()
        
        # Deploy resources
        deployment_result = await tool_hub.deploy_resources(
            request.namespace,
            request.manifests
        )
        
        return {
            "namespace": request.namespace,
            "deployment_result": deployment_result,
            "dry_run": request.dry_run,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def list_architecture_templates():
    """List available architecture templates"""
    return {
        "templates": ARCHITECTURE_TEMPLATES,
        "total_count": len(ARCHITECTURE_TEMPLATES)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)