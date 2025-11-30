#!/bin/bash

# Zeus Nexus Enhanced Deployment Script
# Automated deployment for the layered architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="ac-agentic"
CLUSTER_DOMAIN="apps.your-cluster.com"
GIT_REPO="https://github.com/your-org/zeus-nexus.git"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if oc is installed
    if ! command -v oc &> /dev/null; then
        log_error "OpenShift CLI (oc) is not installed"
        exit 1
    fi
    
    # Check if logged into OpenShift
    if ! oc whoami &> /dev/null; then
        log_error "Not logged into OpenShift cluster"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! oc cluster-info &> /dev/null; then
        log_error "Cannot connect to OpenShift cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if oc get namespace $NAMESPACE &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        oc new-project $NAMESPACE
        log_success "Namespace $NAMESPACE created"
    fi
}

setup_secrets() {
    log_info "Setting up secrets..."
    
    # Check if secrets already exist
    if oc get secret zeus-secrets -n $NAMESPACE &> /dev/null; then
        log_warning "Secrets already exist. Skipping creation."
        return
    fi
    
    # Prompt for secret values
    echo "Please provide the following configuration values:"
    
    read -s -p "OpenAI API Key (optional): " OPENAI_KEY
    echo
    read -s -p "Anthropic API Key (optional): " ANTHROPIC_KEY
    echo
    read -p "Jira Server URL (optional): " JIRA_SERVER
    read -p "Jira Email (optional): " JIRA_EMAIL
    read -s -p "Jira API Token (optional): " JIRA_TOKEN
    echo
    read -s -p "PostgreSQL Password: " POSTGRES_PASSWORD
    echo
    
    # Create secrets
    oc create secret generic zeus-secrets \
        --from-literal=openai-api-key="${OPENAI_KEY:-dummy}" \
        --from-literal=anthropic-api-key="${ANTHROPIC_KEY:-dummy}" \
        --from-literal=jira-server="${JIRA_SERVER:-https://company.atlassian.net}" \
        --from-literal=jira-email="${JIRA_EMAIL:-user@company.com}" \
        --from-literal=jira-api-token="${JIRA_TOKEN:-dummy}" \
        --from-literal=postgres-password="${POSTGRES_PASSWORD}" \
        --from-literal=POSTGRES_DB="zeus_nexus" \
        --from-literal=POSTGRES_USER="zeus_user" \
        --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
        -n $NAMESPACE
    
    log_success "Secrets created successfully"
}

deploy_infrastructure() {
    log_info "Deploying Layer 5: Memory & Storage infrastructure..."
    
    # Deploy PostgreSQL
    oc apply -f manifests/infrastructure/postgresql.yaml -n $NAMESPACE
    
    # Deploy enhanced memory & storage
    oc apply -f manifests/infrastructure/memory-storage-enhanced.yaml -n $NAMESPACE
    
    # Deploy MinIO
    oc apply -f manifests/infrastructure/minio.yaml -n $NAMESPACE
    
    log_success "Infrastructure deployment initiated"
}

wait_for_infrastructure() {
    log_info "Waiting for infrastructure to be ready..."
    
    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL..."
    oc rollout status deployment/postgresql -n $NAMESPACE --timeout=300s
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    oc rollout status deployment/redis -n $NAMESPACE --timeout=300s
    
    # Wait for VectorDB
    log_info "Waiting for VectorDB..."
    oc rollout status deployment/vectordb -n $NAMESPACE --timeout=300s
    
    log_success "Infrastructure is ready"
}

deploy_builds() {
    log_info "Setting up build configurations..."
    
    # Update Git repository in build configs
    sed -i "s|https://github.com/your-org/zeus-nexus.git|$GIT_REPO|g" manifests/zeus-enhanced/builds.yaml
    
    # Apply build configurations
    oc apply -f manifests/zeus-enhanced/builds.yaml -n $NAMESPACE
    
    log_success "Build configurations created"
}

trigger_builds() {
    log_info "Triggering initial builds..."
    
    builds=("zeus-master-build" "athena-build" "hephaestus-build" "apollo-build" "llm-pool-build" "jira-service-build" "openshift-service-build")
    
    for build in "${builds[@]}"; do
        log_info "Starting build: $build"
        oc start-build $build -n $NAMESPACE --follow=false
    done
    
    log_info "All builds triggered. Waiting for completion..."
    
    # Wait for builds to complete
    for build in "${builds[@]}"; do
        log_info "Waiting for build: $build"
        oc wait --for=condition=Complete build --selector=buildconfig=$build -n $NAMESPACE --timeout=900s
    done
    
    log_success "All builds completed successfully"
}

deploy_applications() {
    log_info "Deploying Zeus Nexus applications..."
    
    # Update cluster domain in routes
    sed -i "s|apps.your-cluster.com|$CLUSTER_DOMAIN|g" manifests/zeus-enhanced/routes.yaml
    
    # Deploy applications
    oc apply -f manifests/zeus-enhanced/deployments.yaml -n $NAMESPACE
    
    # Deploy routes and network policies
    oc apply -f manifests/zeus-enhanced/routes.yaml -n $NAMESPACE
    
    log_success "Applications deployment initiated"
}

wait_for_applications() {
    log_info "Waiting for applications to be ready..."
    
    deployments=("zeus-master" "athena" "hephaestus" "apollo" "llm-pool" "jira-service" "openshift-service")
    
    for deployment in "${deployments[@]}"; do
        log_info "Waiting for deployment: $deployment"
        oc rollout status deployment/$deployment -n $NAMESPACE --timeout=300s
    done
    
    log_success "All applications are ready"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    log_info "Pod status:"
    oc get pods -n $NAMESPACE
    
    # Check routes
    log_info "Routes:"
    oc get routes -n $NAMESPACE
    
    # Test health endpoints
    log_info "Testing health endpoints..."
    
    ZEUS_URL=$(oc get route zeus-api-gateway -n $NAMESPACE -o jsonpath='{.spec.host}')
    if [ ! -z "$ZEUS_URL" ]; then
        if curl -s -k "https://$ZEUS_URL/health" > /dev/null; then
            log_success "Zeus Master Agent is healthy"
        else
            log_warning "Zeus Master Agent health check failed"
        fi
    fi
    
    log_success "Deployment verification completed"
}

display_endpoints() {
    echo -e "\n${GREEN}=== Zeus Nexus Enhanced Deployment Complete ===${NC}\n"
    
    echo "🎯 Main Endpoints:"
    echo "├── Zeus Master Agent: https://$(oc get route zeus-api-gateway -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'zeus-nexus.'$CLUSTER_DOMAIN)"
    echo "├── Athena Agent: https://$(oc get route athena-agent -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'athena.zeus-nexus.'$CLUSTER_DOMAIN)"
    echo "├── Hephaestus Agent: https://$(oc get route hephaestus-agent -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'hephaestus.zeus-nexus.'$CLUSTER_DOMAIN)"
    echo "├── Apollo Agent: https://$(oc get route apollo-agent -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'apollo.zeus-nexus.'$CLUSTER_DOMAIN)"
    echo "└── LLM Pool: https://$(oc get route llm-pool -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'llm-pool.zeus-nexus.'$CLUSTER_DOMAIN)"
    
    echo -e "\n📊 Management Commands:"
    echo "├── Check status: oc get pods -n $NAMESPACE"
    echo "├── View logs: oc logs -f deployment/zeus-master -n $NAMESPACE"
    echo "└── Scale up: oc scale deployment/zeus-master --replicas=3 -n $NAMESPACE"
    
    echo -e "\n🔧 Next Steps:"
    echo "1. Configure external integrations (Jira, LLM APIs)"
    echo "2. Test API endpoints using the examples in ARCHITECTURE_ENHANCED.md"
    echo "3. Set up monitoring and alerting"
    echo "4. Configure backup strategies"
    
    echo -e "\n📖 Documentation: ARCHITECTURE_ENHANCED.md"
}

cleanup() {
    if [ "$1" == "--cleanup" ]; then
        log_warning "Cleaning up Zeus Nexus deployment..."
        oc delete project $NAMESPACE
        log_success "Cleanup completed"
        exit 0
    fi
}

# Main execution
main() {
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Zeus Nexus Enhanced Deployment        ║${NC}"
    echo -e "${BLUE}║               v2.0 - Layered Architecture    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}\n"
    
    # Handle cleanup option
    cleanup $1
    
    # Main deployment flow
    check_prerequisites
    create_namespace
    setup_secrets
    deploy_infrastructure
    wait_for_infrastructure
    deploy_builds
    
    # Ask if user wants to trigger builds now or later
    read -p "Trigger builds now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        trigger_builds
    else
        log_info "Builds not triggered. You can start them manually later with: oc start-build <buildconfig-name>"
    fi
    
    deploy_applications
    wait_for_applications
    verify_deployment
    display_endpoints
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Zeus Nexus Enhanced Deployment Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --cleanup      Remove Zeus Nexus deployment"
        echo ""
        echo "Environment Variables:"
        echo "  NAMESPACE      Target namespace (default: ac-agentic)"
        echo "  CLUSTER_DOMAIN Cluster domain (default: apps.your-cluster.com)"
        echo "  GIT_REPO       Git repository URL"
        exit 0
        ;;
    --cleanup)
        cleanup --cleanup
        ;;
    *)
        main $1
        ;;
esac