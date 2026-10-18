"use client";

import { Mic, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Phase } from "@/types";

interface MicButtonProps {
  phase: Phase;
  onClick: () => void;
  label: string;
  disabled?: boolean;
}

export function MicButton({ phase, onClick, label, disabled }: MicButtonProps) {
  const isListening = phase === "LISTENING";
  const isThinking = phase === "THINKING";
  const isSpeaking = phase === "SPEAKING";

  return (
    <div className="relative flex items-center justify-center">
      {/* Subtle pulsing & radar glow rings when listening */}
      {isListening && (
        <>
          <span
            aria-hidden
            className="absolute h-24 w-24 rounded-full bg-purple-500/20 animate-ping"
          />
          <span
            aria-hidden
            className="absolute h-28 w-28 rounded-full border border-purple-400/40 animate-pulse"
          />
        </>
      )}

      {/* Gentle glow ring when speaking */}
      {isSpeaking && (
        <span
          aria-hidden
          className="absolute h-24 w-24 rounded-full border border-purple-400/30 bg-purple-500/10 animate-pulse"
        />
      )}

      {/* Circular Button */}
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-label={label}
        aria-pressed={isListening}
        className={cn(
          "relative z-10 flex h-16 w-16 sm:h-20 sm:w-20 items-center justify-center rounded-full border transition-all duration-300 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed",
          isListening
            ? "border-purple-400 bg-gradient-to-br from-purple-600 to-indigo-700 text-white shadow-[0_0_50px_rgba(168,85,247,0.7)]"
            : isThinking
            ? "border-purple-400/60 bg-purple-950/80 text-purple-200 shadow-[0_0_35px_rgba(147,51,234,0.4)]"
            : isSpeaking
            ? "border-violet-400 bg-gradient-to-br from-violet-600/80 to-purple-800/80 text-white shadow-[0_0_40px_rgba(139,92,246,0.6)]"
            : "border-purple-500/30 bg-purple-950/40 text-purple-200 hover:border-purple-400/60 hover:bg-purple-900/50 hover:text-white shadow-[0_0_30px_rgba(147,51,234,0.25)] hover:shadow-[0_0_45px_rgba(168,85,247,0.5)]"
        )}
      >
        {isThinking ? (
          <Loader2 className="h-7 w-7 sm:h-8 sm:w-8 animate-spin text-purple-200" />
        ) : (
          <Mic
            className={cn(
              "h-7 w-7 sm:h-8 sm:w-8 transition-transform duration-200",
              isListening && "scale-110 text-white",
              isSpeaking && "animate-pulse text-white"
            )}
          />
        )}
      </button>
    </div>
  );
}
