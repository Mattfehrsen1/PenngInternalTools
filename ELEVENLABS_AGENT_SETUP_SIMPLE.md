# 🎯 Fix ElevenLabs Agent - 5 Minute Setup

## The Problem
Your Alex Hormozi agent is using generic knowledge instead of the uploaded content. The backend is working perfectly - we just need to connect it to ElevenLabs.

## ✅ Backend Status: PERFECT
- Knowledge base has 1,272 Alex Hormozi chunks
- Webhook returns detailed content with citations
- Function tested and working: `http://localhost:8000/elevenlabs/function-call`

## 🔧 The Fix (5 minutes)

### Step 1: Open ElevenLabs Dashboard
1. Go to: https://elevenlabs.io/app/conversational-ai
2. Find your Alex Hormozi agent
3. Click "Edit Agent"

### Step 2: Add Webhook Function
1. Go to the "Tools" section
2. Click "Add Tool" → Select "Webhook"
3. Fill in these exact details:

```
Name: query_persona_knowledge
Description: Search Alex Hormozi's knowledge base for business advice
URL: http://localhost:8000/elevenlabs/function-call
Method: POST

Headers:
X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0
Content-Type: application/json

Parameters Schema:
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
          "description": "The user's question"
        },
        "persona_id": {
          "type": "string",
          "description": "Persona ID",
          "default": "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"
        }
      },
      "required": ["query", "persona_id"]
    }
  },
  "required": ["function_name", "parameters"]
}
```

### Step 3: Update System Prompt
Replace the agent's system prompt with this:

```
You are Alex Hormozi, a successful entrepreneur and business coach. You speak directly, focus on actionable advice, and help people build profitable businesses.

CRITICAL: You have access to your comprehensive knowledge base through the query_persona_knowledge function. You MUST use this function for ANY business question.

When users ask about:
- Business strategies  
- Making money
- Customer acquisition
- Offers and value
- Scaling businesses
- Any entrepreneurial topic

ALWAYS call query_persona_knowledge first, then use that information in your response.

When the function returns results:
- Use the content as the foundation of your answer
- Mention it's from your books/teachings
- Include specific details and numbers provided
- Keep responses under 200 words for voice

NEVER say you don't have information if the function returns content.
```

### Step 4: Save and Test
1. Click "Save" to update the agent
2. Test by asking: "What are the core elements of a good business offer?"
3. The agent should now call your function and return detailed answers from your uploaded content

## 🧪 Test Commands
You can test the backend directly:
```bash
curl -X POST http://localhost:8000/elevenlabs/function-call \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0" \
  -d '{"function_name": "query_persona_knowledge", "parameters": {"query": "What is a grand slam offer?", "persona_id": "cd35a4a9-31ad-44f5-9de7-cc7dc3196541"}}'
```

## ✅ Success Criteria
After setup, your agent should:
- Call the function for business questions
- Return content from Alex Hormozi's books
- Include citations and specific details
- Sound like Alex Hormozi with real knowledge

The backend is ready - just need this 5-minute ElevenLabs configuration! 