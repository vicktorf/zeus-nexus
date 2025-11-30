#!/bin/bash

BASE_URL="https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com"
SESSION="demo_$(date +%s)"

echo "🧪 Context Storage - Complete Test Suite"
echo "=========================================="
echo "Session ID: $SESSION"
echo ""

# Test 1: Store User Message
echo "1️⃣ Lưu user message..."
RESPONSE=$(curl -s -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"role\": \"user\",
    \"content\": \"Hôm nay Dũng Phạm log bao nhiêu giờ?\",
    \"importance_score\": 0.8
  }")
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | grep -q "stored"; then
    echo "✅ User message stored successfully"
else
    echo "❌ Failed to store user message"
fi
echo ""

# Test 2: Store Assistant Response
echo "2️⃣ Lưu assistant response..."
RESPONSE=$(curl -s -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"role\": \"assistant\",
    \"content\": \"Dũng Phạm (dungpv30) đã log 8.5 giờ ngày 26/11/2024: AC-1234 (4h), AC-1235 (4.5h)\",
    \"metadata\": {\"total_hours\": 8.5, \"tasks\": [\"AC-1234\", \"AC-1235\"]},
    \"importance_score\": 0.9
  }")
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | grep -q "stored"; then
    echo "✅ Assistant response stored successfully"
else
    echo "❌ Failed to store assistant response"
fi
echo ""

# Test 3: Store Entity
echo "3️⃣ Lưu entity (person mapping: Dũng Phạm → dungpv30)..."
RESPONSE=$(curl -s -X POST $BASE_URL/memory/entity/store \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person",
    "entity_id": "dung.pham",
    "entity_name": "Dũng Phạm",
    "attributes": {
      "jira_username": "dungpv30",
      "email": "dungpv30@fpt.com",
      "team": "AC-Agentic",
      "role": "Developer",
      "discovered_from": "worklog_query"
    },
    "agent_name": "athena"
  }')
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | grep -q "stored"; then
    echo "✅ Entity stored successfully"
else
    echo "❌ Failed to store entity"
fi
echo ""

# Test 4: Store Working Memory
echo "4️⃣ Lưu working memory (task state)..."
RESPONSE=$(curl -s -X POST $BASE_URL/memory/working/store \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"athena\",
    \"session_id\": \"$SESSION\",
    \"context_type\": \"worklog_query\",
    \"context_data\": {
      \"action\": \"get_worklogs\",
      \"date\": \"2024-11-26\",
      \"employee_name\": \"Dũng Phạm\",
      \"jira_username\": \"dungpv30\",
      \"status\": \"completed\",
      \"total_hours\": 8.5
    },
    \"ttl_seconds\": 3600
  }")
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | grep -q "stored"; then
    echo "✅ Working memory stored successfully"
else
    echo "❌ Failed to store working memory"
fi
echo ""

# Test 5: Store Second User Message (Context-Aware)
echo "5️⃣ Lưu user message thứ 2 (context-aware query)..."
RESPONSE=$(curl -s -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"role\": \"user\",
    \"content\": \"Còn hôm qua thì sao?\",
    \"importance_score\": 0.7
  }")
echo "$RESPONSE" | jq '.'

if echo "$RESPONSE" | grep -q "stored"; then
    echo "✅ Second user message stored successfully"
else
    echo "❌ Failed to store second user message"
fi
echo ""

# Test 6: Verify in Database
echo "📊 Verifying data in PostgreSQL..."
echo ""

echo "6️⃣ Conversation Memory:"
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT id, session_id, agent_name, message_role, LEFT(content, 60) as content, importance_score 
   FROM conversation_memory 
   WHERE session_id = '$SESSION'
   ORDER BY created_at ASC;" 2>/dev/null
echo ""

echo "7️⃣ Entity Memory:"
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT entity_type, entity_id, entity_name, attributes->>'jira_username' as jira_username, 
          mention_count, importance 
   FROM entity_memory 
   WHERE entity_id = 'dung.pham'
   ORDER BY last_mentioned DESC 
   LIMIT 1;" 2>/dev/null
echo ""

echo "8️⃣ Working Memory:"
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT agent_name, session_id, context_type, 
          context_data->>'employee_name' as employee,
          context_data->>'total_hours' as hours,
          expires_at
   FROM working_memory 
   WHERE session_id = '$SESSION'
   ORDER BY created_at DESC 
   LIMIT 1;" 2>/dev/null
echo ""

# Summary
echo "=============================================="
echo "✅ Test Suite Complete!"
echo ""
echo "📌 Summary:"
echo "  - Session ID: $SESSION"
echo "  - Total Messages: 3 (1 user, 1 assistant, 1 follow-up)"
echo "  - Entity Stored: Dũng Phạm → dungpv30"
echo "  - Working Memory: Task state cached"
echo ""
echo "🎯 Next time user asks about 'Dũng Phạm':"
echo "  → Athena can directly use 'dungpv30' from entity memory"
echo "  → No need to extract/search Jira username again"
echo "  → FASTER + SMARTER responses!"
echo ""
echo "📖 View full guide: /root/zeus-nexus/context-storage/TEST_GUIDE.md"
