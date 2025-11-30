#!/bin/bash

# Integration test with Claude API
ZEUS_URL="https://zeus-core-ac-agentic.apps.prod01.fis-cloud.fpt.com"
SESSION_ID=$(uuidgen)

echo "🧪 Zeus + Context Storage Integration Test (Claude)"
echo "============================================"
echo ""
echo "📋 Test Scenario:"
echo "  1. User provides age in first message"
echo "  2. User asks general question"
echo "  3. User asks about age from first message"
echo "  4. Zeus should remember and answer correctly"
echo ""

# Message 1: Provide age
echo "1️⃣  Sending first message with age..."
RESPONSE1=$(curl -s -X POST "$ZEUS_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Xin chào! Tôi tên là Dũng, năm nay tôi 28 tuổi.\",
    \"user_id\": \"test_user\",
    \"session_id\": \"$SESSION_ID\",
    \"llm_model\": \"claude-3-5-sonnet-20241022\"
  }")

echo "   ✅ Zeus responded: "
echo "$RESPONSE1" | jq -r '.response' | head -3
echo ""

# Wait and check context storage
sleep 2
echo "2️⃣  Checking Context Storage..."
CONTEXT_CHECK=$(oc rsh -n ac-agentic deployment/context-storage curl -s "http://localhost:8085/memory/conversation/retrieve?session_id=$SESSION_ID&agent_name=zeus&limit=10")
MESSAGE_COUNT=$(echo "$CONTEXT_CHECK" | jq '. | length' 2>/dev/null || echo "0")
echo "   ✅ Found $MESSAGE_COUNT messages in context storage"

if [ "$MESSAGE_COUNT" -ge "2" ]; then
  echo "   ✅ Context storage is working! Found at least 2 messages"
else
  echo "   ❌ Expected at least 2 messages, found $MESSAGE_COUNT"
fi
echo ""

# Message 2: General chat
echo "3️⃣  Sending general message..."
RESPONSE2=$(curl -s -X POST "$ZEUS_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Bạn có thể giúp tôi ghi worklog không?\",
    \"user_id\": \"test_user\",
    \"session_id\": \"$SESSION_ID\",
    \"llm_model\": \"claude-3-5-sonnet-20241022\"
  }")

echo "   ✅ Zeus responded: "
echo "$RESPONSE2" | jq -r '.response' | head -3
echo ""

sleep 2

# Message 3: Ask about age from first message
echo "4️⃣  Testing context memory - asking about age..."
RESPONSE3=$(curl -s -X POST "$ZEUS_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Tôi bao nhiêu tuổi?\",
    \"user_id\": \"test_user\",
    \"session_id\": \"$SESSION_ID\",
    \"llm_model\": \"claude-3-5-sonnet-20241022\"
  }")

echo "   ✅ Zeus responded: "
FINAL_RESPONSE=$(echo "$RESPONSE3" | jq -r '.response')
echo "$FINAL_RESPONSE"
echo ""

# Check if Zeus remembered the age
if echo "$FINAL_RESPONSE" | grep -q "28"; then
  echo "   ✅ SUCCESS! Zeus remembered the age from first message!"
else
  echo "   ⚠️  Zeus responded but didn't mention '28' in the answer"
  echo "   This might mean context loading isn't working properly"
fi
echo ""

# Final verification
sleep 2
echo "5️⃣  Final verification in Context Storage..."
FINAL_CONTEXT=$(oc rsh -n ac-agentic deployment/context-storage curl -s "http://localhost:8085/memory/conversation/retrieve?session_id=$SESSION_ID&agent_name=zeus&limit=20")
FINAL_COUNT=$(echo "$FINAL_CONTEXT" | jq '. | length' 2>/dev/null || echo "0")

echo "   ✅ Total messages in context: $FINAL_COUNT"
echo ""

echo "📊 Test Summary"
echo "==============="
echo "   Session ID: $SESSION_ID"
echo "   Total messages exchanged: 3 (user) + 3 (Zeus) = 6"
echo "   Messages stored in Context Storage: $FINAL_COUNT"

if [ "$FINAL_COUNT" -ge "6" ]; then
  if echo "$FINAL_RESPONSE" | grep -q "28"; then
    echo "   ✅ INTEGRATION TEST PASSED!"
    echo "   Zeus is storing messages AND loading context correctly!"
  else
    echo "   ⚠️  PARTIAL SUCCESS: Messages stored but context not used in responses"
  fi
else
  echo "   ⚠️  Expected 6 messages, found $FINAL_COUNT"
  echo "   ❌ INTEGRATION TEST FAILED"
fi

echo ""
echo "🔍 Check Zeus logs with: oc logs deployment/zeus-core -n ac-agentic | grep -E '(context|Context|✅|⚠️)'"
