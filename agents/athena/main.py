"""
Athena - Project Management AI Agent
Specializes in: Jira, Confluence, Project Management
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from jira import JIRA
import requests

app = FastAPI(
    title="Athena Agent",
    version="1.0.0",
    description="Project Management AI - Jira & Confluence Integration"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TaskRequest(BaseModel):
    action: str  # create_issue, get_issue, update_issue, search_issues
    data: Dict[str, Any]
    llm_context: Optional[str] = None

class JiraConfig(BaseModel):
    server: str
    email: str
    api_token: str
    project_key: Optional[str] = None

class CreateIssueRequest(BaseModel):
    project: str
    summary: str
    description: str
    issue_type: str = "Task"
    assignee: Optional[str] = None
    priority: Optional[str] = None
    duedate: Optional[str] = None  # Format: YYYY-MM-DD
    time_estimate: Optional[str] = None  # Format: 1w 2d 3h 4m

# Global Jira client
jira_client = None

def get_jira_client():
    """Get or create Jira client"""
    global jira_client
    
    if jira_client:
        return jira_client
    
    # Try to get from environment
    jira_server = os.getenv('JIRA_SERVER')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_token = os.getenv('JIRA_API_TOKEN')
    
    if jira_server and jira_email and jira_token:
        try:
            jira_client = JIRA(
                server=jira_server,
                basic_auth=(jira_email, jira_token)
            )
            return jira_client
        except Exception as e:
            print(f"Failed to connect to Jira: {e}")
    
    return None

@app.get("/health")
async def health():
    """Health check endpoint"""
    jira = get_jira_client()
    jira_status = "connected" if jira else "not_configured"
    
    return {
        "status": "healthy",
        "agent": "athena",
        "capabilities": [
            "project_management",
            "jira",
            "confluence"
        ],
        "jira_status": jira_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "Athena",
        "role": "Project Management AI",
        "capabilities": [
            "Create and manage Jira issues",
            "Search and filter issues",
            "Update issue status and fields",
            "Assign tasks to team members",
            "Track project progress",
            "Confluence integration"
        ],
        "status": "active"
    }

@app.post("/jira/configure")
async def configure_jira(config: JiraConfig):
    """Configure Jira connection"""
    global jira_client
    
    try:
        jira_client = JIRA(
            server=config.server,
            basic_auth=(config.email, config.api_token)
        )
        
        # Test connection
        projects = jira_client.projects()
        
        return {
            "status": "success",
            "message": "Jira configured successfully",
            "projects": [{"key": p.key, "name": p.name} for p in projects[:5]]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Jira configuration failed: {str(e)}")

@app.get("/jira/projects")
async def get_projects():
    """Get all Jira projects"""
    jira = get_jira_client()
    
    if not jira:
        raise HTTPException(status_code=503, detail="Jira not configured")
    
    try:
        projects = jira.projects()
        return {
            "projects": [
                {
                    "key": p.key,
                    "name": p.name,
                    "id": p.id
                }
                for p in projects
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

@app.get("/jira/issues")
async def get_issues(
    project: Optional[str] = None,
    assignee: Optional[str] = None,
    status: Optional[str] = None,
    max_results: int = 50
):
    """Search Jira issues"""
    jira = get_jira_client()
    
    if not jira:
        raise HTTPException(status_code=503, detail="Jira not configured")
    
    try:
        # Build JQL query
        jql_parts = []
        if project:
            jql_parts.append(f"project = {project}")
        if assignee:
            jql_parts.append(f"assignee = {assignee}")
        if status:
            jql_parts.append(f"status = '{status}'")
        
        jql = " AND ".join(jql_parts) if jql_parts else "order by created DESC"
        
        issues = jira.search_issues(jql, maxResults=max_results)
        
        return {
            "total": len(issues),
            "issues": [
                {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                    "priority": issue.fields.priority.name if issue.fields.priority else "None",
                    "created": issue.fields.created,
                    "url": f"{jira._options['server']}/browse/{issue.key}"
                }
                for issue in issues
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search issues: {str(e)}")

@app.get("/jira/issue/{issue_key}")
async def get_issue(issue_key: str):
    """Get a specific Jira issue"""
    jira = get_jira_client()
    
    if not jira:
        raise HTTPException(status_code=503, detail="Jira not configured")
    
    try:
        issue = jira.issue(issue_key)
        
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "status": issue.fields.status.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
            "priority": issue.fields.priority.name if issue.fields.priority else "None",
            "created": issue.fields.created,
            "updated": issue.fields.updated,
            "url": f"{jira._options['server']}/browse/{issue.key}"
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Issue not found: {str(e)}")

@app.post("/jira/issue")
async def create_issue(request: CreateIssueRequest):
    """Create a new Jira issue"""
    jira = get_jira_client()
    
    if not jira:
        raise HTTPException(status_code=503, detail="Jira not configured")
    
    try:
        issue_dict = {
            'project': {'key': request.project},
            'summary': request.summary,
            'description': request.description,
            'issuetype': {'name': request.issue_type},
        }
        
        if request.assignee:
            issue_dict['assignee'] = {'name': request.assignee}
        
        if request.priority:
            issue_dict['priority'] = {'name': request.priority}
        
        if request.duedate:
            issue_dict['duedate'] = request.duedate
        
        if request.time_estimate:
            issue_dict['timetracking'] = {'originalEstimate': request.time_estimate}
        
        new_issue = jira.create_issue(fields=issue_dict)
        
        return {
            "status": "success",
            "issue_key": new_issue.key,
            "url": f"{jira._options['server']}/browse/{new_issue.key}",
            "message": f"Issue {new_issue.key} created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")

@app.put("/jira/issue/{issue_key}")
async def update_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    assignee: Optional[str] = None
):
    """Update a Jira issue"""
    jira = get_jira_client()
    
    if not jira:
        raise HTTPException(status_code=503, detail="Jira not configured")
    
    try:
        issue = jira.issue(issue_key)
        
        update_fields = {}
        if summary:
            update_fields['summary'] = summary
        if description:
            update_fields['description'] = description
        if assignee:
            update_fields['assignee'] = {'name': assignee}
        
        if update_fields:
            issue.update(fields=update_fields)
        
        # Update status if provided
        if status:
            transitions = jira.transitions(issue)
            for t in transitions:
                if t['name'].lower() == status.lower():
                    jira.transition_issue(issue, t['id'])
                    break
        
        return {
            "status": "success",
            "issue_key": issue_key,
            "message": f"Issue {issue_key} updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update issue: {str(e)}")

@app.post("/task")
async def execute_task(request: dict):
    """Execute a task with AI-enhanced capabilities"""
    action = request.get("action")
    params = request.get("params", {})
    query = request.get("query", params.get("query", ""))
    llm_model = request.get("llm_model", "gpt-4")
    
    # Extract structured parameters
    date = params.get("date")
    employee_name = params.get("employee_name")
    project = params.get("project", "AC")
    
    if action == "get_worklogs":
        # Get worklogs with structured parameters
        try:
            jira = get_jira_client()
            if not jira:
                return {"response": "Jira is not configured. Please configure Jira connection first."}
            
            if not date:
                return {"response": "Vui lòng cung cấp ngày để lấy worklog. Format: DD/MM/YYYY"}
            
            # Build JQL query
            jql = f'worklogDate = "{date}"'
            
            # Add employee filter if provided
            import unicodedata
            worklog_author_filter = None
            if employee_name:
                # Convert Vietnamese name to username format
                name_normalized = ''.join(
                    c for c in unicodedata.normalize('NFD', employee_name)
                    if unicodedata.category(c) != 'Mn'
                )
                name_normalized = name_normalized.replace('Đ', 'D').replace('đ', 'd')
                username_guess = name_normalized.lower().replace(' ', '.')
                worklog_author_filter = username_guess
                jql += f' AND worklogAuthor = "{username_guess}"'
            
            try:
                issues = jira.search_issues(jql, maxResults=50)
                
                if not issues:
                    date_parts = date.split('-')
                    display_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                    if employee_name:
                        return {"response": f"Không tìm thấy work log nào của **{employee_name}** trong ngày {display_date}."}
                    else:
                        return {"response": f"Không tìm thấy work log nào trong ngày {display_date}."}
                
                # Collect worklog information
                worklog_data = []
                total_time = 0
                
                for issue in issues:
                    worklogs = jira.worklogs(issue.key)
                    for worklog in worklogs:
                        worklog_date = worklog.started.split('T')[0]
                        worklog_author = worklog.author.displayName
                        
                        # Apply filters
                        date_match = worklog_date == date
                        author_match = True
                        if worklog_author_filter:
                            author_match = (
                                worklog_author_filter.lower() in worklog.author.name.lower() or
                                (employee_name and employee_name.lower() in worklog_author.lower())
                            )
                        
                        if date_match and author_match:
                            time_spent_seconds = worklog.timeSpentSeconds
                            time_spent_hours = time_spent_seconds / 3600
                            total_time += time_spent_hours
                            
                            worklog_data.append({
                                "issue": issue.key,
                                "summary": issue.fields.summary,
                                "author": worklog_author,
                                "time_spent": f"{time_spent_hours:.2f}h",
                                "time_spent_seconds": time_spent_seconds,
                                "comment": getattr(worklog, 'comment', '')
                            })
                
                if not worklog_data:
                    date_parts = date.split('-')
                    display_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                    if employee_name:
                        return {"response": f"Không tìm thấy work log nào của **{employee_name}** trong ngày {display_date}.\n\nGợi ý: Kiểm tra lại tên nhân viên hoặc ngày làm việc."}
                    else:
                        return {"response": f"Không tìm thấy work log nào trong ngày {display_date}."}
                
                # Format response
                date_parts = date.split('-')
                display_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                response = f"📊 **Worklog Report - {display_date}**\n\n"
                if employee_name:
                    response += f"👤 Nhân viên: **{employee_name}**\n"
                response += f"⏱️ Tổng thời gian làm việc: **{total_time:.2f} giờ**\n\n"
                
                # Group by author
                by_author = {}
                for wl in worklog_data:
                    author = wl['author']
                    if author not in by_author:
                        by_author[author] = []
                    by_author[author].append(wl)
                
                response += "**Chi tiết:**\n\n"
                for author, logs in by_author.items():
                    author_total = sum(float(log['time_spent'].replace('h', '')) for log in logs)
                    response += f"👤 **{author}** - Tổng: {author_total:.2f}h\n"
                    for log in logs:
                        response += f"  • **{log['issue']}**: {log['summary'][:80]}{'...' if len(log['summary']) > 80 else ''}\n"
                        response += f"    ⏰ {log['time_spent']}\n"
                        if log['comment']:
                            response += f"    💬 {log['comment'][:100]}{'...' if len(log['comment']) > 100 else ''}\n"
                    response += "\n"
                
                return {"response": response}
            except Exception as e:
                return {"response": f"Lỗi khi truy vấn worklog: {str(e)}"}
                
        except Exception as e:
            return {"response": f"Lỗi xử lý yêu cầu: {str(e)}"}
    
    elif action == "jira_query":
        # Parse natural language query and execute Jira operations
        try:
            jira = get_jira_client()
            if not jira:
                return {"response": "Jira is not configured. Please configure Jira connection first."}
            
            query_lower = query.lower()
            
            # Check for worklog/time tracking queries OR task queries
            if any(keyword in query_lower for keyword in ["thời gian", "làm việc", "worklog", "work time", "logged time", "task", "công việc"]):
                # Extract date from query - handle multiple year formats
                import re
                import unicodedata
                # Try different date formats: DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, DD/MM/Y
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{1,4})', query)
                target_date = None
                if date_match:
                    day, month, year = date_match.groups()
                    # Handle short year formats
                    if len(year) <= 2:
                        year = f"20{year.zfill(2)}"
                    elif len(year) == 3:
                        year = f"2{year.zfill(3)}"
                    target_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
                # Extract employee name from query
                # Look for patterns like "của [Name]", "by [Name]"
                employee_name = None
                name_patterns = [
                    r'của\s+([A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+(?:\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+)*)',
                    r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                ]
                
                for pattern in name_patterns:
                    name_match = re.search(pattern, query)
                    if name_match:
                        employee_name = name_match.group(1)
                        break
                
                if target_date:
                    
                    # Search for issues with worklogs on this date
                    jql = f'worklogDate = "{target_date}"'
                    try:
                        issues = jira.search_issues(jql, maxResults=50)
                        
                        if not issues:
                            return {"response": f"Không tìm thấy work log nào trong ngày {day}/{month}/{year}."}
                        
                        # Collect worklog information
                        worklog_data = []
                        total_time = 0
                        
                        for issue in issues:
                            worklogs = jira.worklogs(issue.key)
                            for worklog in worklogs:
                                # Check if worklog is on target date
                                worklog_date = worklog.started.split('T')[0]
                                if worklog_date == target_date:
                                    time_spent_seconds = worklog.timeSpentSeconds
                                    time_spent_hours = time_spent_seconds / 3600
                                    total_time += time_spent_hours
                                    
                                    worklog_data.append({
                                        "issue": issue.key,
                                        "author": worklog.author.displayName,
                                        "time_spent": f"{time_spent_hours:.2f}h",
                                        "comment": getattr(worklog, 'comment', 'No comment')
                                    })
                        
                        # Format response
                        response = f"📊 **Worklog Report - {day}/{month}/{year}**\n\n"
                        response += f"Tổng thời gian làm việc: **{total_time:.2f} giờ**\n\n"
                        
                        # Group by author
                        by_author = {}
                        for wl in worklog_data:
                            author = wl['author']
                            if author not in by_author:
                                by_author[author] = []
                            by_author[author].append(wl)
                        
                        for author, logs in by_author.items():
                            author_total = sum(float(log['time_spent'].replace('h', '')) for log in logs)
                            response += f"👤 **{author}** ({author_total:.2f}h):\n"
                            for log in logs:
                                response += f"  - {log['issue']}: {log['time_spent']}\n"
                                if log['comment'] and log['comment'] != 'No comment':
                                    response += f"    💬 {log['comment']}\n"
                            response += "\n"
                        
                        return {"response": response}
                    except Exception as e:
                        return {"response": f"Error querying worklogs: {str(e)}"}
                else:
                    return {"response": "Không tìm thấy ngày trong query. Vui lòng nhập theo format: DD/MM/YYYY"}
            
            # Check for issue search queries
            elif any(keyword in query_lower for keyword in ["issue", "task", "ticket", "tìm", "search"]):
                jql = "project = AC ORDER BY created DESC"
                issues = jira.search_issues(jql, maxResults=10)
                
                response = f"🔍 **Recent Issues**\n\n"
                for issue in issues:
                    response += f"- **{issue.key}**: {issue.fields.summary}\n"
                    response += f"  Status: {issue.fields.status.name}, Assignee: {getattr(issue.fields.assignee, 'displayName', 'Unassigned')}\n\n"
                
                return {"response": response}
            
            # Check for project queries
            elif "project" in query_lower:
                projects = jira.projects()
                response = f"📁 **Jira Projects ({len(projects)} projects)**\n\n"
                for proj in projects[:10]:
                    response += f"- **{proj.key}**: {proj.name}\n"
                
                return {"response": response}
            
            else:
                return {"response": f"Received query: '{query}'. I'm connected to Jira but need more specific instructions. Try asking about worklogs, issues, or projects."}
                
        except Exception as e:
            return {"response": f"Error processing Jira query: {str(e)}"}
    
    # Legacy actions
    data = request.get("data", {})
    if action == "create_issue":
        return await create_issue(**data)
    elif action == "get_issue":
        return await get_issue(data.get("issue_key"))
    elif action == "update_issue":
        return await update_issue(**data)
    elif action == "search_issues":
        return await get_issues(**data)
    else:
        return {"response": f"Unknown action: {action}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
