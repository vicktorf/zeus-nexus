#!/bin/bash

# Test if Zeus can successfully load conversation history from Context Storage

SESSION_ID="27ca872d-1e63-4512-8b3f-28bf26b8f445"

echo "🔍 Diagnosing Context Loading Issue"
echo "===================================="
echo ""

echo "1️⃣  Checking Context Storage directly..."
CONTEXT_DATA=$(curl -s -G "https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com/memory/conversation/retrieve" \
  --data-urlencode "session_id=$SESSION_ID" \
  --data-urlencode "agent_name=zeus" \
  --data-urlencode "limit=10")

COUNT=$(echo "$CONTEXT_DATA" | jq '.total')
echo "   Found $COUNT messages in Context Storage"

if [ "$COUNT" -gt 0 ]; then
    echo "   ✅ Context Storage has data"
    echo "   First message: $(echo "$CONTEXT_DATA" | jq -r '.conversations[-1].content[:80]')"
else
    echo "   ❌ Context Storage has no data"
    exit 1
fi

echo ""
echo "2️⃣  Checking Zeus logs for context loading..."
LOGS=$(oc logs deployment/zeus-core -n ac-agentic --tail=200 2>&1)

if echo "$LOGS" | grep -q "📚 Loaded"; then
    echo "   ✅ Zeus IS loading context"
    echo "$LOGS" | grep "📚 Loaded" | tail -5
else
    echo "   ❌ Zeus is NOT loading context (no '📚 Loaded' messages)"
fi

if echo "$LOGS" | grep -q "⚠️ Failed to load context"; then
    echo "   ⚠️  Found context loading errors:"
    echo "$LOGS" | grep "⚠️ Failed to load context" | tail -5
fi

echo ""
echo "3️⃣  Analysis:"
if echo "$LOGS" | grep -q "📚 Loaded"; then
    echo "   Context loading code IS being executed"
    echo "   Problem: Zeus not using loaded context in LLM call"
else
    echo "   Context loading code is NOT being executed"
    echo "   Possible causes:"
    echo "   - Code path not reaching context loading section"
    echo "   - Silent exception in context loading try block"
    echo "   - Client library issue"
fi

echo ""
echo "4️⃣  Checking which code path is being used..."
if echo "$LOGS" | grep -q "$SESSION_ID"; then
    echo "   Session found in logs:"
    echo "$LOGS" | grep "$SESSION_ID" | head -3
fi
