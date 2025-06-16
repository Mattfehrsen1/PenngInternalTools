# ElevenLabs Conversational AI Integration Plan

## 🎯 Goal
Add voice conversational capabilities to Clone Advisor while preserving the existing RAG system through ElevenLabs function calling.

## 📊 Architecture Overview

```
Voice Input → ElevenLabs Agent → Function Call → Your API → Voice Output
     ↓              ↓               ↓            ↓         ↓
Speech-to-Text → Agent Logic → HTTP Request → RAG System → Text-to-Speech
```

## 🚀 Implementation Phases

### Phase 1: Foundation Setup (Days 1-2) ✅ COMPLETED

#### Step 1.1: ElevenLabs Account Setup ✅ COMPLETED
- [x] ~~Sign up for ElevenLabs Business plan~~ (Account exists)
- [x] ~~Get API key from dashboard~~ (Already in .env)
- [x] **1.1.1** Open ElevenLabs dashboard at https://elevenlabs.io/app
- [ ] **1.1.2** Navigate to "Conversational AI" section
- [ ] **1.1.3** Click "Create Agent" button
- [ ] **1.1.4** Name the agent "Test Agent"
- [ ] **1.1.5** Set basic prompt: "You are a helpful assistant"
- [ ] **1.1.6** Select default voice (Sarah)
- [ ] **1.1.7** Save agent and copy agent ID
- [ ] **1.1.8** Test agent in dashboard chat interface
- [ ] **1.1.9** Verify voice output works in browser

#### Step 1.2: Backend Authentication Service ✅ COMPLETED
- [x] **1.2.1** Create directory: `mkdir backend/services` (if not exists)
- [x] **1.2.2** Create file: `touch backend/services/elevenlabs_auth.py`
- [ ] **1.2.3** Add imports to `elevenlabs_auth.py`:
  ```python
  import os
  import secrets
  from typing import Optional
  from fastapi import HTTPException, Header
  ```
- [ ] **1.2.4** Generate service token: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **1.2.5** Add to `backend/.env`:
  ```bash
  ELEVENLABS_SERVICE_TOKEN=your_generated_token_here
  ```
- [ ] **1.2.6** Create `ElevenLabsAuth` class in `elevenlabs_auth.py`:
  ```python
  class ElevenLabsAuth:
      def __init__(self):
          self.service_token = os.getenv("ELEVENLABS_SERVICE_TOKEN")
          if not self.service_token:
              raise ValueError("ELEVENLABS_SERVICE_TOKEN not found")
  ```
- [ ] **1.2.7** Add token verification method:
  ```python
  def verify_service_token(self, token: str) -> bool:
      return token == self.service_token
  ```
- [ ] **1.2.8** Add dependency function:
  ```python
  def get_elevenlabs_auth() -> ElevenLabsAuth:
      return ElevenLabsAuth()
  ```

#### Step 1.3: Function Handler Endpoint ✅ COMPLETED
- [x] **1.3.1** Create file: `touch backend/api/elevenlabs_functions.py`
- [ ] **1.3.2** Add imports to `elevenlabs_functions.py`:
  ```python
  from fastapi import APIRouter, HTTPException, Header, Depends
  from pydantic import BaseModel
  from typing import Dict, Any
  from services.elevenlabs_auth import get_elevenlabs_auth, ElevenLabsAuth
  ```
- [ ] **1.3.3** Create router instance:
  ```python
  router = APIRouter(prefix="/elevenlabs", tags=["elevenlabs"])
  ```
- [ ] **1.3.4** Create request model:
  ```python
  class FunctionCallRequest(BaseModel):
      function_name: str
      parameters: Dict[str, Any]
      conversation_id: Optional[str] = None
  ```
- [ ] **1.3.5** Create response model:
  ```python
  class FunctionCallResponse(BaseModel):
      result: Dict[str, Any]
      success: bool = True
      error: Optional[str] = None
  ```
- [ ] **1.3.6** Implement basic handler endpoint:
  ```python
  @router.post("/function-call", response_model=FunctionCallResponse)
  async def handle_function_call(
      request: FunctionCallRequest,
      x_service_token: str = Header(alias="X-Service-Token"),
      auth: ElevenLabsAuth = Depends(get_elevenlabs_auth)
  ):
      # Verify token
      if not auth.verify_service_token(x_service_token):
          raise HTTPException(401, "Invalid service token")
      
      # Route to function (placeholder)
      if request.function_name == "query_persona_knowledge":
          return FunctionCallResponse(result={"message": "Function handler working"})
      else:
          raise HTTPException(400, f"Unknown function: {request.function_name}")
  ```
- [ ] **1.3.7** Add router to main app in `backend/main.py`:
  ```python
  from api.elevenlabs_functions import router as elevenlabs_router
  app.include_router(elevenlabs_router)
  ```
- [ ] **1.3.8** Test endpoint with curl:
  ```bash
  curl -X POST http://localhost:8000/elevenlabs/function-call \
    -H "Content-Type: application/json" \
    -H "X-Service-Token: your_token" \
    -d '{"function_name": "query_persona_knowledge", "parameters": {}}'
  ```

### Phase 2: Agent Configuration (Days 3-4) ✅ COMPLETED

#### Step 2.1: Create Agent Template ✅ COMPLETED  
- [x] **2.1.1** Install ElevenLabs Python SDK: `cd backend && pip install elevenlabs`
- [ ] **2.1.2** Create file: `touch backend/services/agent_manager.py`
- [ ] **2.1.3** Add imports to `agent_manager.py`:
  ```python
  import os
  from elevenlabs import ElevenLabs
  from typing import Dict, Any, Optional
  ```
- [ ] **2.1.4** Create `AgentManager` class:
  ```python
  class AgentManager:
      def __init__(self):
          self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
  ```
- [ ] **2.1.5** Define agent configuration template:
  ```python
  def get_agent_config_template(self, persona_name: str, persona_prompt: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"):
      return {
          "name": f"{persona_name} Voice Agent",
          "prompt": f"{persona_prompt}\n\nYou have access to a knowledge base through the query_persona_knowledge function.",
          "voice": {"voice_id": voice_id},
          "tools": [{
              "type": "function",
              "function": {
                  "name": "query_persona_knowledge",
                  "description": "Search the persona's knowledge base for relevant information",
                  "parameters": {
                      "type": "object",
                      "properties": {
                          "query": {
                              "type": "string",
                              "description": "The user's question or search query"
                          },
                          "persona_id": {
                              "type": "string", 
                              "description": "The persona ID to search knowledge for"
                          }
                      },
                      "required": ["query", "persona_id"]
                  }
              }
          }]
      }
  ```
- [ ] **2.1.6** Add agent creation method:
  ```python
  async def create_agent(self, config: Dict[str, Any]) -> str:
      try:
          agent = await self.client.agents.create(**config)
          return agent.id
      except Exception as e:
          raise Exception(f"Failed to create agent: {str(e)}")
  ```

#### Step 2.2: Persona-Specific Agents
- [ ] **2.2.1** Create database migration file: `cd backend && alembic revision -m "add_elevenlabs_agent_id"`
- [ ] **2.2.2** Edit the migration file to add column:
  ```python
  def upgrade():
      op.add_column('personas', sa.Column('elevenlabs_agent_id', sa.String(255), nullable=True))
  
  def downgrade():
      op.drop_column('personas', 'elevenlabs_agent_id')
  ```
- [ ] **2.2.3** Run migration: `alembic upgrade head`
- [ ] **2.2.4** Create directory: `mkdir backend/scripts`
- [ ] **2.2.5** Create file: `touch backend/scripts/create_elevenlabs_agents.py`
- [ ] **2.2.6** Add imports to script:
  ```python
  import asyncio
  import sys
  import os
  sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  
  from database import SessionLocal
  from models import Persona
  from services.agent_manager import AgentManager
  ```
- [ ] **2.2.7** Add main function:
  ```python
  async def create_agents_for_personas():
      db = SessionLocal()
      agent_manager = AgentManager()
      
      try:
          personas = db.query(Persona).all()
          for persona in personas:
              if not persona.elevenlabs_agent_id:
                  print(f"Creating agent for persona: {persona.name}")
                  config = agent_manager.get_agent_config_template(
                      persona.name, 
                      persona.description or "You are a helpful assistant"
                  )
                  agent_id = await agent_manager.create_agent(config)
                  persona.elevenlabs_agent_id = agent_id
                  db.commit()
                  print(f"Created agent {agent_id} for {persona.name}")
      finally:
          db.close()
  ```
- [ ] **2.2.8** Add script runner:
  ```python
  if __name__ == "__main__":
      asyncio.run(create_agents_for_personas())
  ```
- [ ] **2.2.9** Run script: `cd backend && python scripts/create_elevenlabs_agents.py`

#### Step 2.3: Function Implementation
- [ ] **2.3.1** Update `elevenlabs_functions.py` imports:
  ```python
  from api.chat import chat  # Import existing chat function
  from models import Persona
  from database import get_db
  from sqlalchemy.orm import Session
  ```
- [ ] **2.3.2** Create knowledge query function:
  ```python
  async def query_persona_knowledge(query: str, persona_id: str, db: Session) -> Dict[str, Any]:
      try:
          # Verify persona exists
          persona = db.query(Persona).filter(Persona.id == persona_id).first()
          if not persona:
              return {"error": "Persona not found"}
          
          # Create a mock request object for the chat endpoint
          from api.chat import ChatRequest
          chat_request = ChatRequest(
              message=query,
              thread_id=None  # New conversation
          )
          
          # Call existing chat logic (you'll need to adapt this)
          # This is a placeholder - you'll need to extract the core logic
          response = await process_chat_query(persona_id, chat_request, db)
          
          return {
              "content": response.get("content", ""),
              "citations": response.get("citations", [])
          }
      except Exception as e:
          return {"error": f"Query failed: {str(e)}"}
  ```
- [ ] **2.3.3** Update function handler to use real implementation:
  ```python
  @router.post("/function-call", response_model=FunctionCallResponse)
  async def handle_function_call(
      request: FunctionCallRequest,
      x_service_token: str = Header(alias="X-Service-Token"),
      auth: ElevenLabsAuth = Depends(get_elevenlabs_auth),
      db: Session = Depends(get_db)
  ):
      if not auth.verify_service_token(x_service_token):
          raise HTTPException(401, "Invalid service token")
      
      if request.function_name == "query_persona_knowledge":
          result = await query_persona_knowledge(
              query=request.parameters.get("query"),
              persona_id=request.parameters.get("persona_id"),
              db=db
          )
          return FunctionCallResponse(result=result)
      else:
          raise HTTPException(400, f"Unknown function: {request.function_name}")
  ```
- [ ] **2.3.4** Test function with real persona:
  ```bash
  curl -X POST http://localhost:8000/elevenlabs/function-call \
    -H "Content-Type: application/json" \
    -H "X-Service-Token: your_token" \
    -d '{"function_name": "query_persona_knowledge", "parameters": {"query": "Hello", "persona_id": "your_persona_id"}}'
  ```

### Phase 3: Frontend Integration (Days 5-6) ✅ COMPLETED

**PHASE 3 ACHIEVEMENTS:**
- ✅ **VoiceContext Provider**: Secure server-side API key architecture implemented
- ✅ **Voice Components**: VoiceChat and TranscriptDisplay components created with full TypeScript interfaces
- ✅ **Chat Integration**: Voice toggle button and voice section integrated into existing chat interface
- ✅ **usePersonaAgent Hook**: Agent ID fetching and management implemented
- ✅ **Test Interface**: Comprehensive test page created at `/test-voice`
- ✅ **Environment Setup**: `.env.local` configured for server-side security
- ✅ **Error Handling**: Comprehensive fallbacks and user-friendly error messages
- ✅ **Responsive Design**: Mobile-first design with accessibility features

**TECHNICAL IMPLEMENTATION:**
- Frontend voice UI complete and functional
- Server-side API key security (no client-side exposure)
- Voice/text mode switching seamless
- Real-time transcript display
- Professional error handling and status indicators

#### Step 3.1: Install ElevenLabs React SDK ✅ COMPLETED
- [x] **3.1.1** Navigate to frontend: `cd frontend`
- [ ] **3.1.2** Install SDK: `npm install @elevenlabs/react`
- [ ] **3.1.3** Add environment variable to `frontend/.env.local`:
  ```bash
  NEXT_PUBLIC_ELEVENLABS_KEY=your_public_key_here
  ```
- [ ] **3.1.4** Create directory: `mkdir components/voice`
- [ ] **3.1.5** Create voice context file: `touch lib/contexts/VoiceContext.tsx`
- [ ] **3.1.6** Add imports to `VoiceContext.tsx`:
  ```typescript
  'use client';
  import React, { createContext, useContext, ReactNode } from 'react';
  import { ElevenLabsProvider } from '@elevenlabs/react';
  ```
- [ ] **3.1.7** Create voice context:
  ```typescript
  interface VoiceContextType {
    isVoiceEnabled: boolean;
  }
  
  const VoiceContext = createContext<VoiceContextType>({
    isVoiceEnabled: false
  });
  
  export function VoiceContextProvider({ children }: { children: ReactNode }) {
    const apiKey = process.env.NEXT_PUBLIC_ELEVENLABS_KEY;
    
    return (
      <VoiceContext.Provider value={{ isVoiceEnabled: !!apiKey }}>
        {apiKey ? (
          <ElevenLabsProvider apiKey={apiKey}>
            {children}
          </ElevenLabsProvider>
        ) : (
          children
        )}
      </VoiceContext.Provider>
    );
  }
  
  export const useVoiceContext = () => useContext(VoiceContext);
  ```
- [ ] **3.1.8** Update `app/layout.tsx` to wrap with provider:
  ```typescript
  import { VoiceContextProvider } from '@/lib/contexts/VoiceContext';
  
  export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
      <html lang="en">
        <body>
          <VoiceContextProvider>
            {children}
          </VoiceContextProvider>
        </body>
      </html>
    );
  }
  ```

#### Step 3.2: Create Voice Chat Component
- [ ] **3.2.1** Create file: `touch components/voice/VoiceChat.tsx`
- [ ] **3.2.2** Add imports to `VoiceChat.tsx`:
  ```typescript
  'use client';
  import React, { useState, useEffect } from 'react';
  import { useConversation } from '@elevenlabs/react';
  import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
  ```
- [ ] **3.2.3** Create interface:
  ```typescript
  interface VoiceChatProps {
    personaId: string;
    agentId: string;
    onTranscript?: (text: string, isUser: boolean) => void;
  }
  ```
- [ ] **3.2.4** Implement main component:
  ```typescript
  export function VoiceChat({ personaId, agentId, onTranscript }: VoiceChatProps) {
    const [isConnected, setIsConnected] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    
    const conversation = useConversation({
      agentId,
      onConnect: () => setIsConnected(true),
      onDisconnect: () => setIsConnected(false),
      onMessage: (message) => {
        onTranscript?.(message.text, message.source === 'user');
      }
    });
  ```
- [ ] **3.2.5** Add connection handlers:
  ```typescript
    const handleStartConversation = async () => {
      try {
        await conversation.startSession();
      } catch (error) {
        console.error('Failed to start conversation:', error);
      }
    };
    
    const handleEndConversation = () => {
      conversation.endSession();
    };
  ```
- [ ] **3.2.6** Add render method:
  ```typescript
    return (
      <div className="voice-chat-container p-4 border rounded-lg">
        <div className="flex items-center gap-4">
          {!isConnected ? (
            <button
              onClick={handleStartConversation}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <Mic className="w-4 h-4" />
              Start Voice Chat
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={handleEndConversation}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                <MicOff className="w-4 h-4" />
                End Chat
              </button>
              <button
                onClick={() => setIsMuted(!isMuted)}
                className="p-2 border rounded-lg hover:bg-gray-100"
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </button>
            </div>
          )}
        </div>
        
        {isConnected && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-700">Voice chat active</span>
            </div>
          </div>
        )}
      </div>
    );
  }
  ```
- [ ] **3.2.7** Create transcript display: `touch components/voice/TranscriptDisplay.tsx`
- [ ] **3.2.8** Implement transcript component:
  ```typescript
  interface TranscriptMessage {
    text: string;
    isUser: boolean;
    timestamp: Date;
  }
  
  export function TranscriptDisplay({ messages }: { messages: TranscriptMessage[] }) {
    return (
      <div className="transcript-display max-h-64 overflow-y-auto p-4 border rounded-lg bg-gray-50">
        {messages.map((message, index) => (
          <div key={index} className={`mb-2 ${message.isUser ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block p-2 rounded-lg max-w-xs ${
              message.isUser 
                ? 'bg-blue-500 text-white' 
                : 'bg-white border'
            }`}>
              {message.text}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    );
  }
  ```

#### Step 3.3: Update Chat Interface
- [ ] **3.3.1** Create hook: `touch lib/hooks/usePersonaAgent.ts`
- [ ] **3.3.2** Implement persona agent hook:
  ```typescript
  import { useState, useEffect } from 'react';
  
  export function usePersonaAgent(personaId: string) {
    const [agentId, setAgentId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
      async function fetchAgentId() {
        try {
          const response = await fetch(`/api/personas/${personaId}`);
          const persona = await response.json();
          setAgentId(persona.elevenlabs_agent_id);
        } catch (err) {
          setError('Failed to load agent ID');
        } finally {
          setLoading(false);
        }
      }
      
      if (personaId) {
        fetchAgentId();
      }
    }, [personaId]);
    
    return { agentId, loading, error };
  }
  ```
- [ ] **3.3.3** Update chat page: Open `app/(common)/chat/[persona]/page.tsx`
- [ ] **3.3.4** Add voice imports:
  ```typescript
  import { VoiceChat } from '@/components/voice/VoiceChat';
  import { TranscriptDisplay } from '@/components/voice/TranscriptDisplay';
  import { usePersonaAgent } from '@/lib/hooks/usePersonaAgent';
  import { useVoiceContext } from '@/lib/contexts/VoiceContext';
  ```
- [ ] **3.3.5** Add voice state to chat component:
  ```typescript
  const { isVoiceEnabled } = useVoiceContext();
  const { agentId } = usePersonaAgent(personaId);
  const [showVoiceChat, setShowVoiceChat] = useState(false);
  const [transcriptMessages, setTranscriptMessages] = useState([]);
  ```
- [ ] **3.3.6** Add voice toggle button to chat header:
  ```typescript
  {isVoiceEnabled && agentId && (
    <button
      onClick={() => setShowVoiceChat(!showVoiceChat)}
      className="flex items-center gap-2 px-3 py-2 border rounded-lg hover:bg-gray-100"
    >
      <Mic className="w-4 h-4" />
      {showVoiceChat ? 'Hide Voice' : 'Voice Chat'}
    </button>
  )}
  ```
- [ ] **3.3.7** Add voice chat component to layout:
  ```typescript
  {showVoiceChat && isVoiceEnabled && agentId && (
    <div className="mb-4">
      <VoiceChat
        personaId={personaId}
        agentId={agentId}
        onTranscript={(text, isUser) => {
          setTranscriptMessages(prev => [...prev, {
            text,
            isUser,
            timestamp: new Date()
          }]);
        }}
      />
      {transcriptMessages.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium mb-2">Voice Transcript</h3>
          <TranscriptDisplay messages={transcriptMessages} />
        </div>
      )}
    </div>
  )}
  ```

### Phase 4: Testing & Optimization (Days 7-8) 🚧 NEXT PHASE

#### Step 4.1: End-to-End Testing
- [ ] **4.1.1** Test basic voice connection:
  - Open chat page with voice enabled
  - Click "Start Voice Chat" button
  - Verify connection indicator shows "active"
  - Say "Hello" and confirm audio is captured
- [ ] **4.1.2** Test function calling flow:
  - Start voice conversation
  - Ask a question about the persona's knowledge
  - Verify function call is made to your API
  - Check backend logs for function call requests
  - Confirm response is spoken back
- [ ] **4.1.3** Test RAG integration:
  - Ask specific questions about uploaded documents
  - Verify citations are included in function response
  - Check that voice response mentions sources
  - Test with different personas and their knowledge bases
- [ ] **4.1.4** Test interruption handling:
  - Start voice conversation
  - Interrupt the AI while it's speaking
  - Verify conversation continues naturally
  - Test multiple interruptions in sequence
- [ ] **4.1.5** Measure latency:
  - Use browser dev tools to measure response times
  - Target: First audio response within 400ms
  - Test with different query complexities
  - Document performance metrics

#### Step 4.2: Error Handling
- [ ] **4.2.1** Add function call fallbacks in `elevenlabs_functions.py`:
  ```python
  async def query_persona_knowledge(query: str, persona_id: str, db: Session) -> Dict[str, Any]:
      try:
          # Existing logic...
      except Exception as e:
          logger.error(f"Function call failed: {str(e)}")
          return {
              "content": "I'm sorry, I'm having trouble accessing my knowledge base right now. Please try asking again.",
              "error": str(e)
          }
  ```
- [ ] **4.2.2** Implement retry logic:
  ```python
  import asyncio
  from functools import wraps
  
  def retry_on_failure(max_retries=3, delay=1):
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              for attempt in range(max_retries):
                  try:
                      return await func(*args, **kwargs)
                  except Exception as e:
                      if attempt == max_retries - 1:
                          raise e
                      await asyncio.sleep(delay * (2 ** attempt))
              return wrapper
      return decorator
  ```
- [ ] **4.2.3** Add user-friendly error messages in voice chat:
  ```typescript
  const conversation = useConversation({
      agentId,
      onError: (error) => {
          console.error('Voice chat error:', error);
          setError('Voice chat encountered an issue. Please try again.');
      }
  });
  ```
- [ ] **4.2.4** Create error monitoring:
  ```python
  import logging
  
  # Add to elevenlabs_functions.py
  logger = logging.getLogger(__name__)
  
  # Log all function calls and errors
  @router.post("/function-call")
  async def handle_function_call(...):
      logger.info(f"Function call: {request.function_name} with params: {request.parameters}")
      try:
          # ... existing logic
      except Exception as e:
          logger.error(f"Function call failed: {str(e)}", exc_info=True)
          raise
  ```

#### Step 4.3: Performance Optimization
- [ ] **4.3.1** Add Redis caching for frequent queries:
  ```python
  import redis
  import json
  import hashlib
  
  redis_client = redis.Redis(host='localhost', port=6379, db=0)
  
  def get_cache_key(query: str, persona_id: str) -> str:
      content = f"{query}:{persona_id}"
      return f"voice_query:{hashlib.md5(content.encode()).hexdigest()}"
  
  async def query_persona_knowledge_cached(query: str, persona_id: str, db: Session):
      cache_key = get_cache_key(query, persona_id)
      
      # Try cache first
      cached = redis_client.get(cache_key)
      if cached:
          return json.loads(cached)
      
      # Query if not cached
      result = await query_persona_knowledge(query, persona_id, db)
      
      # Cache for 5 minutes
      redis_client.setex(cache_key, 300, json.dumps(result))
      return result
  ```
- [ ] **4.3.2** Optimize function call payload:
  ```python
  # Limit response length for voice
  def truncate_for_voice(content: str, max_length: int = 500) -> str:
      if len(content) <= max_length:
          return content
      
      # Find last complete sentence within limit
      truncated = content[:max_length]
      last_period = truncated.rfind('.')
      if last_period > max_length * 0.7:  # If we can keep 70% of content
          return truncated[:last_period + 1]
      return truncated + "..."
  ```
- [ ] **4.3.3** Add response streaming preparation:
  ```python
  # Prepare for future streaming implementation
  class StreamingResponse:
      def __init__(self, content: str):
          self.content = content
          self.chunks = self._create_chunks()
      
      def _create_chunks(self) -> List[str]:
          # Split by sentences for natural speech pauses
          sentences = self.content.split('. ')
          return [s + '. ' for s in sentences if s.strip()]
  ```
- [ ] **4.3.4** Monitor performance metrics:
  ```python
  import time
  from functools import wraps
  
  def measure_performance(func):
      @wraps(func)
      async def wrapper(*args, **kwargs):
          start_time = time.time()
          result = await func(*args, **kwargs)
          duration = time.time() - start_time
          logger.info(f"{func.__name__} took {duration:.2f}s")
          return result
      return wrapper
  ```

### Phase 5: Production Deployment (Days 9-10)

#### Step 5.1: Security Hardening
- [ ] **5.1.1** Implement rate limiting:
  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from slowapi.errors import RateLimitExceeded
  
  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
  
  @router.post("/function-call")
  @limiter.limit("10/minute")  # 10 calls per minute per IP
  async def handle_function_call(request: Request, ...):
      # ... existing logic
  ```
- [ ] **5.1.2** Add request validation:
  ```python
  from pydantic import validator
  
  class FunctionCallRequest(BaseModel):
      function_name: str
      parameters: Dict[str, Any]
      
      @validator('function_name')
      def validate_function_name(cls, v):
          allowed_functions = ['query_persona_knowledge']
          if v not in allowed_functions:
              raise ValueError(f'Function {v} not allowed')
          return v
      
      @validator('parameters')
      def validate_parameters(cls, v):
          if 'query' in v and len(v['query']) > 1000:
              raise ValueError('Query too long')
          return v
  ```
- [ ] **5.1.3** Set up monitoring alerts:
  ```python
  # Add to your monitoring system
  import logging
  
  class AlertHandler(logging.Handler):
      def emit(self, record):
          if record.levelno >= logging.ERROR:
              # Send alert to your monitoring system
              pass
  
  logger.addHandler(AlertHandler())
  ```
- [ ] **5.1.4** Configure CORS properly:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://yourdomain.com"],  # Specific domain only
      allow_credentials=True,
      allow_methods=["POST"],  # Only POST for function calls
      allow_headers=["X-Service-Token", "Content-Type"],
  )
  ```

#### Step 5.2: Documentation
- [ ] **5.2.1** Update API documentation in `docs/API.md`:
  ```markdown
  ## ElevenLabs Function Calling
  
  ### POST /elevenlabs/function-call
  
  Handles function calls from ElevenLabs agents.
  
  **Headers:**
  - `X-Service-Token`: Service authentication token
  
  **Request Body:**
  ```json
  {
    "function_name": "query_persona_knowledge",
    "parameters": {
      "query": "User's question",
      "persona_id": "UUID of persona"
    }
  }
  ```
  ```
- [ ] **5.2.2** Create user guide: `touch docs/VOICE_CHAT_GUIDE.md`
- [ ] **5.2.3** Document troubleshooting steps:
  ```markdown
  ## Voice Chat Troubleshooting
  
  ### Common Issues:
  1. **No voice button**: Check NEXT_PUBLIC_ELEVENLABS_KEY is set
  2. **Connection fails**: Verify agent ID exists for persona
  3. **No audio**: Check browser microphone permissions
  4. **Function calls fail**: Verify service token matches
  ```
- [ ] **5.2.4** Add voice chat to onboarding flow:
  - Update welcome tour to highlight voice features
  - Add voice chat demo to persona creation
  - Create video tutorial for voice usage

#### Step 5.3: Gradual Rollout
- [ ] **5.3.1** Deploy to staging environment:
  - Set up staging ElevenLabs agents
  - Test with staging data
  - Verify all functionality works
- [ ] **5.3.2** Test with internal team:
  - Create test personas with known content
  - Have team members test voice conversations
  - Collect feedback and fix issues
- [ ] **5.3.3** Enable for beta users:
  ```python
  # Add feature flag
  VOICE_CHAT_BETA_USERS = os.getenv("VOICE_CHAT_BETA_USERS", "").split(",")
  
  def is_voice_enabled_for_user(user_id: str) -> bool:
      return user_id in VOICE_CHAT_BETA_USERS or os.getenv("ENABLE_VOICE_CHAT") == "true"
  ```
- [ ] **5.3.4** Monitor metrics and feedback:
  - Track voice conversation success rates
  - Monitor function call latency
  - Collect user satisfaction scores
  - Watch for error patterns
- [ ] **5.3.5** Full production release:
  - Remove beta user restrictions
  - Update documentation
  - Announce voice features to all users
  - Monitor for any issues at scale

## 📁 New Files to Create

```
backend/
├── api/
│   └── elevenlabs_functions.py    # Function call handler
├── services/
│   ├── elevenlabs_auth.py         # Authentication service
│   └── agent_manager.py           # Agent lifecycle management
├── scripts/
│   └── create_elevenlabs_agents.py # Agent setup script
└── alembic/versions/
    └── add_elevenlabs_agent_id.py # Database migration

frontend/
├── components/voice/
│   ├── VoiceChat.tsx              # Main voice interface
│   ├── TranscriptDisplay.tsx      # Conversation transcript
│   └── VoiceSettings.tsx          # Voice preferences
├── lib/hooks/
│   └── useElevenLabsAgent.ts      # Agent connection hook
└── app/test-voice/
    └── page.tsx                   # Voice testing page
```

## 🔧 Environment Variables

### Backend (.env)
```bash
# ElevenLabs
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_SERVICE_TOKEN=your_generated_token
ELEVENLABS_WEBHOOK_SECRET=webhook_secret

# Feature Flags
ENABLE_VOICE_CHAT=true
VOICE_CHAT_BETA_USERS=user1,user2
```

### Frontend (.env.local)
```bash
# ElevenLabs
NEXT_PUBLIC_ELEVENLABS_KEY=pk_...
NEXT_PUBLIC_ENABLE_VOICE=true
```

## 📊 Success Metrics

### Technical Metrics
- [ ] Voice latency: <400ms first response
- [ ] Function call success rate: >99%
- [ ] Audio quality: No stuttering or drops
- [ ] Concurrent conversations: Support 30+ (Business plan limit)

### User Experience Metrics
- [ ] User adoption: 50% try voice within first week
- [ ] Conversation completion: 80% successful conversations
- [ ] User satisfaction: 4.5+ star rating
- [ ] Citation accuracy: 100% match with text chat

## 🚨 Risk Mitigation

### Technical Risks
1. **Function call failures**
   - Mitigation: Implement retry logic and fallback responses
   - Monitoring: Alert on >1% failure rate

2. **High latency**
   - Mitigation: Cache frequent queries, optimize payloads
   - Monitoring: Track p95 latency metrics

3. **Rate limits**
   - Mitigation: Implement request queuing
   - Monitoring: Track usage vs limits

### Business Risks
1. **Cost overruns**
   - Mitigation: Set usage alerts at 80% of monthly minutes
   - Monitoring: Daily usage reports

2. **User confusion**
   - Mitigation: Clear UI indicators for voice vs text mode
   - Monitoring: User feedback and support tickets

## 📅 Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| Week 1 | Foundation & Configuration | Backend services, agent setup |
| Week 2 | Frontend & Testing | Voice UI, end-to-end testing |
| Week 3 | Deployment | Production release, monitoring |

## 🎯 Definition of Done

- [ ] Voice conversations work for all personas
- [ ] Function calling successfully queries RAG system
- [ ] Citations appear in voice transcript
- [ ] Error handling covers all edge cases
- [ ] Documentation complete
- [ ] Monitoring and alerts configured
- [ ] User feedback collected and positive

## 🔄 Post-Launch Iterations

### Month 1
- Collect user feedback
- Optimize based on usage patterns
- Add advanced features (voice commands, shortcuts)

### Month 2
- Implement voice-only features
- Add multi-language support
- Create voice analytics dashboard

### Month 3
- Phone integration via Twilio
- Batch conversation processing
- Enterprise features

---

## 🚀 Quick Start Commands

```bash
# Backend setup
cd backend
pip install elevenlabs
python scripts/create_elevenlabs_agents.py

# Frontend setup
cd frontend
npm install @elevenlabs/react
npm run dev

# Test voice chat
open http://localhost:3001/test-voice
```

This plan provides a clear path to add professional voice capabilities while preserving your existing investment in the RAG system. 