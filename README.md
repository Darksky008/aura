# AURA - AI Dining Concierge for Aurelia Grand Hotel

A voice-first, tool-driven digital concierge for hotel restaurants. A chef-costumed avatar (waist-up, with hand gestures,
gaze and audio-driven lip movement) answers menu, ingredient, allergen, dietary and recommendation questions in
**English, Tamil and Hindi** - by voice or text - using the hotel's real menu data stored in PostgreSQL.

> The LLM is **not** the database. Every menu fact is fetched through backend tools; the model only reasons over what the tools return.

Demo data: **Aurelia Grand Hotel / Saffron Terrace**, 7 fictional dishes, seeded automatically.

## Architecture

```
Guest (browser, mic + speakers)
   │  Voice: MediaRecorder + VAD ──► POST /api/voice/transcribe ──► Groq Whisper (language hint + menu vocabulary)
   │  Text : chat box
   ▼
Next.js 16 / React 19 (Vercel)  ── useConcierge hook ── AvatarProvider (swappable) ── VoiceProvider (swappable)
   │  POST /api/assistant/chat/stream  (NDJSON: tool events → final answer)
   ▼
FastAPI (Render)
   ├─ AssistantService  ── AIProvider ─┬─ GroqProvider  (openai/gpt-oss-120b, tool calling)
   │       │                           └─ OfflineProvider (deterministic; no key / automatic fallback / tests)
   │       ▼  tool loop (max 5 steps)
   ├─ Tools: search_menu · get_dish_details · get_ingredients · get_allergens · get_dishes_by_dietary_preference
   │         get_dishes_by_spice_level · get_today_specials · get_available_dishes · recommend_dishes
   │         compare_dishes · search_knowledge
   ├─ MenuService · RecommendationEngine · KnowledgeService (Postgres FTS, pgvector-ready)
   ├─ Voice: GroqSpeechToText · TTSProvider (Azure | Edge neural voices)  → /api/voice/tts
   └─ PostgreSQL (hotel_id on every row, tenant-checked)
```

## What's inside

| Area | Highlights |
|---|---|
| **Avatar** | Procedural SVG chef (toque, whites, saffron neckerchief), waist-up. 12 gestures (present, point, hand-on-chest, welcome, wave, "one moment"…), gaze with glances and pointer-follow, blinking, brows, head nods, breathing. Mouth is driven by the **real audio** (loudness → jaw opening, spectral brightness → lip width). States: IDLE / LISTENING / THINKING / SPEAKING / ERROR. Replaceable via `AvatarProvider`. |
| **Listening (STT)** | Noise-calibrated voice-activity detection, 1.3 s end-of-speech silence, echo/noise suppression, hands-free loop, tap to send/interrupt. Server Whisper (`whisper-large-v3`) with temperature 0, language hint, **menu-vocabulary prompt in the guest's own script**, confidence scoring, silence-hallucination guard, "please repeat" handling. Falls back to the browser Web Speech API. |
| **Speaking (TTS)** | Neural voices `en-IN-Neerja`, `ta-IN-Pallavi`, `hi-IN-Swara` (Azure or Edge), sentence-pipelined so speech starts fast; voice chosen from the reply's script. Falls back to device voices automatically. |
| **Safety** | Dietary claims need an explicit `yes` in the DB (`unknown` is never claimed). Allergy answers always carry a localized cross-contact notice, enforced server-side. Unknown facts → fixed "I don't have that information…" sentence. Prices are never invented (null = not quoted). Unavailable dishes are never recommended. Ingredient-vs-allergen cross-check. |
| **Menu** | Explorer with filters, local dish artwork, detail panel, "Ask AURA about this dish". |
| **Admin** (`/admin`) | Dashboard KPIs & charts, menu CRUD (validated), specials, knowledge base, AI assistant status + test console, conversations, analytics, settings. Protected by `ADMIN_API_KEY`. |
| **SaaS-ready** | `hotel_id`/`restaurant_id` on every entity, tenant-scoped queries, `X-Hotel-Slug` resolution, provider abstractions, analytics event schema. |

## Folder structure

```
backend/   FastAPI app  (app/api · models · schemas · services/{ai,menu,recommendation,knowledge,voice,analytics} · tools · database · core)
           seed/ (demo data + idempotent seeder) · tests/ (58 tests) · seed.py
frontend/  Next.js app  (app/ · components/{avatar,chat,voice,menu,dashboard,ui} · hooks/useConcierge · services/{api,voice/*} · lib/i18n)
docker/    backend.Dockerfile      render.yaml   docker-compose.yml   docs/
```

## Run locally

Prerequisites: Python 3.12, Node 20.9+, Docker (for PostgreSQL) or a local Postgres.

```bash
# 1. configuration
cp .env.example .env            # add GROQ_API_KEY for the full AI; works without it in offline demo mode
cp frontend/.env.example frontend/.env.local

# 2. database
docker compose up -d db         # or point DATABASE_URL at any Postgres / Supabase

# 3. backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                  # creates tables + seeds Aurelia Grand Hotel (python seed.py --reset to rebuild)
uvicorn app.main:app --reload   # http://localhost:8000/docs

# 4. frontend (new terminal)
cd frontend
npm install
npm run dev                     # http://localhost:3000   (admin: /admin)
```

Or run DB + API together: `docker compose up --build`, then start the frontend.

> Microphone access needs `https://` or `localhost`. On Vercel this is automatic.

### Groq setup
1. Create a key at <https://console.groq.com/keys> → `GROQ_API_KEY` (backend only - never in the frontend env).
2. Default `GROQ_MODEL=openai/gpt-oss-120b` (tool calling). **`llama-3.3-70b-versatile` was scheduled for shutdown on 16 Aug 2026** - check <https://console.groq.com/docs/deprecations> for current models and change only this variable.
3. The same key powers speech recognition (`GROQ_STT_MODEL=whisper-large-v3`).
4. Groq's own TTS does not cover Tamil/Hindi, so voice output uses Azure/Edge neural voices (below).

### Voice output providers
`TTS_PROVIDER=auto` uses **Azure Speech** if `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` are set (recommended for a real venue), otherwise the free **Edge neural voices** via the `edge-tts` package (unofficial endpoint - fine for demos, can break without notice). If both fail the browser's own voice is used; if the device has no voice for Tamil/Hindi, replies show as text and a notice appears.

## Tests

```bash
cd backend && pytest        # 58 tests: menu, ingredients, allergens, dietary/spice filters, recommendations, all 10 spec scenarios,
                            # unknown-info handling, Groq tool loop (mocked HTTP), STT guards, voice endpoints, admin CRUD, tenant isolation
cd frontend && npm run typecheck && npm run build
```

## API (full docs at `/docs`)

`GET /api/hotels/current` · `GET /api/menu` · `GET /api/menu/{id}` · `GET /api/specials` · `POST /api/assistant/session` ·
`POST /api/assistant/chat` · `POST /api/assistant/chat/stream` · `POST /api/assistant/recommend` · `GET /api/voice/capabilities` ·
`POST /api/voice/transcribe` · `POST /api/voice/tts` · `POST /api/analytics/events` · `/api/admin/*` (dishes, specials, knowledge, conversations, analytics, settings, assistant).

## Deploy

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** (Render backend + Vercel frontend, step by step) and **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** (voice pipeline, safety design, extension points).

## Extension points (production roadmap)

- **Real hotel data**: edit via `/admin`, or replace `backend/seed/demo_data.py`. Add hotels as new rows; route by `X-Hotel-Slug` / `NEXT_PUBLIC_HOTEL_SLUG` (or subdomain).
- **Realtime avatar vendor** (Tavus, HeyGen…): implement `AvatarProviderProps` - `components/avatar/providers.tsx`.
- **Realtime voice vendor**: implement `VoiceProvider` - `services/voice/types.ts`.
- **Semantic search / RAG**: add a pgvector column and implement `VectorBackend` - `services/knowledge/service.py`.
- **Auth & roles, POS/ordering, payments, WhatsApp**: add routers + a `users` table; every service already takes `hotel_id`.
- **Migrations**: tables are created on boot for the demo; switch to Alembic before production schema changes.

## Known limits

Rate limiting is in-memory (per instance). Edge TTS is an unofficial endpoint. Whisper accuracy for Tamil is good but not perfect in noisy rooms - the UI always shows what was heard and offers chat as an equal alternative. Dish images are generated local artwork, not photos.
