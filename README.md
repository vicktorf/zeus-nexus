# ⚡ Zeus Nexus on OpenShift – Deployment Blueprint v1.0

## 🎯 Kiến trúc Zeus Nexus AI Pantheon-as-a-Service

```
                  ┌──────────────────────────────────────────────────────┐
                  │                    OpenShift Cluster                 │
                  │  (Zeus Nexus Project Namespace: ac-agentic)          │
                  └──────────────────────────────────────────────────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
      ⚡ Zeus Core        🧩 n8n Engine       📊 Grafana / PowerBI
     (FastAPI + LLM)     (Workflow Router)    (Dashboard + Alert)
             │
 ┌───────────┼─────────────────────────────┐
 │           │            │                │
 🎯 Athena   ⚙️ Ares   💼 Hermes       ☁️ Hephaestus
 (PM)        (DM)      (AM)             (Cloud Arch)
 │           │            │                │
 💰 Apollo   🧠 Mnemosyne   📄 Clio          └──> Redis / Postgres / MinIO
 (Sales)     (Learning)    (Docs)
```

## 🚀 Quick Start

### Option 1: Direct Deployment
```bash
# Deploy complete Zeus Nexus stack
./deploy.sh deploy
```

### Option 2: GitOps with ArgoCD (Recommended)
```bash
# Setup ArgoCD and deploy via GitOps
./deploy.sh argocd
```

### Manual Steps
1. **Setup OpenShift Project**:
   ```bash
   oc new-project ac-agentic
   oc apply -f config/
   ```

2. **Deploy Infrastructure**:
   ```bash
   oc apply -f manifests/infrastructure/
   ```

3. **Deploy Zeus Core & Agents**:
   ```bash
   oc apply -f manifests/zeus-core/
   oc apply -f manifests/agents/
   ```

4. **Setup GitOps with ArgoCD**:
   ```bash
   oc apply -f argocd/
   ```

## 📁 Repository Structure

```
zeus-nexus/
├── manifests/
│   ├── infrastructure/          # Redis, PostgreSQL, MinIO
│   ├── zeus-core/              # Zeus Core API
│   ├── agents/                 # 7 AI Agents
│   ├── n8n/                   # Workflow engine
│   └── monitoring/             # Grafana, Prometheus
├── config/                     # ConfigMaps, Secrets
├── agents/                     # Agent source code
├── ci-cd/                     # Tekton/Jenkins pipelines
└── docs/                      # Architecture docs
```

## 🔧 Resource Requirements

| Component | CPU | Memory | Storage | Replicas |
|-----------|-----|---------|---------|----------|
| Zeus Core | 2 | 4GB | - | 2 |
| Athena (PM) | 1 | 2GB | - | 1 |
| Ares (DM) | 1 | 2GB | - | 1 |
| Hermes (AM) | 1 | 2GB | - | 1 |
| Hephaestus (Cloud) | 2 | 4GB | - | 1 |
| Apollo (Sales) | 1 | 2GB | - | 1 |
| Mnemosyne (Learning) | 2 | 4GB | 10GB | 1 |
| Clio (Docs) | 1 | 2GB | 5GB | 1 |
| n8n | 1 | 2GB | 5GB | 1 |
| Redis | 0.5 | 512MB | 1GB | 1 |
| PostgreSQL | 1 | 1GB | 10GB | 1 |
| MinIO | 1 | 2GB | 20GB | 1 |

**Total**: ~16 CPU, ~32GB RAM, ~51GB Storage

## 🌐 Endpoints

- **Zeus Core API**: `https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com`
- **n8n Workflow**: `https://n8n-ac-agentic.apps.prod01.fis-cloud.fpt.com`
- **Grafana Dashboard**: `https://grafana-ac-agentic.apps.prod01.fis-cloud.fpt.com`
- **MinIO Console**: `https://minio-ac-agentic.apps.prod01.fis-cloud.fpt.com`

## 🔐 Security

- All inter-service communication via OpenShift Service mesh
- Secrets managed via OpenShift Secrets
- OAuth2 integration with Google Cloud
- RBAC for agent access control

## 📊 Monitoring & SLA

- **Target SLA**: 99.9% uptime
- **Response Time**: < 3s for API calls
- **Error Rate**: < 1%
- **Alerting**: Telegram + Email notifications

## 🚀 Deployment Commands

```bash
# 1. Create namespace
oc new-project ac-agentic

# 2. Apply configurations
oc apply -f config/zeus-config.yaml
oc apply -f config/secrets.yaml

# 3. Deploy infrastructure
oc apply -f manifests/infrastructure/

# 4. Wait for infrastructure ready
oc wait --for=condition=ready pod -l app=redis --timeout=300s
oc wait --for=condition=ready pod -l app=postgresql --timeout=300s

# 5. Deploy Zeus Core
oc apply -f manifests/zeus-core/

# 6. Deploy agents
oc apply -f manifests/agents/

# 7. Deploy n8n
oc apply -f manifests/n8n/

# 8. Setup monitoring
oc apply -f manifests/monitoring/

# 9. Create routes
oc apply -f manifests/routes/
```

## 🔄 CI/CD Pipeline

1. **Build**: Container images via s2i or Dockerfile
2. **Test**: Health checks and integration tests
3. **Deploy**: ArgoCD GitOps sync
4. **Monitor**: Prometheus metrics and Grafana alerts
5. **Notify**: Telegram notifications via n8n

## 🧠 Agent Capabilities

- **Athena (PM)**: Jira, Confluence, project management
- **Ares (DM)**: Grafana, monitoring, incident response
- **Hermes (AM)**: CRM, Notion, communication
- **Hephaestus (Cloud)**: OpenShift, Terraform, infrastructure
- **Apollo (Sales)**: Pipeline analysis, forecasting
- **Mnemosyne (Learning)**: Knowledge base, vector search
- **Clio (Docs)**: Report generation, documentation

## 📈 Scaling Strategy

- **Horizontal**: Scale agents based on workload
- **Vertical**: Increase resources for Zeus Core
- **Multi-cluster**: Federation across regions
- **Edge**: Deploy lightweight agents at edge locations