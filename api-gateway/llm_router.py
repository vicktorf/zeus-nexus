"""
LLM-Enhanced Router for API Gateway
Hybrid approach: Rules-based + LLM fallback
"""
from typing import Optional, Dict, Any
import httpx
import json
from datetime import datetime
import re

class HybridRouter:
    """
    Intelligent router với rules-based (fast) và LLM fallback (accurate)
    """
    
    def __init__(self, llm_enabled: bool = True):
        self.llm_enabled = llm_enabled
        
        # Rules-based routing (FAST - no LLM needed)
        self.static_routes = {
            r'/api/jira/.*': 'tool-service-jira',
            r'/api/github/.*': 'tool-service-github',
            r'/api/grafana/.*': 'tool-service-grafana',
            r'/api/slack/.*': 'tool-service-slack',
        }
        
        # Keyword-based routing (FAST - no LLM needed)
        self.keyword_routes = {
            'tool-service-jira': [
                'jira', 'issue', 'ticket', 'worklog', 'project', 'sprint',
                'task', 'bug', 'story', 'epic', 'làm việc', 'công việc'
            ],
            'tool-service-github': [
                'github', 'repo', 'pull request', 'pr', 'commit', 'branch',
                'code', 'merge', 'deploy', 'ci/cd', 'pipeline'
            ],
            'tool-service-grafana': [
                'grafana', 'metric', 'dashboard', 'alert', 'monitor',
                'cpu', 'memory', 'error rate', 'latency', 'performance'
            ],
            'tool-service-slack': [
                'slack', 'message', 'channel', 'notify', 'send',
                'team', 'chat', 'mention', 'dm'
            ]
        }
    
    async def route(self, request_path: str, query: Optional[str] = None) -> str:
        """
        Main routing logic:
        1. Try static routes (regex match) - INSTANT
        2. Try keyword matching - VERY FAST
        3. Fallback to LLM routing - ACCURATE but slower
        """
        
        # 1. Static route matching (regex)
        for pattern, service in self.static_routes.items():
            if re.match(pattern, request_path):
                return service
        
        # 2. Keyword-based routing (if query provided)
        if query:
            service = self._keyword_match(query)
            if service:
                return service
        
        # 3. LLM routing (fallback for complex queries)
        if self.llm_enabled and query:
            return await self._llm_route(query)
        
        # Default: zeus-core for orchestration
        return 'zeus-core'
    
    def _keyword_match(self, query: str) -> Optional[str]:
        """
        Fast keyword matching - no LLM call
        Returns service name or None
        """
        query_lower = query.lower()
        
        # Count keyword matches for each service
        scores = {}
        for service, keywords in self.keyword_routes.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[service] = score
        
        # Return service with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    async def _llm_route(self, query: str) -> str:
        """
        LLM-based routing for complex queries
        Uses GPT-3.5-turbo for speed/cost balance
        """
        
        routing_prompt = f"""You are a routing assistant for Zeus Nexus platform.

User Query: "{query}"

Available Services:
1. tool-service-jira - Jira issues, worklogs, project management, time tracking
2. tool-service-github - GitHub repositories, pull requests, code, CI/CD
3. tool-service-grafana - Monitoring, metrics, alerts, dashboards, performance
4. tool-service-slack - Team communication, notifications, messages
5. zeus-core - General AI queries, multi-service orchestration, complex tasks

Rules:
- If query needs ONLY ONE service → return that service name
- If query needs MULTIPLE services → return "zeus-core" for orchestration
- If unclear → return "zeus-core"

Return ONLY the service name, nothing else."""

        try:
            # Call LLM (use lightweight model)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://zeus-core.ac-agentic.svc.cluster.local:8000/llm/classify",
                    json={
                        "prompt": routing_prompt,
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.1,
                        "max_tokens": 30
                    },
                    timeout=3.0  # Fast timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    service = result.get("response", "").strip().lower()
                    
                    # Validate service name
                    valid_services = [
                        'tool-service-jira', 'tool-service-github',
                        'tool-service-grafana', 'tool-service-slack',
                        'zeus-core'
                    ]
                    
                    if service in valid_services:
                        return service
        
        except Exception as e:
            print(f"LLM routing failed: {e}, falling back to zeus-core")
        
        # Fallback
        return 'zeus-core'
    
    async def enrich_request(self, query: str) -> Dict[str, Any]:
        """
        LLM extracts structured parameters from natural language
        
        Example:
        Input: "Get John's worklog for 22/11/2025"
        Output: {
            "intent": "get_worklog",
            "entity": "John",
            "date": "2025-11-22",
            "action": "get"
        }
        """
        
        if not self.llm_enabled:
            return {}
        
        extraction_prompt = f"""Extract structured data from this query.

Query: "{query}"

Return ONLY valid JSON (no markdown, no explanation):
{{
    "intent": "worklog|issue|deployment|alert|general",
    "entity": "person_name or project_name or null",
    "date": "YYYY-MM-DD or null",
    "action": "get|create|update|delete",
    "urgency": "low|medium|high",
    "filters": {{}}
}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://zeus-core.ac-agentic.svc.cluster.local:8000/llm/extract",
                    json={
                        "prompt": extraction_prompt,
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.1,
                        "max_tokens": 150
                    },
                    timeout=2.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    extracted = json.loads(result.get("response", "{}"))
                    return extracted
        
        except Exception as e:
            print(f"Parameter extraction failed: {e}")
        
        return {}


class LLMSecurityValidator:
    """
    LLM-based security validation
    """
    
    @staticmethod
    async def is_safe(request_body: str) -> tuple[bool, str]:
        """
        Check if request contains malicious patterns
        Returns: (is_safe, reason)
        """
        
        # Quick regex checks first (no LLM needed)
        dangerous_patterns = [
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'<script',
            r'javascript:',
            r'eval\(',
            r'exec\(',
            r'\$\(.*\)',  # jQuery injection
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, request_body, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # LLM check for sophisticated attacks
        security_prompt = f"""Analyze this API request for security threats:

Request Body: {request_body[:500]}  # Limit size

Check for:
- SQL/NoSQL injection
- Command injection
- XSS attempts
- Sensitive data leaks (API keys, passwords)
- Unusual patterns

Return JSON: {{"safe": true/false, "threat_type": "none|injection|xss|data_leak|suspicious"}}"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://zeus-core.ac-agentic.svc.cluster.local:8000/llm/classify",
                    json={
                        "prompt": security_prompt,
                        "model": "gpt-4o-mini",  # Better at security analysis
                        "temperature": 0.0,
                        "max_tokens": 50
                    },
                    timeout=2.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = json.loads(result.get("response", "{}"))
                    
                    is_safe = analysis.get("safe", True)
                    threat = analysis.get("threat_type", "unknown")
                    
                    return is_safe, f"LLM detected: {threat}"
        
        except Exception as e:
            print(f"LLM security check failed: {e}")
            # Fail open (allow request) if LLM unavailable
            return True, "LLM check failed, allowing"
        
        return True, "No threats detected"


# Usage Example
if __name__ == "__main__":
    import asyncio
    
    async def test_router():
        router = HybridRouter(llm_enabled=True)
        
        # Test cases
        queries = [
            ("Get John's worklog for 22/11", "tool-service-jira"),
            ("Show me CPU metrics from last hour", "tool-service-grafana"),
            ("Create PR for feature-auth", "tool-service-github"),
            ("Send message to #dev channel", "tool-service-slack"),
            ("What is the weather today?", "zeus-core"),  # LLM will handle
        ]
        
        for query, expected in queries:
            service = await router.route("/api/smart-route", query)
            print(f"Query: {query}")
            print(f"Routed to: {service} (expected: {expected})")
            print(f"Match: {'✅' if service == expected else '❌'}\n")
    
    asyncio.run(test_router())
