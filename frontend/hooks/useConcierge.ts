"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AvatarCue } from "@/components/avatar/ChefAvatar";
import { STRINGS, detectLang } from "@/lib/i18n";
import { uid } from "@/lib/utils";
import { ApiError, api } from "@/services/api";
import { createVoiceProvider } from "@/services/voice/provider";
import type { VoiceProvider } from "@/services/voice/types";
import type { ChatMessage, FinalEvent, HotelInfo, Lang, LipLevel, Mode, Phase, VoiceCaps } from "@/types";

/**
 * The conversation brain of the customer screen. UI components stay dumb: they render `phase`, `messages`,
 * `lipRef` and call the actions below. All voice + AI orchestration lives here (and in services/).
 *
 *   mic tap -> LISTENING (VAD + Whisper) -> THINKING (tool-calling assistant) -> SPEAKING (neural TTS + lip-sync) -> LISTENING ...
 */
export function useConcierge(hotel: HotelInfo | null) {
  const [language, setLanguageState] = useState<Lang>("en");
  const [mode, setModeState] = useState<Mode>("voice");
  const [phase, setPhaseState] = useState<Phase>("IDLE");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const [heard, setHeard] = useState("");
  const [interim, setInterim] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [handsFree, setHandsFreeState] = useState(true);
  const [speakReplies, setSpeakRepliesState] = useState(true);
  const [micOk, setMicOk] = useState(true);
  const [provider, setProvider] = useState<string | null>(null);
  const [cue, setCue] = useState<AvatarCue | null>(null);

  const lipRef = useRef<LipLevel>({ open: 0, wide: 0.3 });
  const micLevelRef = useRef(0);
  const refs = useRef({ session: null as string | null, language: "en" as Lang, mode: "voice" as Mode, handsFree: true, speak: true, phase: "IDLE" as Phase, turn: 0, failures: 0, caps: null as VoiceCaps | null });
  const voiceRef = useRef<VoiceProvider | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const hotelRef = useRef(hotel);
  hotelRef.current = hotel;

  const s = STRINGS[language];
  const setPhase = useCallback((p: Phase) => { refs.current.phase = p; setPhaseState(p); }, []);

  // capabilities are fetched early so the right recognizer is chosen when the guest taps "begin"
  useEffect(() => { api.voiceCaps().then((c) => { refs.current.caps = c; }).catch(() => undefined); }, []);

  const voice = useCallback((): VoiceProvider => {
    if (!voiceRef.current) {
      voiceRef.current = createVoiceProvider({
        serverStt: refs.current.caps?.stt ?? true,
        onFallback: (r) => setNotice(STRINGS[refs.current.language][r === "browser" ? "voiceFallback" : "voiceNone"]),
      });
    }
    return voiceRef.current;
  }, []);

  const addMessage = useCallback((m: Omit<ChatMessage, "id">) => setMessages((prev) => [...prev, { ...m, id: uid() }]), []);
  const flashError = useCallback(() => { setPhase("ERROR"); window.setTimeout(() => { if (refs.current.phase === "ERROR") setPhase("IDLE"); }, 2600); }, [setPhase]);

  const speak = useCallback(async (text: string) => {
    if (!refs.current.speak) { setPhase("IDLE"); return; }
    try {
      await voice().synthesizer.speak(text, detectLang(text, refs.current.language), lipRef, {
        onStart: () => {
          setPhase("SPEAKING");
        },
        onEnd: () => {
          if (refs.current.phase === "SPEAKING") setPhase("IDLE");
        },
      });
    }
    catch { /* a failed voice never blocks the conversation - the text is on screen */ }
    finally { lipRef.current = { open: 0, wide: 0.3 }; if (refs.current.phase === "SPEAKING") setPhase("IDLE"); }
  }, [setPhase, voice]);

  const interrupt = useCallback(() => {
    refs.current.turn++;
    abortRef.current?.abort();
    voiceRef.current?.recognizer.abort();
    voiceRef.current?.synthesizer.stop();
    lipRef.current = { open: 0, wide: 0.3 };
    micLevelRef.current = 0;
    setToolStatus(null);
    setPhase("IDLE");
  }, [setPhase]);

  // forward declarations (listen <-> send are mutually recursive)
  const listenRef = useRef<() => Promise<void>>(async () => undefined);

  const afterReply = useCallback((turn: number) => {
    const r = refs.current;
    if (turn === r.turn && r.mode === "voice" && r.handsFree && r.speak) void listenRef.current();
  }, []);

  const send = useCallback(async (text: string, opts?: { dishId?: string; silent?: boolean }) => {
    const clean = text.trim();
    if (!clean) return;
    const r = refs.current;
    const turn = ++r.turn;
    voiceRef.current?.recognizer.abort();
    voiceRef.current?.synthesizer.stop();
    abortRef.current?.abort();
    const ac = (abortRef.current = new AbortController());
    setNotice(null);
    addMessage({ role: "user", text: clean, lang: r.language });
    setPhase("THINKING");
    setToolStatus(null);

    let final: FinalEvent | null = null;
    let failure: string | null = null;
    const run = () => api.chatStream({ message: clean, session_id: r.session, language: r.language, dish_id: opts?.dishId }, (e) => {
      if (turn !== r.turn) return;
      if (e.type === "tool") setToolStatus(e.name);
      else if (e.type === "final") final = e;
      else if (e.type === "error") failure = e.message;
    }, ac.signal);
    try {
      try { await run(); }
      catch (e) {
        if (e instanceof ApiError && e.status === 404 && r.session) { r.session = null; setNotice(STRINGS[r.language].sessionExpired); await run(); }
        else throw e;
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      failure = e instanceof ApiError && e.status === 0 ? STRINGS[r.language].serviceDown : e instanceof ApiError ? e.message : STRINGS[r.language].serviceDown;
    }
    if (turn !== r.turn) return;
    setToolStatus(null);
    const fin = final as FinalEvent | null;
    if (fin) {
      r.session = fin.session_id;
      setProvider(fin.provider);
      addMessage({ role: "assistant", text: fin.reply, tools: fin.tools_used, lang: detectLang(fin.reply, r.language) });
      await speak(fin.reply);
      afterReply(turn);
    } else {
      addMessage({ role: "assistant", text: failure ?? STRINGS[r.language].serviceDown, failed: true, retryText: clean });
      flashError();
    }
  }, [addMessage, afterReply, flashError, setPhase, speak]);

  const listen = useCallback(async () => {
    const r = refs.current;
    const v = voice();
    const turn = ++r.turn;
    v.synthesizer.stop();
    abortRef.current?.abort();
    setHeard(""); setInterim(""); setNotice(null);
    setPhase("LISTENING");
    const result = await v.recognizer.start({
      language: r.language,
      onLevel: (l) => { micLevelRef.current = l; },
      onInterim: setInterim,
    });
    if (turn !== r.turn) return; // interrupted, or superseded by another action
    micLevelRef.current = 0;
    setInterim("");
    switch (result.status) {
      case "ok":
        r.failures = 0;
        setHeard(result.text);
        void api.event("voice_used", r.session, { language: r.language });
        const cleanQuestion = result.text.replace(/^\s*(hey|hay|hi|ok)?\s*aura[,\s]+/i, "").trim() || result.text;
        await send(cleanQuestion);
        break;
      case "unclear": {
        r.failures++;
        const msg = r.failures >= 2 ? STRINGS[r.language].stillNoCatch : STRINGS[r.language].didntCatch;
        addMessage({ role: "assistant", text: msg, lang: r.language });
        await speak(msg);
        if (r.failures < 2) afterReply(turn); else { r.failures = 0; setPhase("IDLE"); }
        break;
      }
      case "error":
        if (result.code === "denied" || result.code === "unsupported") { setMicOk(false); r.mode = "chat"; setModeState("chat"); }
        setNotice(result.code === "denied" ? STRINGS[r.language].micBlocked : result.code === "unsupported" ? STRINGS[r.language].micUnsupported : STRINGS[r.language].sttDown);
        flashError();
        break;
      default: // no_speech | aborted
        setPhase("IDLE");
    }
  }, [addMessage, afterReply, flashError, send, setPhase, speak, voice]);
  listenRef.current = listen;

  const begin = useCallback(async (initial?: { text: string; dishId?: string }) => {
    const r = refs.current;
    if (r.phase === "SPEAKING" || r.phase === "THINKING") return;
    setStarted(true);
    setPhase("THINKING");
    const v = voice();
    await v.synthesizer.unlock().catch(() => undefined); // inside the tap: unlocks audio on iOS/Chrome
    if (!r.session) {
      try { r.session = (await api.createSession(r.language)).session_id; } catch { setNotice(STRINGS[r.language].serviceDown); }
    }
    setCue({ name: "wave", nonce: Date.now(), seconds: 2.6 });
    const name = STRINGS[r.language].restaurantName(hotelRef.current?.restaurant.name ?? "our restaurant");
    const greeting = STRINGS[r.language].greeting(name);
    addMessage({ role: "assistant", text: greeting, lang: r.language });
    const turn = ++r.turn;
    await speak(greeting);
    if (initial) { await send(initial.text, { dishId: initial.dishId }); return; }
    afterReply(turn);
  }, [addMessage, afterReply, send, speak, voice]);

  const onMic = useCallback(() => {
    const p = refs.current.phase;
    if (p === "LISTENING") { voiceRef.current?.recognizer.finish(); return; }
    if (p === "SPEAKING" || p === "THINKING") interrupt();
    void listenRef.current();
  }, [interrupt]);

  const setLanguage = useCallback((l: Lang) => {
    const r = refs.current;
    if (l === r.language) return;
    if (started) void api.event("language_changed", r.session, { from: r.language, to: l });
    r.language = l;
    setLanguageState(l);
    if (started) {
      interrupt();
      const msg = STRINGS[l].switched;
      addMessage({ role: "assistant", text: msg, lang: l });
      const turn = ++r.turn;
      void speak(msg).then(() => afterReply(turn));
    }
  }, [addMessage, afterReply, interrupt, speak, started]);

  const setMode = useCallback((m: Mode) => {
    refs.current.mode = m;
    setModeState(m);
    if (m === "chat") { interrupt(); voiceRef.current?.recognizer.release(); }
  }, [interrupt]);

  const setHandsFree = useCallback((v: boolean) => { refs.current.handsFree = v; setHandsFreeState(v); }, []);
  const setSpeakReplies = useCallback((v: boolean) => { refs.current.speak = v; setSpeakRepliesState(v); if (!v) voiceRef.current?.synthesizer.stop(); }, []);

  const clear = useCallback(() => { interrupt(); setMessages([]); refs.current.session = null; refs.current.failures = 0; void api.createSession(refs.current.language).then((x) => { refs.current.session = x.session_id; }).catch(() => undefined); }, [interrupt]);

  useEffect(() => {
    const onHide = () => { if (document.hidden) interrupt(); };
    document.addEventListener("visibilitychange", onHide);
    return () => { document.removeEventListener("visibilitychange", onHide); interrupt(); voiceRef.current?.recognizer.release(); };
  }, [interrupt]);

  const lastReply = useMemo(() => [...messages].reverse().find((m) => m.role === "assistant")?.text ?? "", [messages]);

  return { s, language, mode, phase, messages, toolStatus, started, heard, interim, notice, handsFree, speakReplies, micOk, provider, cue, lastReply, lipRef, micLevelRef,
    begin, send, onMic, interrupt, setLanguage, setMode, setHandsFree, setSpeakReplies, clear, dismissNotice: () => setNotice(null), showNotice: (msg: string) => setNotice(msg) };
}
