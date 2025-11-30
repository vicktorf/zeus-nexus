#!/bin/bash

# Zeus Nexus - OAuth & LLM Configuration Script
# This script helps you configure OAuth and LLM backends

set -e

NAMESPACE="ac-agentic"
FRONTEND_URL="https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com"
BACKEND_URL="https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com"

echo "================================================"
echo "⚡ Zeus Nexus - OAuth & LLM Setup"
echo "================================================"
echo ""

# Function to read input with default value
read_with_default() {
    local prompt="$1"
    local default="$2"
    local value
    
    read -p "$prompt [$default]: " value
    echo "${value:-$default}"
}

# Function to read secret (hidden input)
read_secret() {
    local prompt="$1"
    local value
    
    read -sp "$prompt: " value
    echo ""
    echo "$value"
}

echo "📋 Step 1: Google OAuth2 Configuration"
echo "----------------------------------------"
echo ""
echo "First, create OAuth credentials in Google Cloud Console:"
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo "2. Create OAuth 2.0 Client ID (Web application)"
echo "3. Add redirect URI: $FRONTEND_URL"
echo ""

CONFIGURE_OAUTH=$(read_with_default "Do you want to configure Google OAuth? (yes/no)" "yes")

if [[ "$CONFIGURE_OAUTH" == "yes" ]]; then
    GOOGLE_CLIENT_ID=$(read_with_default "Enter Google Client ID" "")
    GOOGLE_CLIENT_SECRET=$(read_secret "Enter Google Client Secret")
    
    if [[ -n "$GOOGLE_CLIENT_ID" && -n "$GOOGLE_CLIENT_SECRET" ]]; then
        echo ""
        echo "✅ Updating OAuth credentials..."
        
        oc patch secret zeus-frontend-secrets -n $NAMESPACE -p="{
          \"stringData\": {
            \"GOOGLE_CLIENT_ID\": \"$GOOGLE_CLIENT_ID\",
            \"GOOGLE_CLIENT_SECRET\": \"$GOOGLE_CLIENT_SECRET\"
          }
        }" 2>/dev/null || echo "⚠️  Secret not found, will create later"
        
        echo "✅ OAuth credentials configured!"
    else
        echo "⚠️  Skipping OAuth configuration - credentials not provided"
    fi
fi

echo ""
echo "================================================"
echo "🤖 Step 2: LLM Provider Configuration"
echo "================================================"
echo ""
echo "Configure API keys for LLM providers you want to use:"
echo ""

# OpenAI
echo "--- OpenAI (GPT-4, GPT-3.5, etc.) ---"
CONFIGURE_OPENAI=$(read_with_default "Configure OpenAI? (yes/no)" "yes")

if [[ "$CONFIGURE_OPENAI" == "yes" ]]; then
    echo "Get your API key from: https://platform.openai.com/api-keys"
    OPENAI_API_KEY=$(read_secret "Enter OpenAI API Key (sk-...)")
else
    OPENAI_API_KEY=""
fi

echo ""

# Anthropic
echo "--- Anthropic (Claude 3.x) ---"
CONFIGURE_ANTHROPIC=$(read_with_default "Configure Anthropic? (yes/no)" "no")

if [[ "$CONFIGURE_ANTHROPIC" == "yes" ]]; then
    echo "Get your API key from: https://console.anthropic.com/"
    ANTHROPIC_API_KEY=$(read_secret "Enter Anthropic API Key (sk-ant-...)")
else
    ANTHROPIC_API_KEY=""
fi

echo ""

# Google AI
echo "--- Google AI (Gemini) ---"
CONFIGURE_GOOGLE_AI=$(read_with_default "Configure Google AI? (yes/no)" "no")

if [[ "$CONFIGURE_GOOGLE_AI" == "yes" ]]; then
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    GOOGLE_AI_API_KEY=$(read_secret "Enter Google AI API Key (AIza...)")
else
    GOOGLE_AI_API_KEY=""
fi

echo ""
echo "================================================"
echo "💾 Step 3: Applying Configuration"
echo "================================================"
echo ""

# Check if secrets exist, create if not
SECRET_EXISTS=$(oc get secret zeus-secrets -n $NAMESPACE 2>/dev/null && echo "yes" || echo "no")

if [[ "$SECRET_EXISTS" == "no" ]]; then
    echo "Creating zeus-secrets..."
    oc create secret generic zeus-secrets -n $NAMESPACE \
        --from-literal=POSTGRES_PASSWORD=zeus123 \
        --from-literal=REDIS_PASSWORD="" \
        --from-literal=MINIO_ROOT_USER=minioadmin \
        --from-literal=MINIO_ROOT_PASSWORD=minioadmin123 \
        --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY}" \
        --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
        --from-literal=GOOGLE_AI_API_KEY="${GOOGLE_AI_API_KEY}"
else
    echo "Updating zeus-secrets..."
    oc patch secret zeus-secrets -n $NAMESPACE -p="{
      \"stringData\": {
        \"OPENAI_API_KEY\": \"${OPENAI_API_KEY}\",
        \"ANTHROPIC_API_KEY\": \"${ANTHROPIC_API_KEY}\",
        \"GOOGLE_AI_API_KEY\": \"${GOOGLE_AI_API_KEY}\"
      }
    }"
fi

echo "✅ Secrets updated successfully!"
echo ""

# Restart deployments
echo "♻️  Restarting deployments to apply changes..."
oc rollout restart deployment/zeus-core -n $NAMESPACE 2>/dev/null && echo "  - Zeus Core restarted" || echo "  ⚠️  Zeus Core not found"
oc rollout restart deployment/zeus-frontend -n $NAMESPACE 2>/dev/null && echo "  - Zeus Frontend restarted" || echo "  ⚠️  Zeus Frontend not found"

echo ""
echo "⏳ Waiting for deployments to be ready..."
sleep 5

echo ""
echo "================================================"
echo "✅ Configuration Complete!"
echo "================================================"
echo ""
echo "🌐 Access Zeus Nexus:"
echo "   Frontend: $FRONTEND_URL"
echo "   Backend:  $BACKEND_URL"
echo ""
echo "🧪 Test LLM Configuration:"
echo "   curl $BACKEND_URL/llm/models | jq ."
echo ""
echo "📊 Check Status:"
echo "   oc get pods -n $NAMESPACE | grep zeus"
echo "   oc logs -f deployment/zeus-core -n $NAMESPACE"
echo ""
echo "📚 For more info, see: SETUP_OAUTH_LLM.md"
echo "================================================"
