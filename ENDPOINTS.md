# Zeus Nexus Endpoints - OpenShift Routes

## 🌐 Base Domain
`apps.prod01.fis-cloud.fpt.com`

## ⚡ Zeus Core Services

| Service | URL | Purpose |
|---------|-----|---------|
| Zeus Core API | https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com | Main API & Chat Interface |
| MinIO Console | https://minio-ac-agentic.apps.prod01.fis-cloud.fpt.com | Object Storage UI |
| MinIO API | https://minio-api-ac-agentic.apps.prod01.fis-cloud.fpt.com | S3-compatible API |
| n8n Workflow | https://n8n-ac-agentic.apps.prod01.fis-cloud.fpt.com | Workflow Automation |
| Grafana | https://grafana-ac-agentic.apps.prod01.fis-cloud.fpt.com | Monitoring Dashboard |

## 🤖 AI Agents

| Agent | URL | Capability |
|-------|-----|------------|
| **Athena** (PM) | https://athena-ac-agentic.apps.prod01.fis-cloud.fpt.com | Project Management, Jira, Confluence |
| **Ares** (DM) | https://ares-ac-agentic.apps.prod01.fis-cloud.fpt.com | DevOps, Monitoring, Grafana |
| **Hermes** (AM) | https://hermes-ac-agentic.apps.prod01.fis-cloud.fpt.com | Account Management, CRM, Notion |
| **Hephaestus** (Cloud) | https://hephaestus-ac-agentic.apps.prod01.fis-cloud.fpt.com | Cloud Architecture, Terraform, OpenShift |
| **Apollo** (Sales) | https://apollo-ac-agentic.apps.prod01.fis-cloud.fpt.com | Sales Analytics, Pipeline, Forecasting |
| **Mnemosyne** (Learning) | https://mnemosyne-ac-agentic.apps.prod01.fis-cloud.fpt.com | Knowledge Base, Vector Search, RAG |
| **Clio** (Docs) | https://clio-ac-agentic.apps.prod01.fis-cloud.fpt.com | Documentation, Reports, PDF Generation |

## 🔍 Health Check Endpoints

```bash
# Zeus Core
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/health

# Athena Agent
curl https://athena-ac-agentic.apps.prod01.fis-cloud.fpt.com/health

# Ares Agent
curl https://ares-ac-agentic.apps.prod01.fis-cloud.fpt.com/health

# All agents follow same pattern
curl https://{agent-name}-ac-agentic.apps.prod01.fis-cloud.fpt.com/health
```

## 📊 Metrics Endpoints

```bash
# Zeus Core Metrics
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/metrics

# Agent Metrics
curl https://{agent-name}-ac-agentic.apps.prod01.fis-cloud.fpt.com/metrics
```

## 🔐 OAuth2 Callback URLs

For Google OAuth integration (n8n, agents):
```
https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/auth/callback
https://n8n-ac-agentic.apps.prod01.fis-cloud.fpt.com/rest/oauth2-credential/callback
```

## 📝 API Documentation

- Swagger UI: `https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/docs`
- ReDoc: `https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/redoc`
- OpenAPI JSON: `https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/openapi.json`

## 🚀 Quick Test Commands

```bash
# Test Zeus Core
curl -X POST https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Zeus", "user_id": "test"}'

# List all agents
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/agents

# Test MinIO Console
open https://minio-ac-agentic.apps.prod01.fis-cloud.fpt.com
```

## 🔧 Internal Service URLs (within cluster)

| Service | Internal URL | Port |
|---------|--------------|------|
| Zeus Core | zeus-core.ac-agentic.svc.cluster.local | 8000 |
| Redis | redis.ac-agentic.svc.cluster.local | 6379 |
| PostgreSQL | postgresql.ac-agentic.svc.cluster.local | 5432 |
| MinIO | minio.ac-agentic.svc.cluster.local | 9000 |
| n8n | n8n.ac-agentic.svc.cluster.local | 5678 |
| Athena | athena.ac-agentic.svc.cluster.local | 8001 |
| Ares | ares.ac-agentic.svc.cluster.local | 8002 |
| Hermes | hermes.ac-agentic.svc.cluster.local | 8003 |
| Hephaestus | hephaestus.ac-agentic.svc.cluster.local | 8004 |
| Apollo | apollo.ac-agentic.svc.cluster.local | 8005 |
| Mnemosyne | mnemosyne.ac-agentic.svc.cluster.local | 8006 |
| Clio | clio.ac-agentic.svc.cluster.local | 8007 |