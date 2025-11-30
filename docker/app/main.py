# Zeus Nexus Core API v3 - With Real LLM Integration
import os
import asyncio
import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import redis.asyncio as redis
import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

# LLM SDKs
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai

# Context Storage Client
from context_storage_client import ContextStorageClient

# Metrics
request_count = Counter('zeus_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('zeus_request_duration_seconds', 'Request duration')
active_agents = Gauge('zeus_active_agents', 'Number of active agents')
llm_requests = Counter('zeus_llm_requests_total', 'Total LLM requests', ['provider', 'model'])

app = FastAPI(
    title="Zeus Nexus Core", 
    version="3.6.1", 
    description="AI Pantheon Command Center - Zeus Core API with Zeus as Primary Assistant"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Context Storage client
context_storage = ContextStorageClient(
    base_url=os.getenv("CONTEXT_STORAGE_URL", "http://context-storage.ac-agentic.svc.cluster.local:8085")
)

# LLM Provider Configuration
class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

# Models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None
    agent_preference: Optional[str] = None
    llm_model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    confidence: float
    execution_time: float

class TaskRequest(BaseModel):
    task_type: str
    agent_name: str
    input_data: Dict[str, Any]
    llm_model: Optional[str] = "gpt-4"

class AgentStatus(BaseModel):
    name: str
    status: str
    endpoint: str
    last_health_check: Optional[str]

class LLMConfigModel(BaseModel):
    model: str
    provider: str
    api_key_configured: bool
    context_length: int
    cost_per_1k_input: float
    cost_per_1k_output: float

# Global connections
redis_client = None
db_pool = None

# In-memory API key storage
runtime_api_keys: Dict[str, str] = {}

# LLM Model Registry with correct Anthropic model names
LLM_MODELS = {
    "gpt-4": {
        "provider": LLMProvider.OPENAI,
        "context_length": 8192,
        "cost": {"input": 0.03, "output": 0.06}
    },
    "gpt-4-turbo": {
        "provider": LLMProvider.OPENAI,
        "context_length": 128000,
        "cost": {"input": 0.01, "output": 0.03}
    },
    "gpt-4o": {
        "provider": LLMProvider.OPENAI,
        "context_length": 128000,
        "cost": {"input": 0.005, "output": 0.015}
    },
    "gpt-3.5-turbo": {
        "provider": LLMProvider.OPENAI,
        "context_length": 16385,
        "cost": {"input": 0.0005, "output": 0.0015}
    },
    "claude-3-opus-20240229": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.015, "output": 0.075}
    },
    "claude-3-5-sonnet-20241022": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.003, "output": 0.015}
    },
    "claude-3-sonnet-20240229": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.003, "output": 0.015}
    },
    "claude-3-haiku-20240307": {
        "provider": LLMProvider.ANTHROPIC,
        "context_length": 200000,
        "cost": {"input": 0.00025, "output": 0.00125}
    },
    "gemini-pro": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 32000,
        "cost": {"input": 0.0005, "output": 0.0015}
    },
    "gemini-1.5-pro": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 1000000,
        "cost": {"input": 0.00125, "output": 0.005}
    },
    "gemini-1.5-flash": {
        "provider": LLMProvider.GOOGLE,
        "context_length": 1000000,
        "cost": {"input": 0.000125, "output": 0.0005}
    }
}

def get_llm_api_key(provider: LLMProvider) -> Optional[str]:
    """Get API key for LLM provider"""
    runtime_key = runtime_api_keys.get(provider.value)
    if runtime_key:
        return runtime_key
    
    key_map = {
        LLMProvider.OPENAI: os.getenv('OPENAI_API_KEY'),
        LLMProvider.ANTHROPIC: os.getenv('ANTHROPIC_API_KEY'),
        LLMProvider.GOOGLE: os.getenv('GOOGLE_AI_API_KEY')
    }
    return key_map.get(provider)

def is_llm_configured(model_id: str) -> bool:
    """Check if LLM model is configured with API key"""
    model_config = LLM_MODELS.get(model_id)
    if not model_config:
        return False
    provider = model_config["provider"]
    return bool(get_llm_api_key(provider))

async def call_llm_api(
    model: str, 
    messages: List[Dict[str, str]], 
    temperature: float = 0.7, 
    max_tokens: int = 1000
) -> str:
    """Call LLM API (OpenAI, Anthropic, or Google) and return response"""
    if model not in LLM_MODELS:
        raise ValueError(f"Unknown model: {model}")
    
    model_config = LLM_MODELS[model]
    provider = model_config["provider"]
    api_key = get_llm_api_key(provider)
    
    if not api_key:
        raise ValueError(f"API key not configured for provider: {provider.value}")
    
    try:
        if provider == LLMProvider.OPENAI:
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        elif provider == LLMProvider.ANTHROPIC:
            client = AsyncAnthropic(api_key=api_key)
            system_message = ""
            anthropic_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append(msg)
            
            response = await client.messages.create(
                model=model,
                system=system_message if system_message else "You are a helpful AI assistant.",
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content[0].text
        
        elif provider == LLMProvider.GOOGLE:
            genai.configure(api_key=api_key)
            google_model = model.replace("gemini-", "gemini-")
            model_instance = genai.GenerativeModel(google_model)
            
            user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            
            response = await model_instance.generate_content_async(
                user_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            return response.text
        
    except Exception as e:
        raise ValueError(f"LLM API call failed: {str(e)}")

async def call_agent_with_llm(
    agent_endpoint: str,
    agent_name: str,
    user_message: str,
    llm_model: str,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """Call agent endpoint với LLM-enhanced processing"""
    try:
        # Check if agent has specific handlers (e.g., Jira for Athena)
        if agent_name == "athena" and any(keyword in user_message.lower() for keyword in ["jira", "issue", "task", "ticket", "sprint", "project"]):
            # Athena can handle Jira queries directly
            # For now, let LLM process and format the request
            pass
        
        # Use LLM to understand and format the request
        async with httpx.AsyncClient() as client:
            # Try to call agent endpoint first
            try:
                response = await client.get(f"{agent_endpoint}/health", timeout=5.0)
                if response.status_code == 200:
                    # Agent is healthy, can add more sophisticated routing here
                    pass
            except:
                pass
        
        # For now, fall back to LLM
        return None
        
    except Exception as e:
        return None

async def init_connections():
    """Initialize database connections"""
    global redis_client, db_pool
    
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis.ac-agentic.svc.cluster.local:6379')
        redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://zeus:zeus123@postgresql.ac-agentic.svc.cluster.local:5432/zeus')
        db_pool = await asyncpg.create_pool(postgres_url, min_size=2, max_size=10)
        
        print("✅ Zeus Nexus Core v3 initialized with Real LLM Integration!")
        print(f"   - Redis: {redis_url}")
        print(f"   - PostgreSQL: Connected")
        
        print("\n🤖 LLM Providers Status:")
        for provider in LLMProvider:
            api_key = get_llm_api_key(provider)
            status = "✅ Configured" if api_key else "❌ Not Configured"
            print(f"   - {provider.value.upper()}: {status}")
            
    except Exception as e:
        print(f"❌ Failed to initialize connections: {e}")
        raise

@app.on_event("startup")
async def startup():
    await init_connections()

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()
    if db_pool:
        await db_pool.close()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat")
async def chat(message: ChatMessage):
    """Chat endpoint with real LLM API integration"""
    request_count.labels(method="POST", endpoint="/chat").inc()
    
    try:
        llm_model = message.llm_model or "gpt-4"
        if llm_model not in LLM_MODELS:
            raise HTTPException(status_code=400, detail=f"Unknown LLM model: {llm_model}")
        
        if not is_llm_configured(llm_model):
            provider = LLM_MODELS[llm_model]["provider"].value
            raise HTTPException(
                status_code=503, 
                detail=f"LLM provider '{provider}' not configured. Please set API key."
            )
        
        provider = LLM_MODELS[llm_model]["provider"].value
        llm_requests.labels(provider=provider, model=llm_model).inc()
        
        session_id = message.session_id or str(uuid.uuid4())
        
        # Agent routing - Determine which agent FIRST
        agent_map = {
            "project": "athena", "jira": "athena", "confluence": "athena",
            "monitor": "ares", "grafana": "ares", "alert": "ares",
            "sales": "apollo", "revenue": "apollo",
            "docs": "clio", "report": "clio",
            "cloud": "hephaestus", "terraform": "hephaestus",
            "notion": "hermes", "customer": "hermes",
            "learn": "mnemosyne", "knowledge": "mnemosyne"
        }
        
        selected_agent = message.agent_preference
        if not selected_agent:
            message_lower = message.message.lower()
            for keyword, agent in agent_map.items():
                if keyword in message_lower:
                    selected_agent = agent
                    break
        
        if not selected_agent:
            selected_agent = "zeus"
        
        # Load conversation history (using correct agent name)
        context_messages = []
        try:
            history_response = await context_storage.get_conversation_history(
                session_id=session_id,
                agent_name=selected_agent,
                limit=10
            )
            
            # Extract conversations array from response
            history = history_response.get("conversations", []) if isinstance(history_response, dict) else []
            
            # Build context messages for LLM
            for msg in history:
                context_messages.append({
                    "role": msg["message_role"],
                    "content": msg["content"]
                })
            
            if context_messages:
                print(f"📚 Loaded {len(context_messages)} previous messages from context for {selected_agent}")
            else:
                print(f"📭 No previous context found for session {session_id}, agent {selected_agent}")
        except Exception as e:
            print(f"⚠️ Failed to load context: {e}, proceeding without history")
            context_messages = []
        
        # Store user message in Context Storage (using correct agent name)
        try:
            await context_storage.store_message(
                session_id=session_id,
                agent_name=selected_agent,
                user_id=message.user_id or "anonymous",
                role="user",
                content=message.message,
                importance_score=0.8,
                metadata={"llm_model": llm_model}
            )
            print(f"✅ Stored user message in context (session: {session_id}, agent: {selected_agent})")
        except Exception as e:
            print(f"⚠️ Failed to store user message in context: {e}")
        
        async with db_pool.acquire() as conn:
            # Zeus is always available as the core coordinator
            if selected_agent == "zeus":
                agent_info = {
                    'name': 'zeus',
                    'endpoint': None,  # Zeus is built-in, no external endpoint
                    'status': 'active'
                }
            else:
                agent_info = await conn.fetchrow("""
                    SELECT name, endpoint, status
                    FROM agents
                    WHERE name = $1
                """, selected_agent)
                
                if not agent_info:
                    raise HTTPException(status_code=404, detail=f"Agent '{selected_agent}' not found")
                
                if agent_info['status'] != 'active':
                    raise HTTPException(status_code=503, detail=f"Agent '{selected_agent}' is not active")
            
            conversation_id = await conn.fetchval("""
                INSERT INTO conversations (session_id, agent_name, message, user_id, llm_model, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, session_id, selected_agent, message.message, message.user_id, llm_model, datetime.utcnow())
            
            # Agent profiles with Zeus as primary assistant
            agent_profiles = {
                "zeus": """You are Zeus, the Chief AI Assistant and Coordinator of the AI Pantheon system.

Your role:
- Primary assistant to the user for all general queries
- Intelligent coordinator who delegates to specialist agents when needed
- Information processor who adds context and clarity to specialist responses
- Friendly, professional, and conversational in Vietnamese and English

Your capabilities:
- Answer general questions, provide information, and assist with various tasks
- Understand user intent and determine when specialist help is needed
- Coordinate with specialist agents (Athena for Jira, Ares for DevOps, etc.)
- Synthesize and present information from multiple sources clearly

Communication style:
- Warm and approachable but professional
- Explain things clearly without being condescending
- Use emojis sparingly and appropriately
- Respond in the same language as the user (Vietnamese or English)

When you don't need specialist help, answer directly. When you do, I'll call the specialist and you'll present their response with added context.""",
                "athena": "You are Athena, the Project Manager AI specialist. You focus on Jira, Confluence, project management, and team coordination. Provide accurate data from Jira systems.",
                "ares": "You are Ares, the DevOps & Monitoring AI specialist. You focus on infrastructure monitoring, Grafana, alerts, and incident response.",
                "apollo": "You are Apollo, the Sales Intelligence AI specialist. You focus on sales forecasting, CRM, revenue tracking, and customer insights.",
                "clio": "You are Clio, the Documentation AI specialist. You focus on technical documentation, reports, wikis, and knowledge management.",
                "hephaestus": "You are Hephaestus, the Infrastructure AI specialist. You focus on cloud infrastructure, Terraform, AWS, and deployment automation.",
                "hermes": "You are Hermes, the Customer Success AI specialist. You focus on customer communication, Notion, contact management, and support.",
                "mnemosyne": "You are Mnemosyne, the Knowledge & Learning AI specialist. You focus on training, analytics, knowledge base, and data insights."
            }
            
            system_prompt = agent_profiles.get(selected_agent, agent_profiles["zeus"])
            
            # Try calling agent endpoint first for specialized queries
            response_text = None
            if agent_info and selected_agent == "athena":
                # LLM-based intent detection - more intelligent
                try:
                    intent_prompt = f"""You are an intent classifier for Zeus AI system.

User message: "{message.message}"

Determine if this message requires accessing Jira/project management data.

Answer "YES" ONLY if the user is:
- Requesting Jira data (issues, tasks, worklogs, projects)
- Asking about work hours, time tracking, or project status  
- Creating or updating Jira issues
- Querying project information or team workload

Answer "NO" if it's:
- A greeting (xin chào, hello, hi, hey)
- General conversation or chitchat
- Asking who you are or introducing yourself
- Questions about your capabilities or features
- Thanking or saying goodbye
- Any question that doesn't need actual Jira data

Return ONLY one word: YES or NO"""

                    intent_response = await call_llm_api(
                        model=llm_model,
                        messages=[
                            {"role": "system", "content": "You are a precise intent classifier. Return only YES or NO."},
                            {"role": "user", "content": intent_prompt}
                        ],
                        temperature=0.1,
                        max_tokens=10
                    )
                    
                    requires_jira = "YES" in intent_response.upper()
                    print(f"🧠 LLM Intent Detection: query='{message.message[:50]}...', requires_jira={requires_jira}, llm_response='{intent_response}'")
                    
                except Exception as e:
                    print(f"⚠️ Intent detection failed: {e}, falling back to keyword matching")
                    # Fallback to keyword matching if LLM fails
                    query_lower = message.message.lower()
                    jira_keywords = ["worklog", "work log", "thời gian", "làm việc", "issue", "ticket", "task", "project", "dự án", "jira"]
                    general_keywords = ["xin chào", "hello", "hi", "bạn là ai", "giới thiệu", "who are you"]
                    is_general = any(keyword in query_lower for keyword in general_keywords)
                    requires_jira = any(keyword in query_lower for keyword in jira_keywords) and not is_general
                
                # If no Jira data needed, Zeus responds directly
                if not requires_jira:
                    try:
                        # Use the context_messages loaded at the start
                        llm_messages = [
                            {"role": "system", "content": system_prompt}
                        ] + context_messages + [
                            {"role": "user", "content": message.message}
                        ]
                        
                        response_text = await call_llm_api(
                            model=llm_model,
                            messages=llm_messages,
                            temperature=message.temperature,
                            max_tokens=message.max_tokens
                        )
                        
                        # Save to database
                        await conn.execute("""
                            UPDATE conversations
                            SET response = $1, llm_provider = $2, updated_at = $3
                            WHERE id = $4
                        """, response_text, provider, datetime.utcnow(), conversation_id)
                        
                        # Cache the response
                        cache_key = f"chat:{session_id}:{selected_agent}"
                        await redis_client.setex(
                            cache_key,
                            86400,
                            json.dumps({
                                "message": message.message,
                                "response": response_text,
                                "agent": selected_agent,
                                "llm_model": llm_model,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        )
                        
                        # Store Zeus response in Context Storage
                        try:
                            await context_storage.store_message(
                                session_id=session_id,
                                agent_name=selected_agent,
                                user_id=message.user_id or "anonymous",
                                role="assistant",
                                content=response_text,
                                importance_score=0.9,
                                metadata={"llm_model": llm_model, "llm_provider": provider}
                            )
                            print(f"✅ Stored Zeus response in context (session: {session_id})")
                        except Exception as e:
                            print(f"⚠️ Failed to store Zeus response in context: {e}")
                        
                        return {
                            "session_id": session_id,
                            "response": response_text,
                            "agent": selected_agent,
                            "llm_model": llm_model,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    except Exception as llm_error:
                        # Fallback to basic response when API key is not configured
                        print(f"LLM call failed: {llm_error}")
                        
                        # Provide a basic but helpful response based on query type
                        if any(word in message.message.lower() for word in ["xin chào", "hello", "hi"]):
                            response_text = """Xin chào! 👋

Tôi là **Zeus**, trợ lý AI chính của hệ thống AI Pantheon. Tôi có thể giúp bạn:

🔹 Trả lời câu hỏi chung
🔹 Điều phối các chuyên gia AI (Athena cho Jira, Ares cho DevOps, v.v.)
🔹 Xử lý và tổng hợp thông tin từ nhiều nguồn

Bạn cần giúp gì không?

*⚠️ Lưu ý: Hiện tại LLM API key chưa được cấu hình. Vui lòng cấu hình API key trong phần Settings để có trải nghiệm tốt hơn.*"""
                        
                        elif any(word in message.message.lower() for word in ["bạn là ai", "giới thiệu", "who are you"]):
                            response_text = """Tôi là **Zeus** - Trưởng nhóm AI của hệ thống AI Pantheon! ⚡

**Vai trò của tôi:**
- 🎯 Trợ lý AI chính phục vụ bạn
- 🧭 Điều phối viên thông minh giữa các chuyên gia AI
- 📊 Xử lý và làm giàu thông tin từ các nguồn khác nhau

**Đội ngũ chuyên gia:**
- **Athena** 🏛️ - Chuyên gia Jira & Quản lý dự án
- **Ares** ⚔️ - Chuyên gia DevOps & Giám sát
- **Apollo** ☀️ - Chuyên gia Phân tích Kinh doanh
- **Hephaestus** 🔨 - Chuyên gia Hạ tầng
- **Hermes** 📨 - Chuyên gia Chăm sóc Khách hàng

Khi bạn cần thông tin Jira, tôi sẽ nhờ Athena giúp. Khi cần giám sát hệ thống, tôi gọi Ares. Nhưng với câu hỏi chung, tôi sẽ trả lời trực tiếp!

*⚠️ Hiện tại LLM API key chưa được cấu hình. Vui lòng vào Settings > LLM Setup để cấu hình.*"""
                        
                        else:
                            response_text = f"""Tôi là Zeus, trợ lý AI của bạn. Tôi đã nhận được tin nhắn: "{message.message}"

⚠️ **Lưu ý:** Hiện tại hệ thống chưa được cấu hình LLM API key nên tôi không thể xử lý câu hỏi phức tạp.

**Để sử dụng đầy đủ tính năng:**
1. Vào **Settings** > **LLM Setup**
2. Chọn provider (OpenAI, Anthropic, hoặc Google)
3. Nhập API key hợp lệ
4. Lưu cấu hình

Sau đó tôi sẽ có thể trả lời mọi câu hỏi của bạn một cách thông minh! 🚀"""
                        
                        await conn.execute("""
                            UPDATE conversations
                            SET response = $1, llm_provider = $2, updated_at = $3
                            WHERE id = $4
                        """, response_text, provider, datetime.utcnow(), conversation_id)
                        
                        # Store fallback response in Context Storage
                        try:
                            await context_storage.store_message(
                                session_id=session_id,
                                agent_name=selected_agent,
                                user_id=message.user_id or "anonymous",
                                role="assistant",
                                content=response_text,
                                importance_score=0.7,
                                metadata={"llm_model": llm_model, "llm_provider": provider, "fallback": True}
                            )
                            print(f"✅ Stored fallback response in context (session: {session_id})")
                        except Exception as e:
                            print(f"⚠️ Failed to store fallback response in context: {e}")
                        
                        return {
                            "session_id": session_id,
                            "response": response_text,
                            "agent": selected_agent,
                            "llm_model": llm_model,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                
                # Only call Athena if Jira data is actually needed
                if requires_jira:
                    try:
                        # First, use LLM to parse the query and extract structured parameters
                        parse_prompt = f"""You are a query parser. Extract structured information from the user's question.

User question: "{message.message}"

Extract and return ONLY a JSON object with these fields:
{{
    "action": "get_worklogs" or "search_tasks" or "get_projects" or "create_issue",
    "date": "YYYY-MM-DD format if date mentioned, else null",
    "employee_name": "full name if mentioned, else null",
    "project": "project key if mentioned, else null",
    "summary": "brief description of what user wants"
}}

Rules:
- Convert Vietnamese dates like "22/11/2025" or "22/11/025" to "2025-11-22"
- If year is 3 digits like "025", prepend "2" to make "2025"
- If year is 2 digits like "25", prepend "20" to make "2025"
- Extract full Vietnamese names with proper accents
- For worklog/time queries, use action "get_worklogs"
- Return ONLY the JSON, no explanation."""

                        llm_messages = [
                            {"role": "system", "content": "You are a precise JSON parser. Return only valid JSON."},
                            {"role": "user", "content": parse_prompt}
                        ]
                        
                        parse_response = await call_llm_api(
                            model=llm_model,
                            messages=llm_messages,
                            temperature=0.1,
                            max_tokens=500
                        )
                        
                        # Extract JSON from response
                        json_match = re.search(r'\{.*\}', parse_response, re.DOTALL)
                        if json_match:
                            parsed_params = json.loads(json_match.group(0))
                            
                            # Call Athena with structured parameters
                            agent_endpoint = agent_info["endpoint"]
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                agent_response = await client.post(
                                    f"{agent_endpoint}/task",
                                    json={
                                        "action": parsed_params.get("action", "jira_query"),
                                        "params": {
                                            "date": parsed_params.get("date"),
                                            "employee_name": parsed_params.get("employee_name"),
                                            "project": parsed_params.get("project"),
                                            "query": message.message
                                        },
                                        "llm_model": llm_model
                                    }
                                )
                                if agent_response.status_code == 200:
                                    raw_response = agent_response.json().get("response", "")
                                    
                                    # Zeus processes and enriches Athena's response
                                    if raw_response:
                                        enrich_prompt = f"""You are Zeus, the coordinator. Athena (the Jira specialist) has provided data for the user.

User's original question: "{message.message}"

Athena's raw data:
{raw_response}

Your task:
1. Present Athena's data clearly
2. Add brief helpful context if needed
3. Maintain the data format (tables, lists, emojis, etc.)
4. Be conversational but professional
5. Respond in the same language as the user

Keep it concise - don't over-explain unless the data needs clarification."""

                                        try:
                                            response_text = await call_llm_api(
                                                model=llm_model,
                                                messages=[
                                                    {"role": "system", "content": "You are Zeus, presenting specialist data with helpful context."},
                                                    {"role": "user", "content": enrich_prompt}
                                                ],
                                                temperature=0.7,
                                                max_tokens=2000
                                            )
                                        except Exception as e:
                                            print(f"Response enrichment failed: {e}")
                                            # Fallback to raw response
                                            response_text = raw_response
                                    else:
                                        response_text = raw_response
                        else:
                            # Fallback to old method if parsing fails
                            agent_endpoint = agent_info["endpoint"]
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                agent_response = await client.post(
                                    f"{agent_endpoint}/task",
                                    json={
                                        "action": "jira_query",
                                        "query": message.message,
                                        "llm_model": llm_model
                                    }
                                )
                                if agent_response.status_code == 200:
                                    raw_response = agent_response.json().get("response", "")
                                    
                                    # Zeus enriches the response
                                    if raw_response:
                                        enrich_prompt = f"""You are Zeus. Athena provided this data for: "{message.message}"

Athena's data:
{raw_response}

Present it clearly with brief context. Use the user's language."""

                                        try:
                                            response_text = await call_llm_api(
                                                model=llm_model,
                                                messages=[
                                                    {"role": "system", "content": "You are Zeus, presenting data clearly."},
                                                    {"role": "user", "content": enrich_prompt}
                                                ],
                                                temperature=0.7,
                                                max_tokens=2000
                                            )
                                        except:
                                            response_text = raw_response
                                    else:
                                        response_text = raw_response
                    except Exception as agent_error:
                        print(f"Agent call failed: {agent_error}")
                        # Fall back to LLM
            
            # Fall back to LLM if agent didn't handle it
            if not response_text:
                try:
                    # Use the context_messages loaded at the start
                    llm_messages = [
                        {"role": "system", "content": system_prompt}
                    ] + context_messages + [
                        {"role": "user", "content": message.message}
                    ]
                    
                    response_text = await call_llm_api(
                        model=llm_model,
                        messages=llm_messages,
                        temperature=message.temperature,
                        max_tokens=message.max_tokens
                    )
                except Exception as llm_error:
                    response_text = f"[{selected_agent.capitalize()}] I received your message but couldn't process it with {llm_model}. Error: {str(llm_error)}"
            
            await conn.execute("""
                UPDATE conversations
                SET response = $1, llm_provider = $2, updated_at = $3
                WHERE id = $4
            """, response_text, provider, datetime.utcnow(), conversation_id)
            
            cache_key = f"chat:{session_id}:{selected_agent}"
            await redis_client.setex(
                cache_key,
                86400,
                json.dumps({
                    "message": message.message,
                    "response": response_text,
                    "agent": selected_agent,
                    "llm_model": llm_model,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            capabilities_raw = await conn.fetchval("SELECT capabilities FROM agents WHERE name = $1", selected_agent)
            capabilities = json.loads(capabilities_raw) if capabilities_raw else []
            
            # Store assistant response in Context Storage
            try:
                await context_storage.store_message(
                    session_id=session_id,
                    agent_name=selected_agent,
                    user_id=message.user_id or "anonymous",
                    role="assistant",
                    content=response_text,
                    importance_score=0.9,
                    metadata={
                        "llm_model": llm_model,
                        "llm_provider": provider,
                        "agent_endpoint": agent_info['endpoint'] if agent_info else None
                    }
                )
                print(f"✅ Stored assistant response in context (session: {session_id}, agent: {selected_agent})")
            except Exception as e:
                print(f"⚠️ Failed to store assistant response in context: {e}")
            
            return {
                "session_id": session_id,
                "agent": selected_agent,
                "response": response_text,
                "llm_model": llm_model,
                "llm_provider": provider,
                "metadata": {
                    "agent_endpoint": agent_info['endpoint'],
                    "agent_capabilities": capabilities,
                    "temperature": message.temperature,
                    "max_tokens": message.max_tokens
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/llm/models")
async def get_llm_models():
    """Get all available LLM models with configuration status"""
    models = []
    for model_id, config in LLM_MODELS.items():
        models.append({
            "model": model_id,
            "provider": config["provider"].value,
            "api_key_configured": is_llm_configured(model_id),
            "context_length": config["context_length"],
            "cost_per_1k_input": config["cost"]["input"],
            "cost_per_1k_output": config["cost"]["output"]
        })
    return models

@app.get("/llm/config")
async def get_llm_config():
    """Get LLM provider configuration status"""
    providers = {}
    for provider in LLMProvider:
        api_key = get_llm_api_key(provider)
        providers[provider.value] = {
            "configured": bool(api_key),
            "key_preview": f"{api_key[:10]}..." if api_key else None
        }
    return {"providers": providers}

@app.post("/llm/config")
async def update_llm_config(config: dict):
    """Update LLM API keys"""
    for key, value in config.items():
        if key.endswith("_api_key"):
            provider = key.replace("_api_key", "")
            if provider in [p.value for p in LLMProvider]:
                runtime_api_keys[provider] = value
                os.environ[key.upper()] = value
    
    return {"message": "API keys updated", "providers": list(runtime_api_keys.keys())}

@app.delete("/llm/config/{provider}")
async def delete_llm_config(provider: str):
    """Delete LLM API key"""
    if provider in runtime_api_keys:
        del runtime_api_keys[provider]
    return {"message": f"API key for {provider} removed"}

@app.post("/admin/migrate")
async def run_migration():
    """Run database migrations"""
    # Use POSTGRES_URL if available, otherwise fall back to individual vars
    postgres_url = os.getenv('POSTGRES_URL')
    if postgres_url:
        conn = await asyncpg.connect(postgres_url)
    else:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'zeus_nexus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    try:
        # Check if user_settings table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_settings'
            )
        """)
        
        if table_exists:
            return {"message": "user_settings table already exists", "status": "skipped"}
        
        # Create user_settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) DEFAULT 'default_user',
                llm_provider VARCHAR(50),
                llm_model VARCHAR(100),
                api_keys JSONB DEFAULT '{}',
                last_chat_model VARCHAR(100),
                last_chat_provider VARCHAR(50),
                default_temperature FLOAT DEFAULT 0.7,
                default_max_tokens INTEGER DEFAULT 2000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """)
        
        # Create index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)
        """)
        
        # Insert default settings
        await conn.execute("""
            INSERT INTO user_settings (user_id, llm_provider, llm_model, last_chat_model, last_chat_provider)
            VALUES ('default_user', 'openai', 'gpt-4o', 'gpt-4o', 'openai')
            ON CONFLICT (user_id) DO NOTHING
        """)
        
        # Create trigger function
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_user_settings_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        
        # Create trigger
        await conn.execute("""
            CREATE TRIGGER user_settings_updated_at
            BEFORE UPDATE ON user_settings
            FOR EACH ROW
            EXECUTE FUNCTION update_user_settings_updated_at()
        """)
        
        return {"message": "Migration completed successfully", "status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
    finally:
        await conn.close()

@app.get("/user/settings")
async def get_user_settings(user_id: str = "default_user"):
    """Get user settings from database"""
    postgres_url = os.getenv('POSTGRES_URL')
    if postgres_url:
        conn = await asyncpg.connect(postgres_url)
    else:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'zeus_nexus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    try:
        settings = await conn.fetchrow("""
            SELECT llm_provider, llm_model, api_keys, last_chat_model, 
                   last_chat_provider, default_temperature, default_max_tokens
            FROM user_settings
            WHERE user_id = $1
        """, user_id)
        
        if not settings:
            return {"exists": False, "user_id": user_id}
        
        return {
            "exists": True,
            "user_id": user_id,
            "llm_provider": settings['llm_provider'],
            "llm_model": settings['llm_model'],
            "api_keys": dict(settings['api_keys']) if settings['api_keys'] else {},
            "last_chat_model": settings['last_chat_model'],
            "last_chat_provider": settings['last_chat_provider'],
            "default_temperature": settings['default_temperature'],
            "default_max_tokens": settings['default_max_tokens']
        }
    
    finally:
        await conn.close()

@app.post("/user/settings")
async def save_user_settings(settings: dict, user_id: str = "default_user"):
    """Save user settings to database"""
    postgres_url = os.getenv('POSTGRES_URL')
    if postgres_url:
        conn = await asyncpg.connect(postgres_url)
    else:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'zeus_nexus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    try:
        await conn.execute("""
            INSERT INTO user_settings (
                user_id, llm_provider, llm_model, api_keys, 
                last_chat_model, last_chat_provider,
                default_temperature, default_max_tokens
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id) DO UPDATE SET
                llm_provider = EXCLUDED.llm_provider,
                llm_model = EXCLUDED.llm_model,
                api_keys = EXCLUDED.api_keys,
                last_chat_model = EXCLUDED.last_chat_model,
                last_chat_provider = EXCLUDED.last_chat_provider,
                default_temperature = EXCLUDED.default_temperature,
                default_max_tokens = EXCLUDED.default_max_tokens,
                updated_at = CURRENT_TIMESTAMP
        """, 
            user_id,
            settings.get('llm_provider'),
            settings.get('llm_model'),
            json.dumps(settings.get('api_keys', {})),
            settings.get('last_chat_model'),
            settings.get('last_chat_provider'),
            settings.get('default_temperature', 0.7),
            settings.get('default_max_tokens', 2000)
        )
        
        return {"message": "Settings saved successfully", "user_id": user_id}
    
    finally:
        await conn.close()

@app.get("/conversations")
async def get_conversations(user_id: str = "anonymous", limit: int = 10):
    """Get recent conversation history for a user"""
    postgres_url = os.getenv('POSTGRES_URL')
    if postgres_url:
        conn = await asyncpg.connect(postgres_url)
    else:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'zeus_nexus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    try:
        # Get distinct conversations with latest message
        conversations = await conn.fetch("""
            SELECT DISTINCT ON (session_id)
                session_id,
                user_message,
                response,
                agent_name,
                llm_model,
                created_at,
                SUBSTRING(user_message, 1, 50) as preview
            FROM conversations
            WHERE user_id = $1
            ORDER BY session_id, created_at DESC
            LIMIT $2
        """, user_id, limit)
        
        result = []
        for conv in conversations:
            result.append({
                "session_id": conv['session_id'],
                "preview": conv['preview'] + ("..." if len(conv['user_message']) > 50 else ""),
                "full_message": conv['user_message'],
                "response": conv['response'],
                "agent": conv['agent_name'],
                "model": conv['llm_model'],
                "timestamp": conv['created_at'].isoformat() if conv['created_at'] else None
            })
        
        return {"conversations": result, "count": len(result)}
    
    finally:
        await conn.close()

@app.get("/conversation/{session_id}")
async def get_conversation_detail(session_id: str):
    """Get all messages in a conversation"""
    postgres_url = os.getenv('POSTGRES_URL')
    if postgres_url:
        conn = await asyncpg.connect(postgres_url)
    else:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'zeus_nexus'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
    
    try:
        messages = await conn.fetch("""
            SELECT 
                user_message,
                response,
                agent_name,
                llm_model,
                llm_provider,
                created_at
            FROM conversations
            WHERE session_id = $1
            ORDER BY created_at ASC
        """, session_id)
        
        result = []
        for msg in messages:
            result.append({
                "user_message": msg['user_message'],
                "response": msg['response'],
                "agent": msg['agent_name'],
                "model": msg['llm_model'],
                "provider": msg['llm_provider'],
                "timestamp": msg['created_at'].isoformat() if msg['created_at'] else None
            })
        
        return {"session_id": session_id, "messages": result, "count": len(result)}
    
    finally:
        await conn.close()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
