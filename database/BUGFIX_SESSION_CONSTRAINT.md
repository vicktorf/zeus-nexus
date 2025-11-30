## 🐛 Bug Fix: Database Constraint Error

**Lỗi**: `duplicate key value violates unique constraint conversations_session_id_key`

**Nguyên nhân**: 
- Table `conversations` có UNIQUE constraint trên column `session_id`
- Điều này ngăn không cho nhiều messages trong cùng 1 session
- Đây là sai thiết kế - mỗi session chat nên có nhiều conversations

**Giải pháp**:
```sql
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_session_id_key;
```

**Kết quả**:
✅ Chat đã hoạt động bình thường
✅ Có thể gửi nhiều messages trong cùng 1 session
✅ Model được nhận đúng (claude-3-haiku)

**Test kết quả**:
```bash
curl -X POST /chat -d '{"message": "Xin chào Zeus lần 2", "llm_model": "claude-3-haiku"}'

Response:
{
  "session_id": "00eb0bad-cce6-4a90-ae1a-d66288c74659",
  "agent": "athena",
  "response": "Hello! I'm Athena... I'm using claude-3-haiku...",
  "llm_model": "claude-3-haiku",
  "llm_provider": "anthropic"
}
```

**Migration script đã cập nhật**: `/root/zeus-nexus/database/migration_llm_support.sql`

---

**Bây giờ hãy test trên browser!** 🚀
