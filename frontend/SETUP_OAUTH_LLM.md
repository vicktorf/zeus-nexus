# 🔐 OAuth & LLM Backend Configuration Guide

## 📋 Table of Contents
1. [Google OAuth2 Setup](#google-oauth2-setup)
2. [LLM Provider Configuration](#llm-provider-configuration)
3. [OpenShift Deployment](#openshift-deployment)
4. [Testing & Verification](#testing--verification)

---

## 🔑 Google OAuth2 Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing: `ac-n8n-479314` (or your project)
3. Enable required APIs:
   ```
   - Google+ API (for OAuth user info)
   - People API (optional, for profile data)
   ```

### Step 2: Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Choose **Internal** (for organization) or **External** (for public)
3. Fill in application details:
   - **App name**: Zeus Nexus AI
   - **User support email**: your-email@fpt.com
   - **App logo**: (optional)
   - **Application home page**: https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
   - **Authorized domains**: `fis-cloud.fpt.com`
   - **Developer contact**: your-email@fpt.com

4. Add scopes:
   ```
   - openid
   - email
   - profile
   ```

5. Add test users (if app not published):
   ```
   - your-email@fpt.com
   - team-member@fpt.com
   ```

### Step 3: Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
3. Select **Web application**
4. Fill in details:
   - **Name**: Zeus Nexus Frontend
   - **Authorized JavaScript origins**:
     ```
     https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
     ```
   - **Authorized redirect URIs**:
     ```
     https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
     https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com/oauth/callback
     ```

5. Click **CREATE**
6. **Copy Client ID and Client Secret** - you'll need these!

### Step 4: Update OpenShift Secrets

```bash
# Update the secret with your OAuth credentials
oc edit secret zeus-frontend-secrets -n ac-agentic

# Or use this command:
oc patch secret zeus-frontend-secrets -n ac-agentic -p='
{
  "stringData": {
    "GOOGLE_CLIENT_ID": "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com",
    "GOOGLE_CLIENT_SECRET": "YOUR_CLIENT_SECRET_HERE"
  }
}'

# Restart frontend pods to pick up new secrets
oc rollout restart deployment/zeus-frontend -n ac-agentic
```

---

## 🤖 LLM Provider Configuration

Zeus Nexus supports multiple LLM providers. Configure API keys for the providers you want to use.

### Option 1: OpenAI (GPT models)

1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Update Zeus Core secret:

```bash
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "OPENAI_API_KEY": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}'

# Restart Zeus Core to apply
oc rollout restart deployment/zeus-core -n ac-agentic
```

**Supported models:**
- `gpt-4` - Most capable, best for complex tasks
- `gpt-4-turbo` - Faster with 128K context
- `gpt-4o` - Optimized version
- `gpt-3.5-turbo` - Fast and cost-effective

### Option 2: Anthropic (Claude models)

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Update secret:

```bash
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "ANTHROPIC_API_KEY": "sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"
  }
}'

oc rollout restart deployment/zeus-core -n ac-agentic
```

**Supported models:**
- `claude-3-opus` - Most capable Claude model
- `claude-3.5-sonnet` - Latest with improved reasoning
- `claude-3-sonnet` - Balanced performance
- `claude-3-haiku` - Fastest, most cost-effective

### Option 3: Google AI (Gemini models)

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Update secret:

```bash
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "GOOGLE_AI_API_KEY": "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}'

oc rollout restart deployment/zeus-core -n ac-agentic
```

**Supported models:**
- `gemini-1.5-pro` - 1M context window
- `gemini-1.5-flash` - Fast and efficient
- `gemini-pro` - General purpose

### Configure Multiple Providers

To use all providers simultaneously:

```bash
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "OPENAI_API_KEY": "sk-proj-xxxxx",
    "ANTHROPIC_API_KEY": "sk-ant-xxxxx",
    "GOOGLE_AI_API_KEY": "AIzaSyxxxxx"
  }
}'

# Verify secrets
oc get secret zeus-secrets -n ac-agentic -o jsonpath='{.data}' | jq 'keys'

# Restart both frontend and backend
oc rollout restart deployment/zeus-core deployment/zeus-frontend -n ac-agentic
```

---

## ☸️ OpenShift Deployment

### Quick Deploy

```bash
cd /root/zeus-nexus/frontend

# 1. Apply configs and secrets
oc apply -f config-secrets.yaml

# 2. Update secrets with real values (see above)

# 3. Rebuild and deploy frontend (if needed)
oc start-build zeus-frontend --from-dir=. --follow -n ac-agentic

# 4. Check deployment
oc get pods -n ac-agentic | grep zeus-frontend
oc get route zeus-frontend -n ac-agentic
```

### Update Deployment with Secrets

Edit `deployment.yaml` to mount secrets:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zeus-frontend
spec:
  template:
    spec:
      containers:
      - name: streamlit
        envFrom:
        - configMapRef:
            name: zeus-frontend-config
        - secretRef:
            name: zeus-frontend-secrets
```

Apply changes:

```bash
oc apply -f deployment.yaml
oc rollout status deployment/zeus-frontend -n ac-agentic
```

---

## ✅ Testing & Verification

### Test OAuth Flow

1. Open frontend: https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
2. Click **"Sign in with Google"**
3. You should be redirected to Google login
4. After authentication, redirect back to Zeus Nexus
5. You should see your profile in sidebar

**Troubleshooting OAuth:**

```bash
# Check frontend logs
oc logs -f deployment/zeus-frontend -n ac-agentic

# Common issues:
# - "redirect_uri_mismatch" → Check redirect URI in Google Console
# - "invalid_client" → Check Client ID and Secret
# - "access_denied" → Add user to test users list
```

### Test LLM Models

1. Sign in to Zeus Nexus
2. Click **"Check Health"** in sidebar - verify services are healthy
3. Click **"Load Agents"** - should show 7 agents
4. Select different LLM models from dropdown
5. Send test messages:

```
# For Athena (Project Management)
"Show me current Jira projects"

# For Ares (DevOps)
"Check Grafana monitoring alerts"

# For Apollo (Sales)
"What's the revenue forecast?"
```

### Verify LLM Configuration

```bash
# Check which LLM models are configured
curl -s https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/models | jq .

# Expected response:
# [
#   {
#     "model": "gpt-4",
#     "provider": "openai",
#     "api_key_configured": true,   # ← Should be true
#     "context_length": 8192,
#     "cost_per_1k_input": 0.03
#   },
#   ...
# ]

# Test chat with specific model
curl -X POST https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Zeus",
    "llm_model": "gpt-4"
  }' | jq .
```

### Check Logs

```bash
# Frontend logs
oc logs -f deployment/zeus-frontend -n ac-agentic

# Backend logs (Zeus Core)
oc logs -f deployment/zeus-core -n ac-agentic

# Look for:
# ✅ Zeus Nexus Core initialized successfully!
# 🤖 LLM Providers Status:
#    - openai: ✅ Configured
#    - anthropic: ✅ Configured
#    - google: ❌ Not Configured
```

---

## 🔧 Advanced Configuration

### Custom OAuth Provider

To add Azure AD, Okta, or other OAuth providers, modify `auth.py`:

```python
# auth.py - Add new provider
class AzureOAuthManager(OAuthManager):
    def get_authorization_url(self):
        # Azure AD specific implementation
        pass
```

### LLM Model Fine-tuning

Add custom models in Zeus Core (`main-v2.py`):

```python
LLM_MODELS["gpt-4-custom"] = {
    "provider": LLMProvider.OPENAI,
    "context_length": 32000,
    "cost": {"input": 0.01, "output": 0.03}
}
```

### Environment-specific Configs

For different environments (dev/staging/prod):

```bash
# Development
oc create secret generic zeus-frontend-secrets-dev \
  --from-literal=GOOGLE_CLIENT_ID=dev-client-id \
  -n ac-agentic-dev

# Production
oc create secret generic zeus-frontend-secrets-prod \
  --from-literal=GOOGLE_CLIENT_ID=prod-client-id \
  -n ac-agentic-prod
```

---

## 📚 References

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Google AI Gemini](https://ai.google.dev/docs)
- [Streamlit OAuth](https://docs.streamlit.io/)

---

## 🆘 Support

For issues or questions:
1. Check logs: `oc logs -f deployment/zeus-frontend -n ac-agentic`
2. Verify secrets: `oc get secret zeus-frontend-secrets -n ac-agentic`
3. Test API: `curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/health`

**Common Issues:**

| Issue | Solution |
|-------|----------|
| OAuth redirect error | Update redirect URI in Google Console |
| LLM model not available | Set API key in `zeus-secrets` |
| Frontend not loading | Check pod logs and route configuration |
| Chat returns 503 | Verify Zeus Core is running and healthy |
