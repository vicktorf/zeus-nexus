# 🔐 OpenShift OAuth Integration Guide

## 📋 Tổng quan

Zeus Nexus sử dụng **OpenShift OAuth Proxy** để authentication - không cần setup Google OAuth hay external provider! 

### Ưu điểm:
- ✅ Không cần external OAuth provider (Google, Azure AD, etc.)
- ✅ Tự động integrate với OpenShift user management
- ✅ SSO với tất cả OpenShift services
- ✅ RBAC built-in với Kubernetes
- ✅ Auto SSL/TLS với OpenShift service certificates

---

## 🏗️ Kiến trúc

```
┌─────────────────────────────────────────────┐
│  User Browser                               │
└──────────────┬──────────────────────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────────────────────┐
│  OpenShift Route (TLS Reencrypt)            │
│  zeus-ui-ac-agentic.apps.prod01...          │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Zeus Frontend Pod                          │
│  ┌─────────────────────────────────────┐   │
│  │ OAuth Proxy (Port 8443)             │   │
│  │ - Authenticate with OpenShift       │   │
│  │ - Check RBAC permissions            │   │
│  │ - Set user headers                  │   │
│  └──────────┬──────────────────────────┘   │
│             │ Proxy to                      │
│             ▼                                │
│  ┌─────────────────────────────────────┐   │
│  │ Streamlit App (Port 8501)           │   │
│  │ - Chat interface                    │   │
│  │ - LLM selection                     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 🚀 Deployment Steps

### 1. Apply RBAC Configuration

```bash
cd /root/zeus-nexus/frontend

# Create ServiceAccount with OAuth redirect annotation
oc apply -f oauth-rbac.yaml

# Verify ServiceAccount
oc get sa zeus-service-account -n ac-agentic
oc describe sa zeus-service-account -n ac-agentic
```

**Expected output:**
```
Annotations:  serviceaccounts.openshift.io/oauth-redirectreference.zeus: 
              {"kind":"OAuthRedirectReference","apiVersion":"v1","reference":{"kind":"Route","name":"zeus-frontend"}}
```

### 2. Deploy Frontend with OAuth Proxy

```bash
# Delete old deployment (if exists)
oc delete deployment zeus-frontend -n ac-agentic 2>/dev/null || true

# Apply new deployment with OAuth Proxy sidecar
oc apply -f deployment-oauth.yaml

# Check deployment status
oc get pods -n ac-agentic | grep zeus-frontend
```

**Expected pods:**
```
zeus-frontend-xxxxx-xxxxx   2/2   Running   0   30s
```
*Note: 2/2 = OAuth Proxy + Streamlit*

### 3. Verify Service Certificate

OpenShift tự động tạo TLS certificate cho service:

```bash
# Check if secret was created
oc get secret zeus-frontend-tls -n ac-agentic

# View certificate details
oc get secret zeus-frontend-tls -n ac-agentic -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text | grep -A2 Subject
```

### 4. Test OAuth Flow

```bash
# Get route URL
FRONTEND_URL=$(oc get route zeus-frontend -n ac-agentic -o jsonpath='{.spec.host}')
echo "Frontend URL: https://$FRONTEND_URL"

# Open in browser (manual step)
echo "Open this URL in browser: https://$FRONTEND_URL"
```

**Expected flow:**
1. Browser → Zeus Frontend URL
2. Redirect → OpenShift OAuth login page
3. Login with OpenShift credentials
4. Redirect back → Zeus Frontend (authenticated)

---

## 🔧 Configuration Details

### OAuth Proxy Arguments

```yaml
args:
- --https-address=:8443              # HTTPS port
- --provider=openshift                # Use OpenShift OAuth
- --openshift-service-account=zeus-service-account
- --upstream=http://localhost:8501    # Streamlit app
- --tls-cert=/etc/tls/private/tls.crt # Auto-generated cert
- --tls-key=/etc/tls/private/tls.key
- --cookie-secret=SECRET              # Session cookie encryption
- --openshift-delegate-urls={"/": {"resource": "pods", "verb": "get", "namespace": "ac-agentic"}}
- --skip-auth-regex=^/metrics         # Public endpoints
- --skip-provider-button              # Auto-redirect to login
```

### User Headers

OAuth Proxy tự động inject headers vào requests:

```
X-Forwarded-User: dungpv30@fpt.com
X-Forwarded-Email: dungpv30@fpt.com
X-Forwarded-Preferred-Username: dungpv30
X-Forwarded-Groups: system:authenticated,system:authenticated:oauth
```

Streamlit app có thể đọc user info từ headers này!

---

## 📝 Streamlit Integration

Update `app.py` để đọc user info từ OpenShift OAuth headers:

```python
import streamlit as st
import os

# Get user info from OAuth Proxy headers
# These are injected by the reverse proxy
def get_authenticated_user():
    # In production, these come from request headers
    # For local dev, use environment variables
    user_email = os.environ.get('HTTP_X_FORWARDED_EMAIL', 'demo@local')
    user_name = os.environ.get('HTTP_X_FORWARDED_USER', 'Demo User')
    return {
        "email": user_email,
        "name": user_name,
        "authenticated": True
    }

# Display user in sidebar
user_info = get_authenticated_user()
with st.sidebar:
    st.markdown("### 👤 Logged in as")
    st.write(f"**{user_info['name']}**")
    st.write(f"_{user_info['email']}_")
```

---

## 🔒 Access Control (RBAC)

### Grant Access to Users

```bash
# Allow specific user to access Zeus Frontend
oc adm policy add-role-to-user view <username> -n ac-agentic

# Allow group access
oc adm policy add-role-to-group view <groupname> -n ac-agentic

# Example: Grant access to dungpv30
oc adm policy add-role-to-user view dungpv30 -n ac-agentic
```

### Create Custom Role (Optional)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: zeus-user
  namespace: ac-agentic
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: zeus-users
  namespace: ac-agentic
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: zeus-user
subjects:
- kind: User
  name: dungpv30
- kind: User
  name: user2@fpt.com
```

Apply:
```bash
oc apply -f custom-rbac.yaml
```

---

## ✅ Testing & Verification

### 1. Check Pod Status

```bash
oc get pods -n ac-agentic -l app=zeus-frontend

# Should show 2/2 containers running
NAME                             READY   STATUS    RESTARTS   AGE
zeus-frontend-xxxxx-xxxxx        2/2     Running   0          5m
```

### 2. Check Logs

```bash
# OAuth Proxy logs
oc logs -f deployment/zeus-frontend -n ac-agentic -c oauth-proxy

# Streamlit logs
oc logs -f deployment/zeus-frontend -n ac-agentic -c streamlit
```

### 3. Test Authentication Flow

```bash
# Get route
oc get route zeus-frontend -n ac-agentic

# Test with curl (will get redirect to OAuth)
curl -I https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com

# Expected: 302 redirect to OpenShift OAuth
```

### 4. Access via Browser

1. Open: `https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com`
2. Should redirect to OpenShift login
3. Login with OpenShift credentials (e.g., `dungpv30`)
4. Redirect back to Zeus Frontend
5. Should see Streamlit app with user info

---

## 🐛 Troubleshooting

### Issue: 503 Service Unavailable

```bash
# Check pods
oc get pods -n ac-agentic -l app=zeus-frontend

# Check pod logs
oc logs deployment/zeus-frontend -n ac-agentic -c oauth-proxy --tail=50
```

**Common cause:** Service certificate not ready yet
**Solution:** Wait 1-2 minutes for cert to be issued

### Issue: 403 Forbidden after login

**Cause:** User doesn't have RBAC permissions
**Solution:** Grant view role to user

```bash
oc adm policy add-role-to-user view <username> -n ac-agentic
```

### Issue: OAuth loop (keeps redirecting)

**Cause:** Cookie issues or wrong redirect URL
**Solutions:**
1. Check ServiceAccount annotation:
   ```bash
   oc get sa zeus-service-account -n ac-agentic -o yaml | grep redirect
   ```
2. Clear browser cookies
3. Check route hostname matches annotation

### Issue: TLS certificate error

```bash
# Check if secret exists
oc get secret zeus-frontend-tls -n ac-agentic

# If missing, add annotation to service
oc annotate svc zeus-frontend -n ac-agentic \
  service.beta.openshift.io/serving-cert-secret-name=zeus-frontend-tls
```

---

## 🔄 Update Deployment

To update OAuth Proxy or Streamlit:

```bash
# Update OAuth Proxy configuration
oc edit deployment zeus-frontend -n ac-agentic

# Or apply changes
oc apply -f deployment-oauth.yaml

# Restart deployment
oc rollout restart deployment/zeus-frontend -n ac-agentic
oc rollout status deployment/zeus-frontend -n ac-agentic
```

---

## 📚 Advanced Configuration

### Custom Cookie Secret

Generate secure cookie secret:

```bash
# Generate random secret
COOKIE_SECRET=$(openssl rand -base64 32)

# Create secret
oc create secret generic zeus-oauth-cookie \
  --from-literal=cookie-secret=$COOKIE_SECRET \
  -n ac-agentic

# Update deployment to use secret
# Change --cookie-secret=SECRET to:
# --cookie-secret-file=/etc/oauth/cookie-secret

# Mount secret in deployment
```

### Skip Auth for Specific Paths

```yaml
args:
- --skip-auth-regex=^/metrics|^/health|^/_stcore/health
```

### Session Timeout

```yaml
args:
- --cookie-expire=24h0m0s  # 24 hours
```

---

## 📊 Monitoring

### Check OAuth Metrics

```bash
# OAuth Proxy exposes metrics on /metrics
oc port-forward deployment/zeus-frontend 9091:8443 -n ac-agentic

# In another terminal
curl -k https://localhost:9091/metrics | grep oauth
```

### View Active Sessions

OAuth Proxy logs show authentication events:

```bash
oc logs deployment/zeus-frontend -c oauth-proxy -n ac-agentic | grep authenticated
```

---

## 🔗 References

- [OpenShift OAuth Proxy Documentation](https://docs.openshift.com/container-platform/4.14/authentication/configuring-oauth-clients.html)
- [OAuth Proxy GitHub](https://github.com/openshift/oauth-proxy)
- [Service Serving Certificates](https://docs.openshift.com/container-platform/4.14/security/certificates/service-serving-certificate.html)

---

## 🎯 Quick Reference

```bash
# Deploy with OAuth
cd /root/zeus-nexus/frontend
oc apply -f oauth-rbac.yaml
oc apply -f deployment-oauth.yaml

# Grant user access
oc adm policy add-role-to-user view <username> -n ac-agentic

# Check status
oc get pods -n ac-agentic -l app=zeus-frontend
oc logs -f deployment/zeus-frontend -c oauth-proxy -n ac-agentic

# Get URL
echo "https://$(oc get route zeus-frontend -n ac-agentic -o jsonpath='{.spec.host}')"
```

---

**✨ That's it! OpenShift OAuth là built-in, không cần external setup!**
