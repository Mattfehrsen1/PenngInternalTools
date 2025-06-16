#!/bin/bash

# 🎯 Clone Advisor - ElevenLabs Voice Integration Test Script
# This script helps you test the complete voice integration setup

echo "🎯 Clone Advisor - ElevenLabs Voice Integration Test"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check backend health
echo -e "${BLUE}Step 1: Checking backend health...${NC}"
if curl -s https://clone-api.fly.dev/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend is not responding${NC}"
    exit 1
fi

# Step 2: Test function calling endpoint
echo -e "${BLUE}Step 2: Testing function calling endpoint...${NC}"
response=$(curl -s -X POST https://clone-api.fly.dev/elevenlabs/function-call \
    -H "Content-Type: application/json" \
    -H "X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0" \
    -d '{"function_name": "query_persona_knowledge", "parameters": {"query": "test", "persona_id": "test"}}')

if echo "$response" | grep -q "success"; then
    echo -e "${GREEN}✅ Function endpoint is working${NC}"
else
    echo -e "${RED}❌ Function endpoint failed${NC}"
    echo "Response: $response"
fi

# Step 3: Check if frontend dependencies are installed
echo -e "${BLUE}Step 3: Checking frontend setup...${NC}"
if [ -d "frontend/node_modules/@elevenlabs/react" ]; then
    echo -e "${GREEN}✅ ElevenLabs React SDK is installed${NC}"
else
    echo -e "${YELLOW}⚠️  ElevenLabs React SDK not found${NC}"
    echo "Run: cd frontend && npm install"
fi

# Step 4: Display next steps
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "1. Go to: https://elevenlabs.io/app/conversational-ai"
echo "2. Create a new agent with these settings:"
echo "   - Name: Alex Hormozi Clone"
echo "   - Webhook URL: https://clone-api.fly.dev/elevenlabs/function-call"
echo "   - Service Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0"
echo "3. Copy the Agent ID and update frontend/app/test-conversational-ai/page.tsx"
echo "4. Start frontend: cd frontend && npm run dev"
echo "5. Test at: http://localhost:3001/test-conversational-ai"
echo ""
echo -e "${GREEN}📚 Full setup guide: docs/ELEVENLABS_AGENT_SETUP.md${NC}"
echo -e "${GREEN}🎯 System is ready for voice integration!${NC}" 