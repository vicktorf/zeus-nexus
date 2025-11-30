# Context Storage Service - Deployment Status

## ✅ Deployment Complete

**Service URL (Internal):** `http://context-storage.ac-agentic.svc.cluster.local:8085`  
**Service URL (External):** `https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com`  
**Version:** v1.0.4  
**Status:** ✅ RUNNING & HEALTHY

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌──────────────┐
│  Zeus Core /    │─────▶│ Context Storage  │─────▶│ PostgreSQL   │
│  Athena Agent   │      │   Service :8085  │      │  :5432       │
└─────────────────┘      └──────────────────┘      └──────────────┘
                                  │
                                  │
                                  ▼
                         ┌──────────────┐
                         │    Redis     │
                         │    :6379     │
                         └──────────────┘
```

## 4 Memory Layers

### 1. **Short-term Memory** (Redis)
- Session data, recent interactions
- 30 minute TTL
- Fast access < 1ms

### 2. **Long-term Memory** (PostgreSQL)
- Complete conversation history
- Importance scoring
- Full-text search ready

### 3. **Entity Memory** (PostgreSQL)
- People, projects, concepts
- Relationship tracking
- Mention frequency

### 4. **Working Memory** (Redis)
- Current task state
- 1 hour TTL
- Agent context

## Database Configuration

**PostgreSQL:**
- Host: `postgresql.ac-agentic.svc.cluster.local`
- Port: `5432`
- Database: `zeus`
- User: `zeus`
- Connection pool: 5-20 connections

**Redis:**
- Host: `redis.ac-agentic.svc.cluster.local`
- Port: `6379`
- Decode responses: UTF-8

## Deployment Details

### OpenShift Resources
```bash
# Deployment
oc get deployment context-storage -n ac-agentic

# Service (ClusterIP)
oc get service context-storage -n ac-agentic

# Route (External Access)
oc get route context-storage -n ac-agentic

# Pod Status
oc get pods -l app=context-storage -n ac-agentic
```

### Environment Variables
```bash
DB_HOST=postgresql.ac-agentic.svc.cluster.local
DB_PORT=5432
DB_NAME=zeus
DB_USER=zeus
DB_PASSWORD=<configured>
REDIS_HOST=redis.ac-agentic.svc.cluster.local
REDIS_PORT=6379
```

### Container Image
```
Image: default-route-openshift-image-registry.apps.prod01.fis-cloud.fpt.com/ac-agentic/context-storage:v1.0.4
Base: python:3.11-slim
Workers: 2 (Uvicorn)
User: 1001 (non-root)
```

## Database Schema

### conversation_memory
```sql
CREATE TABLE conversation_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(255),
    message_role VARCHAR(50) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    metadata JSONB,
    importance_score FLOAT DEFAULT 0.5,
    memory_type VARCHAR(50) DEFAULT 'episodic',
    created_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);
CREATE INDEX idx_conversation_session ON conversation_memory(session_id, created_at);
```

### entity_memory
```sql
CREATE TABLE entity_memory (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,  -- person, project, task, concept
    entity_id VARCHAR(255) NOT NULL,
    entity_name VARCHAR(500) NOT NULL,
    attributes JSONB NOT NULL,
    relationships JSONB,
    agent_name VARCHAR(100),
    last_mentioned TIMESTAMP DEFAULT NOW(),
    mention_count INTEGER DEFAULT 1,
    importance FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id, agent_name)
);
```

### working_memory
```sql
CREATE TABLE working_memory (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    context_type VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    UNIQUE(agent_name, session_id, context_type)
);
```

## API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "healthy", "service": "context-storage", "timestamp": "..."}
```

### Short-term Memory
```bash
POST /memory/short-term
Body: {"key": "session_123", "value": {...}, "ttl": 1800}

GET /memory/short-term/{key}
```

### Long-term Conversation Memory
```bash
POST /memory/conversation
Body: {
    "session_id": "user_123_session_456",
    "agent_name": "zeus",
    "user_id": "dungpv30",
    "message_role": "user",
    "content": "How many hours did I log today?",
    "metadata": {"channel": "teams", "timestamp": "..."},
    "importance_score": 0.7
}

GET /memory/conversation/{session_id}?limit=10&agent_name=zeus
```

### Entity Memory
```bash
POST /memory/entity
Body: {
    "entity_type": "person",
    "entity_id": "dungpv30",
    "entity_name": "Dung Pham",
    "attributes": {"jira_username": "dungpv30", "team": "AC-Agentic"},
    "agent_name": "athena"
}

GET /memory/entity/{entity_type}/{entity_id}?agent_name=athena
```

### Working Memory
```bash
POST /memory/working
Body: {
    "agent_name": "athena",
    "session_id": "task_789",
    "context_type": "current_query",
    "context_data": {"query": "worklog", "date_from": "2024-01-01"},
    "ttl": 3600
}

GET /memory/working/{agent_name}/{session_id}/{context_type}
```

## Integration with Zeus & Athena

### Copy Client Library
```bash
cp /root/zeus-nexus/context-storage/client.py /root/zeus-nexus/docker/app/context_storage_client.py
```

### Zeus Core Integration (Example)
```python
from context_storage_client import ContextStorageClient

# Initialize client
context_client = ContextStorageClient(
    base_url="http://context-storage.ac-agentic.svc.cluster.local:8085"
)

# In chat endpoint - load recent context
@app.post("/chat")
async def chat(request: ChatRequest):
    # Load conversation history
    history = await context_client.get_conversation_history(
        session_id=request.session_id,
        agent_name="zeus",
        limit=10
    )
    
    # Add history to prompt context
    context_messages = [
        {"role": msg["message_role"], "content": msg["content"]}
        for msg in history
    ]
    
    # Get LLM response
    response = await llm_client.chat(context_messages + [new_message])
    
    # Store conversation
    await context_client.store_message(
        session_id=request.session_id,
        agent_name="zeus",
        user_id=request.user_id,
        role="user",
        content=request.message,
        importance=0.7
    )
    
    await context_client.store_message(
        session_id=request.session_id,
        agent_name="zeus",
        user_id=request.user_id,
        role="assistant",
        content=response.content,
        importance=0.8
    )
    
    return {"response": response.content}
```

### Athena Integration (Entity Memory)
```python
# Check if we've seen this person before
person = await context_client.get_entity("person", employee_name, agent_name="athena")

if person and "jira_username" in person["attributes"]:
    # Use cached mapping
    jira_username = person["attributes"]["jira_username"]
else:
    # Query Jira to find username
    jira_username = await find_jira_user(employee_name)
    
    # Store for next time
    await context_client.store_entity(
        entity_type="person",
        entity_id=employee_name,
        entity_name=employee_name,
        attributes={"jira_username": jira_username},
        agent_name="athena"
    )
```

## Testing

### Test Memory Storage
```bash
# Store a test message
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_001",
    "agent_name": "zeus",
    "user_id": "dungpv30",
    "message_role": "user",
    "content": "Hello, can you help me check my worklog?",
    "importance_score": 0.7
  }'

# Retrieve conversation history
curl "https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/conversation/test_session_001?limit=10"
```

### Test Entity Memory
```bash
# Store entity
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/entity \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person",
    "entity_id": "dungpv30",
    "entity_name": "Dung Pham",
    "attributes": {
      "jira_username": "dungpv30",
      "team": "AC-Agentic",
      "email": "dungpv30@fpt.com"
    },
    "agent_name": "athena"
  }'

# Retrieve entity
curl "https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/entity/person/dungpv30?agent_name=athena"
```

## Monitoring

### Check Logs
```bash
# Stream logs
oc logs -f deployment/context-storage -n ac-agentic

# Recent logs
oc logs deployment/context-storage --tail=100 -n ac-agentic
```

### Database Queries
```bash
# Check conversation count
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c "SELECT COUNT(*) FROM conversation_memory;"

# Check entity count
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c "SELECT entity_type, COUNT(*) FROM entity_memory GROUP BY entity_type;"

# Recent conversations
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c "SELECT session_id, agent_name, message_role, LEFT(content, 50), created_at FROM conversation_memory ORDER BY created_at DESC LIMIT 10;"
```

## Performance Considerations

### Redis (Short-term Memory)
- **Latency**: < 1ms for GET/SET operations
- **Memory**: Monitor Redis memory usage
- **TTL**: Auto-cleanup after expiration
- **Max Keys**: Unlimited (within memory constraints)

### PostgreSQL (Long-term Memory)
- **Connection Pool**: 5-20 connections (configured)
- **Index Usage**: Session ID + created_at indexed
- **Query Performance**: < 50ms for typical conversation retrieval (10 messages)
- **Storage**: ~1KB per message average

### Recommended Cleanup
```sql
-- Archive conversations older than 90 days
DELETE FROM conversation_memory 
WHERE created_at < NOW() - INTERVAL '90 days' 
  AND importance_score < 0.5;

-- Archive inactive entities (not mentioned in 30 days)
DELETE FROM entity_memory 
WHERE last_mentioned < NOW() - INTERVAL '30 days' 
  AND mention_count < 5;
```

## Next Steps

### 1. Integrate with Zeus Core ✅ Ready
- Copy `client.py` to Zeus Core
- Update chat endpoint to load/store context
- Test conversation continuity

### 2. Integrate with Athena ✅ Ready
- Use entity memory for person → Jira username mapping
- Cache worklog query results
- Track frequently asked queries

### 3. Add Memory Consolidation (Optional)
- Scheduled job to summarize old conversations
- Merge duplicate entities
- Update importance scores based on access patterns

### 4. Add Monitoring (Optional)
- Prometheus metrics endpoint
- Grafana dashboard
- Alert on high memory usage or slow queries

## Troubleshooting

### Pod Not Starting
```bash
# Check logs
oc logs deployment/context-storage --tail=50

# Check events
oc describe pod -l app=context-storage

# Verify environment variables
oc set env deployment/context-storage --list
```

### Database Connection Issues
```bash
# Test PostgreSQL connectivity
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c "SELECT 1;"

# Test Redis connectivity
oc exec redis-<pod> -- redis-cli PING
```

### Schema Issues
```bash
# Recreate tables
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus <<EOF
DROP TABLE IF EXISTS conversation_memory CASCADE;
DROP TABLE IF EXISTS entity_memory CASCADE;
DROP TABLE IF EXISTS working_memory CASCADE;
EOF

# Restart pod to reinitialize
oc delete pod -l app=context-storage
```

## Success Criteria

✅ **All Achieved:**
- [x] Service deployed to OpenShift
- [x] Health endpoint returns 200
- [x] PostgreSQL connection established
- [x] Redis connection established
- [x] Database schema initialized
- [x] External route created and accessible
- [x] API endpoints functional
- [x] Client library ready for integration

## Contact & Support

**Service Owner:** AC-Agentic Team  
**Namespace:** ac-agentic  
**Deployed by:** dungpv30@fpt.com  
**Date:** 2025-11-26  

---

**Context Storage Service v1.0.4** - Solving the context persistence problem for Zeus & Athena agents! 🎉
