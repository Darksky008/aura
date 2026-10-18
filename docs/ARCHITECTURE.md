# Architecture notes

## Grounding: how hallucinations are prevented
1. **No menu in the prompt.** The system prompt holds persona + rules only. Facts arrive via tool calls (`app/tools`).
2. **Explicit tri-state data.** Dietary flags are `yes | no | unknown`. Only `yes` may be claimed; `unknown` is passed to the model verbatim. Price `null` → "not in menu data".
3. **Deterministic filtering.** Recommendations are computed in SQL/Python (`RecommendationEngine`); the LLM only explains them. Unavailable dishes are excluded.
4. **Allergen safety net.** `get_allergens` merges *declared* allergens with *ingredient keyword hits* (e.g. "Mustard seeds" for a mustard question even though mustard isn't a tracked allergen) and flags the difference rather than calling a dish safe.
5. **Server-enforced notices.** If any allergy-related tool ran, the localized cross-contact sentence is appended unless the model already said it (`AssistantService._postprocess`). The "I don't have that information…" sentence is fixed text in three languages (`core/i18n.py`).
6. **Ambiguity is surfaced.** "biryani" matches two dishes → the tool returns candidates and the assistant asks which one.
7. **Graceful degradation.** Groq error → `OfflineProvider` (same tools, deterministic answers) → friendly localized apology. Raw errors never reach guests.

## Voice pipeline
```
tap / hands-free ─► getUserMedia (echoCancellation, noiseSuppression, AGC)
   ─► 450 ms noise calibration ─► adaptive VAD (start: 140 ms above 3× noise floor, end: 1.3 s below 1.8×)
   ─► MediaRecorder blob ─► POST /api/voice/transcribe
         Groq Whisper: language=en|ta|hi, temperature=0, prompt = menu vocabulary in that script, verbose_json
         ─► confidence = exp(avg_logprob), no_speech_prob, compression_ratio ─► ok | empty | unclear
   ─► useConcierge.send ─► NDJSON stream (tool status) ─► final reply
   ─► sentence split ─► /api/voice/tts per sentence (prefetch 2 ahead) ─► decodeAudioData ─► AnalyserNode ─► speakers
                                                                              └► lip level {open, wide} @30 Hz ─► avatar mouth
```
- Half-duplex: the mic is never open while AURA speaks (no echo loops). Tapping the mic interrupts her (barge-in).
- Two consecutive "unclear" results end the hands-free loop and suggest typing; silence never loops.
- Replies are plain spoken sentences (no markdown); `clean_for_speech` normalises anything that slips through.

## Avatar contract
`AvatarProviderProps = { phase, lipRef, cue }`. `lipRef.current = { open, wide }` is written by the synthesizer ~30×/s (real audio analysis, or a simulation for browser voices) and read by the avatar in its own animation loop - no React re-render per audio frame. A vendor avatar (Tavus/HeyGen) implements the same props; `ExternalAvatarProvider` is the integration point.

## Multi-tenancy
Every business table has `hotel_id`; all service queries filter by it; admin writes validate ownership (dish/category/special/document). Tenant is resolved from `X-Hotel-Slug` → `?hotel=` → `DEFAULT_HOTEL_SLUG`. For production add auth (JWT with hotel claims) in `api/deps.py::get_tenant`.

## Data model
`hotels → restaurants → menu_categories → dishes → {dish_ingredients→ingredients, dish_allergens→allergens, dish_dietary_tags→dietary_tags(value yes/no)}`,
`specials`, `knowledge_documents`, `conversation_sessions → conversation_messages`, `analytics_events` (structured payloads only - never guest free text).
UUID keys, `created_at/updated_at`, portable to Supabase Postgres.

## Analytics events
`conversation_started · question_asked · dish_viewed · dish_recommended · special_viewed · ingredient_question · allergen_question · dietary_question · voice_used · language_changed`
(server-emitted from tool usage; UI-emitted ones go through the whitelisted `POST /api/analytics/events`).
