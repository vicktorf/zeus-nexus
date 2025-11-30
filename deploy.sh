#!/bin/bash

set -e

echo "🚀 Zeus Nexus Deployment Script v1.0"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="ac-agentic"
PROJECT_DIR="/root/zeus-nexus"

# Helper functions
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

check_oc_login() {
    if ! oc whoami &>/dev/null; then
        log_error "Not logged into OpenShift. Please run 'oc login' first."
        exit 1
    fi
    log_success "OpenShift login verified: $(oc whoami)"
}

create_project() {
    log_info "Creating OpenShift project: $NAMESPACE"
    
    if oc get project $NAMESPACE &>/dev/null; then
        log_warning "Project $NAMESPACE already exists"
    else
        oc new-project $NAMESPACE --description="Zeus Nexus AI Pantheon-as-a-Service" --display-name="AC Agentic AI Platform"
        log_success "Project $NAMESPACE created"
    fi
}

apply_configs() {
    log_info "Applying configurations and secrets..."
    
    cd $PROJECT_DIR
    
    # Apply namespace and RBAC
    oc apply -f config/namespace-rbac.yaml
    
    # Apply ConfigMaps and Secrets
    oc apply -f config/zeus-config.yaml
    oc apply -f config/secrets.yaml
    
    log_success "Configurations applied"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure layer (Redis, PostgreSQL, MinIO, GitLab)..."
    
    # Deploy infrastructure components
    oc apply -f manifests/infrastructure/redis.yaml
    oc apply -f manifests/infrastructure/postgresql.yaml
    oc apply -f manifests/infrastructure/minio.yaml
    oc apply -f manifests/infrastructure/gitlab.yaml
    
    log_info "Waiting for core infrastructure to be ready..."
    
    # Wait for Redis
    oc wait --for=condition=ready pod -l app=redis --timeout=300s -n $NAMESPACE
    log_success "Redis is ready"
    
    # Wait for PostgreSQL  
    oc wait --for=condition=ready pod -l app=postgresql --timeout=300s -n $NAMESPACE
    log_success "PostgreSQL is ready"
    
    # Wait for MinIO
    oc wait --for=condition=ready pod -l app=minio --timeout=300s -n $NAMESPACE
    log_success "MinIO is ready"
    
    log_info "Waiting for GitLab CE to be ready (this may take several minutes)..."
    # GitLab takes longer to start up
    if oc wait --for=condition=ready pod -l app=gitlab-ce --timeout=900s -n $NAMESPACE; then
        log_success "GitLab CE is ready"
        GITLAB_URL=$(oc get route gitlab-ce -n $NAMESPACE -o jsonpath='{.spec.host}')
        log_info "GitLab CE available at: https://$GITLAB_URL"
        log_info "Default login: root / zeus123456"
    else
        log_warning "GitLab CE did not become ready within timeout, but continuing deployment"
    fi
    
    log_success "Infrastructure layer deployed successfully"
}

deploy_zeus_core() {
    log_info "Deploying Zeus Core API..."
    # Use BuildConfig to build the zeus-core image, then deploy using the built image (deployment-v2)
    oc apply -f manifests/zeus-core/buildconfig.yaml -n $NAMESPACE
    oc apply -f manifests/zeus-core/deployment-v2.yaml -n $NAMESPACE

    # Trigger a build to ensure image is available in internal registry (start-build will use the git defined in BC)
    log_info "Starting build for zeus-core image (this may take a few minutes)..."
    if ! oc start-build zeus-core -n $NAMESPACE --follow; then
        log_warning "Build failed or could not follow build logs. Continuing to apply deployment and attempting to wait for pods."
    fi

    log_info "Waiting for Zeus Core pods to become ready..."
    # Wait for pods to be ready (increase timeout because build and image pull may take time)
    if oc wait --for=condition=ready pod -l app=zeus-core --timeout=600s -n $NAMESPACE; then
        log_success "Zeus Core API deployed successfully"
    else
        log_error "Zeus Core pods did not become ready within timeout. Check 'oc logs' for details."
        return 1
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check all pods
    log_info "Pod status:"
    oc get pods -n $NAMESPACE
    
    # Check services
    log_info "Service status:"
    oc get svc -n $NAMESPACE
    
    # Check routes
    log_info "Route status:"
    oc get routes -n $NAMESPACE
    
    # Test Zeus Core API
    ZEUS_URL=$(oc get route zeus-core -n $NAMESPACE -o jsonpath='{.spec.host}')
    if [ ! -z "$ZEUS_URL" ]; then
        log_info "Testing Zeus Core API at https://$ZEUS_URL"
        if curl -f -s https://$ZEUS_URL/health >/dev/null; then
            log_success "Zeus Core API is responding"
        else
            log_warning "Zeus Core API health check failed"
        fi
    fi
}

show_endpoints() {
    log_info "Deployment completed! Access endpoints:"
    echo ""
    echo "📊 Zeus Core API: https://$(oc get route zeus-core -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com')"
    echo "💾 MinIO Console: https://$(oc get route minio-console -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'minio-ac-agentic.apps.prod01.fis-cloud.fpt.com')"
    echo "🔧 MinIO API: https://$(oc get route minio-api -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'minio-api-ac-agentic.apps.prod01.fis-cloud.fpt.com')"
    echo "🦊 GitLab CE: https://$(oc get route gitlab-ce -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo 'gitlab-ac-agentic.apps.prod01.fis-cloud.fpt.com') (root/zeus123456)"
    echo ""
    echo "🤖 AI Agents:"
    echo "  Athena (PM):  https://athena-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Ares (DM):    https://ares-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Hermes (AM):  https://hermes-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Hephaestus:   https://hephaestus-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Apollo:       https://apollo-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Mnemosyne:    https://mnemosyne-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo "  Clio:         https://clio-ac-agentic.apps.prod01.fis-cloud.fpt.com"
    echo ""
    echo "🔍 Useful commands:"
    echo "  oc get pods -n $NAMESPACE"
    echo "  oc logs -f deployment/zeus-core -n $NAMESPACE"
    echo "  oc get routes -n $NAMESPACE"
    echo ""
    echo "📖 See ENDPOINTS.md for complete API documentation"
    echo ""
}

cleanup() {
    log_warning "Cleaning up Zeus Nexus deployment..."
    read -p "Are you sure you want to delete the entire Zeus Nexus deployment? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        oc delete project $NAMESPACE
        log_success "Zeus Nexus deployment cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

# ArgoCD deployment function
deploy_argocd() {
    log_info "Setting up ArgoCD for Zeus Nexus..."
    
    if [ ! -f "./setup-argocd.sh" ]; then
        log_error "ArgoCD setup script not found"
        exit 1
    fi
    
    bash ./setup-argocd.sh
    
    log_success "ArgoCD setup completed"
    log_info "Zeus Nexus will be deployed via GitOps"
    log_info "Monitor deployment at ArgoCD UI"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        log_info "Starting Zeus Nexus deployment..."
        check_oc_login
        create_project
        apply_configs
        deploy_infrastructure
        deploy_zeus_core
        verify_deployment
        show_endpoints
        log_success "🎉 Zeus Nexus deployment completed successfully!"
        ;;
    "argocd")
        log_info "Starting Zeus Nexus ArgoCD deployment..."
        check_oc_login
        deploy_argocd
        log_success "🎉 Zeus Nexus ArgoCD setup completed successfully!"
        ;;
    "cleanup")
        cleanup
        ;;
    "verify")
        verify_deployment
        ;;
    "endpoints")
        show_endpoints
        ;;
    *)
        echo "Usage: $0 {deploy|argocd|cleanup|verify|endpoints}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy complete Zeus Nexus stack (direct)"
        echo "  argocd    - Setup ArgoCD and deploy via GitOps"
        echo "  cleanup   - Remove entire deployment"
        echo "  verify    - Verify current deployment status"
        echo "  endpoints - Show service endpoints"
        exit 1
        ;;
esac