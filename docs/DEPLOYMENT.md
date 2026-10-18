# Deployment: Render (backend + Postgres) and Vercel (frontend)

Deploy the **backend first** (the frontend needs its URL), then the frontend, then come back to set CORS.

## 0. Put the project on GitHub
```bash
cd hotel-ai-concierge
git init && git add . && git commit -m "AURA concierge"
# create an empty GitHub repo, then:
git remote add origin https://github.com/<you>/<repo>.git && git push -u origin main
```
`.env` files are git-ignored; never commit keys.

## 1. Backend on Render

**Option A - Blueprint (recommended):** Render dashboard → *New +* → *Blueprint* → pick the repo. `render.yaml` creates the Postgres database and the `aura-api` web service, wires `DATABASE_URL`, generates `ADMIN_API_KEY`, and seeds the demo hotel on first boot (`AUTO_SEED=true`).

**Option B - manual:** *New +* → *PostgreSQL* (copy the **Internal** connection string) → *New +* → *Web Service* →
- Root Directory `backend` · Runtime `Python 3`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'`
- Health check path: `/api/health`
- Env vars: see table below.

| Variable | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.8` |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Render Postgres connection string (postgres:// is auto-converted) |
| `GROQ_API_KEY` | your Groq key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` (verify at console.groq.com/docs/models) |
| `GROQ_STT_MODEL` | `whisper-large-v3` |
| `ADMIN_API_KEY` | long random string (Blueprint generates one) |
| `AUTO_SEED` | `true` for the demo (free plans have no shell) |
| `CORS_ORIGINS` | your Vercel URL, e.g. `https://aura-xyz.vercel.app` (set in step 3) |
| `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` | optional, production-grade Tamil/Hindi voices |

Verify: open `https://<service>.onrender.com/docs` and `/api/health`, then `/api/menu` - you should see the 7 dishes.

**Free-plan notes:** the web service sleeps after ~15 min idle (first request takes up to ~50 s - open the site once before a demo), and the free Postgres expires after 30 days. For a live venue use a Starter web service and a paid Postgres (or Supabase: paste its connection string into `DATABASE_URL`).

## 2. Frontend on Vercel
*Add New* → *Project* → import the repo →
- **Root Directory: `frontend`** (Framework: Next.js is auto-detected)
- Environment variable: `NEXT_PUBLIC_API_URL` = `https://<service>.onrender.com` (no trailing slash)
- Optional: `NEXT_PUBLIC_AVATAR_PROVIDER=demo`, `NEXT_PUBLIC_VOICE_PROVIDER=server`
- Deploy.

## 3. Close the loop (CORS)
In Render → `aura-api` → Environment: set `CORS_ORIGINS` to your exact Vercel URL (add your custom domain too, comma-separated) and save (the service redeploys). For Vercel preview deployments you may set `CORS_ORIGIN_REGEX=https://<project>-.*\.vercel\.app`.

## 4. Smoke test
1. Open the Vercel URL → **Tap to begin** → allow the microphone. AURA waves, greets in the selected language, then listens.
2. Say *"I want something vegetarian and not too spicy"* (try Tamil/Hindi via the language selector).
3. `/admin` → enter `ADMIN_API_KEY` → Menu, Specials, Conversations.
4. Admin → *AI Assistant* should show `groq · openai/gpt-oss-120b` and `whisper-large-v3`. If it says `offline`, `GROQ_API_KEY` isn't set.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| "We can't reach the concierge service" | Render service asleep (wait ~50 s) or wrong `NEXT_PUBLIC_API_URL`; redeploy Vercel after changing it. |
| Browser console CORS error | `CORS_ORIGINS` doesn't exactly match the Vercel URL (scheme + host, no trailing slash). |
| Mic button does nothing / "microphone blocked" | Allow the mic for the site; the page must be https. Use Chat mode meanwhile. |
| Listening works but AURA is silent | `/api/voice/capabilities` → check `tts`. If Edge TTS is blocked, add Azure Speech keys; otherwise the device voice is used. |
| Tamil/Hindi spoken by robotic/no voice | Device has no voice for the language and server TTS failed; configure Azure Speech. |
| `/admin` says "disabled" | `ADMIN_API_KEY` not set while `APP_ENV=production`. |
| `/api/menu` returns "venue isn't set up" | Database empty: set `AUTO_SEED=true` once, or run `python seed.py` in a Render shell. |
| LLM replies are the rule-based "offline" style | `GROQ_API_KEY` missing/invalid, or the model name was retired - update `GROQ_MODEL`. |
