# Single-Origin Deployment Plan

This document outlines the steps to deploy Clone Advisor MVP 0.1 under a single origin `https://app.penng.ai` using Vercel (frontend) and Fly.io (backend). CORS is eliminated via same-origin edge rewrites.

---

## 1. Overview
- **Frontend**: Next.js on Vercel Hobby → `https://app.penng.ai`
- **Backend**: FastAPI on Fly.io → `https://clone-api.fly.dev` (private)
- Browser requests to `/api/...` on `app.penng.ai` get proxied to Fly service.

## 2. Prerequisites
1. GitHub repo with `/frontend` (Next.js) and `/backend` (FastAPI).
2. `.env` containing all variables (OpenAI, Pinecone, Postgres, R2, JWT, etc).
3. Domain `penng.ai` in Cloudflare (with CNAME control).

## 3. Fly.io Setup (Backend)
```bash
cd backend
# Initialize Fly without deploy
afly launch --name clone-api --region sjc --dockerfile ./Dockerfile --no-deploy
# Import secrets from .env
fly secrets import < ../.env
# Deploy
fly deploy
# Verify
curl https://clone-api.fly.dev/health
```

## 4. Vercel Setup (Frontend)
```bash
cd frontend
vercel init         # if not done
vercel link         # select existing or new project
# In Vercel dashboard:
#  • Add custom domain: app.penng.ai → CNAME to vercel-dns.com
#  • Set Env var: NEXT_PUBLIC_API_BASE=/api
```

## 5. Edge Rewrite Configuration
Add `next.config.js` at `/frontend/next.config.js`:
```js
const isDev = process.env.NODE_ENV !== 'production';
const dest = isDev
  ? 'http://localhost:8000'
  : 'https://clone-api.fly.dev';
module.exports = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${dest}/:path*` },
    ];
  },
};
```

## 6. Deploy Frontend
```bash
cd frontend
vercel deploy --prod
```

## 7. Smoke Test
1. Visit `https://app.penng.ai`
2. Upload a small text snippet → `/api/persona/upload` returns 200
3. Chat → `/api/chat` streams tokens in real time
4. No CORS errors; requests originate from `app.penng.ai`

## 8. Documentation Updates
- Update `docs/SRS_v0.3.md` → add Deployment section
- Ensure CORS note: same-origin rewrites remove need for Access-Control headers
- Commit this file under `infra/README.md`

## 9. Acceptance Criteria
- **Origin**: All requests under `app.penng.ai/api/...`
- **CORS**: No CORS errors, no `Access-Control-*` headers
- **Latency**: First token ≤ 2s
- **Cost**: Free tiers only (Vercel Hobby, Fly free)

---

*Infra PR name*: `infra/01-single-origin-vercel-fly`

*Next Actions*:
- Create PR with changes.
- Add screenshot/GIF of upload→chat flow.
