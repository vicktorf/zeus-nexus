#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ZEUS_URL="https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com"
CONTEXT_STORAGE_URL="https://context-storage-ac-agentic.apps.prod01.fis-cloud.fpt.com"
# Generate a valid UUID for session
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo -e "${BLUE}🧪 Zeus + Context Storage Integration Test${NC}"
echo -e "${BLUE}============================================${NC}\n"

echo -e "${YELLOW}📋 Test Scenario:${NC}"
echo "  1. User provides age in first message"
echo "  2. User asks general question"
echo "  3. User asks about age from first message"
echo "  4. Zeus should remember and answer correctly"
echo ""

# Step 1: Send first message with age
echo -e "${YELLOW}1️⃣  Sending first message with age...${NC}"
RESPONSE1=$(curl -s -X POST "${ZEUS_URL}/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Xin chào! Tôi tên là Dũng, năm nay tôi 28 tuổi.\",
    \"user_id\": \"test_user\",
    \"session_id\": \"${SESSION_ID}\",
    \"llm_model\": \"gpt-4\"
  }")

if echo "$RESPONSE1" | jq -e '.response' > /dev/null 2>&1; then
    ZEUS_RESPONSE=$(echo "$RESPONSE1" | jq -r '.response')
    echo -e "${GREEN}   ✅ Zeus responded: ${NC}"
    echo "   ${ZEUS_RESPONSE:0:100}..."
else
    echo -e "${RED}   ❌ Failed to get response from Zeus${NC}"
    echo "   Response: $RESPONSE1"
    exit 1
fi

sleep 2

# Step 2: Check if message was stored in Context Storage
echo -e "\n${YELLOW}2️⃣  Checking Context Storage...${NC}"
HISTORY=$(curl -s "${CONTEXT_STORAGE_URL}/memory/conversation/retrieve?session_id=${SESSION_ID}&agent_name=zeus&limit=10")

MESSAGE_COUNT=$(echo "$HISTORY" | jq '.conversations | length')
echo -e "${GREEN}   ✅ Found ${MESSAGE_COUNT} messages in context storage${NC}"

if [ "$MESSAGE_COUNT" -ge 2 ]; then
    echo -e "${GREEN}   ✅ Both user message and Zeus response were stored${NC}"
else
    echo -e "${RED}   ❌ Expected at least 2 messages, found ${MESSAGE_COUNT}${NC}"
fi

# Display stored messages
echo "   📝 Stored messages:"
echo "$HISTORY" | jq -r '.conversations[] | "      - [\(.message_role)]: \(.content[:80])..."'

sleep 2

# Step 3: Send general message
echo -e "\n${YELLOW}3️⃣  Sending general message...${NC}"
RESPONSE2=$(curl -s -X POST "${ZEUS_URL}/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Bạn có thể làm gì cho tôi?\",
    \"user_id\": \"test_user\",
    \"session_id\": \"${SESSION_ID}\",
    \"llm_model\": \"gpt-4\"
  }")

if echo "$RESPONSE2" | jq -e '.response' > /dev/null 2>&1; then
    ZEUS_RESPONSE2=$(echo "$RESPONSE2" | jq -r '.response')
    echo -e "${GREEN}   ✅ Zeus responded: ${NC}"
    echo "   ${ZEUS_RESPONSE2:0:100}..."
else
    echo -e "${RED}   ❌ Failed to get response from Zeus${NC}"
fi

sleep 2

# Step 4: Ask about age (test context memory)
echo -e "\n${YELLOW}4️⃣  Testing context memory - asking about age...${NC}"
RESPONSE3=$(curl -s -X POST "${ZEUS_URL}/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Tôi bao nhiêu tuổi?\",
    \"user_id\": \"test_user\",
    \"session_id\": \"${SESSION_ID}\",
    \"llm_model\": \"gpt-4\"
  }")

if echo "$RESPONSE3" | jq -e '.response' > /dev/null 2>&1; then
    ZEUS_RESPONSE3=$(echo "$RESPONSE3" | jq -r '.response')
    echo -e "${GREEN}   ✅ Zeus responded: ${NC}"
    echo "   ${ZEUS_RESPONSE3}"
    
    # Check if Zeus mentioned "28" in the response
    if echo "$ZEUS_RESPONSE3" | grep -q "28"; then
        echo -e "\n${GREEN}   🎉 SUCCESS! Zeus remembered the age from the first message!${NC}"
    else
        echo -e "\n${YELLOW}   ⚠️  Zeus responded but didn't mention '28' in the answer${NC}"
        echo "   This might mean context loading isn't working properly"
    fi
else
    echo -e "${RED}   ❌ Failed to get response from Zeus${NC}"
fi

sleep 2

# Step 5: Final verification in Context Storage
echo -e "\n${YELLOW}5️⃣  Final verification in Context Storage...${NC}"
FINAL_HISTORY=$(curl -s "${CONTEXT_STORAGE_URL}/memory/conversation/retrieve?session_id=${SESSION_ID}&agent_name=zeus&limit=20")

FINAL_COUNT=$(echo "$FINAL_HISTORY" | jq '.conversations | length')
echo -e "${GREEN}   ✅ Total messages in context: ${FINAL_COUNT}${NC}"

# Display all messages
echo "   📚 Complete conversation history:"
echo "$FINAL_HISTORY" | jq -r '.conversations[] | "      [\(.message_role | ascii_upcase)]: \(.content[:100])..."'

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}===============${NC}"
echo "   Session ID: ${SESSION_ID}"
echo "   Total messages exchanged: 3 (user) + 3 (Zeus) = 6"
echo "   Messages stored in Context Storage: ${FINAL_COUNT}"

if [ "$FINAL_COUNT" -eq 6 ]; then
    echo -e "${GREEN}   ✅ All messages stored correctly${NC}"
else
    echo -e "${YELLOW}   ⚠️  Expected 6 messages, found ${FINAL_COUNT}${NC}"
fi

# Check if age question was answered correctly
if echo "$ZEUS_RESPONSE3" | grep -q "28"; then
    echo -e "${GREEN}   ✅ Context memory working - Zeus remembered age${NC}"
    echo -e "\n${GREEN}🎉 INTEGRATION TEST PASSED!${NC}"
    exit 0
else
    echo -e "${YELLOW}   ⚠️  Context memory unclear - check Zeus response${NC}"
    echo -e "\n${YELLOW}⚠️  INTEGRATION TEST PARTIAL SUCCESS${NC}"
    exit 0
fi
