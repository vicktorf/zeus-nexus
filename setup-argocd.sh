#!/bin/bash

# Zeus Nexus ArgoCD Setup Script
# This script sets up ArgoCD for Zeus Nexus deployment

set -e

NAMESPACE="argocd"
ZEUS_NAMESPACE="ac-agentic"
ARGO_VERSION="v2.9.3"

echo "🚀 Setting up ArgoCD for Zeus Nexus..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists oc; then
    echo "❌ OpenShift CLI (oc) is required but not installed."
    exit 1
fi

if ! command_exists kubectl; then
    echo "❌ kubectl is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create ArgoCD namespace if it doesn't exist
echo "📦 Creating ArgoCD namespace..."
oc new-project $NAMESPACE 2>/dev/null || oc project $NAMESPACE

# Install ArgoCD
echo "🔧 Installing ArgoCD..."
if ! oc get deployment argocd-server -n $NAMESPACE >/dev/null 2>&1; then
    echo "Installing ArgoCD $ARGO_VERSION..."
    oc apply -n $NAMESPACE -f https://raw.githubusercontent.com/argoproj/argo-cd/$ARGO_VERSION/manifests/install.yaml
    
    echo "⏳ Waiting for ArgoCD to be ready..."
    oc wait --for=condition=Available --timeout=300s deployment/argocd-server -n $NAMESPACE
    oc wait --for=condition=Available --timeout=300s deployment/argocd-application-controller -n $NAMESPACE
    oc wait --for=condition=Available --timeout=300s deployment/argocd-repo-server -n $NAMESPACE
    
    echo "✅ ArgoCD installed successfully"
else
    echo "✅ ArgoCD is already installed"
fi

# Create route for ArgoCD server
echo "🌐 Creating ArgoCD server route..."
cat <<EOF | oc apply -f -
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: argocd-server
  namespace: $NAMESPACE
  labels:
    app.kubernetes.io/component: server
    app.kubernetes.io/name: argocd-server
spec:
  port:
    targetPort: https
  tls:
    termination: passthrough
  to:
    kind: Service
    name: argocd-server
EOF

# Get ArgoCD server URL
ARGOCD_URL=$(oc get route argocd-server -n $NAMESPACE -o jsonpath='{.spec.host}')
echo "🔗 ArgoCD Server URL: https://$ARGOCD_URL"

# Get admin password
echo "🔑 Getting ArgoCD admin password..."
ADMIN_PASSWORD=$(oc get secret argocd-initial-admin-secret -n $NAMESPACE -o jsonpath='{.data.password}' | base64 -d)
echo "👤 Admin username: admin"
echo "🔐 Admin password: $ADMIN_PASSWORD"

# Apply Zeus Nexus ArgoCD configurations
echo "⚙️ Applying Zeus Nexus ArgoCD configurations..."

# Apply project first
oc apply -f argocd/zeus-nexus-project.yaml

# Wait a moment for project to be created
sleep 5

# Apply applications
oc apply -f argocd/zeus-nexus-application.yaml
oc apply -f argocd/zeus-agents-applicationset.yaml

echo "✅ Zeus Nexus ArgoCD setup completed!"
echo ""
echo "📋 Summary:"
echo "  - ArgoCD Server: https://$ARGOCD_URL"
echo "  - Username: admin"
echo "  - Password: $ADMIN_PASSWORD"
echo "  - Project: zeus-nexus-project"
echo "  - Applications: zeus-nexus, zeus-infrastructure, zeus-agents"
echo ""
echo "🎯 Next steps:"
echo "  1. Login to ArgoCD UI with the credentials above"
echo "  2. Verify applications are syncing properly"
echo "  3. Monitor deployment status in ArgoCD dashboard"
echo "  4. Access Zeus Nexus at: https://zeus-dashboard-ac-agentic.apps.your-cluster.com"
echo ""
echo "🔧 To sync applications manually:"
echo "  argocd app sync zeus-infrastructure"
echo "  argocd app sync zeus-nexus"