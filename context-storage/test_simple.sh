#!/bin/bash

BASE_URL="https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com"
SESSION="test_$(date +%s)"

echo "🧪 Test Context Storage - Simple Version"
echo "========================================"
echo ""

# Test 1: Store conversation
echo "1️⃣ Lưu user message..."
curl -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"role\": \"user\",
    \"content\": \"Hôm nay tôi log bao nhiêu giờ?\",
    \"importance_score\": 0.8
  }" | jq '.'
echo ""

# Test 2: Store assistant response
echo "2️⃣ Lưu assistant response..."
curl -X POST $BASE_URL/memory/conversation/store \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION\",
    \"agent_name\": \"athena\",
    \"user_id\": \"dungpv30\",
    \"role\": \"assistant\",
    \"content\": \"Bạn đã log 8.5 giờ hôm nay\",
    \"importance_score\": 0.9
  }" | jq '.'
echo ""

# Test 3: Get conversation history
echo "3️⃣ Lấy lại conversation history..."
curl -s "$BASE_URL/memory/conversation/get/$SESSION?limit=10" | jq '.'
echo ""

# Test 4: Store entity
echo "4️⃣ Lưu entity (person mapping)..."
curl -X POST $BASE_URL/memory/entity/store \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "person",
    "entity_id": "dungpv30",
    "entity_name": "Dũng Phạm",
    "attributes": {
      "jira_username": "dungpv30",
      "team": "AC-Agentic"
    },
    "agent_name": "athena"
  }' | jq '.'
echo ""

# Test 5: Get entity
echo "5️⃣ Lấy lại entity..."
curl -s "$BASE_URL/memory/entity/get/person/dungpv30?agent_name=athena" | jq '.'
echo ""

# Test 6: Store working memory
echo "6️⃣ Lưu working memory (task context)..."
curl -X POST $BASE_URL/memory/working/store \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_name\": \"athena\",
    \"session_id\": \"$SESSION\",
    \"context_type\": \"current_task\",
    \"context_data\": {
      \"action\": \"worklog_query\",
      \"status\": \"processing\"
    },
    \"ttl_seconds\": 3600
  }" | jq '.'
echo ""

# Test 7: Get working memory
echo "7️⃣ Lấy lại working memory..."
curl -s "$BASE_URL/memory/working/get/athena/$SESSION/current_task" | jq '.'
echo ""

# Test 8: Short-term memory (Redis)
echo "8️⃣ Lưu short-term memory..."
curl -X POST $BASE_URL/memory/short-term/store \
  -H "Content-Type: application/json" \
  -d "{
    \"key\": \"session_$SESSION\",
    \"value\": {\"last_query\": \"worklog\", \"timestamp\": \"$(date -Iseconds)\"},
    \"ttl_seconds\": 1800
  }" | jq '.'
echo ""

# Test 9: Get short-term memory
echo "9️⃣ Lấy lại short-term memory..."
curl -s "$BASE_URL/memory/short-term/get/session_$SESSION" | jq '.'
echo ""

echo "✅ Test hoàn tất! Session ID: $SESSION"
