# 🎯 ElevenLabs Function Calling Configuration Guide

## 🚨 PROBLEM SOLVED: Agent using generic knowledge instead of RAG system

### ⚡ Quick Fix (5 minutes)

1. **Go to ElevenLabs Dashboard**
   - Visit: https://elevenlabs.io/app/conversational-ai
   - Find agent: `agent_01jxmeyxz2fh0v3cqx848qk1e0`

2. **Add Server Tool**
   - Click "Edit Agent" → "Tools" section
   - Click "Add Tool" → Select "Webhook" type
   - Configure as follows:

   ```
   Tool Type: Webhook
   Name: query_persona_knowledge
   Description: Search the persona's knowledge base for relevant information to answer user questions
   Method: POST
   URL: http://127.0.0.1:8000/elevenlabs/function-call
   
   Headers:
   X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0
   Content-Type: application/json
   
   Parameters:
   - query (string, required): The user's question or search query
   - persona_id (string, required): The persona ID to search knowledge for
   ```

3. **Update System Prompt**
   Add this to the agent's system prompt:
   ```
   You have access to a comprehensive knowledge base through the query_persona_knowledge function. 
   When users ask questions, always search your knowledge base first for relevant information. 
   Provide detailed, accurate responses with proper citations when available.
   
   Use query_persona_knowledge for ANY question that might be answered by your documents, 
   including topics about business, processes, concepts, or any subject matter.
   ```

4. **Save Changes**
   - Click "Save" to update the agent configuration

### 🧪 Test the Fix

1. **Start voice chat** with any persona
2. **Ask a specific question** about the persona's knowledge (e.g., "What is Alex Hormozi's approach to value stacks?")
3. **Expected behavior**: Agent should call the function and return knowledge-based answers with citations

### 🔧 Backend Configuration (Already Working)

Your backend is already properly configured:
- ✅ Function endpoint: `POST /elevenlabs/function-call`
- ✅ Authentication: Service token validation
- ✅ RAG integration: Returns cited responses
- ✅ Error handling: Comprehensive fallbacks

### 📋 For Production Deployment

When deploying, update the webhook URL to your production domain:
```
URL: https://your-domain.com/elevenlabs/function-call
```

### 🎯 Success Criteria

After configuration, you should see:
- Agent calls `query_persona_knowledge` function for knowledge questions
- Responses include content from uploaded documents  
- Citations are provided when available
- Fallback to generic responses only when no relevant docs found

### 🐛 Troubleshooting

**If function calling doesn't work:**
1. Check service token in backend `.env` file
2. Verify webhook URL is accessible from ElevenLabs servers
3. Check backend logs for function call attempts
4. Ensure persona has uploaded documents in knowledge base

**If agent still uses generic knowledge:**
1. Update system prompt to emphasize function usage
2. Test with very specific questions about uploaded content
3. Check if persona namespace has documents in vector database 