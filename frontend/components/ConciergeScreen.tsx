"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import { CharacterVideo } from "@/components/avatar/CharacterVideo";
import { Skeleton } from "@/components/ui";
import { MicButton } from "@/components/voice/MicButton";
import { useConcierge } from "@/hooks/useConcierge";
import { useWakeWord } from "@/hooks/useWakeWord";
import { STRINGS } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { ApiError, api } from "@/services/api";
import type { HotelInfo, Lang } from "@/types";

const LANG_KEY = "aura-lang";

export function ConciergeScreen() {
  const params = useSearchParams();
  const [hotel, setHotel] = useState<HotelInfo | null>(null);
  const [hotelError, setHotelError] = useState<string | null>(null);
  const c = useConcierge(hotel);
  const { s, phase } = c;

  useEffect(() => {
    api
      .hotel()
      .then(setHotel)
      .catch((e) =>
        setHotelError(
          e instanceof ApiError ? e.message : STRINGS.en.serviceDown
        )
      );
    const saved = (params.get("lang") ||
      localStorage.getItem(LANG_KEY)) as Lang | null;
    if (saved && ["en", "ta", "hi"].includes(saved)) c.setLanguage(saved);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const askParam = params.get("ask");
  const pending = useRef(askParam);
  const begin = () =>
    void c.begin(
      pending.current
        ? { text: s.askWhy, dishId: pending.current }
        : undefined
    );

  const onWake = (query?: string) => {
    if (query) {
      if (!c.started) {
        void c.begin({ text: query });
      } else {
        void c.send(query);
      }
    } else {
      if (!c.started) {
        setTimeout(() => {
          begin();
        }, 150);
      } else if (phase === "IDLE") {
        setTimeout(() => {
          c.onMic();
        }, 150);
      }
    }
  };

  const wakeWord = useWakeWord({
    onWake,
    phase,
    language: c.language,
    disabled: !c.micOk,
    onNotice: c.showNotice,
  });

  const statusLabel =
    phase === "LISTENING"
      ? s.listening
      : phase === "THINKING"
      ? c.toolStatus
        ? s.tools[c.toolStatus] ?? s.thinking
        : s.thinking
      : phase === "SPEAKING"
      ? s.speaking
      : phase === "ERROR"
      ? s.errorState
      : wakeWord.isListening
      ? 'Say "Hey Aura" or tap mic'
      : s.idleHint;

  /* ── Error / loading states ───────────────────────────────── */
  if (hotelError)
    return (
      <main className="flex h-dvh items-center justify-center p-6 bg-[#07050d]">
        <p className="max-w-sm text-center text-purple-200/70">{hotelError}</p>
      </main>
    );
  if (!hotel)
    return (
      <main className="flex h-dvh items-center justify-center p-6 bg-[#07050d]">
        <Skeleton className="h-96 w-72 rounded-3xl bg-purple-950/30" />
      </main>
    );

  /* ─── MAIN ASSISTANT SCREEN ──────────────────────────────── */
  return (
    <div className="relative flex h-dvh w-full overflow-hidden bg-[#07050d] text-white">

      {/* Ambient purple/violet glow effects */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute left-[30%] top-[10%] h-[60vmin] w-[60vmin] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(147,51,234,0.18),transparent_70%)] blur-3xl animate-pulse" />
        <div className="absolute right-[10%] bottom-[10%] h-[55vmin] w-[55vmin] rounded-full bg-[radial-gradient(closest-side,rgba(168,85,247,0.12),transparent_70%)] blur-3xl" />
      </div>

      {/* ══ LEFT SIDEBAR ═══════════════════════════════════════ */}
      <aside
        aria-label="Sidebar"
        className="
          relative z-20 flex w-16 shrink-0 flex-col items-center border-r border-purple-500/10
          bg-[#0a0714]/80 backdrop-blur-2xl py-6
          sm:w-52 lg:w-60
        "
      >
        {/* Branding */}
        <div className="flex w-full flex-col items-center px-3 sm:items-start sm:px-6">
          <span className="font-display text-2xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-purple-200 via-violet-100 to-purple-300 sm:text-3xl">
            AURA
          </span>
          <p className="mt-1 hidden truncate text-xs font-medium tracking-wide text-purple-300/80 sm:block">
            {hotel.name}
          </p>
          <p className="hidden truncate text-[11px] text-purple-400/50 sm:block">
            {hotel.restaurant.name}
          </p>
        </div>

        <div className="mt-4 h-px w-full bg-purple-500/10" />

        {/* Status indicator badge */}
        <div className="mt-4 hidden w-full px-4 sm:block">
          <div className="flex items-center gap-2 rounded-xl border border-purple-500/15 bg-purple-950/30 px-3 py-2 text-xs text-purple-300/80">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                phase === "LISTENING"
                  ? "bg-purple-400 animate-ping"
                  : phase === "SPEAKING"
                  ? "bg-violet-400 animate-pulse"
                  : phase === "THINKING"
                  ? "bg-purple-300 animate-spin"
                  : "bg-purple-500/50"
              )}
            />
            <span className="truncate">{statusLabel}</span>
          </div>
        </div>

        {/* ── Hey Aura Wake Word Control (Desktop) ── */}
        <div className="mt-3 hidden w-full px-4 sm:block">
          <div
            className={cn(
              "flex flex-col gap-2 rounded-xl border p-3 transition-all",
              wakeWord.wakeWordEnabled
                ? "border-purple-500/30 bg-purple-950/40 shadow-[0_0_15px_rgba(168,85,247,0.12)]"
                : "border-purple-500/10 bg-purple-950/20"
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "relative flex h-2 w-2 items-center justify-center rounded-full",
                    wakeWord.isListening
                      ? "bg-emerald-400"
                      : wakeWord.wakeWordEnabled
                      ? "bg-purple-400"
                      : "bg-purple-500/30"
                  )}
                >
                  {wakeWord.isListening && (
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  )}
                </span>
                <span className="text-xs font-medium tracking-wide text-purple-200">
                  “Hey Aura”
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={wakeWord.wakeWordEnabled}
                aria-label="Toggle Hey Aura wake word"
                onClick={wakeWord.toggleWakeWord}
                className={cn(
                  "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                  wakeWord.wakeWordEnabled ? "bg-purple-600" : "bg-purple-950/80 border-purple-500/30"
                )}
              >
                <span
                  className={cn(
                    "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out",
                    wakeWord.wakeWordEnabled ? "translate-x-4" : "translate-x-0"
                  )}
                />
              </button>
            </div>
            <p className="text-[10px] leading-tight text-purple-300/60">
              {!wakeWord.supported
                ? "Wake word not supported in browser"
                : wakeWord.error
                ? wakeWord.error
                : wakeWord.isListening
                ? "Listening for “Hey Aura”…"
                : wakeWord.wakeWordEnabled
                ? "Active (listening paused)"
                : "Wake word disabled"}
            </p>
          </div>
        </div>

        {/* ── Hey Aura Wake Word Control (Mobile w-16 sidebar) ── */}
        <div className="mt-3 flex flex-col items-center sm:hidden">
          <button
            type="button"
            aria-label="Toggle Hey Aura wake word"
            onClick={wakeWord.toggleWakeWord}
            title={wakeWord.wakeWordEnabled ? "Wake word active" : "Enable Hey Aura wake word"}
            className={cn(
              "relative flex h-9 w-9 items-center justify-center rounded-xl border text-[9px] font-bold tracking-wider transition-all",
              wakeWord.isListening
                ? "border-emerald-500/50 bg-emerald-950/40 text-emerald-300 shadow-[0_0_10px_rgba(52,211,153,0.3)]"
                : wakeWord.wakeWordEnabled
                ? "border-purple-500/40 bg-purple-950/50 text-purple-200"
                : "border-purple-500/15 bg-purple-950/20 text-purple-400/50"
            )}
          >
            WAKE
            {wakeWord.isListening && (
              <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
            )}
          </button>
        </div>

        <div className="flex-1" />

        {/* Minimal indicator */}
        <div className="hidden px-4 text-center sm:block">
          <p className="text-[10px] tracking-wider text-purple-400/40 uppercase">
            AI Voice Concierge
          </p>
        </div>
      </aside>

      {/* ══ MAIN CONTENT AREA ══════════════════════════════════ */}
      <main className="relative z-10 flex min-w-0 flex-1 flex-col items-center justify-between overflow-hidden">

        {/* ── Character Video: Full-window background layer ── */}
        <div className="absolute inset-0 h-full w-full overflow-hidden pointer-events-none">
          <CharacterVideo
            phase={phase}
            className="h-full w-full"
          />
        </div>

        {/* Notice banner (if any) */}
        {c.notice ? (
          <div
            role="alert"
            className="relative z-30 animate-rise mx-4 mt-4 flex shrink-0 items-center gap-3 rounded-2xl border border-purple-500/20 bg-purple-950/70 px-4 py-2 text-xs text-purple-200 backdrop-blur-xl shadow-lg"
          >
            <span className="flex-1">{c.notice}</span>
            <button
              aria-label="Dismiss"
              onClick={c.dismissNotice}
              className="text-purple-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="h-4 shrink-0" />
        )}

        {/* Flexible spacer */}
        <div className="flex-1 min-h-0" />

        {/* ── Perfectly Circular Glowing Microphone Button ── */}
        <div className="relative z-30 flex shrink-0 flex-col items-center justify-center pb-6 pt-2 sm:pb-8">
          <MicButton
            phase={phase}
            onClick={!c.started ? begin : c.onMic}
            label={
              phase === "LISTENING"
                ? s.sendNow
                : phase === "SPEAKING"
                ? s.tapToInterrupt
                : wakeWord.isListening
                ? 'Say "Hey Aura" or tap'
                : s.mic
            }
            disabled={!c.micOk}
          />
        </div>
      </main>
    </div>

  );
}
