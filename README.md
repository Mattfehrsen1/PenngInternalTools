# Clone Advisor MVP 0.1

An AI-powered chat application that allows users to upload PDFs or text to create persona "clones" and ask questions using RAG (Retrieval-Augmented Generation).

## Features

- **PDF/Text Upload**: Upload PDFs or paste text to create searchable knowledge bases
- **Smart Chunking**: Automatic document processing with intelligent text chunking
- **LLM Model Selection**: Choose between GPT-4o, Claude 3, or auto-selection
- **Citation Support**: View source citations for each response
- **Streaming Responses**: Real-time token-by-token streaming chat
- **Usage Tracking**: Monitor API usage and costs
- **JWT Authentication**: Secure authentication with demo credentials

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Pinecone** - Vector database for embeddings
- **OpenAI/Anthropic** - LLM providers
- **SQLAlchemy** - ORM with async support
- **Pydantic** - Data validation
- **PyPDF** - PDF text extraction

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Radix UI** - Accessible primitives
- **React Dropzone** - File uploads
- **SSE Streaming** - Real-time responses

## Project Structure

```
clone-advisor/
├── backend/
│   ├── api/              # API routes
│   ├── services/         # Business logic
│   ├── models.py         # Database models
│   ├── main.py          # FastAPI app
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── app/             # Next.js app router
│   ├── components/      # React components
│   ├── lib/            # Utilities & API client
│   └── package.json    # Node dependencies
├── infra/
│   └── docker-compose.yml  # Local PostgreSQL
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- API Keys: OpenAI, Anthropic, Pinecone

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clone-advisor
   ```

2. **Run setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure environment variables**
   
   Update `backend/.env`:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/cloneadvisor
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   PINECONE_API_KEY=your_key_here
   PINECONE_ENV=your_environment
   PINECONE_PROJECT_ID=your_project_id
   JWT_SECRET=your_secret_key
   ```

4. **Create database**
   ```bash
   createdb cloneadvisor
   cd backend
   source venv/bin/activate
   alembic upgrade head
   ```

5. **Run the application**
   ```bash
   ./run-local.sh
   ```

   Access:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Demo Credentials
- Username: `demo`
- Password: `demo123`

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend E2E tests
cd frontend
npm run test:e2e
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `GET /auth/me` - Get current user

### Personas
- `POST /api/personas/upload` - Upload PDF/text
- `GET /api/personas` - List user's personas
- `GET /api/personas/{id}` - Get persona details

### Chat
- `POST /api/chat` - Stream chat response (SSE)
- `GET /api/chat/history/{persona_id}` - Get chat history

## Deployment

### Backend (Fly.io)
```bash
cd backend
fly launch
fly deploy
fly secrets set OPENAI_API_KEY=xxx ANTHROPIC_API_KEY=xxx ...
```

### Frontend (Vercel)
```bash
cd frontend
vercel
```

## Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_ENV` - Pinecone environment
- `PINECONE_PROJECT_ID` - Pinecone project ID
- `JWT_SECRET` - Secret for JWT tokens
- `MAX_UPLOAD_SIZE_MB` - Max file upload size (default: 10)
- `CHUNK_SIZE_TOKENS` - Chunk size for text splitting (default: 800)

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Architecture Decisions

1. **Async PostgreSQL**: Better performance for concurrent requests
2. **Pinecone for vectors**: Managed solution, easier to scale
3. **JWT auth**: Stateless, works well with distributed systems
4. **SSE for streaming**: Better than WebSockets for one-way streaming
5. **shadcn/ui**: Modern, accessible components with Tailwind
6. **Background processing**: Non-blocking document processing

## Roadmap

- [ ] Multi-file upload support
- [ ] Conversation history persistence
- [ ] Advanced search filters
- [ ] Export chat history
- [ ] User management UI
- [ ] Rate limiting
- [ ] Webhook notifications
- [ ] Mobile app

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and confidential.

## Support

For issues or questions, please contact the development team.
