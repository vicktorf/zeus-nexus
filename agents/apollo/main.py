"""
Apollo - Business Consultant AI Agent
Specializes in: Business Analysis, Strategy Consulting, Solution Architecture
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Apollo Agent",
    version="2.0.0",
    description="Business Consultant AI - Strategy & Solution Architecture"
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

class BusinessAnalysisRequest(BaseModel):
    business_domain: str
    requirements: List[str]
    constraints: Optional[Dict[str, Any]] = None
    stakeholders: Optional[List[str]] = None

# LLM Integration
async def call_llm_service(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Call LLM Pool service for business reasoning"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://llm-pool.ac-agentic.svc.cluster.local:8000/generate",
                json={
                    "prompt": f"As a senior business consultant, provide strategic analysis for: {query}",
                    "context": context,
                    "agent": "apollo",
                    "max_tokens": 1500
                }
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"LLM service error: {response.status_code}"}
    except Exception as e:
        return {"error": f"LLM connection failed: {str(e)}"}

# Business Analysis Templates
ANALYSIS_FRAMEWORKS = {
    "swot": {
        "name": "SWOT Analysis",
        "description": "Strengths, Weaknesses, Opportunities, Threats analysis",
        "structure": ["strengths", "weaknesses", "opportunities", "threats"]
    },
    "pestle": {
        "name": "PESTLE Analysis", 
        "description": "Political, Economic, Social, Technological, Legal, Environmental analysis",
        "structure": ["political", "economic", "social", "technological", "legal", "environmental"]
    },
    "business_model_canvas": {
        "name": "Business Model Canvas",
        "description": "Nine key business model components analysis",
        "structure": [
            "key_partners", "key_activities", "key_resources",
            "value_propositions", "customer_relationships", "channels",
            "customer_segments", "cost_structure", "revenue_streams"
        ]
    }
}

def generate_business_recommendations(domain: str, requirements: List[str]) -> List[Dict[str, Any]]:
    """Generate business recommendations based on domain and requirements"""
    
    recommendations = []
    
    # Technology recommendations
    if "digital transformation" in " ".join(requirements).lower():
        recommendations.append({
            "category": "Technology Strategy",
            "title": "Digital Transformation Roadmap",
            "priority": "high",
            "recommendations": [
                "Implement cloud-first architecture",
                "Adopt microservices for scalability",
                "Establish DevOps practices",
                "Invest in data analytics capabilities"
            ]
        })
    
    # Process optimization
    if any(keyword in " ".join(requirements).lower() for keyword in ["efficiency", "optimization", "automation"]):
        recommendations.append({
            "category": "Process Optimization",
            "title": "Operational Excellence Initiative", 
            "priority": "medium",
            "recommendations": [
                "Implement business process automation",
                "Establish continuous improvement culture",
                "Deploy monitoring and analytics",
                "Standardize workflows and procedures"
            ]
        })
    
    # Security and compliance
    if any(keyword in " ".join(requirements).lower() for keyword in ["security", "compliance", "risk"]):
        recommendations.append({
            "category": "Risk Management",
            "title": "Security & Compliance Framework",
            "priority": "high",
            "recommendations": [
                "Implement zero-trust security model",
                "Establish compliance monitoring",
                "Regular security assessments",
                "Employee security training program"
            ]
        })
    
    return recommendations

# API Endpoints
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "apollo",
        "capabilities": [
            "business_analysis",
            "strategy_consulting",
            "solution_architecture",
            "stakeholder_analysis",
            "business_process_optimization"
        ],
        "frameworks": list(ANALYSIS_FRAMEWORKS.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/process")
async def process_request(request: ProcessRequest):
    """Main processing endpoint for Zeus Master Agent"""
    
    try:
        query = request.query.lower()
        context = request.context or {}
        
        # Analyze request with LLM for business insights
        llm_response = await call_llm_service(request.query, context)
        
        result = {
            "agent": "apollo",
            "request_id": request.request_id,
            "business_analysis": llm_response.get("response", ""),
            "recommendations": [],
            "frameworks_applied": []
        }
        
        # Business strategy analysis
        if any(keyword in query for keyword in ["strategy", "business", "analysis", "consultant"]):
            
            # Apply SWOT analysis for strategic questions
            if "strength" in query or "weakness" in query or "opportunity" in query or "threat" in query:
                result["frameworks_applied"].append("swot")
                result["swot_analysis"] = {
                    "strengths": ["Existing technical expertise", "Established client base"],
                    "weaknesses": ["Limited automation", "Legacy systems"],
                    "opportunities": ["Digital transformation market", "Cloud adoption trends"],
                    "threats": ["Competitive pressure", "Technology disruption"]
                }
            
            # Generate business recommendations
            requirements = context.get("requirements", [request.query])
            domain = context.get("domain", "technology")
            
            recommendations = generate_business_recommendations(domain, requirements)
            result["recommendations"] = recommendations
        
        # Solution architecture consulting
        if any(keyword in query for keyword in ["solution", "architecture", "design", "implementation"]):
            result["solution_architecture"] = {
                "approach": "Phased implementation with MVP focus",
                "key_components": [
                    "User authentication and authorization",
                    "Data management and analytics",
                    "Integration capabilities", 
                    "Monitoring and observability"
                ],
                "implementation_phases": [
                    "Phase 1: Core functionality and MVP",
                    "Phase 2: Advanced features and integrations",
                    "Phase 3: Scaling and optimization"
                ],
                "success_metrics": [
                    "User adoption rate",
                    "System performance metrics",
                    "Business value delivered",
                    "Return on investment (ROI)"
                ]
            }
        
        # Stakeholder analysis
        if "stakeholder" in query or "requirement" in query:
            result["stakeholder_analysis"] = {
                "primary_stakeholders": ["Business users", "IT operations", "Management"],
                "secondary_stakeholders": ["Compliance team", "Security team", "End customers"],
                "key_concerns": [
                    "System reliability and uptime",
                    "Data security and privacy",
                    "Cost optimization",
                    "User experience"
                ]
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing request {request.request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def business_analysis(request: BusinessAnalysisRequest):
    """Comprehensive business analysis"""
    
    try:
        # Generate recommendations
        recommendations = generate_business_recommendations(
            request.business_domain,
            request.requirements
        )
        
        # Call LLM for detailed analysis
        analysis_context = {
            "domain": request.business_domain,
            "requirements": request.requirements,
            "constraints": request.constraints,
            "stakeholders": request.stakeholders
        }
        
        llm_response = await call_llm_service(
            f"Provide comprehensive business analysis for {request.business_domain}",
            analysis_context
        )
        
        return {
            "business_domain": request.business_domain,
            "executive_summary": llm_response.get("response", ""),
            "recommendations": recommendations,
            "implementation_roadmap": {
                "immediate_actions": [
                    "Stakeholder alignment meeting",
                    "Requirements validation workshop",
                    "Risk assessment session"
                ],
                "short_term": [
                    "Proof of concept development",
                    "Technology stack selection", 
                    "Team resource allocation"
                ],
                "long_term": [
                    "Full solution implementation",
                    "Change management program",
                    "Continuous improvement process"
                ]
            },
            "success_factors": [
                "Strong leadership commitment",
                "Clear communication plan",
                "Adequate resource allocation",
                "Regular progress monitoring"
            ],
            "risk_assessment": {
                "technical_risks": ["Integration complexity", "Scalability challenges"],
                "business_risks": ["User adoption", "Budget overrun"],
                "mitigation_strategies": ["Phased rollout", "Regular stakeholder updates"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/frameworks")
async def list_frameworks():
    """List available analysis frameworks"""
    return {
        "frameworks": ANALYSIS_FRAMEWORKS,
        "total_count": len(ANALYSIS_FRAMEWORKS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)