"""
OpenShift Service - ToolHub Integration
Provides OpenShift/Kubernetes API integration for all agents
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import yaml
import json
import logging
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenShift ToolHub Service", 
    version="1.0.0",
    description="OpenShift/Kubernetes Integration Service for Zeus Nexus Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DeploymentRequest(BaseModel):
    namespace: str
    resources: List[Dict[str, Any]]
    dry_run: bool = False

class PodLogsRequest(BaseModel):
    namespace: str
    pod_name: str
    container: Optional[str] = None
    tail_lines: int = 100

class ResourceScaleRequest(BaseModel):
    namespace: str
    resource_type: str  # deployment, statefulset, etc.
    resource_name: str
    replicas: int

# Global Kubernetes client
k8s_client = None
k8s_apps_client = None

def initialize_k8s_client():
    """Initialize Kubernetes client"""
    global k8s_client, k8s_apps_client
    
    try:
        # Try to load in-cluster config first (for pods running in cluster)
        config.load_incluster_config()
    except:
        try:
            # Fall back to kubeconfig file
            config.load_kube_config()
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            return False
    
    k8s_client = client.CoreV1Api()
    k8s_apps_client = client.AppsV1Api()
    return True

@app.on_event("startup")
async def startup():
    """Initialize connections on startup"""
    if not initialize_k8s_client():
        logger.warning("Kubernetes client initialization failed")

@app.get("/health")
async def health():
    """Health check endpoint"""
    k8s_connected = k8s_client is not None
    cluster_info = {}
    
    if k8s_client:
        try:
            # Try to get cluster info
            version = k8s_client.get_api_resources()
            cluster_info["connected"] = True
        except:
            cluster_info["connected"] = False
    
    return {
        "status": "healthy",
        "service": "openshift-toolhub",
        "kubernetes_connected": k8s_connected,
        "cluster_info": cluster_info,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/cluster/info")
async def get_cluster_info():
    """Get OpenShift cluster information"""
    
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not available")
    
    try:
        # Get cluster version info
        version_info = {}
        try:
            # This might not work in all K8s distributions
            nodes = k8s_client.list_node()
            version_info["nodes_count"] = len(nodes.items)
            if nodes.items:
                version_info["kubernetes_version"] = nodes.items[0].status.node_info.kube_proxy_version
        except:
            version_info["error"] = "Could not retrieve detailed version info"
        
        # Get namespaces
        namespaces = k8s_client.list_namespace()
        namespace_list = [ns.metadata.name for ns in namespaces.items]
        
        return {
            "cluster_info": version_info,
            "namespaces": namespace_list,
            "total_namespaces": len(namespace_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ApiException as e:
        logger.error(f"Kubernetes API error: {e}")
        raise HTTPException(status_code=500, detail=f"Kubernetes API error: {e}")

@app.post("/deploy")
async def deploy_resources(request: DeploymentRequest):
    """Deploy resources to OpenShift/Kubernetes"""
    
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not available")
    
    results = []
    
    try:
        for resource in request.resources:
            kind = resource.get('kind')
            api_version = resource.get('apiVersion')
            
            result = {
                "kind": kind,
                "name": resource.get('metadata', {}).get('name', 'unknown'),
                "status": "unknown"
            }
            
            try:
                if kind == "Namespace":
                    if request.dry_run:
                        result["status"] = "dry-run-success"
                    else:
                        namespace = client.V1Namespace(
                            metadata=client.V1ObjectMeta(
                                name=resource['metadata']['name']
                            )
                        )
                        k8s_client.create_namespace(body=namespace)
                        result["status"] = "created"
                
                elif kind == "Deployment":
                    # Handle deployment creation
                    if request.dry_run:
                        result["status"] = "dry-run-success"
                    else:
                        # Convert resource dict to Kubernetes object
                        deployment = client.V1Deployment(
                            api_version=api_version,
                            kind=kind,
                            metadata=client.V1ObjectMeta(**resource.get('metadata', {})),
                            spec=client.V1DeploymentSpec(**resource.get('spec', {}))
                        )
                        k8s_apps_client.create_namespaced_deployment(
                            namespace=request.namespace,
                            body=deployment
                        )
                        result["status"] = "created"
                
                elif kind == "Service":
                    if request.dry_run:
                        result["status"] = "dry-run-success"
                    else:
                        service = client.V1Service(
                            api_version=api_version,
                            kind=kind,
                            metadata=client.V1ObjectMeta(**resource.get('metadata', {})),
                            spec=client.V1ServiceSpec(**resource.get('spec', {}))
                        )
                        k8s_client.create_namespaced_service(
                            namespace=request.namespace,
                            body=service
                        )
                        result["status"] = "created"
                
                else:
                    result["status"] = "unsupported_kind"
                    result["message"] = f"Kind {kind} not supported yet"
                
            except ApiException as e:
                result["status"] = "failed"
                result["error"] = f"API error: {e.reason}"
            except Exception as e:
                result["status"] = "failed" 
                result["error"] = str(e)
            
            results.append(result)
        
        return {
            "namespace": request.namespace,
            "dry_run": request.dry_run,
            "results": results,
            "total_resources": len(request.resources),
            "successful": len([r for r in results if r["status"] in ["created", "dry-run-success"]]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/namespaces/{namespace}/pods")
async def list_pods(namespace: str):
    """List pods in a namespace"""
    
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not available")
    
    try:
        pods = k8s_client.list_namespaced_pod(namespace=namespace)
        
        pod_list = []
        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                "node": pod.spec.node_name,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                        "ready": False
                    }
                    for container in pod.spec.containers
                ]
            }
            
            # Check container readiness
            if pod.status.container_statuses:
                container_status_map = {cs.name: cs.ready for cs in pod.status.container_statuses}
                for container in pod_info["containers"]:
                    container["ready"] = container_status_map.get(container["name"], False)
            
            pod_list.append(pod_info)
        
        return {
            "namespace": namespace,
            "pods": pod_list,
            "total_count": len(pod_list)
        }
        
    except ApiException as e:
        logger.error(f"Failed to list pods in namespace {namespace}: {e}")
        raise HTTPException(status_code=404, detail=f"Namespace {namespace} not found or access denied")

@app.post("/pods/logs")
async def get_pod_logs(request: PodLogsRequest):
    """Get logs from a pod"""
    
    if not k8s_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not available")
    
    try:
        logs = k8s_client.read_namespaced_pod_log(
            name=request.pod_name,
            namespace=request.namespace,
            container=request.container,
            tail_lines=request.tail_lines
        )
        
        return {
            "pod_name": request.pod_name,
            "namespace": request.namespace,
            "container": request.container,
            "tail_lines": request.tail_lines,
            "logs": logs,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ApiException as e:
        logger.error(f"Failed to get logs for pod {request.pod_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Pod {request.pod_name} not found in namespace {request.namespace}")

@app.post("/scale")
async def scale_resource(request: ResourceScaleRequest):
    """Scale a deployment or statefulset"""
    
    if not k8s_apps_client:
        raise HTTPException(status_code=503, detail="Kubernetes client not available")
    
    try:
        if request.resource_type.lower() == "deployment":
            # Get current deployment
            deployment = k8s_apps_client.read_namespaced_deployment(
                name=request.resource_name,
                namespace=request.namespace
            )
            
            # Update replicas
            deployment.spec.replicas = request.replicas
            
            # Patch the deployment
            k8s_apps_client.patch_namespaced_deployment(
                name=request.resource_name,
                namespace=request.namespace,
                body=deployment
            )
            
            return {
                "resource_type": request.resource_type,
                "resource_name": request.resource_name,
                "namespace": request.namespace,
                "new_replicas": request.replicas,
                "status": "scaled",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Resource type {request.resource_type} not supported for scaling")
        
    except ApiException as e:
        logger.error(f"Failed to scale {request.resource_type} {request.resource_name}: {e}")
        raise HTTPException(status_code=404, detail=f"Resource {request.resource_name} not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)