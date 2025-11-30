#!/bin/bash

# Test Zeus Integration với Context Storage
# Test THỰC SỰ qua Zeus API (không phải direct API)

ZEUS_URL="http://zeus-core.ac-agentic.svc.cluster.local:8000"
CONTEXT_URL="https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com"
SESSION="zeus_integration_$(date +%s)"

echo "🧪 Zeus Integration Test - End-to-End with Context Storage"
echo "============================================================"
echo ""
echo "⚠️  IMPORTANT: This test requires Zeus Core to be integrated with Context Storage"
echo "    Currently Zeus Core does NOT have context integration yet!"
echo ""
echo "📋 Test Plan:"
echo "  1. Check if Zeus Core is running"
echo "  2. Send chat message to Zeus"
echo "  3. Check if Zeus stored conversation in Context Storage"
echo "  4. Send follow-up message"
echo "  5. Verify Zeus loaded previous context"
echo ""

# Step 1: Check Zeus Core
echo "1️⃣ Checking Zeus Core availability..."
ZEUS_HEALTH=$(curl -s $ZEUS_URL/health 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✅ Zeus Core is running"
    echo "$ZEUS_HEALTH" | jq '.' 2>/dev/null || echo "$ZEUS_HEALTH"
else
    echo "   ❌ Zeus Core is NOT accessible at $ZEUS_URL"
    echo "   Error: $ZEUS_HEALTH"
    echo ""
    echo "   🔧 To fix:"
    echo "      oc get pods -l app=zeus-core"
    echo "      oc port-forward svc/zeus-core 8000:8000"
    exit 1
fi
echo ""

# Step 2: Send first message to Zeus
echo "2️⃣ Sending first message to Zeus: 'Tôi tên Dũng, 28 tuổi'..."
ZEUS_RESPONSE=$(curl -s -X POST $ZEUS_URL/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Xin chào! Tôi tên là Dũng, năm nay tôi 28 tuổi.\",
    \"session_id\": \"$SESSION\",
    \"user_id\": \"test_user\",
    \"context\": {}
  }")

if [ $? -eq 0 ]; then
    echo "   ✅ Zeus responded"
    echo "$ZEUS_RESPONSE" | jq -r '.response' 2>/dev/null || echo "$ZEUS_RESPONSE"
else
    echo "   ❌ Zeus did not respond"
fi
echo ""

# Step 3: Check if Zeus stored conversation in Context Storage
echo "3️⃣ Checking if Zeus stored conversation in Context Storage..."
sleep 2

# Check conversation memory
oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
  "SELECT COUNT(*) as count FROM conversation_memory WHERE session_id = '$SESSION';" 2>/dev/null | grep -E "[0-9]+" | tail -1 | xargs

CONV_COUNT=$(oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -t -c \
  "SELECT COUNT(*) FROM conversation_memory WHERE session_id = '$SESSION';" 2>/dev/null | xargs)

if [ "$CONV_COUNT" -gt 0 ]; then
    echo "   ✅ Found $CONV_COUNT messages in Context Storage"
    echo ""
    echo "   Messages:"
    oc exec postgresql-7f5c4d7f5-hvt7x -- psql -U zeus -d zeus -c \
      "SELECT message_role, LEFT(content, 60) as content FROM conversation_memory 
       WHERE session_id = '$SESSION' ORDER BY created_at;" 2>/dev/null
else
    echo "   ❌ No messages found in Context Storage"
    echo ""
    echo "   ⚠️  This means Zeus is NOT integrated with Context Storage yet!"
    echo ""
    echo "   🔧 To integrate:"
    echo "      1. Copy context_storage_client.py to Zeus Core"
    echo "      2. Update /chat endpoint to store/load context"
    echo "      3. Redeploy Zeus Core"
fi
echo ""

# Step 4: Send follow-up message
echo "4️⃣ Sending follow-up message: 'Tôi bao nhiêu tuổi?'..."
ZEUS_RESPONSE2=$(curl -s -X POST $ZEUS_URL/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Nhân tiện, tôi bao nhiêu tuổi nhỉ?\",
    \"session_id\": \"$SESSION\",
    \"user_id\": \"test_user\",
    \"context\": {}
  }")

if [ $? -eq 0 ]; then
    echo "   ✅ Zeus responded"
    RESPONSE_TEXT=$(echo "$ZEUS_RESPONSE2" | jq -r '.response' 2>/dev/null)
    echo "   Response: $RESPONSE_TEXT"
    echo ""
    
    # Check if Zeus used context
    if echo "$RESPONSE_TEXT" | grep -qi "28"; then
        echo "   ✅ Zeus remembered the age (28)!"
        echo "   ✅ CONTEXT INTEGRATION IS WORKING!"
    else
        echo "   ❌ Zeus did NOT remember the age"
        echo "   ❌ CONTEXT INTEGRATION IS NOT WORKING"
        echo ""
        echo "   Expected: Zeus should say '28 tuổi'"
        echo "   Got: $RESPONSE_TEXT"
    fi
else
    echo "   ❌ Zeus did not respond"
fi
echo ""

# Summary
echo "=========================================="
echo "📊 INTEGRATION TEST SUMMARY"
echo "=========================================="
echo ""
echo "Session: $SESSION"
echo ""

if [ "$CONV_COUNT" -gt 0 ]; then
    echo "✅ Zeus Core → Context Storage: INTEGRATED"
    echo ""
    echo "Next steps:"
    echo "  1. ✅ Context Storage is working"
    echo "  2. ✅ Zeus is storing conversations"
    echo "  3. 📝 Verify Zeus loads context before responding"
else
    echo "❌ Zeus Core → Context Storage: NOT INTEGRATED"
    echo ""
    echo "Next steps:"
    echo "  1. Copy context_storage_client.py to Zeus Core"
    echo "  2. Update chat endpoint to use Context Storage"
    echo "  3. Test again with this script"
    echo ""
    echo "📖 Integration Guide:"
    echo "   See: /root/zeus-nexus/context-storage/DEPLOYMENT.md"
    echo "   Section: 'Integration with Zeus & Athena'"
fi
