# Clone Advisor Sprint 2 - Async Ingestion Pipeline

## 🎯 What's New in Sprint 2

Sprint 2 transforms the Clone Advisor from a simple file upload system into a **production-grade async processing pipeline** that can handle dozens of files with real-time progress tracking.

### ✅ Key Features Added

1. **🔄 Redis Queue System**: Background job processing with RQ (Redis Queue)
2. **📊 Real-time Progress Tracking**: Live SSE updates for file processing
3. **🚀 Batch Processing**: Upload 50+ files with smart deduplication
4. **📈 Enhanced Progress UI**: See current file being processed + chunk counts
5. **🛡️ Error Handling**: Robust error recovery and retry mechanisms
6. **⚡ Performance**: 500-token chunks with 50-token overlap for optimal search

---

## 🚀 Quick Start

### Prerequisites

1. **Redis** - For job queue
   ```bash
   brew install redis
   brew services start redis
   ```

2. **PostgreSQL** - For database
   ```bash
   # Should already be running from Sprint 1
   ```

3. **Python Dependencies** - New packages added
   ```bash
   cd backend
   source venv310/bin/activate
   pip install -r requirements.txt
   ```

### Start Everything

Use the new startup script:

```bash
./start_sprint2.sh
```

This will:
- ✅ Check Redis & PostgreSQL connections
- 🔄 Install new dependencies (redis, rq, boto3, python-magic)
- 📊 Run database migrations
- 🌐 Start FastAPI server (port 8000)
- ⚙️ Start Redis worker for ingestion queue
- 🎨 Start Next.js frontend (port 3000)

### Manual Start (for debugging)

```bash
# Terminal 1: API Server
cd backend
source venv310/bin/activate
uvicorn main:app --reload

# Terminal 2: Redis Worker
cd backend
source venv310/bin/activate
python worker.py ingestion

# Terminal 3: Frontend
cd frontend
npm run dev
```

---

## 🧪 Testing the System

### 1. Test Redis Queue
```bash
cd backend
source venv310/bin/activate
python test_queue.py
```

### 2. Test Multi-File Upload

1. Go to http://localhost:3000/fullchat
2. Create or select a persona
3. Click "Add Files" button
4. Drag & drop multiple PDF/TXT files
5. Watch real-time progress updates!

### 3. Monitor Jobs

**Queue Status:**
```bash
redis-cli llen rq:queue:ingestion  # Number of pending jobs
redis-cli monitor                  # Real-time Redis activity
```

**API Endpoints:**
- `GET /persona/jobs/{job_id}/status` - Current job status
- `GET /persona/jobs/{job_id}/stream` - SSE progress stream

---

## 🏗️ Architecture Overview

### Request Flow

```
Frontend Upload → FastAPI → Create Job → Redis Queue
                     ↓
                 Job Worker → Process Files → Update Progress
                     ↓
                 Pinecone ← Embeddings ← Chunks ← Files
                     ↓
                 SSE Stream → Frontend Updates
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Queue Manager** | `services/queue_manager.py` | Redis + RQ |
| **Ingestion Worker** | `services/ingestion_worker.py` | Async file processing |
| **Job Tracking** | `models.py:IngestionJob` | PostgreSQL |
| **Progress API** | `/persona/jobs/{id}/stream` | Server-Sent Events |
| **Frontend UI** | `MultiFileUpload.tsx` | React + SSE |

### Database Schema

```sql
-- New table for tracking async jobs
CREATE TABLE ingestion_jobs (
    id VARCHAR PRIMARY KEY,
    persona_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    total_files INTEGER NOT NULL,
    processed_files INTEGER DEFAULT 0,
    status job_status_enum DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    job_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Database (existing)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/clone_advisor

# File Limits (existing)
MAX_UPLOAD_SIZE_MB=10
```

### Queue Configuration

- **Queue Name**: `ingestion`
- **Job Timeout**: 30 minutes
- **Batch Size**: 100 chunks per embedding call
- **File Limit**: 50 files per upload

---

## 📊 Monitoring & Debugging

### Monitor Queue Activity
```bash
# Queue length
redis-cli llen rq:queue:ingestion

# Failed jobs
redis-cli llen rq:queue:failed

# Worker status
redis-cli keys rq:worker:*

# Real-time monitoring
redis-cli monitor
```

### Check Job Status
```bash
# Via API
curl http://localhost:8000/persona/jobs/{job_id}/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Database query
psql clone_advisor -c "
  SELECT id, status, progress, processed_files, total_files 
  FROM ingestion_jobs 
  ORDER BY created_at DESC 
  LIMIT 10;
"
```

### Debug Worker Issues
```bash
# Check worker logs
cd backend
python worker.py ingestion  # Run in foreground

# Test individual job
python -c "
from services.queue_manager import enqueue_job
from services.ingestion_worker import run_ingestion_job
job_id = enqueue_job(run_ingestion_job, 'job_id', 'persona_id', [])
print('Job ID:', job_id)
"
```

---

## 🚧 Known Limitations & TODO

### Current Limitations
- ⚠️ **File Storage**: Still using local storage (S3 planned for Sprint 3)
- ⚠️ **Rate Limiting**: No rate limiting (internal tool)
- ⚠️ **Retry Logic**: Basic retry (enhanced retry planned)

### Upcoming in Sprint 3
- 📁 **S3 Integration**: Proper file storage
- 🧠 **Advanced Prompts**: Multi-layer prompt system  
- 📈 **Quality Evaluation**: LLM judge scoring
- 🔍 **Content Search**: Advanced filtering and search

---

## 🎯 Success Metrics

After implementing Sprint 2, you should be able to:

- ✅ Upload 20+ files simultaneously
- ✅ See real-time progress updates
- ✅ Process files in background without blocking UI
- ✅ Handle failures gracefully with error messages
- ✅ Monitor queue status via Redis CLI
- ✅ Scale to 50+ files without timeouts

**Performance Target**: Process 20 files (≈40MB) in under 3 minutes

---

## 🆘 Troubleshooting

### Redis Connection Issues
```bash
# Start Redis
brew services start redis
# OR
redis-server

# Test connection
redis-cli ping  # Should return "PONG"
```

### Worker Not Processing
```bash
# Check if worker is running
ps aux | grep worker

# Restart worker
killall python
cd backend && python worker.py ingestion
```

### Database Migration Issues
```bash
cd backend
alembic upgrade head  # Apply migrations
alembic current       # Check current version
```

### Frontend Issues
```bash
cd frontend
npm install           # Reinstall dependencies
rm -rf .next          # Clear Next.js cache
npm run dev           # Restart dev server
```

---

## 📞 Support

For issues with Sprint 2 implementation:

1. **Check logs**: API server, worker, and frontend consoles
2. **Monitor Redis**: `redis-cli monitor` for queue activity
3. **Database queries**: Check `ingestion_jobs` table for job status
4. **Use test script**: `python test_queue.py` to verify queue system

The Sprint 2 pipeline is designed to be **reliable and observable** - you should always be able to see what's happening and why. 