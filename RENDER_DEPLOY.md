# UMCAO – Render Deployment Guide

This guide explains how UMCAO is configured for **Render** and how to fix **"Backend / API not connected"** issues.

---

## Why "API Not Connected" Happened Previously

1. **Missing `/api` suffix or scheme in `VITE_API_BASE_URL`:**
   - All FastAPI routes are under `/api/...` (e.g., `/api/health`, `/api/analyze`, `/api/code/analyze-run`).
   - `frontend/src/services/api.js` now automatically normalizes `VITE_API_BASE_URL` / `VITE_API_URL` (adding `https://` or `/api` if omitted) and falls back cleanly to `/api` in production or `http://127.0.0.1:8000/api` locally.
2. **Render Free-Tier Cold Start Timeout (3s was too short):**
   - Render Free Web Services sleep after 15 minutes of inactivity and take ~30–50 seconds to wake up.
   - `checkBackendHealth()` now waits up to **45 seconds** in production instead of timing out at 3 seconds.
3. **Strict CORS & Dynamic Port Binding:**
   - `backend/main.py` now permits explicit `CORS_ORIGINS` **plus** all `https://*.onrender.com` domains via `allow_origin_regex`, and binds to `0.0.0.0:$PORT`.

---

## Deployment Option 1: Single Unified Docker Service (Recommended)

Deploy **one** Web Service on Render that serves the React UI, FastAPI backend, **and** includes Python 3.12, Node.js, GCC, G++, and OpenJDK (so all 5 languages compile and execute!):

1. In Render Dashboard, click **New +** -> **Blueprint** (or **Web Service** using **Docker**).
2. Connect repository `https://github.com/HarshulRSolanki/UMCAO.git`.
3. Render automatically reads `render.yaml` + root `Dockerfile`.
4. Add Environment Variable in Render Dashboard:
   - `GEMINI_API_KEY` = your Google Gemini API key
   - `GEMINI_MODEL` = `gemini-3.5-flash-lite` *(optional)*
   - `SERVE_FRONTEND` = `true`
5. Click **Deploy**. Everything runs on a single URL (`https://umcao.onrender.com`) with zero CORS issues.

---

## Deployment Option 2: Separate Backend + Frontend Services on Render

If you already created two separate Render services:

### 1. Backend Web Service
- **Root Directory:** `backend`
- **Runtime:** `Docker` *(uses `backend/Dockerfile` — gives Python + Node + GCC + G++ + Java)*
  - *(Or Python 3 runtime with Build Command `pip install -r requirements.txt` and Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`)*
- **Health Check Path:** `/api/health` *(or `/health`)*
- **Environment Variables:**
  - `GEMINI_API_KEY` = your Gemini API key
  - `GEMINI_MODEL` = `gemini-3.5-flash-lite`
  - `CORS_ORIGINS` = `https://umcao.onrender.com` *(your exact frontend URL)*

### 2. Frontend Static Site
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`
- **Environment Variable:**
  - `VITE_API_BASE_URL` = `https://<your-backend-service-name>.onrender.com/api`
- **Important:** Because Vite bakes `VITE_*` variables into the bundle during build, click **Manual Deploy -> Clear build cache & deploy** on your Frontend service after setting `VITE_API_BASE_URL`.

