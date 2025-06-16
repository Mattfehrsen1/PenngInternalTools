# ElevenLabs Conversational AI Integration Guide

## 🎯 Overview

This guide shows how to integrate ElevenLabs Conversational AI with Clone Advisor to get **true conversational AI** (speech-to-speech) working with your existing RAG system.

## ✅ RAG Integration Confirmed!

**YES, you can still use RAG!** ElevenLabs provides multiple ways to integrate your knowledge base:

1. **Built-in Knowledge Base** - Upload documents directly to ElevenLabs
2. **Function Calling** - Keep your existing RAG system and call it via functions
3. **Custom LLM** - Bring your own LLM server with RAG built-in

## 🚀 Quick Setup (15 minutes)

### Step 1: Sign Up for ElevenLabs
1. Go to [https://elevenlabs.io/conversational-ai](https://elevenlabs.io/conversational-ai)
2. Sign up (free tier includes 15,000 minutes)
3. Navigate to the Conversational AI dashboard

### Step 2: Create Your First Agent
1. Click "Create Agent" in the dashboard
2. Configure basic settings:
   ```
   Name: Alex Hormozi Clone
   Voice: Select from 3,000+ voices (or clone your own)
   Language: English
   ```

### Step 3: Configure Agent Prompt
Set up your system prompt (same as your current persona prompts):
```
You are Alex Hormozi, a successful entrepreneur and business coach. 
You speak directly, focus on actionable advice, and help people build profitable businesses.
Your responses should be concise, practical, and results-oriented.

When you need specific information, use the search_knowledge_base function.
```

### Step 4: Add Function Calling for RAG
In the agent configuration, add this function:
```json
{
  "name": "search_knowledge_base",
  "description": "Search the knowledge base for specific information about business, entrepreneurship, or Alex Hormozi's teachings",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query"
      },
      "persona_id": {
        "type": "string", 
        "description": "The persona ID to search within"
      }
    },
    "required": ["query", "persona_id"]
  }
}
```

### Step 5: Get Your Agent ID
1. Copy the Agent ID from the dashboard
2. Replace `'your-agent-id-here'` in the test page

### Step 6: Test the Integration
1. Start your Clone Advisor backend: `cd backend && source venv310/bin/activate && uvicorn main:app --reload --port 8000`
2. Start your frontend: `cd frontend && npm run dev`
3. Go to `http://localhost:3001/test-conversational-ai`
4. Click "Start Voice Conversation" and speak!

## 🔧 Integration Options

### Option 1: Built-in Knowledge Base (Easiest)
- Upload your documents directly to ElevenLabs
- They handle chunking, embeddings, and retrieval
- No code changes needed

### Option 2: Function Calling (Recommended)
- Keep your existing Pinecone + RAG system
- Agent calls your `/api/chat` endpoint when it needs knowledge
- Full control over retrieval and citations

### Option 3: Custom LLM Server
- Bring your own server with RAG built-in
- ElevenLabs handles only speech-to-text and text-to-speech
- Maximum control and customization

## 📋 Integration with Clone Advisor

### Current Architecture:
```
User → Text Input → Your Chat API → OpenAI + RAG → Text Response → User
```

### New Architecture with ElevenLabs:
```
User → Voice Input → ElevenLabs Agent → Function Call → Your RAG API → Voice Response → User
```

### Code Integration:
```typescript
// Replace your voice streaming with:
import { useConversation } from '@elevenlabs/react';

const conversation = useConversation({
  onFunctionCall: async (functionCall) => {
    if (functionCall.name === 'search_knowledge_base') {
      // Call your existing RAG system
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: functionCall.parameters.query,
          persona_id: functionCall.parameters.persona_id,
          use_rag: true
        })
      });
      
      const result = await response.json();
      return {
        result: result.response,
        citations: result.citations
      };
    }
  }
});
```

## 💰 Cost Comparison

### Current Approach (Building Custom):
- Development time: 2-3 months
- Engineer cost: $50k-100k+
- Infrastructure: $500-2000/month ongoing

### ElevenLabs Approach:
- Setup time: 2-3 days
- Cost: $0.08/minute (includes LLM + STT + TTS)
- 15,000 free minutes to start

## 🎯 Success Metrics

After integration, you should have:
- **Real conversational AI** (speak and get voice responses)
- **<500ms latency** for natural conversation flow
- **Your existing RAG system** still working
- **Persona-specific voices** for each clone
- **Phone calling capabilities** (via Twilio integration)

## 🚨 Important Notes

1. **Keep Your Current System**: ElevenLabs can complement your existing chat interface
2. **Gradual Migration**: Start with one persona, expand gradually
3. **Data Privacy**: Conversations are processed by ElevenLabs
4. **API Limits**: Monitor usage and upgrade plans as needed

## 🔄 Migration Strategy

### Phase 1: Proof of Concept (This Week)
- Set up one agent (Alex Hormozi)
- Test basic conversation flow
- Verify RAG integration works

### Phase 2: Full Integration (Next Week)
- Create agents for all personas
- Wire into existing chat interface
- Add voice toggles to current UI

### Phase 3: Enhanced Features (Following Week)
- Phone calling integration
- Advanced voice settings
- Performance optimization

## 🆘 Troubleshooting

### Common Issues:
1. **Microphone Permission**: Ensure browser allows microphone access
2. **Agent ID**: Double-check the agent ID from ElevenLabs dashboard
3. **CORS Issues**: May need to proxy requests through your backend
4. **Rate Limits**: Monitor usage in ElevenLabs dashboard

### Getting Help:
- ElevenLabs Documentation: [https://elevenlabs.io/docs](https://elevenlabs.io/docs)
- Discord Community: Available in their docs
- Support: Contact through their platform

## 🎉 Expected Outcome

With ElevenLabs integration, Clone Advisor will transform from a text-based chat system to a **true conversational AI platform** where users can have natural voice conversations with your AI clones, complete with persona-specific voices and access to their knowledge bases.

**This is exactly what you envisioned - talking to Alex Hormozi like he's right there!** 🗣️ 