#!/bin/bash

# Test Context Storage với Athena Worklog Query
# Scenario: User hỏi về worklog, Athena nhớ mapping name -> Jira username

BASE_URL="https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com"
SESSION_ID="test_athena_$(date +%s)"

echo "🧪 Testing Context Storage for Athena Agent"
echo "=============================================="
echo ""

# Step 1: User asks about worklog (first time)
echo "📝 Step 1: User hỏi worklog lần đầu..."
curl -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"message_role\": \"user\",
    \"content\": \"Hôm nay Dũng Phạm log bao nhiêu giờ?\",
    \"importance_score\": 0.7
  }" -s | jq '.'
echo ""

# Step 2: Athena extracts entity and saves mapping
echo "📝 Step 2: Athena lưu entity mapping (Dũng Phạm -> dungpv30)..."
curl -X POST $BASE_URL/memory/entity/store \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person",
    "entity_id": "dung.pham",
    "entity_name": "Dũng Phạm",
    "attributes": {
      "jira_username": "dungpv30",
      "discovered_from": "worklog_query",
      "confidence": 0.95
    },
    "agent_name": "athena"
  }' -s | jq '.'
echo ""

# Step 3: Save working memory (current task)
echo "📝 Step 3: Lưu working memory (task đang thực hiện)..."
curl -X POST $BASE_URL/memory/working/store \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"athena\",
    \"session_id\": \"$SESSION_ID\",
    \"context_type\": \"current_query\",
    \"context_data\": {
      \"action\": \"get_worklogs\",
      \"date\": \"2024-11-26\",
      \"employee_name\": \"Dũng Phạm\",
      \"jira_username\": \"dungpv30\",
      \"status\": \"querying\"
    },
    \"ttl\": 3600
  }" -s | jq '.'
echo ""

# Step 4: Athena responds
echo "📝 Step 4: Athena trả lời..."
curl -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"message_role\": \"assistant\",
    \"content\": \"Dũng Phạm (dungpv30) đã log 8.5 giờ ngày 26/11/2024: AC-1234 (4h), AC-1235 (4.5h)\",
    \"metadata\": {\"total_hours\": 8.5, \"tasks\": [\"AC-1234\", \"AC-1235\"]},
    \"importance_score\": 0.9
  }" -s | jq '.'
echo ""

# Step 5: Second query - Athena should remember the mapping
echo "📝 Step 5: User hỏi lại (lần 2) - Test nếu Athena nhớ..."
sleep 2
curl -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"message_role\": \"user\",
    \"content\": \"Còn hôm qua thì sao?\",
    \"importance_score\": 0.7
  }" -s | jq '.'
echo ""

# Step 6: Load conversation history
echo "📊 Step 6: Load conversation history (kiểm tra context)..."
curl -s "$BASE_URL/memory/conversation/get/$SESSION_ID?limit=10&agent_name=athena" | jq '.'
echo ""

# Step 7: Check entity memory
echo "📊 Step 7: Kiểm tra entity memory (mapping đã lưu chưa)..."
curl -s "$BASE_URL/memory/entity/get/person/dung.pham?agent_name=athena" | jq '.'
echo ""

# Step 8: Check working memory
echo "📊 Step 8: Kiểm tra working memory (task context)..."
curl -s "$BASE_URL/memory/working/get/athena/$SESSION_ID/current_query" | jq '.'
echo ""

echo "✅ Test hoàn tất!"
echo ""
echo "📌 Key Points:"
echo "  - Conversation history: Lưu cả câu hỏi và câu trả lời"
echo "  - Entity memory: Nhớ mapping 'Dũng Phạm' -> 'dungpv30'"
echo "  - Working memory: Track task đang thực hiện"
echo "  - Lần query tiếp theo không cần extract lại entity!"
