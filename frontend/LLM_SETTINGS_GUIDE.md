# 🔐 Zeus Nexus - LLM Settings Feature

## ✨ Tính năng mới: Quản lý API Keys cho LLM Providers

Bây giờ bạn có thể cấu hình API keys trực tiếp trong giao diện web Zeus Nexus mà không cần edit deployment hay secrets!

---

## 🎯 Tính năng

### 1. **Settings Page**
- **Truy cập**: Click vào "⚙️ Settings" trong sidebar
- **Quản lý API keys** cho 3 providers:
  - 🤖 OpenAI (GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo)
  - 🧠 Anthropic (Claude 3 Opus, Sonnet, Haiku, Claude 3.5 Sonnet)
  - 🔍 Google AI (Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash)

### 2. **Dynamic LLM Model Selector**
- **Chỉ hiển thị models đã có API key**
- **Auto-refresh** khi thêm API key mới
- **Model info**: Context length, cost per 1k tokens

### 3. **Backend API Endpoints**
- `GET /llm/config` - Xem trạng thái cấu hình
- `POST /llm/config` - Thêm/update API keys
- `DELETE /llm/config/{provider}` - Xóa API key
- `GET /llm/models` - List models với trạng thái configured

---

## 🚀 Hướng dẫn sử dụng

### Bước 1: Truy cập Zeus Frontend
```bash
URL: https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
```

### Bước 2: Mở Settings Page
1. Click vào radio button "⚙️ Settings" trong sidebar
2. Xem trạng thái hiện tại của các providers

### Bước 3: Thêm API Keys

#### **OpenAI:**
1. Truy cập: https://platform.openai.com/api-keys
2. Tạo secret key (bắt đầu bằng `sk-...`)
3. Copy và paste vào Settings
4. Click "💾 Save Configuration"

#### **Anthropic (Claude):**
1. Truy cập: https://console.anthropic.com/settings/keys
2. Tạo API key (bắt đầu bằng `sk-ant-...`)
3. Copy và paste vào Settings
4. Click "💾 Save Configuration"

#### **Google AI:**
1. Truy cập: https://makersuite.google.com/app/apikey
2. Tạo API key (bắt đầu bằng `AIza...`)
3. Copy và paste vào Settings
4. Click "💾 Save Configuration"

### Bước 4: Verify & Chat
1. Quay lại "💬 Chat" page
2. Xem LLM dropdown - sẽ hiển thị models mới
3. Chọn model và bắt đầu chat!

---

## 📊 Kiểm tra trạng thái qua API

```bash
# Xem provider configuration
curl -s https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/config | jq '.'

# Output example:
{
  "providers": {
    "openai": {
      "configured": true,
      "key_length": 27,
      "key_preview": "sk-your-...here"
    },
    "anthropic": {
      "configured": false,
      "key_length": 0,
      "key_preview": null
    },
    "google": {
      "configured": false,
      "key_length": 0,
      "key_preview": null
    }
  },
  "total_configured": 1,
  "total_providers": 3
}

# List available models
curl -s https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/models | jq '.[] | {model, provider, configured: .api_key_configured}'

# Thêm API key qua curl (nếu cần)
curl -X POST https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/llm/config \
  -H "Content-Type: application/json" \
  -d '{
    "openai_api_key": "sk-your-key-here",
    "anthropic_api_key": "sk-ant-your-key-here",
    "google_api_key": "AIzayour-key-here"
  }'
```

---

## 🤖 Available Models by Provider

### OpenAI (4 models)
| Model | Context | Cost (Input) | Cost (Output) |
|-------|---------|--------------|---------------|
| gpt-4 | 8,192 tokens | $0.03/1k | $0.06/1k |
| gpt-4-turbo | 128,000 tokens | $0.01/1k | $0.03/1k |
| gpt-4o | 128,000 tokens | $0.005/1k | $0.015/1k |
| gpt-3.5-turbo | 16,384 tokens | $0.0005/1k | $0.0015/1k |

### Anthropic (4 models)
| Model | Context | Cost (Input) | Cost (Output) |
|-------|---------|--------------|---------------|
| claude-3-opus | 200,000 tokens | $0.015/1k | $0.075/1k |
| claude-3.5-sonnet | 200,000 tokens | $0.003/1k | $0.015/1k |
| claude-3-sonnet | 200,000 tokens | $0.003/1k | $0.015/1k |
| claude-3-haiku | 200,000 tokens | $0.00025/1k | $0.00125/1k |

### Google AI (3 models)
| Model | Context | Cost (Input) | Cost (Output) |
|-------|---------|--------------|---------------|
| gemini-pro | 32,000 tokens | $0.0005/1k | $0.0015/1k |
| gemini-1.5-pro | 1,000,000 tokens | $0.00125/1k | $0.005/1k |
| gemini-1.5-flash | 1,000,000 tokens | $0.000125/1k | $0.0005/1k |

---

## 🔒 Security Notes

### Runtime Storage
- API keys được lưu **in-memory** trong Zeus Core pod
- **Không persist** vào disk hay database
- Khi pod restart → API keys bị clear → cần nhập lại

### Production Recommendations
1. **Kubernetes Secrets**: Lưu API keys trong OpenShift Secrets
2. **Environment Variables**: Mount secrets as env vars vào deployment
3. **Vault**: Sử dụng HashiCorp Vault hoặc similar
4. **RBAC**: Giới hạn access vào Settings page

### Best Practices
- ✅ Rotate API keys định kỳ (30-90 ngày)
- ✅ Không share API keys qua email/chat
- ✅ Monitor usage qua provider dashboard
- ✅ Set spending limits trên provider account
- ❌ Không commit API keys vào Git
- ❌ Không log API keys ra console/file

---

## 🛠️ Troubleshooting

### Models không hiển thị trong dropdown
**Nguyên nhân**: Chưa có API key configured
**Giải pháp**: 
1. Vào Settings page
2. Thêm API key cho provider tương ứng
3. Quay lại Chat page

### API key invalid
**Nguyên nhân**: Key sai format hoặc đã revoked
**Giải pháp**:
1. Verify key trên provider dashboard
2. Generate new key
3. Update lại trong Settings

### Pods restart → mất API keys
**Nguyên nhân**: Runtime storage không persist
**Giải pháp tạm thời**: Nhập lại API keys
**Giải pháp lâu dài**: Setup Kubernetes Secrets

---

## 📝 Test Cases

### Test 1: Add OpenAI key
```bash
1. Settings → Nhập OpenAI API key → Save
2. Chat → Verify GPT-4, GPT-4 Turbo, GPT-4o, GPT-3.5 Turbo xuất hiện
3. Select GPT-4 → Chat: "Hello" → Verify response
```

### Test 2: Add Anthropic key
```bash
1. Settings → Nhập Anthropic API key → Save
2. Chat → Verify Claude models xuất hiện
3. Select Claude 3.5 Sonnet → Chat: "Explain AI" → Verify response
```

### Test 3: Add Google AI key
```bash
1. Settings → Nhập Google AI API key → Save
2. Chat → Verify Gemini models xuất hiện
3. Select Gemini 1.5 Pro → Chat: "Write a poem" → Verify response
```

### Test 4: Multiple providers
```bash
1. Settings → Nhập cả 3 API keys → Save
2. Chat → Verify dropdown có 11 models
3. Switch giữa các models và test chat
```

---

## 🎉 Summary

**Đã hoàn thành:**
- ✅ Backend API endpoints (`/llm/config`, `/llm/models`)
- ✅ Settings page với form nhập API keys
- ✅ Dynamic LLM selector (chỉ show configured models)
- ✅ Frontend deployed với OAuth Proxy
- ✅ Zeus Core deployed với LLM config support

**Sẵn sàng sử dụng:**
- 🌐 Frontend: https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com
- 🔧 Backend: https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com
- 📚 API Docs: https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/docs

---

**Zeus Nexus is ready with LLM Settings! 🚀**
