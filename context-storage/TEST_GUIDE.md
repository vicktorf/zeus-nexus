# 📖 Hướng Dẫn Test Context Storage

## ✅ Context Storage đã deploy thành công!

**URL:** `https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com`

---

## 🧪 Test Cases

### 1. Health Check
```bash
curl https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/health | jq '.'
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "context-storage",
  "timestamp": "2025-11-26T..."
}
```

---

### 2. Lưu Conversation (User Message)

```bash
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_test_session_001",
    "agent_name": "athena",
    "user_id": "dungpv30",
    "role": "user",
    "content": "Hôm nay tôi log bao nhiêu giờ?",
    "importance_score": 0.8
  }'
```

**Expected:**
```json
{
  "status": "stored",
  "memory_id": 1
}
```

---

### 3. Lưu Conversation (Assistant Response)

```bash
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my_test_session_001",
    "agent_name": "athena",
    "user_id": "dungpv30",
    "role": "assistant",
    "content": "Bạn đã log 8.5 giờ trong ngày hôm nay trên 3 tasks",
    "importance_score": 0.9
  }'
```

---

### 4. Lưu Entity Memory (Person → Jira Username Mapping)

```bash
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/entity/store \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person",
    "entity_id": "dung.pham",
    "entity_name": "Dũng Phạm",
    "attributes": {
      "jira_username": "dungpv30",
      "email": "dungpv30@fpt.com",
      "team": "AC-Agentic",
      "role": "Developer"
    },
    "agent_name": "athena"
  }'
```

**Expected:**
```json
{
  "status": "stored",
  "entity_id": "dung.pham"
}
```

**Use case:** Lần sau user hỏi về "Dũng Phạm", Athena không cần extract lại username!

---

### 5. Lưu Working Memory (Current Task State)

```bash
curl -X POST https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/working/store \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "athena",
    "session_id": "worklog_query_001",
    "context_type": "current_task",
    "context_data": {
      "action": "get_worklogs",
      "date": "2024-11-26",
      "employee": "Dũng Phạm",
      "jira_username": "dungpv30",
      "status": "querying_jira"
    },
    "ttl_seconds": 3600
  }'
```

**Expected:**
```json
{
  "status": "stored",
  "expires_at": "2025-11-26T08:14:26"
}
```

**Use case:** Track task đang thực hiện, tự động expire sau 1 giờ

---

### 6. Kiểm Tra Dữ Liệu Đã Lưu (PostgreSQL)

```bash
# Kiểm tra conversation_memory table
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT id, session_id, agent_name, role, LEFT(content, 50), importance_score, created_at 
   FROM conversation_memory 
   ORDER BY created_at DESC 
   LIMIT 5;"
```

```bash
# Kiểm tra entity_memory table
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT entity_type, entity_id, entity_name, attributes, mention_count, last_mentioned 
   FROM entity_memory 
   ORDER BY last_mentioned DESC 
   LIMIT 5;"
```

```bash
# Kiểm tra working_memory table
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT agent_name, session_id, context_type, context_data, expires_at 
   FROM working_memory 
   ORDER BY created_at DESC 
   LIMIT 5;"
```

---

## ✨ Complete Test Scenario

Chạy script test hoàn chỉnh:

```bash
bash /root/zeus-nexus/context-storage/test_complete.sh
```

Script này sẽ:
1. ✅ Lưu user message
2. ✅ Lưu assistant response  
3. ✅ Lưu entity mapping (Dũng Phạm → dungpv30)
4. ✅ Lưu working memory (task state)
5. 📊 Verify data trong PostgreSQL
6. 🧪 Test lần query thứ 2 (agent nên nhớ entity)

---

## 🎯 Lợi Ích Thực Tế

### Before Context Storage:
```
User: "Hôm nay Dũng Phạm log bao nhiêu giờ?"
Athena: *extract entity* "Dũng Phạm" → query Jira API → find username → query worklogs

User: "Còn hôm qua thì sao?"
Athena: *extract entity again* "Dũng Phạm" → query Jira API again → ...
```

### After Context Storage:
```
User: "Hôm nay Dũng Phạm log bao nhiêu giờ?"
Athena: 
  - Check entity memory → MISS
  - Extract entity → "Dũng Phạm" = "dungpv30"
  - Store entity
  - Query worklogs
  - Store conversation

User: "Còn hôm qua thì sao?"
Athena:
  - Load conversation history → "đang nói về Dũng Phạm"
  - Check entity memory → HIT! "Dũng Phạm" = "dungpv30"
  - Direct query worklogs (NO extraction needed!)
  - Store conversation
```

**Kết quả:**
- ⚡ **Faster:** Không cần extract entity lại
- 🎯 **Smarter:** Context-aware responses
- 💾 **Memory:** Nhớ tất cả conversations
- 🔗 **Relationships:** Track entity relationships

---

## 📊 Monitoring

### Check Service Health
```bash
curl https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/health
```

### Check Logs
```bash
oc logs -f deployment/context-storage -n ac-agentic
```

### Check Pod Status
```bash
oc get pods -l app=context-storage -n ac-agentic
```

### Database Stats
```bash
# Total conversations
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT COUNT(*) as total_conversations FROM conversation_memory;"

# Total entities
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT entity_type, COUNT(*) as count FROM entity_memory GROUP BY entity_type;"

# Conversations per agent
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT agent_name, COUNT(*) as count FROM conversation_memory GROUP BY agent_name;"
```

---

## 🚀 Next Steps

### 1. Integrate vào Athena Agent
Copy client library và sử dụng trong code:

```bash
cp /root/zeus-nexus/context-storage/client.py \
   /root/zeus-nexus/agents/athena/context_storage_client.py
```

### 2. Update Athena Code
Thêm context tracking vào worklog query function.

### 3. Test End-to-End
Query worklog 2 lần để verify entity caching hoạt động.

---

## 📞 Support

- **Service:** Context Storage v1.0.4
- **Namespace:** ac-agentic  
- **Owner:** dungpv30@fpt.com
- **Documentation:** /root/zeus-nexus/context-storage/DEPLOYMENT.md

✅ **Context Storage is LIVE and READY!**
