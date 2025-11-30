# Zeus Nexus Enhanced Architecture - Deployment Documentation

## 🏗️ Kiến Trúc Layered Zeus Nexus v2.0

Đây là tài liệu triển khai cho kiến trúc Zeus Nexus mới được thiết kế theo mô hình 5 lớp:

### 📋 Tổng Quan Kiến Trúc

```
Layer 1: Orchestrator (ZEUS Master Agent)
    ↓
Layer 2: Satellite Agents (FastAPI)
    ↓  
Layer 3: ToolHub Services
    ↓
Layer 4: LLM Pool
    ↓
Layer 5: Memory & Storage
```

### 🚀 Triển Khai Nhanh

1. **Chuẩn bị môi trường:**
   ```bash
   oc new-project ac-agentic
   oc apply -f config/secrets.yaml
   ```

2. **Triển khai Memory & Storage Layer:**
   ```bash
   oc apply -f manifests/infrastructure/memory-storage-enhanced.yaml
   oc apply -f manifests/infrastructure/postgresql.yaml
   oc apply -f manifests/infrastructure/minio.yaml
   ```

3. **Triển khai Zeus Enhanced:**
   ```bash
   oc apply -f manifests/zeus-enhanced/builds.yaml
   oc apply -f manifests/zeus-enhanced/deployments.yaml
   oc apply -f manifests/zeus-enhanced/routes.yaml
   ```

4. **Kiểm tra trạng thái:**
   ```bash
   oc get pods -n ac-agentic
   oc get routes -n ac-agentic
   ```

### 🎯 Thành Phần Chính

#### Layer 1: Zeus Master Agent (Orchestrator)
- **Endpoint:** `https://zeus-nexus.apps.your-cluster.com`
- **Chức năng:** Điều phối và routing requests đến các satellite agents
- **Features:**
  - Intent analysis và reasoning engine
  - Load balancing giữa agents
  - Task execution monitoring
  - Centralized logging và metrics

#### Layer 2: Satellite Agents
- **Athena (PM/Jira):** `https://athena.zeus-nexus.apps.your-cluster.com`
- **Hephaestus (Cloud Arch):** `https://hephaestus.zeus-nexus.apps.your-cluster.com`
- **Apollo (Consultant):** `https://apollo.zeus-nexus.apps.your-cluster.com`
- **Hermes (Sales):** *Coming soon*
- **Vulcan (Platform Eng):** *Coming soon*
- **Ares (Security):** *Coming soon*

#### Layer 3: ToolHub Services
- **Jira Service:** Integration với Jira API
- **OpenShift Service:** Kubernetes/OpenShift management
- **Confluence Service:** *Coming soon*
- **Grafana Service:** *Coming soon*
- **Terraform Service:** *Coming soon*
- **OWASP Service:** *Coming soon*

#### Layer 4: LLM Pool
- **Endpoint:** `https://llm-pool.zeus-nexus.apps.your-cluster.com`
- **Supported Models:**
  - OpenAI: GPT-4, GPT-4-Turbo, GPT-3.5-Turbo
  - Anthropic: Claude-3 Opus, Sonnet, Haiku
  - Local: Llama2, CodeLlama, Mistral (via Ollama)
- **Features:**
  - Intelligent routing based on request type
  - Cost optimization và load balancing
  - Rate limiting và caching

#### Layer 5: Memory & Storage
- **Redis:** Caching, session management, task queues
- **PostgreSQL:** Persistent data storage
- **VectorDB (Qdrant):** Embeddings và context storage
- **MinIO:** Object storage cho files và artifacts

### 🔧 Configuration

#### Environment Variables
```yaml
# Zeus Master Agent
REDIS_HOST: redis.ac-agentic.svc.cluster.local
POSTGRES_HOST: postgresql.ac-agentic.svc.cluster.local
LOG_LEVEL: INFO

# LLM Pool
OPENAI_API_KEY: <your-openai-key>
ANTHROPIC_API_KEY: <your-anthropic-key>
LOCAL_LLM_ENDPOINT: http://ollama.ac-agentic.svc.cluster.local:11434

# Jira Service
JIRA_SERVER: https://your-company.atlassian.net
JIRA_EMAIL: <your-email>
JIRA_API_TOKEN: <your-token>
```

#### Secrets Configuration
```bash
oc create secret generic zeus-secrets \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=anthropic-api-key="sk-ant-..." \
  --from-literal=jira-server="https://company.atlassian.net" \
  --from-literal=jira-email="user@company.com" \
  --from-literal=jira-api-token="ATATT..." \
  --from-literal=postgres-password="zeus_secure_password"
```

### 📊 Monitoring & Health Checks

#### Health Endpoints
- Zeus Master: `/health`
- All Agents: `/health` 
- LLM Pool: `/health`
- ToolHub Services: `/health`

#### Key Metrics
- Request latency per layer
- LLM token usage và cost
- Agent availability và load
- Database connection pool status

### 🔒 Security Features

- **Network Policies:** Micro-segmentation giữa các layers
- **RBAC:** Service accounts với least-privilege access
- **TLS Termination:** All routes secured với SSL/TLS
- **Secret Management:** Centralized secret storage
- **API Rate Limiting:** Protection against abuse

### 🎛️ API Usage Examples

#### 1. General Query qua Zeus Master
```bash
curl -X POST https://zeus-nexus.apps.your-cluster.com/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "query": "Create a Jira ticket for implementing microservices architecture",
    "priority": "high"
  }'
```

#### 2. Direct Agent Call
```bash
curl -X POST https://athena.zeus-nexus.apps.your-cluster.com/process \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-123",
    "query": "List all open issues in PROJECT-KEY",
    "context": {"project": "PROJECT-KEY"}
  }'
```

#### 3. LLM Pool Usage
```bash
curl -X POST https://llm-pool.zeus-nexus.apps.your-cluster.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain microservices architecture benefits",
    "model": "gpt-4",
    "max_tokens": 500
  }'
```

### 🔄 Data Flow

1. **User Request** → Zeus Master Agent
2. **Intent Analysis** → Route to appropriate Satellite Agent(s)
3. **Agent Processing** → Call ToolHub Services + LLM Pool
4. **Tool Integration** → Execute via specialized services
5. **LLM Reasoning** → Generate intelligent responses
6. **Context Storage** → Save to Memory & Storage Layer
7. **Response Synthesis** → Return unified result to user

### 📈 Scaling Strategy

- **Horizontal Scaling:** Increase replicas for high-demand agents
- **LLM Pool:** Intelligent routing giảm cost, tăng performance
- **Database Sharding:** Scale PostgreSQL khi needed
- **Cache Strategy:** Redis cho frequently accessed data
- **CDN Integration:** MinIO với external CDN cho static assets

### 🚨 Troubleshooting

#### Common Issues
1. **Agent không healthy:** Check dependencies (Redis, PostgreSQL)
2. **LLM Pool timeout:** Verify external API keys và network
3. **Jira integration failed:** Validate credentials và permissions
4. **High latency:** Check resource limits và scaling

#### Debug Commands
```bash
# Check pod logs
oc logs -f deployment/zeus-master -n ac-agentic

# Check network connectivity
oc exec -it pod/zeus-master-xxx -- curl http://redis:6379

# Monitor resource usage
oc top pods -n ac-agentic
```

### 📞 Support

- **Documentation:** `/docs` endpoint trên mỗi service
- **Health Dashboard:** Grafana integration (coming soon)
- **Alerts:** Prometheus + AlertManager setup
- **Logs:** Centralized logging với ELK stack

---

## ⚡ Kết Luận

Kiến trúc Zeus Nexus Enhanced cung cấp:
- **Scalability:** Horizontal scaling cho từng layer
- **Modularity:** Independent deployment và updates
- **Intelligence:** Multi-LLM routing với cost optimization
- **Security:** Network segmentation và access control
- **Observability:** Comprehensive monitoring và logging

Kiến trúc này được thiết kế để hỗ trợ enterprise-grade agentic platform với high availability, performance, và security.