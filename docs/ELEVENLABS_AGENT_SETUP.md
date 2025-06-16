# 🎯 ElevenLabs Agent Setup Guide

## 🚀 Quick Setup (15 minutes)

This guide will walk you through setting up an ElevenLabs Conversational AI agent that integrates with your Clone Advisor RAG system.

### Step 1: Access ElevenLabs Dashboard

1. Go to [https://elevenlabs.io/app/conversational-ai](https://elevenlabs.io/app/conversational-ai)
2. Sign in with your ElevenLabs account
3. Click "Create Agent"

### Step 2: Basic Agent Configuration

Configure the agent with these settings:

```
Name: Alex Hormozi Clone
Voice: Choose from 3,000+ available voices
Language: English (US)
Model: Turbo v2.5 (recommended for speed)
```

### Step 3: System Prompt Configuration

Replace the default system prompt with this:

```
You are Alex Hormozi, a successful entrepreneur and business coach. You speak directly, focus on actionable advice, and help people build profitable businesses. Your responses should be concise, practical, and results-oriented.

You have access to a comprehensive knowledge base through the query_persona_knowledge function. When users ask questions, always search your knowledge base first for relevant information. Provide detailed, accurate responses with proper citations when available.

Use query_persona_knowledge for ANY question that might be answered by your documents, including topics about business, processes, concepts, or any subject matter.

Keep responses conversational and under 200 words for voice delivery.
```

### Step 4: Configure Webhook Function

In the "Tools" section, add a new webhook:

**Function Configuration:**
```json
{
  "name": "query_persona_knowledge",
  "description": "Search the persona's knowledge base for relevant information to answer user questions",
  "url": "https://clone-api.fly.dev/elevenlabs/function-call",
  "method": "POST",
  "headers": {
    "X-Service-Token": "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0",
    "Content-Type": "application/json"
  }
}
```

**Function Parameters:**
```json
{
  "type": "object",
  "properties": {
    "function_name": {
      "type": "string",
      "enum": ["query_persona_knowledge"]
    },
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The user's question or search query"
        },
        "persona_id": {
          "type": "string",
          "description": "The persona ID to search knowledge for",
          "default": "default"
        }
      },
      "required": ["query"]
    }
  },
  "required": ["function_name", "parameters"]
}
```

### Step 5: Advanced Settings

**Conversation Settings:**
- Response Length: Medium (100-200 words)
- Interruption Handling: Enabled
- Pause Detection: 1.5 seconds

**Voice Settings:**
- Stability: 0.8
- Similarity Boost: 0.9
- Style Exaggeration: 0.3

### Step 6: Get Your Agent ID

1. After saving the agent, copy the Agent ID from the dashboard
2. It will look like: `agent_01jxmeyxz2fh0v3cqx848qk1e0`

### Step 7: Update Frontend Code

1. Open `clone-advisor/frontend/app/test-conversational-ai/page.tsx`
2. Replace `'your-agent-id-here'` with your actual Agent ID:

```typescript
const conversationId = await conversation.startSession({
  agentId: 'agent_01jxmeyxz2fh0v3cqx848qk1e0' // Your actual agent ID
});
```

### Step 8: Test the Integration

1. Start your frontend: `cd frontend && npm run dev`
2. Go to: `http://localhost:3001/test-conversational-ai`
3. Click "Start Voice Conversation"
4. Allow microphone access
5. Speak: "What is Alex Hormozi's approach to building businesses?"
6. The agent should:
   - Call your webhook function
   - Search the knowledge base
   - Respond with voice including citations

## 🔧 Webhook Testing

You can test the webhook directly:

```bash
curl -X POST https://clone-api.fly.dev/elevenlabs/function-call \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0" \
  -d '{
    "function_name": "query_persona_knowledge",
    "parameters": {
      "query": "What is value stacking?",
      "persona_id": "default"
    }
  }'
```

Expected response:
```json
{
  "result": {
    "content": "According to source 1: Value stacking is...",
    "citations": [...],
    "persona_name": "Alex Hormozi"
  },
  "success": true
}
```

## 🚨 Troubleshooting

### Common Issues:

1. **"Agent not found" error**
   - Double-check the Agent ID is correct
   - Ensure the agent is published, not in draft mode

2. **Webhook not being called**
   - Verify the webhook URL is accessible
   - Check the service token is correct
   - Ensure function parameters match exactly

3. **Function calls fail**
   - Check backend logs for errors
   - Verify the persona has documents in the knowledge base
   - Test the webhook endpoint directly

4. **Voice not working**
   - Ensure microphone permissions are granted
   - Check browser console for WebRTC errors
   - Try a different browser or device

### Debug Steps:

1. **Check webhook accessibility:**
   ```bash
   curl https://clone-api.fly.dev/health
   ```

2. **Verify function endpoint:**
   ```bash
   curl -X POST https://clone-api.fly.dev/elevenlabs/function-call \
     -H "X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0" \
     -H "Content-Type: application/json" \
     -d '{"function_name": "query_persona_knowledge", "parameters": {"query": "test", "persona_id": "test"}}'
   ```

3. **Check browser console:**
   - Open DevTools → Console
   - Start conversation and look for errors
   - Check Network tab for failed requests

## 🎯 Success Criteria

After setup, you should have:
- ✅ Agent responds to voice input
- ✅ Agent calls webhook for knowledge questions
- ✅ Agent provides cited responses from your knowledge base
- ✅ Conversation flows naturally with <500ms latency
- ✅ Voice quality is clear and natural

## 📞 Next Steps

Once the basic integration is working:

1. **Create Multiple Personas**: Set up agents for different personas with their own knowledge bases
2. **Production Deployment**: Test with production data and real user scenarios
3. **Performance Optimization**: Monitor latency and optimize for your use case
4. **Phone Integration**: Add Twilio integration for phone-based conversations

## 🎉 You're Done!

Your Clone Advisor now has true conversational AI capabilities with voice-to-voice interaction while preserving your existing RAG investment. Users can literally talk to Alex Hormozi and get responses backed by your knowledge base! 