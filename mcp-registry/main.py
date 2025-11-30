"""
MCP Registry Service
Manages Model Context Protocol tool schemas and metadata
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import json
from enum import Enum

app = FastAPI(
    title="MCP Registry",
    description="Model Context Protocol Tool Registry",
    version="1.0.0"
)

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host="postgresql.ac-agentic.svc.cluster.local",
        port=5432,
        database="zeus_nexus",
        user="postgres",
        password="your-password",
        min_size=5,
        max_size=20
    )
    
    # Create tables
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_tools (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                version VARCHAR(50) NOT NULL,
                schema JSONB NOT NULL,
                service_endpoint VARCHAR(500),
                category VARCHAR(100),
                tags TEXT[],
                authentication_required BOOLEAN DEFAULT false,
                rate_limit INTEGER DEFAULT 100,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_tool_usage (
                id SERIAL PRIMARY KEY,
                tool_name VARCHAR(255) NOT NULL,
                user_id VARCHAR(255),
                execution_time_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tool_usage_timestamp 
            ON mcp_tool_usage(timestamp DESC)
        """)

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

# Models
class ToolCategory(str, Enum):
    PROJECT_MANAGEMENT = "project_management"
    DEVOPS = "devops"
    COMMUNICATION = "communication"
    DATA_ANALYTICS = "data_analytics"
    SECURITY = "security"
    DOCUMENTATION = "documentation"

class ToolParameter(BaseModel):
    name: str
    type: str  # string, integer, boolean, array, object
    description: str
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None

class ToolSchema(BaseModel):
    name: str = Field(..., description="Tool name (unique identifier)")
    description: str = Field(..., description="Tool description")
    version: str = Field(default="1.0.0")
    category: ToolCategory
    tags: List[str] = Field(default_factory=list)
    service_endpoint: str = Field(..., description="Service URL endpoint")
    authentication_required: bool = False
    rate_limit: int = 100
    parameters: List[ToolParameter]
    response_schema: Dict[str, Any]

class ToolRegistration(BaseModel):
    tool: ToolSchema

class ToolUsageLog(BaseModel):
    tool_name: str
    user_id: Optional[str] = None
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None

# Endpoints
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "mcp-registry",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/tools/register")
async def register_tool(registration: ToolRegistration):
    """Register a new tool in MCP registry"""
    tool = registration.tool
    
    async with db_pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO mcp_tools 
                (name, description, version, schema, service_endpoint, category, tags, 
                 authentication_required, rate_limit, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active')
                ON CONFLICT (name) 
                DO UPDATE SET
                    description = EXCLUDED.description,
                    version = EXCLUDED.version,
                    schema = EXCLUDED.schema,
                    service_endpoint = EXCLUDED.service_endpoint,
                    category = EXCLUDED.category,
                    tags = EXCLUDED.tags,
                    authentication_required = EXCLUDED.authentication_required,
                    rate_limit = EXCLUDED.rate_limit,
                    updated_at = NOW()
            """, 
                tool.name,
                tool.description,
                tool.version,
                json.dumps({
                    "parameters": [p.dict() for p in tool.parameters],
                    "response_schema": tool.response_schema
                }),
                tool.service_endpoint,
                tool.category.value,
                tool.tags,
                tool.authentication_required,
                tool.rate_limit
            )
            
            return {
                "status": "success",
                "message": f"Tool '{tool.name}' registered successfully",
                "tool_name": tool.name,
                "version": tool.version
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/tools")
async def list_tools(
    category: Optional[ToolCategory] = None,
    tags: Optional[str] = None,
    status: str = "active"
):
    """List all registered tools"""
    query = "SELECT * FROM mcp_tools WHERE status = $1"
    params = [status]
    
    if category:
        query += " AND category = $2"
        params.append(category.value)
    
    if tags:
        query += f" AND tags @> ARRAY[${len(params) + 1}]::text[]"
        params.append(tags)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        
        return {
            "total": len(rows),
            "tools": [
                {
                    "name": row["name"],
                    "description": row["description"],
                    "version": row["version"],
                    "category": row["category"],
                    "tags": row["tags"],
                    "service_endpoint": row["service_endpoint"],
                    "authentication_required": row["authentication_required"],
                    "rate_limit": row["rate_limit"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]
        }

@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """Get tool details and schema"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM mcp_tools WHERE name = $1",
            tool_name
        )
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return {
            "name": row["name"],
            "description": row["description"],
            "version": row["version"],
            "category": row["category"],
            "tags": row["tags"],
            "service_endpoint": row["service_endpoint"],
            "authentication_required": row["authentication_required"],
            "rate_limit": row["rate_limit"],
            "schema": row["schema"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat()
        }

@app.post("/tools/{tool_name}/usage")
async def log_usage(tool_name: str, usage: ToolUsageLog):
    """Log tool usage for analytics"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO mcp_tool_usage 
            (tool_name, user_id, execution_time_ms, success, error_message)
            VALUES ($1, $2, $3, $4, $5)
        """,
            tool_name,
            usage.user_id,
            usage.execution_time_ms,
            usage.success,
            usage.error_message
        )
    
    return {"status": "logged"}

@app.get("/tools/{tool_name}/analytics")
async def get_analytics(tool_name: str, days: int = 7):
    """Get tool usage analytics"""
    async with db_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_calls,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
                AVG(execution_time_ms) as avg_execution_time,
                MAX(execution_time_ms) as max_execution_time
            FROM mcp_tool_usage
            WHERE tool_name = $1 
              AND timestamp > NOW() - INTERVAL '%s days'
        """ % days, tool_name)
        
        return {
            "tool_name": tool_name,
            "period_days": days,
            "total_calls": stats["total_calls"],
            "successful_calls": stats["successful_calls"],
            "success_rate": (stats["successful_calls"] / stats["total_calls"] * 100) if stats["total_calls"] > 0 else 0,
            "avg_execution_time_ms": float(stats["avg_execution_time"]) if stats["avg_execution_time"] else 0,
            "max_execution_time_ms": stats["max_execution_time"]
        }

@app.delete("/tools/{tool_name}")
async def deactivate_tool(tool_name: str):
    """Deactivate a tool"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE mcp_tools 
            SET status = 'inactive', updated_at = NOW()
            WHERE name = $1
        """, tool_name)
    
    return {"status": "deactivated", "tool_name": tool_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
