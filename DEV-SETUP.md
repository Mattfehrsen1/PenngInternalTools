# 🚀 Clone Advisor Development Setup

Choose the best development method for your needs:

## Option 1: Quick Start (Recommended)
**Single command to start everything**

```bash
./dev-start.sh
```

This will:
- ✅ Start all services (frontend, backend, worker)
- ✅ Check dependencies and install if needed
- ✅ Show service status and logs
- ✅ One Ctrl+C stops everything

To stop:
```bash
./dev-stop.sh
```

## Option 2: Docker (Most Efficient)
**Better resource management, isolated environment**

```bash
# Start everything
docker-compose -f docker-compose.dev.yml up

# Stop everything  
docker-compose -f docker-compose.dev.yml down
```

Benefits:
- 🔥 Lower memory usage
- 🔒 Isolated environment
- 📦 Includes database and Redis
- 🔄 Auto-restart on crashes

## Option 3: Manual (Traditional)
**If you prefer separate terminals**

Terminal 1 - Backend:
```bash
cd backend
source venv310/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Worker:
```bash
cd backend
source venv310/bin/activate
python worker.py
```

Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

## 🔧 Access Points
- 🎨 **Frontend**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 📋 **Logs**: `./logs/` directory

## 🔑 Login Credentials
- **Username**: `demo`
- **Password**: `demo123`

## 🐛 Debugging

Check service status:
```bash
cd backend
source venv310/bin/activate

# Check specific persona status
python check_persona_status.py YOUR-PERSONA-ID

# Check job queue status
python check_queue_status.py
```

View logs:
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/backend.log
tail -f logs/frontend.log  
tail -f logs/worker.log
```

## ⚡ Performance Tips

1. **Use Option 1 or 2** - Much more efficient than manual setup
2. **Close unused browser tabs** - Next.js dev server uses memory
3. **Restart services if sluggish**: `./dev-stop.sh && ./dev-start.sh`
4. **Monitor memory**: `Activity Monitor` → Filter by "node" and "python"

## 🚨 Troubleshooting

**Frontend won't start**:
```bash
cd frontend && rm -rf .next node_modules && npm install
```

**Backend API errors**:
```bash
cd backend && source venv310/bin/activate && pip install -r requirements.txt
```

**Worker not processing**:
- Check Redis is running
- Check environment variables in `.env`
- Restart worker: `./dev-stop.sh && ./dev-start.sh`

**Port conflicts**:
```bash
# Kill everything on ports 3000, 8000
lsof -ti:3000,8000 | xargs kill -9
``` 