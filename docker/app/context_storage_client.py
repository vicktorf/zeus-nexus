"""
Context Storage Client Library
Python SDK for agents to easily interact with Context Storage Service
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


class ContextStorageClient:
    """Client library for Context Storage Service"""
    
    def __init__(self, base_url: str = "http://context-storage.ac-agentic.svc.cluster.local:8085"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    # ===== SHORT-TERM MEMORY (Redis) =====
    
    async def store_short_term(
        self,
        session_id: str,
        agent_name: str,
        key: str,
        data: Dict[str, Any],
        ttl_seconds: int = 1800
    ):
        """Store short-term memory (fast, auto-expire)"""
        response = await self.client.post(
            f"{self.base_url}/memory/short-term/store",
            params={
                "session_id": session_id,
                "agent_name": agent_name,
                "key": key,
                "ttl_seconds": ttl_seconds
            },
            json=data
        )
        return response.json()
    
    async def get_short_term(self, session_id: str, agent_name: str, key: str):
        """Retrieve short-term memory"""
        response = await self.client.get(
            f"{self.base_url}/memory/short-term/retrieve",
            params={
                "session_id": session_id,
                "agent_name": agent_name,
                "key": key
            }
        )
        if response.status_code == 404:
            return None
        return response.json()
    
    # ===== LONG-TERM CONVERSATION MEMORY =====
    
    async def store_message(
        self,
        session_id: str,
        agent_name: str,
        role: str,  # user, assistant, system
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        importance_score: float = 0.5
    ):
        """Store conversation message in long-term memory"""
        response = await self.client.post(
            f"{self.base_url}/memory/conversation/store",
            json={
                "session_id": session_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "role": role,
                "content": content,
                "metadata": metadata,
                "importance_score": importance_score,
                "memory_type": "episodic"
            }
        )
        return response.json()
    
    async def get_conversation_history(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        min_importance: float = 0.0,
        time_range_hours: Optional[int] = None
    ):
        """Retrieve conversation history with filters"""
        response = await self.client.get(
            f"{self.base_url}/memory/conversation/retrieve",
            params={
                "session_id": session_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "limit": limit,
                "min_importance": min_importance,
                "time_range_hours": time_range_hours
            }
        )
        return response.json()
    
    # ===== ENTITY MEMORY (Knowledge Graph) =====
    
    async def store_entity(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        attributes: Dict[str, Any],
        agent_name: Optional[str] = None,
        relationships: Optional[Dict[str, List[str]]] = None,
        importance: float = 0.5
    ):
        """Store entity knowledge"""
        response = await self.client.post(
            f"{self.base_url}/memory/entity/store",
            json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "attributes": attributes,
                "relationships": relationships,
                "agent_name": agent_name,
                "importance": importance
            }
        )
        return response.json()
    
    async def get_entity(
        self,
        entity_type: str,
        entity_id: str,
        agent_name: Optional[str] = None
    ):
        """Retrieve entity information"""
        response = await self.client.get(
            f"{self.base_url}/memory/entity/retrieve",
            params={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "agent_name": agent_name
            }
        )
        if response.status_code == 404:
            return None
        return response.json()
    
    async def search_entities(
        self,
        entity_type: Optional[str] = None,
        name_contains: Optional[str] = None,
        agent_name: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 50
    ):
        """Search entities"""
        response = await self.client.get(
            f"{self.base_url}/memory/entity/search",
            params={
                "entity_type": entity_type,
                "name_contains": name_contains,
                "agent_name": agent_name,
                "min_importance": min_importance,
                "limit": limit
            }
        )
        return response.json()
    
    # ===== WORKING MEMORY (Current Task) =====
    
    async def store_working(
        self,
        agent_name: str,
        session_id: str,
        context_type: str,
        context_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ):
        """Store working memory for current task"""
        response = await self.client.post(
            f"{self.base_url}/memory/working/store",
            json={
                "agent_name": agent_name,
                "session_id": session_id,
                "context_type": context_type,
                "context_data": context_data,
                "ttl_seconds": ttl_seconds
            }
        )
        return response.json()
    
    async def get_working(
        self,
        agent_name: str,
        session_id: str,
        context_type: Optional[str] = None
    ):
        """Retrieve working memory"""
        response = await self.client.get(
            f"{self.base_url}/memory/working/retrieve",
            params={
                "agent_name": agent_name,
                "session_id": session_id,
                "context_type": context_type
            }
        )
        if response.status_code == 404:
            return None
        return response.json()
    
    async def clear_working(self, agent_name: str, session_id: str):
        """Clear working memory"""
        response = await self.client.delete(
            f"{self.base_url}/memory/working/clear",
            params={
                "agent_name": agent_name,
                "session_id": session_id
            }
        )
        return response.json()
    
    # ===== SEMANTIC SEARCH =====
    
    async def semantic_search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        limit: int = 10
    ):
        """Search memories by semantic similarity"""
        response = await self.client.post(
            f"{self.base_url}/memory/semantic/search",
            params={
                "query": query,
                "agent_name": agent_name,
                "limit": limit
            }
        )
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# ===== CONVENIENCE DECORATORS =====

def with_context_tracking(agent_name: str):
    """
    Decorator to automatically track agent function calls
    
    Usage:
    @with_context_tracking("athena")
    async def get_worklogs(...):
        ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            context_client = ContextStorageClient()
            
            # Extract session_id from kwargs
            session_id = kwargs.get("session_id", "default")
            
            # Store function call in working memory
            await context_client.store_working(
                agent_name=agent_name,
                session_id=session_id,
                context_type="current_operation",
                context_data={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "started_at": datetime.utcnow().isoformat()
                },
                ttl_seconds=300  # 5 minutes
            )
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Update with result
            await context_client.store_working(
                agent_name=agent_name,
                session_id=session_id,
                context_type="last_operation_result",
                context_data={
                    "function": func.__name__,
                    "result_summary": str(result)[:500],
                    "completed_at": datetime.utcnow().isoformat()
                },
                ttl_seconds=1800  # 30 minutes
            )
            
            await context_client.close()
            return result
        
        return wrapper
    return decorator
