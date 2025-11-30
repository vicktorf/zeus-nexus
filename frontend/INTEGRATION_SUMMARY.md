# 🎯 Zeus Nexus - OAuth & LLM Integration Summary

## ✅ Đã hoàn thành

### 1. Frontend OAuth Authentication
- ✅ Tạo `auth.py` - OAuth authentication module
- ✅ Support Google OAuth2 với JWT session management
- ✅ Demo mode cho testing không cần OAuth
- ✅ User profile display trong sidebar
- ✅ Session persistence và logout functionality

### 2. LLM Backend Configuration
- ✅ Tạo `llm_config.py` - Multi-LLM provider management
- ✅ Support 3 providers: OpenAI, Anthropic, Google AI
- ✅ 11 models total:
  - OpenAI: gpt-4, gpt-4-turbo, gpt-4o, gpt-3.5-turbo
  - Anthropic: claude-3-opus, claude-3.5-sonnet, claude-3-sonnet, claude-3-haiku
  - Google: gemini-pro, gemini-1.5-pro, gemini-1.5-flash
- ✅ Cost tracking per model
- ✅ Context length management

### 3. Zeus Core API Updates
- ✅ Tạo `main-v2.py` với multi-LLM support
- ✅ New endpoint: `/llm/models` - List available models
- ✅ Chat endpoint updated với `llm_model` parameter
- ✅ Task endpoint updated với LLM model selection
- ✅ Prometheus metrics cho LLM usage tracking
- ✅ Provider validation và error handling

### 4. OpenShift Configuration
- ✅ ConfigMap: `zeus-frontend-config` (API URLs, OAuth redirect)
- ✅ Secret: `zeus-frontend-secrets` (OAuth credentials)
- ✅ Secret: `zeus-secrets` updated (LLM API keys)
- ✅ Deployment ready với environment variables

### 5. Documentation & Scripts
- ✅ `SETUP_OAUTH_LLM.md` - Comprehensive setup guide
- ✅ `setup-oauth-llm.sh` - Interactive configuration script
- ✅ `secrets.toml.example` - Local development template

---

## 🚀 Cách sử dụng

### A. Setup OAuth (Google Cloud Console)

1. **Tạo OAuth Client:**
   ```
   https://console.cloud.google.com/apis/credentials
   → Create Credentials → OAuth 2.0 Client ID
   ```

2. **Configure Consent Screen:**
   - App name: Zeus Nexus AI
   - Authorized domain: fis-cloud.fpt.com
   - Scopes: openid, email, profile

3. **Add Redirect URI:**
   ```
   https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
   ```

4. **Update OpenShift Secret:**
   ```bash
   oc patch secret zeus-frontend-secrets -n ac-agentic -p='
   {
     "stringData": {
       "GOOGLE_CLIENT_ID": "YOUR_CLIENT_ID.apps.googleusercontent.com",
       "GOOGLE_CLIENT_SECRET": "YOUR_CLIENT_SECRET"
     }
   }'
   ```

### B. Setup LLM Providers

#### Option 1: Interactive Script (Recommended)
```bash
cd /root/zeus-nexus/frontend
./setup-oauth-llm.sh
```

#### Option 2: Manual Configuration

**OpenAI:**
```bash
# Get key from: https://platform.openai.com/api-keys
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "OPENAI_API_KEY": "sk-proj-xxxxxxxxxxxxxx"
  }
}'
```

**Anthropic:**
```bash
# Get key from: https://console.anthropic.com/
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "ANTHROPIC_API_KEY": "sk-ant-xxxxxxxxxxxxxx"
  }
}'
```

**Google AI:**
```bash
# Get key from: https://makersuite.google.com/app/apikey
oc patch secret zeus-secrets -n ac-agentic -p='
{
  "stringData": {
    "GOOGLE_AI_API_KEY": "AIzaSyxxxxxxxxxxxxxx"
  }
}'
```

### C. Deploy Updated Zeus Core

```bash
cd /root/zeus-nexus/docker

# Backup current main.py
cp app/main.py app/main-v1-backup.py

# Use new version with LLM support
cp app/main-v2.py app/main.py

# Rebuild image
oc start-build zeus-core --from-dir=. --follow -n ac-agentic

# Deployment will auto-rollout with new image
oc rollout status deployment/zeus-core -n ac-agentic
```

### D. Verify Configuration

```bash
# 1. Check LLM models availability
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/models | jq .

# 2. Test chat with specific model
curl -X POST https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Zeus",
    "llm_model": "gpt-4"
  }' | jq .

# 3. Check Zeus Core logs
oc logs -f deployment/zeus-core -n ac-agentic | grep LLM

# Expected output:
# 🤖 LLM Providers Status:
#    - openai: ✅ Configured
#    - anthropic: ✅ Configured
#    - google: ✅ Configured
```

---

## 📱 Frontend Usage

### 1. Access Zeus UI
```
https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
```

### 2. Sign In
- Click **"Sign in with Google"**
- Or use **Demo Mode** for testing

### 3. Select LLM Model
- Sidebar → **LLM Model** dropdown
- Choose from 11 available models
- Models display provider and cost info

### 4. Chat with Agents
```
Examples:
- "Show me Jira projects" → Routes to Athena (PM)
- "Check Grafana alerts" → Routes to Ares (DevOps)
- "What's the revenue?" → Routes to Apollo (Sales)
```

### 5. View Response Metadata
- Each response shows:
  - Selected agent
  - LLM model used
  - Provider info
  - Agent capabilities

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│   Zeus Frontend (Streamlit)                 │
│   - OAuth authentication                    │
│   - LLM model selector                      │
│   - Chat interface                          │
└──────────────┬──────────────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────────────┐
│   Zeus Core API (FastAPI)                   │
│   - Agent routing                           │
│   - LLM provider management                 │
│   - Multi-model support                     │
└──────┬───────────────┬──────────────────────┘
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────────────┐
│  Databases  │  │  LLM Providers      │
│  - Redis    │  │  - OpenAI           │
│  - PostgreSQL│  │  - Anthropic        │
└─────────────┘  │  - Google AI        │
                 └─────────────────────┘
```

---

## 🔐 Security Best Practices

1. **OAuth Credentials:**
   - Never commit to Git
   - Use OpenShift Secrets
   - Rotate regularly

2. **LLM API Keys:**
   - Store in `zeus-secrets` only
   - Monitor usage via Prometheus
   - Set spending limits on provider dashboards

3. **Session Management:**
   - JWT tokens expire after 24 hours
   - Use secure cookies in production
   - Implement refresh token logic

---

## 📊 Monitoring

### Prometheus Metrics

```bash
# View metrics
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/metrics

# Key metrics:
# - zeus_llm_requests_total{provider="openai",model="gpt-4"}
# - zeus_requests_total{endpoint="/chat"}
# - zeus_active_agents
```

### Logs

```bash
# Frontend logs
oc logs -f deployment/zeus-frontend -n ac-agentic

# Backend logs
oc logs -f deployment/zeus-core -n ac-agentic

# Filter for LLM activity
oc logs deployment/zeus-core -n ac-agentic | grep -i "llm\|provider"
```

---

## 🐛 Troubleshooting

### OAuth Issues

| Error | Solution |
|-------|----------|
| `redirect_uri_mismatch` | Add exact URL to Google Console |
| `invalid_client` | Check Client ID/Secret in secret |
| `access_denied` | Add user to test users list |

### LLM Issues

| Error | Solution |
|-------|----------|
| `LLM provider not configured` | Set API key in zeus-secrets |
| `Unknown LLM model` | Check model name spelling |
| `Rate limit exceeded` | Check provider dashboard, add rate limiting |

### Deployment Issues

```bash
# Pods not starting
oc get events -n ac-agentic --sort-by='.lastTimestamp'

# Secret not mounted
oc describe pod <pod-name> -n ac-agentic | grep -A5 Mounts

# Config not applied
oc get configmap zeus-frontend-config -n ac-agentic -o yaml
```

---

## 📚 API Reference

### GET /llm/models
List available LLM models with configuration status

**Response:**
```json
[
  {
    "model": "gpt-4",
    "provider": "openai",
    "api_key_configured": true,
    "context_length": 8192,
    "cost_per_1k_input": 0.03,
    "cost_per_1k_output": 0.06
  }
]
```

### POST /chat
Send message with LLM model selection

**Request:**
```json
{
  "message": "Hello Zeus",
  "llm_model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "agent": "athena",
  "response": "Hello! ...",
  "llm_model": "gpt-4",
  "llm_provider": "openai",
  "metadata": {...}
}
```

---

## 🎯 Next Steps

1. **Deploy Updated Zeus Core:**
   ```bash
   cd /root/zeus-nexus/docker
   cp app/main-v2.py app/main.py
   oc start-build zeus-core --from-dir=. --follow
   ```

2. **Configure Real OAuth:**
   - Get credentials from Google Cloud Console
   - Update `zeus-frontend-secrets`

3. **Add LLM API Keys:**
   - Run `./setup-oauth-llm.sh`
   - Or manually patch secrets

4. **Test Integration:**
   - Sign in via OAuth
   - Select different LLM models
   - Send test messages

5. **Monitor Usage:**
   - Check Prometheus metrics
   - Review logs for errors
   - Monitor API costs

---

## 📞 Support

- Documentation: `/root/zeus-nexus/frontend/SETUP_OAUTH_LLM.md`
- Script: `/root/zeus-nexus/frontend/setup-oauth-llm.sh`
- Frontend: `https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com`
- Backend: `https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com`

**Quick Commands:**
```bash
# Status check
oc get pods -n ac-agentic | grep zeus

# View logs
oc logs -f deployment/zeus-frontend -n ac-agentic
oc logs -f deployment/zeus-core -n ac-agentic

# Test API
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/health
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/models | jq .
```
