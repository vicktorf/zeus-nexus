"""
Example: Integration of Context Storage into Zeus Core
Demonstrates how to use Context Storage Client in agents
"""

# Add to Zeus Core main.py imports:
from context_storage_client import ContextStorageClient

# Initialize Context Storage Client (add to startup)
context_storage = ContextStorageClient()

@app.on_event("shutdown")
async def shutdown():
    # ... existing cleanup ...
    await context_storage.close()

# ===== EXAMPLE 1: Enhanced Chat Endpoint with Context Tracking =====

@app.post("/chat")
async def chat_enhanced(message: ChatMessage):
    """
    Enhanced chat endpoint with full context tracking
    """
    session_id = message.session_id or str(uuid.uuid4())
    agent_name = message.agent_preference or "zeus"
    
    # 1. Retrieve recent conversation history from context storage
    recent_context = await context_storage.get_conversation_history(
        session_id=session_id,
        agent_name=agent_name,
        limit=10,
        time_range_hours=24
    )
    
    # 2. Get working memory (current task state)
    working_memory = await context_storage.get_working(
        agent_name=agent_name,
        session_id=session_id
    )
    
    # 3. Build context-aware system prompt
    context_prompt = f"""You are {agent_name.upper()}.

Recent conversation context:
{json.dumps(recent_context.get('memories', [])[-5:], indent=2)}

Current task state:
{json.dumps(working_memory, indent=2) if working_memory else 'No active task'}

User message: {message.message}
"""
    
    # 4. Store user message in long-term memory
    await context_storage.store_message(
        session_id=session_id,
        agent_name=agent_name,
        role="user",
        content=message.message,
        user_id=message.user_id,
        metadata={"llm_model": message.llm_model},
        importance_score=0.7  # User messages are important
    )
    
    # 5. Extract entities from user message (people, projects, dates)
    entities = extract_entities_from_message(message.message)
    for entity in entities:
        await context_storage.store_entity(
            entity_type=entity["type"],
            entity_id=entity["id"],
            entity_name=entity["name"],
            attributes=entity["attributes"],
            agent_name=agent_name,
            importance=0.6
        )
    
    # 6. Call LLM with context
    llm_response = await call_llm_api(
        model=message.llm_model,
        messages=[
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": message.message}
        ],
        temperature=message.temperature,
        max_tokens=message.max_tokens
    )
    
    # 7. Store assistant response
    await context_storage.store_message(
        session_id=session_id,
        agent_name=agent_name,
        role="assistant",
        content=llm_response,
        user_id=message.user_id,
        metadata={"llm_model": message.llm_model, "response_length": len(llm_response)},
        importance_score=0.6
    )
    
    # 8. Update working memory with current state
    await context_storage.store_working(
        agent_name=agent_name,
        session_id=session_id,
        context_type="last_interaction",
        context_data={
            "user_message": message.message[:200],
            "response_summary": llm_response[:200],
            "timestamp": datetime.utcnow().isoformat(),
            "llm_model": message.llm_model
        },
        ttl_seconds=3600
    )
    
    return {
        "session_id": session_id,
        "response": llm_response,
        "agent": agent_name,
        "context_used": len(recent_context.get('memories', [])),
        "entities_extracted": len(entities)
    }

# ===== EXAMPLE 2: Entity Extraction Helper =====

def extract_entities_from_message(message: str) -> List[Dict]:
    """
    Extract entities from user message
    TODO: Use NER model or LLM for better extraction
    """
    import re
    entities = []
    
    # Extract dates
    date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    dates = re.findall(date_pattern, message)
    for date in dates:
        entities.append({
            "type": "date",
            "id": date,
            "name": date,
            "attributes": {"mentioned_in": message[:100]}
        })
    
    # Extract names (capitalized words)
    name_pattern = r'\b([A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+(?:\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zđàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]+)*)\b'
    names = re.findall(name_pattern, message)
    for name in names:
        if len(name) > 3:  # Filter out short words
            entities.append({
                "type": "person",
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "attributes": {"context": message[:100]}
            })
    
    # Extract Jira issue keys
    jira_pattern = r'\b([A-Z]+-\d+)\b'
    issues = re.findall(jira_pattern, message)
    for issue in issues:
        entities.append({
            "type": "jira_issue",
            "id": issue,
            "name": issue,
            "attributes": {"mentioned_in": message[:100]}
        })
    
    return entities

# ===== EXAMPLE 3: Athena Integration with Context =====

# In Athena agent main.py:

@app.post("/task")
async def execute_task_with_context(request: dict):
    """
    Enhanced task execution with context storage
    """
    context_client = ContextStorageClient()
    session_id = request.get("session_id", "default")
    action = request.get("action")
    
    try:
        # 1. Check if we have context about this user/project
        user_context = await context_client.get_working(
            agent_name="athena",
            session_id=session_id,
            context_type="user_preferences"
        )
        
        # 2. Get relevant entities (projects, people)
        if action == "get_worklogs":
            employee_name = request.get("params", {}).get("employee_name")
            
            if employee_name:
                # Check if we know this person
                person_entity = await context_client.get_entity(
                    entity_type="person",
                    entity_id=employee_name.lower().replace(" ", "_"),
                    agent_name="athena"
                )
                
                if person_entity:
                    # Use stored username mapping
                    username = person_entity["attributes"].get("jira_username")
                    if username:
                        request["params"]["jira_username"] = username
        
        # 3. Execute the actual task (existing logic)
        result = await original_execute_task(request)
        
        # 4. Store result in context
        await context_client.store_working(
            agent_name="athena",
            session_id=session_id,
            context_type="last_worklog_query",
            context_data={
                "action": action,
                "params": request.get("params", {}),
                "result_summary": result.get("response", "")[:200],
                "timestamp": datetime.utcnow().isoformat()
            },
            ttl_seconds=1800
        )
        
        # 5. Extract and store entities from result
        if "employee_name" in request.get("params", {}):
            employee = request["params"]["employee_name"]
            # Store person entity with worklog stats
            await context_client.store_entity(
                entity_type="person",
                entity_id=employee.lower().replace(" ", "_"),
                entity_name=employee,
                attributes={
                    "last_worklog_query": datetime.utcnow().isoformat(),
                    "department": "engineering",  # Could extract from Jira
                    "jira_username": request.get("params", {}).get("jira_username", "")
                },
                agent_name="athena",
                importance=0.7
            )
        
        return result
        
    finally:
        await context_client.close()

# ===== EXAMPLE 4: Context-Aware Error Handling =====

@app.exception_handler(Exception)
async def context_aware_error_handler(request: Request, exc: Exception):
    """
    Store errors in context for learning
    """
    context_client = ContextStorageClient()
    
    try:
        # Store error in working memory
        await context_client.store_working(
            agent_name="zeus",
            session_id=request.headers.get("X-Session-ID", "default"),
            context_type="last_error",
            context_data={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "endpoint": str(request.url),
                "timestamp": datetime.utcnow().isoformat()
            },
            ttl_seconds=3600
        )
        
        # Check for similar past errors
        similar_errors = await context_client.semantic_search(
            query=str(exc),
            agent_name="zeus",
            limit=3
        )
        
        error_context = ""
        if similar_errors.get("results"):
            error_context = f"\n\nSimilar errors occurred {len(similar_errors['results'])} times before."
        
    finally:
        await context_client.close()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "context": error_context
        }
    )

# ===== EXAMPLE 5: Context-Based Personalization =====

@app.post("/chat/personalized")
async def personalized_chat(message: ChatMessage):
    """
    Personalized responses based on user history
    """
    context_client = ContextStorageClient()
    
    # Get user's interaction history
    user_history = await context_client.get_conversation_history(
        user_id=message.user_id,
        agent_name="zeus",
        limit=100,
        time_range_hours=168  # Last week
    )
    
    # Analyze user preferences
    user_preferences = analyze_user_preferences(user_history)
    
    # Store preferences in working memory
    await context_client.store_working(
        agent_name="zeus",
        session_id=message.session_id,
        context_type="user_preferences",
        context_data=user_preferences,
        ttl_seconds=86400  # 24 hours
    )
    
    # Build personalized system prompt
    personalized_prompt = f"""You are Zeus, personalized assistant.

User preferences:
- Preferred language: {user_preferences.get('language', 'Vietnamese')}
- Response style: {user_preferences.get('style', 'professional')}
- Common tasks: {', '.join(user_preferences.get('common_tasks', []))}
- Interaction frequency: {user_preferences.get('frequency', 'occasional')}

Adapt your responses accordingly."""
    
    # Continue with LLM call...
    
    await context_client.close()
    return {"response": "Personalized response..."}

def analyze_user_preferences(history: Dict) -> Dict:
    """Analyze user interaction patterns"""
    memories = history.get("memories", [])
    
    # Detect language
    vietnamese_count = sum(1 for m in memories if any(c in m["content"] for c in "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"))
    language = "Vietnamese" if vietnamese_count > len(memories) / 2 else "English"
    
    # Detect common tasks
    task_keywords = {}
    for memory in memories:
        content = memory["content"].lower()
        if "worklog" in content:
            task_keywords["worklog"] = task_keywords.get("worklog", 0) + 1
        if "jira" in content or "issue" in content:
            task_keywords["jira"] = task_keywords.get("jira", 0) + 1
        if "deploy" in content or "monitoring" in content:
            task_keywords["devops"] = task_keywords.get("devops", 0) + 1
    
    common_tasks = sorted(task_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "language": language,
        "style": "concise" if len(memories) > 50 else "detailed",
        "common_tasks": [task[0] for task in common_tasks],
        "frequency": "frequent" if len(memories) > 20 else "occasional"
    }
