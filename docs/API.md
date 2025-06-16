# Clone Advisor API Documentation

**Base URL**: `http://localhost:8000` (development)

**Authentication**: Bearer token required for most endpoints
- Header: `Authorization: Bearer <token>`
- Token expires after 24 hours

---

## 🔐 Authentication

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "string"
  }
}
```

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

---

## 🎭 Personas Management

### List Personas
```http
GET /persona/list
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "personas": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "chunks": 0,
      "namespace": "string",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Persona Details
```http
GET /persona/{persona_id}
Authorization: Bearer <token>
```

### Create Persona
```http
POST /persona/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

name: string
description?: string
file?: File (PDF/TXT)
text?: string
```

### Update Persona
```http
PUT /persona/{persona_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "description": "string"
}
```

### Delete Persona
```http
DELETE /persona/{persona_id}
Authorization: Bearer <token>
```

---

## 📝 Persona Prompts Management

⭐ **NEW API PREFIX**: All prompt APIs are available at both:
- `/persona/{persona_id}/*` (legacy)
- `/api/personas/{persona_id}/*` (new, matches frontend expectations)

### Get Persona Prompts
```http
GET /api/personas/{persona_id}/prompts
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "prompts": {
    "system": [
      {
        "id": "uuid",
        "name": "main",
        "layer": "system",
        "content": "You are Alex Hormozi...",
        "version": 1,
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "commit_message": "Initial prompt"
      }
    ],
    "rag": [...],
    "user": [...]
  }
}
```

### Create/Update Prompt Version
```http
POST /api/personas/{persona_id}/prompts/{layer}/{name}/versions
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Your new prompt content...",
  "commit_message": "Updated greeting style"
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "layer": "system",
  "name": "main",
  "content": "Your new prompt content...",
  "version": 2,
  "is_active": true,
  "commit_message": "Updated greeting style",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Activate Prompt Version
```http
PUT /api/personas/{persona_id}/prompts/{version_id}/activate
Authorization: Bearer <token>
```

### Apply Template to Persona
```http
POST /api/personas/{persona_id}/prompts/from-template
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_name": "alex_hormozi"
}
```

**Response**: `200 OK`
```json
{
  "prompts": {
    "system": {
      "id": "uuid",
      "version": 1,
      "content_preview": "You are Alex Hormozi, a direct..."
    },
    "rag": {...},
    "user": {...}
  },
  "success": true,
  "message": "Successfully applied alex_hormozi template"
}
```

### Test Persona Prompts
```http
POST /api/personas/{persona_id}/prompts/test
Authorization: Bearer <token>
Content-Type: application/json

{
  "testQuery": "How do I scale my business?",
  "useActivePrompts": true
}
```

**Response**: Server-Sent Events stream
```
data: {"type": "token", "content": "Based on"}
data: {"type": "token", "content": " your question about"}
data: {"type": "done"}
```

---

## 📋 Prompt Templates

### List Available Templates
```http
GET /api/personas/templates
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "templates": [
    {
      "id": "alex_hormozi",
      "name": "Alex Hormozi Business Mentor",
      "description": "High-energy business mentor focused on scaling companies",
      "tags": ["business", "sales", "entrepreneurship"],
      "preview": {
        "system": "Direct, no-nonsense business advice...",
        "example_response": "Look, here's the thing about scaling..."
      }
    },
    {
      "id": "empathetic_therapist",
      "name": "Empathetic Therapist",
      "description": "Compassionate mental health professional",
      "tags": ["therapy", "mental health", "empathy"],
      "preview": {
        "system": "Warm, non-judgmental therapeutic approach...",
        "example_response": "I hear that you're feeling overwhelmed..."
      }
    }
  ]
}
```

---

## 📁 Document Management

⭐ **NEW ENDPOINTS**: For the `/files/{persona}` page

### List Persona Files
```http
GET /api/personas/{persona_id}/files
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "files": [
    {
      "id": "uuid",
      "name": "$100M Offers Summary.pdf",
      "size": 2457600,
      "type": "application/pdf",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "status": "processed",
      "chunks": 47
    },
    {
      "id": "uuid",
      "name": "Business Notes.txt",
      "size": 512000,
      "type": "text/plain",
      "uploaded_at": "2024-01-08T09:15:00Z",
      "status": "processing"
    }
  ],
  "total": 2
}
```

### Upload Files to Persona
```http
POST /api/personas/{persona_id}/files
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: File[] (multiple files supported)
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "name": "new-document.pdf",
  "size": 1024000,
  "status": "uploading",
  "message": "File upload started"
}
```

### Delete File
```http
DELETE /api/personas/files/{file_id}
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "message": "File {file_id} deleted successfully"
}
```

### Get File Processing Status
```http
GET /api/personas/files/{file_id}/status
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "status": "processed",
  "progress": 100,
  "chunks": 25,
  "message": "File processed successfully"
}
```

---

## 💬 Chat & Conversations

### Chat with Persona
```http
POST /chat/{persona_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "How do I scale my business?",
  "thread_id": "uuid"  // optional, for continuing conversation
}
```

**Response**: Server-Sent Events stream
```
data: {"type": "thread_info", "thread_id": "uuid"}
data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "citation", "text": "scaling strategies", "source": "document.pdf", "page": 15}
data: {"type": "done"}
```

### List Conversations
```http
GET /conversations
Authorization: Bearer <token>
```

### Get Conversation Messages
```http
GET /conversations/{thread_id}
Authorization: Bearer <token>
```

---

## 🧪 Testing & Quality

### Run Persona Tests
```http
POST /chat/tests/run/{persona_id}
Authorization: Bearer <token>
```

### Get Test Results
```http
GET /chat/tests/suites
Authorization: Bearer <token>
```

---

## ⚙️ Persona Settings

### Get Persona Settings
```http
GET /api/personas/{persona_id}/settings
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "persona_id": "uuid",
  "voice_id": "elevenlabs_voice_id",
  "voice_settings": {
    "speed": 1.0,
    "pitch": 0.0
  },
  "default_model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### Update Persona Settings
```http
PUT /api/personas/{persona_id}/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "voice_id": "new_voice_id",
  "default_model": "gpt-4o-mini",
  "temperature": 0.8
}
```

---

## 📊 Error Codes

| Code | Description |
|------|-------------|
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Invalid/missing token |
| `403` | Forbidden - Access denied |
| `404` | Not Found - Resource doesn't exist |
| `413` | Payload Too Large - File size exceeded |
| `422` | Unprocessable Entity - Validation error |
| `500` | Internal Server Error |

## 🔄 Rate Limits

- **Chat requests**: 100 per hour per user
- **File uploads**: 20 files per request, 50MB total
- **Prompt updates**: 50 per hour per persona

---

## 🚀 Frontend Integration Status

### ✅ Working Pages
- **Prompts Page** (`/prompts/{persona}`): Fully connected to backend APIs
- **Files Page** (`/files/{persona}`): Connected with mock data, ready for real uploads
- **Chat Interface**: Full conversation persistence and streaming

### 🎯 API Compatibility
- All frontend API calls now match backend endpoints
- Proper error handling and loading states
- Authentication flow working correctly

---

## 🌐 Deployment & Infrastructure

### Production URLs
- **Frontend**: `https://app.penng.ai` (Vercel)
- **Backend API**: `https://clone-api.fly.dev` (Fly.io)
- **API Proxy**: `https://app.penng.ai/api/*` → `https://clone-api.fly.dev/*`

### ElevenLabs Integration Endpoints

#### Function Call Webhook
```http
POST /elevenlabs/function-call
X-Service-Token: NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0
Content-Type: application/json

{
  "query": "string",
  "persona_id": "uuid"
}
```

**Response**: `200 OK`
```json
{
  "response": "Based on the persona's knowledge...",
  "citations": [
    {
      "text": "relevant quote",
      "source": "document.pdf",
      "page": 15
    }
  ],
  "confidence": 0.95,
  "metadata": {
    "model": "gpt-4o",
    "tokens_used": 450
  }
}
```

#### Cache Statistics (Redis)
```http
GET /elevenlabs/cache/stats
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "total_requests": 1542,
  "cache_hits": 791,
  "cache_misses": 751,
  "hit_rate": 0.513,
  "avg_latency_ms": {
    "cache_hit": 7.89,
    "cache_miss": 1576.15
  }
}
```

### Health Check
```http
GET /health
```

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "clone-advisor-api"
}
```

### Deployment Notes
- **Backend Host Issues**: If Fly.io machines are stopped, check `fly status` and restart with `fly machines start`
- **API Proxy**: Configured in `frontend/next.config.js` using rewrites
- **CORS**: Backend configured to accept requests from `app.penng.ai`
- **SSL**: All endpoints must use HTTPS in production

---

**Last Updated**: January 2025  
**API Version**: 0.1.0 