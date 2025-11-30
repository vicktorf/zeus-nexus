"""
Jira Service - ToolHub Integration
Provides Jira API integration for all agents
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import json
import logging
from datetime import datetime
from jira import JIRA
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Jira ToolHub Service",
    version="1.0.0",
    description="Jira Integration Service for Zeus Nexus Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class JiraIssueRequest(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Task"
    assignee: Optional[str] = None
    priority: Optional[str] = "Medium"
    labels: Optional[List[str]] = None

class JiraSearchRequest(BaseModel):
    jql: str
    max_results: int = 50
    fields: Optional[List[str]] = None

# Global Jira client
jira_client = None

def get_jira_client():
    """Get or create Jira client"""
    global jira_client
    
    if jira_client:
        return jira_client
    
    # Get configuration from environment or config service
    jira_server = os.getenv('JIRA_SERVER', 'https://your-company.atlassian.net')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    if jira_server and jira_email and jira_token:
        try:
            jira_client = JIRA(
                server=jira_server,
                basic_auth=(jira_email, jira_token),
                options={'verify': True}
            )
            return jira_client
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
    
    return None

@app.get("/health")
async def health():
    """Health check endpoint"""
    jira = get_jira_client()
    status = "healthy" if jira else "unhealthy"
    
    return {
        "status": status,
        "service": "jira-toolhub",
        "jira_connected": jira is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/issues")
async def create_issue(request: JiraIssueRequest):
    """Create a new Jira issue"""
    
    jira = get_jira_client()
    if not jira:
        raise HTTPException(status_code=503, detail="Jira service unavailable")
    
    try:
        issue_dict = {
            'project': {'key': request.project_key},
            'summary': request.summary,
            'description': request.description,
            'issuetype': {'name': request.issue_type},
        }
        
        if request.assignee:
            issue_dict['assignee'] = {'name': request.assignee}
        
        if request.priority:
            issue_dict['priority'] = {'name': request.priority}
        
        if request.labels:
            issue_dict['labels'] = request.labels
        
        new_issue = jira.create_issue(fields=issue_dict)
        
        return {
            "success": True,
            "issue_key": new_issue.key,
            "issue_id": new_issue.id,
            "url": f"{jira._options['server']}/browse/{new_issue.key}",
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create Jira issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/issues/{issue_key}")
async def get_issue(issue_key: str):
    """Get Jira issue details"""
    
    jira = get_jira_client()
    if not jira:
        raise HTTPException(status_code=503, detail="Jira service unavailable")
    
    try:
        issue = jira.issue(issue_key)
        
        return {
            "key": issue.key,
            "id": issue.id,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "status": issue.fields.status.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
            "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
            "priority": issue.fields.priority.name if issue.fields.priority else None,
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "url": f"{jira._options['server']}/browse/{issue.key}"
        }
        
    except Exception as e:
        logger.error(f"Failed to get Jira issue {issue_key}: {e}")
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

@app.post("/search")
async def search_issues(request: JiraSearchRequest):
    """Search Jira issues using JQL"""
    
    jira = get_jira_client()
    if not jira:
        raise HTTPException(status_code=503, detail="Jira service unavailable")
    
    try:
        fields = request.fields or ['summary', 'status', 'assignee', 'created', 'updated']
        
        issues = jira.search_issues(
            request.jql,
            maxResults=request.max_results,
            fields=','.join(fields)
        )
        
        results = []
        for issue in issues:
            issue_data = {
                "key": issue.key,
                "id": issue.id,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "url": f"{jira._options['server']}/browse/{issue.key}"
            }
            
            if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                issue_data["assignee"] = issue.fields.assignee.displayName
            
            if hasattr(issue.fields, 'created'):
                issue_data["created"] = issue.fields.created
                
            if hasattr(issue.fields, 'updated'):
                issue_data["updated"] = issue.fields.updated
                
            results.append(issue_data)
        
        return {
            "total": len(results),
            "issues": results,
            "jql": request.jql
        }
        
    except Exception as e:
        logger.error(f"Failed to search Jira issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def list_projects():
    """List all Jira projects"""
    
    jira = get_jira_client()
    if not jira:
        raise HTTPException(status_code=503, detail="Jira service unavailable")
    
    try:
        projects = jira.projects()
        
        result = []
        for project in projects:
            result.append({
                "key": project.key,
                "name": project.name,
                "id": project.id,
                "description": getattr(project, 'description', ''),
                "lead": project.lead.displayName if hasattr(project, 'lead') and project.lead else None
            })
        
        return {
            "total": len(result),
            "projects": result
        }
        
    except Exception as e:
        logger.error(f"Failed to list Jira projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/issues/{issue_key}")
async def update_issue(issue_key: str, update_data: Dict[str, Any]):
    """Update Jira issue"""
    
    jira = get_jira_client()
    if not jira:
        raise HTTPException(status_code=503, detail="Jira service unavailable")
    
    try:
        issue = jira.issue(issue_key)
        
        # Build update fields
        fields = {}
        if 'summary' in update_data:
            fields['summary'] = update_data['summary']
        if 'description' in update_data:
            fields['description'] = update_data['description']
        if 'assignee' in update_data:
            fields['assignee'] = {'name': update_data['assignee']}
        if 'priority' in update_data:
            fields['priority'] = {'name': update_data['priority']}
        
        if fields:
            issue.update(fields=fields)
        
        return {
            "success": True,
            "issue_key": issue_key,
            "updated_fields": list(fields.keys()),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update Jira issue {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)