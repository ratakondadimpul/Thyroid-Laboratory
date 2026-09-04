# Publishing — Vercel + Firebase

This project is a **monorepo** with:
- `frontend/` — Next.js 16.3.2 (Tailwind 4, Recharts) → best on **Vercel**
- `backend/` — FastAPI + XGBoost + SQLite → best on **Vercel Python** *or* **Cloud Run**; Firebase Hosting serves the static frontend, Cloud Functions/Run serves the API

Both configs are **already prepared** in this repo (no rebuild from scratch).

---

## What was prepared for you

| File | Purpose |
|------|---------|
| `frontend/next.config.ts` | `FIREBASE_BUILD=true` → `output: export` for Firebase static hosting; rewrites only for localhost dev, production uses `NEXT_PUBLIC_API_URL` |
| `frontend/.env.example` | Template for `NEXT_PUBLIC_API_URL` |
| `frontend/vercel.json` | Vercel Next.js project config (iad1) |
| `backend/api/index.py` + `api/index.py` | Vercel Python serverless entry (`@vercel/python` 3.11, 50mb for XGBoost) |
| `backend/vercel.json` | Vercel Python builds/routes for backend |
| `backend/.env.example` | `SECRET_KEY`, `ALLOWED_ORIGINS`, `DATABASE_URL` |
| `firebase.json` | Hosting `frontend/out` + headers; `functions` placeholder |
| `.firebaserc` | Default project `thyroid-lab-intelligence` (change to yours) |
| `api/index.py` (root) | Monorepo Vercel entry that imports `backend/app/main.py` |

**CLIs installed:** `vercel 59.11.7`, `firebase-tools 15.29.0` (via `npm i -g`). Verify: `vercel --version` / `firebase --version`.

---

## Recommended architecture (uses **both** as requested)

```
[ Vercel ]  → frontend (Next.js SSR, optimal)  — https://<xxx>.vercel.app
      \
       +-- NEXT_PUBLIC_API_URL → [ Backend ]  → choose ONE:
              a) Vercel Python (api/index.py) — https://<api>.vercel.app
              b) Cloud Run / Render / Fly   — https://<api>.run.app  (recommended for ML + SQLite)
[ Firebase Hosting ] → second frontend mirror — https://<xxx>.web.app  (static export)
```

**Why not Firebase for backend FastAPI directly?** Firebase Functions is Node-centric; Python FastAPI is best on Cloud Run (1 command) or Vercel Python. Firebase Hosting is perfect for the frontend static export as a second publish.

---

## Option A — Frontend on Vercel, Backend on Vercel (simplest, both Vercel)

### 1) Deploy backend first (so you get its URL)

```bash
cd "AI-Powered Thyroid/backend"
vercel login                # browser login, select your scope
vercel --prod               # first run: Link? N → Project name: thyroid-lab-api → Directory: ./ → Settings: keep
# Note the output URL, e.g. https://thyroid-lab-api.vercel.app
# Test:
curl https://thyroid-lab-api.vercel.app/health
curl https://thyroid-lab-api.vercel.app/api/model/performance | head
```

If you see `maxLambdaSize` or memory warnings (XGBoost ~300MB), upgrade Vercel plan or use Option B for backend.

**Set backend env on Vercel dashboard:**
`Project → Settings → Environment Variables`
```
SECRET_KEY=<openssl rand -hex 32>
ALLOWED_ORIGINS=https://thyroid-lab-frontend.vercel.app,https://thyroid-lab-intelligence.web.app
# For Postgres (recommended, SQLite is ephemeral on Vercel):
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
```

### 2) Deploy frontend

```bash
cd "../frontend"
vercel login
# Set env var for frontend to talk to deployed backend:
vercel env add NEXT_PUBLIC_API_URL production
# paste: https://thyroid-lab-api.vercel.app  (or your Cloud Run URL)
vercel --prod
# Output: https://thyroid-lab-frontend.vercel.app
```

**Test live:**
```bash
curl https://thyroid-lab-frontend.vercel.app | head
# Login admin@lab.local / admin123 → upload frontend/public/sample_lab.csv → analyze → download
```

---

## Option B — Frontend on Firebase Hosting (static export) + Backend on Cloud Run (recommended for ML)

**Firebase excels at Hosting CDN; Cloud Run excels at Python ML.**

### 1) Create Firebase project (one-time)

```bash
firebase login                # browser login
firebase projects:list        # pick or create
# If no project:
firebase projects:create thyroid-lab-intelligence --display-name "Thyroid Lab"
# Or use existing, then:
firebase use thyroid-lab-intelligence
# Update .firebaserc if you used a different name:
# { "projects": { "default": "YOUR-ID" } }
```

### 2) Build frontend for Firebase

```bash
cd "AI-Powered Thyroid/frontend"
# Point to your deployed backend (from Option A backend step or Cloud Run URL)
echo "NEXT_PUBLIC_API_URL=https://thyroid-lab-api.vercel.app" > .env.local
# Or for local test of static export:
# echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > .env.local

FIREBASE_BUILD=true npm run build   # creates frontend/out
ls out/index.html  # should exist
firebase hosting:channel:deploy preview --expires 7d   # preview URL
firebase deploy --only hosting   # prod → https://thyroid-lab-intelligence.web.app
```

### 3) Deploy backend to Cloud Run (alternative to Vercel Python, better for XGBoost)

```bash
cd "../backend"
gcloud auth login
gcloud config set project thyroid-lab-intelligence
gcloud run deploy thyroid-lab-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY=$(openssl rand -hex 32),ALLOWED_ORIGINS=https://thyroid-lab-intelligence.web.app,https://thyroid-lab-frontend.vercel.app \
  --memory 1Gi --cpu 1
# Note URL: https://thyroid-lab-api-xxx-uc.a.run.app
# Then update frontend envs and redeploy both frontends as above
```

---

## Option C — Everything on Firebase (Hosting + Functions) — Node Functions only

If you insist on *only* Firebase, you must rewrite the FastAPI backend as Node Cloud Functions or deploy it as Cloud Run (above) and keep Firebase Hosting for frontend. Firebase Functions Python (2nd gen) also works but is heavier to set up; ask if you want a `functions/` Node wrapper.

For now, **Hosting-only** config is ready (`firebase.json` serves `frontend/out`). Deploy Hosting as in Option B step 2, keep backend on Vercel/Cloud Run.

---

## Environment — what to set where

| Where | Var | Value Example |
|-------|-----|---------------|
| Vercel Frontend | `NEXT_PUBLIC_API_URL` | `https://thyroid-lab-api.vercel.app` |
| Vercel Backend | `SECRET_KEY` | `openssl rand -hex 32` |
| Vercel Backend | `ALLOWED_ORIGINS` | `https://<frontend>.vercel.app,https://<frontend>.web.app` |
| Vercel Backend | `DATABASE_URL` | `postgresql://...` (or leave SQLite ephemeral) |
| Firebase Hosting | `NEXT_PUBLIC_API_URL` (build-time) | same backend URL, set in `frontend/.env.local` before `FIREBASE_BUILD=true npm run build` |
| Cloud Run | `SECRET_KEY`, `ALLOWED_ORIGINS`, `DATABASE_URL` | as above via `--set-env-vars` |

**CORS:** `backend/app/main.py:28` now allows `*.vercel.app`, `*.web.app`, `*.firebaseapp.com`, `*.run.app` + `ALLOWED_ORIGINS` env. No code change needed.

---

## Step-by-step for you (copy-paste)

```bash
# 1 — Verify local
cd "AI-Powered Thyroid/frontend" && npm run build
cd "../backend" && python -c "from app.main import app; print('backend ok')"

# 2 — Vercel frontend
cd "../frontend"
vercel login
vercel env add NEXT_PUBLIC_API_URL   # paste backend URL after you deploy backend, or use http://127.0.0.1:8000 for preview
vercel --prod

# 3 — Vercel backend (if using Vercel for API)
cd "../backend"
vercel --prod

# 4 — Firebase frontend (second publish)
firebase login
firebase use thyroid-lab-intelligence  # or your project
cd "../frontend"
echo "NEXT_PUBLIC_API_URL=https://thyroid-lab-api.vercel.app" > .env.local
FIREBASE_BUILD=true npm run build
cd ..
firebase deploy --only hosting
# → Hosting URL: https://thyroid-lab-intelligence.web.app
```

---

## Important production notes

- **SQLite on Vercel/Firebase is ephemeral** — data resets on redeploy/cold start. For real publishing, switch `DATABASE_URL` to **Vercel Postgres / Neon / Supabase** (add to Vercel env, `sqlalchemy` will auto-use Postgres when URL starts with `postgresql://`).
- **Cold start:** First request to Vercel Python after idle ~2-5s (loads XGBoost 369K + scaler). Subsequent <300ms.
- **CORS:** After you get final frontend URLs, add them to backend `ALLOWED_ORIGINS` and redeploy backend.
- **Rewrites:** In production frontend does **not** use Next.js rewrites; it calls `NEXT_PUBLIC_API_URL` directly. Local dev still proxies to `127.0.0.1:8000`.
- **Cleaning Firebase static warning:** `FIREBASE_BUILD=true` intentionally disables rewrites for `output: export` — the warning is expected.

---

## Troubleshooting

```bash
vercel --version   # should be 59.x
firebase --version # 15.x
vercel logs <deployment-url>  # backend logs
firebase hosting:channel:list
# If Vercel plugin not found:
cat ~/.config/opencode/opencode.jsonc  # should contain superpowers@git+...
# If frontend 404 on Vercel, check vercel.json is in frontend/ and NEXT_PUBLIC_API_URL is set
# If backend 500, check vercel logs for missing env vars or Python version (needs 3.11)
```

Need me to run `vercel login` / `firebase login` and deploy now? Say `deploy to vercel` or `deploy to firebase` and I’ll execute.
