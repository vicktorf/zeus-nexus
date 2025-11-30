"""
Context Storage Service
Multi-layered memory system for agents to store and retrieve context
Supports: Short-term, Long-term, Semantic, and Working Memory
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
from enum import Enum
import asyncpg
import redis.asyncio as redis
import json
import hashlib
import numpy as np
from collections import defaultdict
import os

app = FastAPI(
    title="Zeus Context Storage Service",
    description="Multi-layered memory system for intelligent agents",
    version="1.0.0"
)

# Database connections
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

# Vector storage for semantic memory (simulated - would use Qdrant/Pinecone in production)
semantic_store: Dict[str, List[Dict]] = defaultdict(list)

@app.on_event("startup")
async def startup():
    global db_pool, redis_client
    
    # PostgreSQL for long-term memory
    db_host = os.getenv("DB_HOST", "postgresql.ac-agentic.svc.cluster.local")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "zeus_nexus")
    db_user = os.getenv("DB_USER", "zeus")
    db_password = os.getenv("DB_PASSWORD", "zeus123")
    
    db_pool = await asyncpg.create_pool(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_size=5,
        max_size=20
    )
    
    # Redis for short-term memory (fast access)
    redis_host = os.getenv("REDIS_HOST", "redis.ac-agentic.svc.cluster.local")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_url = f"redis://{redis_host}:{redis_port}"
    
    redis_client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Initialize database schema
    async with db_pool.acquire() as conn:
        # Long-term conversation memory (simplified - no vector/tsvector)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                user_id VARCHAR(255),
                message_role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB,
                importance_score FLOAT DEFAULT 0.5,
                memory_type VARCHAR(50) DEFAULT 'episodic',
                created_at TIMESTAMP DEFAULT NOW(),
                accessed_at TIMESTAMP DEFAULT NOW(),
                access_count INTEGER DEFAULT 0
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_memory(session_id, created_at)")
        
        # Entity memory (people, projects, concepts)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_memory (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(100) NOT NULL,  -- person, project, task, concept
                entity_id VARCHAR(255) NOT NULL,
                entity_name VARCHAR(500) NOT NULL,
                attributes JSONB NOT NULL,
                relationships JSONB,  -- Links to other entities
                agent_name VARCHAR(100),
                last_mentioned TIMESTAMP DEFAULT NOW(),
                mention_count INTEGER DEFAULT 1,
                importance FLOAT DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(entity_type, entity_id, agent_name)
            )
        """)
        
        # Agent working memory (current task context)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS working_memory (
                id SERIAL PRIMARY KEY,
                agent_name VARCHAR(100) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                context_type VARCHAR(100) NOT NULL,  -- current_task, user_preferences, system_state
                context_data JSONB NOT NULL,
                ttl_seconds INTEGER DEFAULT 3600,  -- Auto-expire after 1 hour
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '1 hour',
                UNIQUE(agent_name, session_id, context_type)
            )
        """)
        
        # Memory consolidation log (for background processing)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_consolidation (
                id SERIAL PRIMARY KEY,
                agent_name VARCHAR(100) NOT NULL,
                consolidation_type VARCHAR(100) NOT NULL,  -- summarize, extract_entities, compute_importance
                source_ids INTEGER[],
                result JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_session 
            ON conversation_memory(session_id, created_at DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_agent 
            ON conversation_memory(agent_name, created_at DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_type 
            ON entity_memory(entity_type, entity_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_working_expires 
            ON working_memory(expires_at)
        """)
    
    print("✅ Context Storage Service initialized")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

# ==================== MODELS ====================

class MemoryType(str, Enum):
    EPISODIC = "episodic"      # Specific events/conversations
    SEMANTIC = "semantic"       # Facts and knowledge
    PROCEDURAL = "procedural"   # How to do things
    WORKING = "working"         # Current task context

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class ConversationMemory(BaseModel):
    session_id: str
    agent_name: str
    user_id: Optional[str] = None
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    memory_type: MemoryType = MemoryType.EPISODIC

class EntityMemory(BaseModel):
    entity_type: str  # person, project, task, concept, tool
    entity_id: str
    entity_name: str
    attributes: Dict[str, Any]
    relationships: Optional[Dict[str, List[str]]] = None
    agent_name: Optional[str] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)

class WorkingMemory(BaseModel):
    agent_name: str
    session_id: str
    context_type: str
    context_data: Dict[str, Any]
    ttl_seconds: int = 3600

class MemoryQuery(BaseModel):
    agent_name: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    limit: int = 50
    min_importance: float = 0.0
    time_range_hours: Optional[int] = None

# ==================== ENDPOINTS ====================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "context-storage",
        "timestamp": datetime.utcnow().isoformat()
    }

# ===== SHORT-TERM MEMORY (Redis) =====

@app.post("/memory/short-term/store")
async def store_short_term(
    session_id: str,
    agent_name: str,
    key: str,
    data: Dict[str, Any],
    ttl_seconds: int = 1800
):
    """
    Store short-term memory in Redis (fast access, auto-expire)
    Use for: current conversation context, temporary states
    """
    cache_key = f"memory:short:{agent_name}:{session_id}:{key}"
    
    await redis_client.setex(
        cache_key,
        ttl_seconds,
        json.dumps({
            "data": data,
            "stored_at": datetime.utcnow().isoformat(),
            "agent": agent_name
        })
    )
    
    return {
        "status": "stored",
        "cache_key": cache_key,
        "expires_in_seconds": ttl_seconds
    }

@app.get("/memory/short-term/retrieve")
async def retrieve_short_term(session_id: str, agent_name: str, key: str):
    """Retrieve short-term memory from Redis"""
    cache_key = f"memory:short:{agent_name}:{session_id}:{key}"
    
    data = await redis_client.get(cache_key)
    if not data:
        raise HTTPException(status_code=404, detail="Memory not found or expired")
    
    return json.loads(data)

@app.get("/memory/short-term/list")
async def list_short_term(session_id: str, agent_name: str):
    """List all short-term memories for a session"""
    pattern = f"memory:short:{agent_name}:{session_id}:*"
    keys = []
    
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key.split(":")[-1])
    
    return {"session_id": session_id, "agent": agent_name, "keys": keys}

# ===== LONG-TERM MEMORY (PostgreSQL) =====

@app.post("/memory/conversation/store")
async def store_conversation_memory(memory: ConversationMemory):
    """
    Store conversation message in long-term memory
    Use for: historical context, training data, audit trails
    """
    async with db_pool.acquire() as conn:
        memory_id = await conn.fetchval("""
            INSERT INTO conversation_memory 
            (session_id, agent_name, user_id, message_role, content, metadata, 
             importance_score, memory_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            memory.session_id,
            memory.agent_name,
            memory.user_id,
            memory.role.value,
            memory.content,
            json.dumps(memory.metadata) if memory.metadata else None,
            memory.importance_score,
            memory.memory_type.value
        )
        
        # Also cache in Redis for fast recent access
        recent_key = f"memory:recent:{memory.agent_name}:{memory.session_id}"
        await redis_client.lpush(recent_key, json.dumps({
            "id": memory_id,
            "role": memory.role.value,
            "content": memory.content[:200],  # Truncate for cache
            "timestamp": datetime.utcnow().isoformat()
        }))
        await redis_client.ltrim(recent_key, 0, 49)  # Keep last 50 messages
        await redis_client.expire(recent_key, 86400)  # 24 hours
        
        return {"status": "stored", "memory_id": memory_id}

@app.get("/memory/conversation/retrieve")
async def retrieve_conversation_memory(
    agent_name: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    min_importance: float = 0.0,
    time_range_hours: Optional[int] = None
):
    """
    Retrieve conversation history with filters
    Supports: agent, session, time range, importance filtering
    """
    conditions = ["1=1"]
    params = []
    param_count = 1
    
    if agent_name:
        conditions.append(f"agent_name = ${param_count}")
        params.append(agent_name)
        param_count += 1
    
    if session_id:
        conditions.append(f"session_id = ${param_count}")
        params.append(session_id)
        param_count += 1
    
    if user_id:
        conditions.append(f"user_id = ${param_count}")
        params.append(user_id)
        param_count += 1
    
    if min_importance > 0:
        conditions.append(f"importance_score >= ${param_count}")
        params.append(min_importance)
        param_count += 1
    
    if time_range_hours:
        conditions.append(f"created_at > NOW() - INTERVAL '{time_range_hours} hours'")
    
    where_clause = " AND ".join(conditions)
    
    async with db_pool.acquire() as conn:
        # Update access tracking
        if session_id:
            await conn.execute("""
                UPDATE conversation_memory 
                SET accessed_at = NOW(), access_count = access_count + 1
                WHERE session_id = $1
            """, session_id)
        
        rows = await conn.fetch(f"""
            SELECT id, session_id, agent_name, user_id, message_role, content, 
                   metadata, importance_score, memory_type, created_at, access_count
            FROM conversation_memory
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count}
        """, *params, limit)
        
        return {
            "total": len(rows),
            "conversations": [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "agent_name": row["agent_name"],
                    "message_role": row["message_role"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "importance_score": row["importance_score"],
                    "memory_type": row["memory_type"],
                    "created_at": row["created_at"].isoformat(),
                    "access_count": row["access_count"]
                }
                for row in rows
            ]
        }

# ===== ENTITY MEMORY (Structured Knowledge) =====

@app.post("/memory/entity/store")
async def store_entity_memory(entity: EntityMemory):
    """
    Store entity knowledge (people, projects, concepts)
    Use for: relationship tracking, entity attributes, knowledge graph
    """
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO entity_memory 
            (entity_type, entity_id, entity_name, attributes, relationships, 
             agent_name, importance, mention_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 1)
            ON CONFLICT (entity_type, entity_id, agent_name)
            DO UPDATE SET
                entity_name = EXCLUDED.entity_name,
                attributes = entity_memory.attributes || EXCLUDED.attributes,
                relationships = EXCLUDED.relationships,
                last_mentioned = NOW(),
                mention_count = entity_memory.mention_count + 1,
                importance = EXCLUDED.importance,
                updated_at = NOW()
        """,
            entity.entity_type,
            entity.entity_id,
            entity.entity_name,
            json.dumps(entity.attributes),
            json.dumps(entity.relationships) if entity.relationships else None,
            entity.agent_name,
            entity.importance
        )
        
        return {"status": "stored", "entity_id": entity.entity_id}

@app.get("/memory/entity/retrieve")
async def retrieve_entity(entity_type: str, entity_id: str, agent_name: Optional[str] = None):
    """Retrieve entity information"""
    async with db_pool.acquire() as conn:
        query = """
            SELECT * FROM entity_memory 
            WHERE entity_type = $1 AND entity_id = $2
        """
        params = [entity_type, entity_id]
        
        if agent_name:
            query += " AND agent_name = $3"
            params.append(agent_name)
        
        query += " ORDER BY importance DESC, mention_count DESC LIMIT 1"
        
        row = await conn.fetchrow(query, *params)
        
        if not row:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "entity_name": row["entity_name"],
            "attributes": row["attributes"],
            "relationships": row["relationships"],
            "agent": row["agent_name"],
            "mention_count": row["mention_count"],
            "importance": row["importance"],
            "last_mentioned": row["last_mentioned"].isoformat(),
            "updated_at": row["updated_at"].isoformat()
        }

@app.get("/memory/entity/search")
async def search_entities(
    entity_type: Optional[str] = None,
    name_contains: Optional[str] = None,
    agent_name: Optional[str] = None,
    min_importance: float = 0.0,
    limit: int = 50
):
    """Search entities by type, name, or importance"""
    conditions = ["1=1"]
    params = []
    param_count = 1
    
    if entity_type:
        conditions.append(f"entity_type = ${param_count}")
        params.append(entity_type)
        param_count += 1
    
    if name_contains:
        conditions.append(f"entity_name ILIKE ${param_count}")
        params.append(f"%{name_contains}%")
        param_count += 1
    
    if agent_name:
        conditions.append(f"agent_name = ${param_count}")
        params.append(agent_name)
        param_count += 1
    
    if min_importance > 0:
        conditions.append(f"importance >= ${param_count}")
        params.append(min_importance)
        param_count += 1
    
    where_clause = " AND ".join(conditions)
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT entity_type, entity_id, entity_name, attributes, 
                   mention_count, importance, last_mentioned
            FROM entity_memory
            WHERE {where_clause}
            ORDER BY importance DESC, mention_count DESC
            LIMIT ${param_count}
        """, *params, limit)
        
        return {
            "total": len(rows),
            "entities": [
                {
                    "type": row["entity_type"],
                    "id": row["entity_id"],
                    "name": row["entity_name"],
                    "attributes": row["attributes"],
                    "mention_count": row["mention_count"],
                    "importance": row["importance"],
                    "last_mentioned": row["last_mentioned"].isoformat()
                }
                for row in rows
            ]
        }

# ===== WORKING MEMORY (Current Task Context) =====

@app.post("/memory/working/store")
async def store_working_memory(memory: WorkingMemory):
    """
    Store working memory for current task
    Use for: current task state, intermediate results, temporary preferences
    Auto-expires after TTL
    """
    expires_at = datetime.utcnow() + timedelta(seconds=memory.ttl_seconds)
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO working_memory 
            (agent_name, session_id, context_type, context_data, ttl_seconds, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (agent_name, session_id, context_type)
            DO UPDATE SET
                context_data = working_memory.context_data || EXCLUDED.context_data,
                expires_at = EXCLUDED.expires_at,
                created_at = NOW()
        """,
            memory.agent_name,
            memory.session_id,
            memory.context_type,
            json.dumps(memory.context_data),
            memory.ttl_seconds,
            expires_at
        )
        
        return {
            "status": "stored",
            "expires_at": expires_at.isoformat()
        }

@app.get("/memory/working/retrieve")
async def retrieve_working_memory(agent_name: str, session_id: str, context_type: Optional[str] = None):
    """Retrieve working memory for current session"""
    async with db_pool.acquire() as conn:
        if context_type:
            row = await conn.fetchrow("""
                SELECT * FROM working_memory 
                WHERE agent_name = $1 AND session_id = $2 AND context_type = $3
                  AND expires_at > NOW()
            """, agent_name, session_id, context_type)
            
            if not row:
                raise HTTPException(status_code=404, detail="Working memory not found or expired")
            
            return {
                "context_type": row["context_type"],
                "context_data": row["context_data"],
                "expires_at": row["expires_at"].isoformat()
            }
        else:
            rows = await conn.fetch("""
                SELECT * FROM working_memory 
                WHERE agent_name = $1 AND session_id = $2 AND expires_at > NOW()
            """, agent_name, session_id)
            
            return {
                "agent": agent_name,
                "session": session_id,
                "contexts": [
                    {
                        "type": row["context_type"],
                        "data": row["context_data"],
                        "expires_at": row["expires_at"].isoformat()
                    }
                    for row in rows
                ]
            }

@app.delete("/memory/working/clear")
async def clear_working_memory(agent_name: str, session_id: str):
    """Clear all working memory for a session"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM working_memory 
            WHERE agent_name = $1 AND session_id = $2
        """, agent_name, session_id)
        
        return {"status": "cleared"}

# ===== MEMORY CONSOLIDATION & CLEANUP =====

@app.post("/memory/consolidate")
async def consolidate_memories(background_tasks: BackgroundTasks, agent_name: str, session_id: str):
    """
    Consolidate old memories (summarize, extract key entities, compute importance)
    Run as background task
    """
    background_tasks.add_task(run_consolidation, agent_name, session_id)
    return {"status": "consolidation_started"}

async def run_consolidation(agent_name: str, session_id: str):
    """Background task to consolidate memories"""
    async with db_pool.acquire() as conn:
        # Get old messages (> 1 day)
        rows = await conn.fetch("""
            SELECT id, content, importance_score 
            FROM conversation_memory 
            WHERE agent_name = $1 AND session_id = $2 
              AND created_at < NOW() - INTERVAL '1 day'
              AND access_count < 2
            ORDER BY created_at ASC
            LIMIT 100
        """, agent_name, session_id)
        
        if len(rows) < 10:
            return  # Not enough to consolidate
        
        # TODO: Use LLM to summarize old conversations
        # For now, just mark low-importance memories for potential deletion
        low_importance_ids = [row["id"] for row in rows if row["importance_score"] < 0.3]
        
        if low_importance_ids:
            await conn.execute("""
                UPDATE conversation_memory 
                SET importance_score = importance_score * 0.8
                WHERE id = ANY($1)
            """, low_importance_ids)
        
        # Log consolidation
        await conn.execute("""
            INSERT INTO memory_consolidation 
            (agent_name, consolidation_type, source_ids, result)
            VALUES ($1, 'reduce_importance', $2, $3)
        """, agent_name, low_importance_ids, json.dumps({"count": len(low_importance_ids)}))

@app.delete("/memory/cleanup")
async def cleanup_expired_memories():
    """
    Cleanup expired working memories and low-value conversation histories
    Should be run periodically (cron job)
    """
    async with db_pool.acquire() as conn:
        # Remove expired working memories
        await conn.execute("""
            DELETE FROM working_memory WHERE expires_at < NOW()
        """)
        
        # Archive very old, low-importance conversation memories
        archived = await conn.fetchval("""
            DELETE FROM conversation_memory 
            WHERE created_at < NOW() - INTERVAL '90 days'
              AND importance_score < 0.2
              AND access_count = 0
            RETURNING COUNT(*)
        """)
        
        return {
            "status": "cleaned",
            "archived_count": archived or 0
        }

# ===== SEMANTIC SEARCH (Future: integrate with vector DB) =====

@app.post("/memory/semantic/search")
async def semantic_search(
    query: str,
    agent_name: Optional[str] = None,
    limit: int = 10
):
    """
    Semantic search across memories (requires vector embeddings)
    TODO: Integrate with Qdrant/Pinecone for real vector search
    """
    # Placeholder: simple keyword search for now
    async with db_pool.acquire() as conn:
        where_clause = "content ILIKE $1"
        params = [f"%{query}%"]
        
        if agent_name:
            where_clause += " AND agent_name = $2"
            params.append(agent_name)
        
        rows = await conn.fetch(f"""
            SELECT id, session_id, agent_name, content, importance_score, created_at
            FROM conversation_memory
            WHERE {where_clause}
            ORDER BY importance_score DESC, created_at DESC
            LIMIT ${ len(params) + 1}
        """, *params, limit)
        
        return {
            "query": query,
            "results": [
                {
                    "id": row["id"],
                    "agent": row["agent_name"],
                    "content": row["content"],
                    "importance": row["importance_score"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in rows
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
