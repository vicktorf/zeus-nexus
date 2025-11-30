# Zeus Nexus Context Storage Service

## 📚 Overview

Multi-layered memory system for intelligent agents to store and retrieve context across conversations, tasks, and time.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  CONTEXT STORAGE LAYERS                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  SHORT-TERM │  │  WORKING    │  │  LONG-TERM  │     │
│  │  (Redis)    │  │  MEMORY     │  │ (PostgreSQL)│     │
│  │             │  │             │  │             │     │
│  │ • Fast      │  │ • Current   │  │ • History   │     │
│  │ • Volatile  │  │   task      │  │ • Audit     │     │
│  │ • < 30min   │  │ • TTL 1hr   │  │ • Permanent │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  ENTITY     │  │  SEMANTIC   │  │CONSOLIDATION│     │
│  │  MEMORY     │  │  SEARCH     │  │   WORKER    │     │
│  │             │  │             │  │             │     │
│  │ • People    │  │ • Vector    │  │ • Summarize │     │
│  │ • Projects  │  │   DB        │  │ • Extract   │     │
│  │ • Concepts  │  │ • Similarity│  │ • Compress  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Memory Types

### **1. Short-Term Memory (Redis)**
- **Purpose**: Fast, temporary storage
- **TTL**: 30 minutes default
- **Use cases**:
  - Current conversation context
  - Temporary states
  - Quick lookups
  - Session data

**Example:**
```python
# Store current user input
await context_storage.store_short_term(
    session_id="abc123",
    agent_name="zeus",
    key="current_query",
    data={"query": "Get worklog for 22/11", "timestamp": "2025-11-26T10:30:00Z"},
    ttl_seconds=1800  # 30 minutes
)

# Retrieve
data = await context_storage.get_short_term(
    session_id="abc123",
    agent_name="zeus",
    key="current_query"
)
```

---

### **2. Long-Term Conversation Memory (PostgreSQL)**
- **Purpose**: Persistent conversation history
- **Retention**: Configurable (default: 90 days for low-importance)
- **Features**:
  - Message role tracking (user/assistant/system)
  - Importance scoring
  - Access tracking
  - Metadata support

**Example:**
```python
# Store user message
await context_storage.store_message(
    session_id="abc123",
    agent_name="zeus",
    role="user",
    content="Get worklog for John on 22/11/2025",
    user_id="user_001",
    metadata={"llm_model": "gpt-4", "intent": "worklog_query"},
    importance_score=0.8  # High importance
)

# Retrieve conversation history
history = await context_storage.get_conversation_history(
    session_id="abc123",
    agent_name="zeus",
    limit=20,
    time_range_hours=24
)
```

---

### **3. Entity Memory (Knowledge Graph)**
- **Purpose**: Store knowledge about people, projects, concepts
- **Features**:
  - Entity relationships
  - Attribute tracking
  - Mention counting
  - Importance scoring

**Supported Entity Types:**
- `person` - People (employees, users, contacts)
- `project` - Projects, initiatives
- `task` - Tasks, issues, tickets
- `concept` - Abstract concepts, topics
- `tool` - Tools, services, systems
- `document` - Files, reports, docs

**Example:**
```python
# Store person entity
await context_storage.store_entity(
    entity_type="person",
    entity_id="john_doe",
    entity_name="John Doe",
    attributes={
        "department": "Engineering",
        "role": "Senior Developer",
        "jira_username": "john.doe",
        "email": "john@company.com"
    },
    relationships={
        "works_on": ["project_ac", "project_zeus"],
        "reports_to": ["manager_jane"]
    },
    agent_name="athena",
    importance=0.8
)

# Retrieve entity
person = await context_storage.get_entity(
    entity_type="person",
    entity_id="john_doe",
    agent_name="athena"
)

# Search entities
engineers = await context_storage.search_entities(
    entity_type="person",
    name_contains="John",
    min_importance=0.5
)
```

---

### **4. Working Memory (Current Task Context)**
- **Purpose**: Store state of current active task
- **TTL**: 1 hour default
- **Use cases**:
  - Current task state
  - Intermediate results
  - User preferences for session
  - Temporary computations

**Example:**
```python
# Store current task state
await context_storage.store_working(
    agent_name="athena",
    session_id="abc123",
    context_type="worklog_query_state",
    context_data={
        "date": "2025-11-22",
        "employee": "John Doe",
        "status": "fetching_data",
        "partial_results": {"total_hours": 6.5}
    },
    ttl_seconds=3600
)

# Retrieve working memory
state = await context_storage.get_working(
    agent_name="athena",
    session_id="abc123",
    context_type="worklog_query_state"
)

# Clear after task completion
await context_storage.clear_working(
    agent_name="athena",
    session_id="abc123"
)
```

---

## 🔍 Semantic Search

Search across memories by meaning (not just keywords).

**Example:**
```python
# Find similar past conversations
results = await context_storage.semantic_search(
    query="worklog reports for engineering team",
    agent_name="athena",
    limit=10
)
```

**TODO**: Integrate with vector database (Qdrant/Pinecone) for true semantic search using embeddings.

---

## 🔄 Memory Consolidation

Background process to:
1. **Summarize** old conversations
2. **Extract** important entities
3. **Compute** importance scores
4. **Compress** redundant data
5. **Archive** old memories

**Trigger consolidation:**
```python
# Run consolidation (background task)
await context_storage.consolidate_memories(
    agent_name="zeus",
    session_id="abc123"
)
```

**Cleanup expired memories:**
```python
# Periodic cleanup (run via cron)
result = await context_storage.cleanup_expired_memories()
# Returns: {"status": "cleaned", "archived_count": 150}
```

---

## 📊 Memory Lifecycle

```
1. NEW MESSAGE
   ↓
2. Store in SHORT-TERM (Redis, 30min)
   ↓
3. Extract ENTITIES → Entity Memory
   ↓
4. Store in LONG-TERM (PostgreSQL)
   ↓
5. Update WORKING MEMORY (current task)
   ↓
6. After 24 hours: CONSOLIDATION
   ↓
7. After 90 days: ARCHIVE or DELETE (if low importance)
```

---

## 🎨 Integration Patterns

### **Pattern 1: Context-Aware Chat**

```python
@app.post("/chat")
async def chat_with_context(message: ChatMessage):
    # 1. Load recent context
    history = await context_storage.get_conversation_history(
        session_id=message.session_id,
        limit=10
    )
    
    # 2. Build context-aware prompt
    context_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history["memories"]
    ]
    
    # 3. Call LLM with context
    response = await llm.chat(context_messages + [{"role": "user", "content": message.text}])
    
    # 4. Store both user message and response
    await context_storage.store_message(session_id, "user", message.text)
    await context_storage.store_message(session_id, "assistant", response)
    
    return response
```

### **Pattern 2: Entity Tracking**

```python
@app.post("/worklog/query")
async def worklog_with_entity_tracking(request: WorklogRequest):
    # 1. Check if we know this person
    person = await context_storage.get_entity(
        entity_type="person",
        entity_id=request.employee_name.lower().replace(" ", "_")
    )
    
    # 2. Use cached info if available
    if person and "jira_username" in person["attributes"]:
        jira_username = person["attributes"]["jira_username"]
    else:
        # Fetch from Jira
        jira_username = await fetch_jira_username(request.employee_name)
        
        # 3. Store for next time
        await context_storage.store_entity(
            entity_type="person",
            entity_id=request.employee_name.lower().replace(" ", "_"),
            entity_name=request.employee_name,
            attributes={"jira_username": jira_username}
        )
    
    # 4. Query worklogs
    worklogs = await fetch_worklogs(jira_username, request.date)
    
    return worklogs
```

### **Pattern 3: Task State Management**

```python
@app.post("/task/long-running")
async def long_running_task(task: Task):
    # 1. Initialize task state
    await context_storage.store_working(
        agent_name="worker",
        session_id=task.id,
        context_type="task_state",
        context_data={
            "status": "started",
            "progress": 0,
            "steps_completed": []
        }
    )
    
    # 2. Process steps, update state
    for i, step in enumerate(task.steps):
        await process_step(step)
        
        await context_storage.store_working(
            agent_name="worker",
            session_id=task.id,
            context_type="task_state",
            context_data={
                "status": "in_progress",
                "progress": (i + 1) / len(task.steps) * 100,
                "steps_completed": task.steps[:i+1]
            }
        )
    
    # 3. Mark complete
    await context_storage.store_working(
        agent_name="worker",
        session_id=task.id,
        context_type="task_state",
        context_data={"status": "completed", "progress": 100}
    )
```

---

## 📈 Performance Considerations

### **Latency**
- Short-term memory (Redis): **< 10ms**
- Working memory (PostgreSQL): **< 50ms**
- Long-term memory (PostgreSQL): **< 100ms**
- Semantic search: **< 500ms** (will improve with vector DB)

### **Storage**
- Short-term: **Auto-expire** (no cleanup needed)
- Working memory: **Auto-expire** after TTL
- Long-term: **Archive after 90 days** (low importance)
- Entity memory: **Keep indefinitely** (knowledge accumulation)

### **Scalability**
- Redis: Handles **100K+ ops/sec**
- PostgreSQL: Optimized with indexes
- Can shard by agent_name or user_id if needed

---

## 🚀 Deployment

```bash
# Build
cd /root/zeus-nexus/context-storage
podman build -t context-storage:v1.0.0 .

# Deploy to OpenShift
oc apply -f deployment.yaml

# Verify
curl http://context-storage.ac-agentic.svc.cluster.local:8085/health
```

---

## 🔒 Security

- **Access Control**: Agent-based isolation
- **Data Encryption**: At rest (PostgreSQL) and in transit (TLS)
- **PII Handling**: Automatic PII detection and masking (TODO)
- **Audit Trail**: All access logged

---

## 📝 TODO / Roadmap

- [ ] **Vector Database Integration** (Qdrant/Pinecone)
- [ ] **Embeddings Generation** (OpenAI/Sentence Transformers)
- [ ] **True Semantic Search** with cosine similarity
- [ ] **PII Detection** and automatic redaction
- [ ] **Memory Compression** with LLM summarization
- [ ] **Knowledge Graph Visualization**
- [ ] **Multi-tenant Support** with user isolation
- [ ] **Backup & Restore** for critical memories
- [ ] **Analytics Dashboard** (Grafana)
- [ ] **Memory Export** (JSON/CSV)

---

## 📚 API Reference

See full API documentation at: `http://context-storage:8085/docs` (FastAPI auto-generated)

---

## 🤝 Contributing

When adding new memory types:
1. Add table schema in `startup()`
2. Create Pydantic models
3. Add CRUD endpoints
4. Update `client.py` with convenience methods
5. Add integration examples
6. Update this README

---

## 📞 Support

Questions? Issues? Contact the Zeus Nexus team or open an issue in the repo.
