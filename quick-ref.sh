#!/bin/bash

# Zeus Nexus Quick Reference - Domain: apps.prod01.fis-cloud.fpt.com

cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════╗
║                   Zeus Nexus - Quick Reference                         ║
║                   Namespace: ac-agentic                                ║
║                   Domain: apps.prod01.fis-cloud.fpt.com                ║
╚════════════════════════════════════════════════════════════════════════╝

🌐 MAIN ENDPOINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Zeus Core:    https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com
  MinIO UI:     https://minio-ac-agentic.apps.prod01.fis-cloud.fpt.com
  MinIO API:    https://minio-api-ac-agentic.apps.prod01.fis-cloud.fpt.com
  n8n:          https://n8n-ac-agentic.apps.prod01.fis-cloud.fpt.com

🤖 AI AGENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Athena:       https://athena-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Ares:         https://ares-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Hermes:       https://hermes-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Hephaestus:   https://hephaestus-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Apollo:       https://apollo-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Mnemosyne:    https://mnemosyne-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Clio:         https://clio-ac-agentic.apps.prod01.fis-cloud.fpt.com

🔧 DEPLOYMENT COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Deploy:       cd /root/zeus-nexus && ./deploy.sh deploy
  Verify:       ./deploy.sh verify
  Endpoints:    ./deploy.sh endpoints
  Cleanup:      ./deploy.sh cleanup

🔍 USEFUL COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pods:         oc get pods -n ac-agentic
  Logs:         oc logs -f deployment/zeus-core -n ac-agentic
  Routes:       oc get routes -n ac-agentic
  Services:     oc get svc -n ac-agentic
  Events:       oc get events -n ac-agentic --sort-by='.lastTimestamp'

🧪 QUICK TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Health:       curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/health
  Agents:       curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/agents
  Chat:         curl -X POST https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/chat \
                  -H "Content-Type: application/json" \
                  -d '{"message": "Hello Zeus", "user_id": "test"}'

📊 MONITORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Metrics:      curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/metrics
  Grafana:      https://grafana-ac-agentic.apps.prod01.fis-cloud.fpt.com
  Prometheus:   http://prometheus.ac-agentic.svc.cluster.local:9090

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  README:       /root/zeus-nexus/README.md
  Endpoints:    /root/zeus-nexus/ENDPOINTS.md
  Swagger:      https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/docs

EOF
