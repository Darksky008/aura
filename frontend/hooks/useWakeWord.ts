"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Lang, Phase } from "@/types";

/* eslint-disable @typescript-eslint/no-explicit-any */
type SpeechRecognitionCtor = new () => any;

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  return (
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition ||
    null
  );
}

const WAKE_WORD_REGEX = /\b(hey|hay|hi|ok|hello)?\s*(aura|ora|aurora|aroa|laurel)\b/i;
const WAKE_WORD_STORAGE_KEY = "aura-wake-word-enabled";

const LOCALE: Record<Lang, string> = {
  en: "en-US",
  ta: "ta-IN",
  hi: "hi-IN",
};

export interface UseWakeWordOptions {
  onWake: (query?: string) => void;
  phase: Phase;
  language?: Lang;
  disabled?: boolean;
  onNotice?: (msg: string) => void;
}

export function useWakeWord({
  onWake,
  phase,
  language = "en",
  disabled = false,
  onNotice,
}: UseWakeWordOptions) {
  const [wakeWordEnabled, setWakeWordEnabledState] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem(WAKE_WORD_STORAGE_KEY);
    if (saved !== null) return saved === "true";
    return true; // Default to active on supported devices
  });
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recRef = useRef<any>(null);
  const isTriggeringRef = useRef(false);
  const restartTimerRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef(0);
  const enabledRef = useRef(wakeWordEnabled);
  enabledRef.current = wakeWordEnabled;

  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  const onWakeRef = useRef(onWake);
  onWakeRef.current = onWake;

  const onNoticeRef = useRef(onNotice);
  onNoticeRef.current = onNotice;

  useEffect(() => {
    setSupported(!!getSpeechRecognitionCtor());
  }, []);

  const stopRecognition = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    const currentRec = recRef.current;
    recRef.current = null;
    if (currentRec) {
      try {
        currentRec.onresult = null;
        currentRec.onerror = null;
        currentRec.onend = null;
        currentRec.abort();
      } catch {
        /* ignore */
      }
    }
    setIsListening(false);
  }, []);

  const startRecognition = useCallback(() => {
    stopRecognition();

    if (!enabledRef.current || disabled) {
      setIsListening(false);
      return;
    }

    // Only listen when the assistant is completely IDLE
    if (phaseRef.current !== "IDLE") {
      setIsListening(false);
      return;
    }

    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      setSupported(false);
      setError("Speech recognition is not supported in this browser.");
      return;
    }

    try {
      const rec = new Ctor();
      recRef.current = rec;
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = LOCALE[language] || "en-US";
      rec.maxAlternatives = 2;

      rec.onstart = () => {
        setIsListening(true);
        setError(null);
        consecutiveErrorsRef.current = 0;
      };

      rec.onresult = (event: any) => {
        if (isTriggeringRef.current) return;

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          for (let j = 0; j < result.length; j++) {
            const transcript = result[j].transcript;
            const match = transcript.match(WAKE_WORD_REGEX);
            if (match && typeof match.index === "number") {
              isTriggeringRef.current = true;
              const trailing = transcript
                .slice(match.index + match[0].length)
                .replace(/^[,.?! ]+/, "")
                .trim();

              // Stop wake word recognizer immediately to free the microphone
              stopRecognition();

              // Safety timer to clear triggering lock if state does not change
              setTimeout(() => {
                isTriggeringRef.current = false;
              }, 4000);

              // Trigger assistant flow with extracted trailing question if present
              onWakeRef.current(trailing || undefined);
              return;
            }
          }
        }
      };

      rec.onerror = (e: any) => {
        if (e.error === "not-allowed" || e.error === "service-not-allowed") {
          // Pause until user interacts or grants permission; keep setting active
          setError("Microphone permission needed.");
          setIsListening(false);
          stopRecognition();
        } else if (e.error === "aborted") {
          // Expected when stopping or pausing
          setIsListening(false);
        } else if (e.error === "no-speech") {
          // Normal timeout on silence - will restart cleanly via onend
        } else {
          // Transient recognition error (audio-capture, network, etc.)
          consecutiveErrorsRef.current++;
        }
      };

      rec.onend = () => {
        setIsListening(false);
        recRef.current = null;

        // Restart continuous listening only if still enabled and assistant is IDLE
        if (enabledRef.current && !disabled && phaseRef.current === "IDLE" && !isTriggeringRef.current) {
          const delay = Math.min(350 + consecutiveErrorsRef.current * 300, 2500);
          restartTimerRef.current = setTimeout(() => {
            if (enabledRef.current && phaseRef.current === "IDLE" && !isTriggeringRef.current) {
              startRecognition();
            }
          }, delay);
        }
      };

      rec.start();
    } catch {
      setIsListening(false);
      consecutiveErrorsRef.current++;
      // If start failed (e.g. mic busy), retry with backoff if still enabled
      if (enabledRef.current && phaseRef.current === "IDLE") {
        const delay = Math.min(500 + consecutiveErrorsRef.current * 400, 2500);
        restartTimerRef.current = setTimeout(() => {
          if (enabledRef.current && phaseRef.current === "IDLE") {
            startRecognition();
          }
        }, delay);
      }
    }
  }, [disabled, language, stopRecognition]);

  // Handle phase changes (pause when assistant is active, resume when IDLE)
  useEffect(() => {
    if (!enabledRef.current || disabled) {
      stopRecognition();
      return;
    }

    if (phase === "IDLE") {
      isTriggeringRef.current = false;
      const t = setTimeout(() => {
        if (enabledRef.current && phaseRef.current === "IDLE") {
          startRecognition();
        }
      }, 350);
      return () => clearTimeout(t);
    } else {
      // LISTENING, THINKING, SPEAKING, ERROR -> Pause wake word listening
      stopRecognition();
    }
  }, [disabled, phase, startRecognition, stopRecognition]);

  // Clean up on unmount or tab backgrounding
  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.hidden) {
        stopRecognition();
      } else if (enabledRef.current && phaseRef.current === "IDLE") {
        setTimeout(startRecognition, 300);
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      stopRecognition();
    };
  }, [startRecognition, stopRecognition]);

  const toggleWakeWord = useCallback(() => {
    const nextState = !enabledRef.current;
    if (nextState && !getSpeechRecognitionCtor()) {
      onNoticeRef.current?.("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    enabledRef.current = nextState;
    setWakeWordEnabledState(nextState);
    if (typeof window !== "undefined") {
      try { localStorage.setItem(WAKE_WORD_STORAGE_KEY, String(nextState)); } catch { /* ignore */ }
    }
    setError(null);

    if (nextState) {
      startRecognition();
    } else {
      stopRecognition();
    }
  }, [startRecognition, stopRecognition]);

  return {
    wakeWordEnabled,
    isListening,
    supported,
    error,
    toggleWakeWord,
    setWakeWordEnabled: (v: boolean) => {
      if (v === enabledRef.current) return;
      enabledRef.current = v;
      setWakeWordEnabledState(v);
      if (typeof window !== "undefined") {
        try { localStorage.setItem(WAKE_WORD_STORAGE_KEY, String(v)); } catch { /* ignore */ }
      }
      if (v) startRecognition();
      else stopRecognition();
    },
  };
}
