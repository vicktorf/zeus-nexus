# Zeus Nexus ArgoCD GitOps Deployment

This directory contains ArgoCD configurations for deploying Zeus Nexus using GitOps methodology.

## Overview

Zeus Nexus uses ArgoCD for GitOps-based deployment with the following structure:

- **zeus-nexus-project.yaml**: ArgoCD project definition with RBAC and policies
- **zeus-nexus-application.yaml**: Main applications for infrastructure and core services  
- **zeus-agents-applicationset.yaml**: ApplicationSet for managing AI agents dynamically

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │────│   ArgoCD Apps    │────│  OpenShift      │
│                 │    │                  │    │                 │
│ vicktorf/       │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ zeus-nexus      │────│ │Infrastructure│ │────│ │Redis/Postgres│ │
│                 │    │ └──────────────┘ │    │ │MinIO        │ │
│ ├── manifests/  │    │ ┌──────────────┐ │    │ └─────────────┘ │
│ ├── argocd/     │────│ │  Zeus Core   │ │────│ ┌─────────────┐ │
│ └── agents/     │    │ └──────────────┘ │    │ │Zeus API     │ │
│                 │    │ ┌──────────────┐ │    │ │Web Interface│ │
└─────────────────┘    │ │ Agent Set    │ │────│ │Agents       │ │
                       │ └──────────────┘ │    │ └─────────────┘ │
                       └──────────────────┘    └─────────────────┘
```

## Deployment Strategy

### Sync Waves
Applications are deployed in order using sync waves:

1. **Wave 0**: Infrastructure (Redis, PostgreSQL, MinIO)
2. **Wave 1**: Zeus Core (API Gateway, LLM Pool, Web Interface)  
3. **Wave 2**: AI Agents (Athena, Apollo, Hephaestus)

### Automated Policies
- **Auto-sync**: Enabled for all applications
- **Self-heal**: Automatic recovery from configuration drift
- **Pruning**: Removes orphaned resources
- **Retry**: Automatic retry on sync failures

## Quick Start

1. **Setup ArgoCD and deploy Zeus Nexus:**
   ```bash
   ./deploy.sh argocd
   ```

2. **Access ArgoCD UI:**
   - Get URL: `oc get route argocd-server -n argocd`
   - Get password: `oc get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d`

3. **Monitor deployment:**
   - Login to ArgoCD with admin/password
   - View applications: zeus-infrastructure, zeus-nexus, zeus-agent-*

## Manual Operations

### Sync Applications
```bash
# Sync infrastructure first
argocd app sync zeus-infrastructure

# Sync main application
argocd app sync zeus-nexus

# Sync all agents
argocd app sync zeus-agent-athena
```

### Check Application Status
```bash
argocd app list
argocd app get zeus-nexus
argocd app logs zeus-nexus
```

### Force Refresh
```bash
argocd app refresh zeus-nexus --hard
```

## Project Structure

### zeus-nexus-project.yaml
- Defines project scope and RBAC
- Whitelists allowed resources  
- Sets up sync windows and policies
- Configures roles (admin, developer)

### Applications
- **zeus-infrastructure**: Database, cache, storage services
- **zeus-nexus**: Core API, web interface, networking
- **zeus-agents**: AI agents using ApplicationSet

### Security
- Namespace isolation (ac-agentic)
- RBAC with project-scoped permissions
- Resource whitelisting
- Sync window controls

## Troubleshooting

### Application Won't Sync
1. Check project permissions: `argocd proj get zeus-nexus-project`
2. Verify source repo access: `argocd repo get https://github.com/vicktorf/zeus-nexus.git`
3. Review application events: `argocd app get zeus-nexus`

### Resource Pruning Issues
1. Check ignore differences in application spec
2. Review finalizers on stuck resources
3. Use `--prune=false` if needed

### Build Failures
1. Check BuildConfig in OpenShift console
2. Verify GitHub repository access
3. Review build logs: `oc logs build/zeus-core-1 -n ac-agentic`

## Integration with Zeus Nexus

ArgoCD integrates with Zeus Nexus through:

1. **Source Control**: GitHub repository monitoring
2. **Container Registry**: OpenShift internal registry  
3. **Configuration**: Kubernetes ConfigMaps/Secrets
4. **Monitoring**: ArgoCD application health status
5. **Rollback**: Git-based rollback capabilities

## Best Practices

1. **Git Workflow**: Use feature branches for changes
2. **Testing**: Validate manifests before merge
3. **Rollback**: Keep git history clean for easy rollback
4. **Monitoring**: Watch ArgoCD notifications
5. **Security**: Regular review of RBAC policies

## Support

- **ArgoCD Docs**: https://argo-cd.readthedocs.io/
- **Zeus Nexus**: See main README.md
- **OpenShift**: Internal documentation