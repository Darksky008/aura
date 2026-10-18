"use client";

import { useEffect, useRef } from "react";
import { AVATAR_PROVIDER } from "@/lib/config";
import { cn } from "@/lib/utils";
import type { LipLevel, Phase } from "@/types";
import type { AvatarCue } from "./ChefAvatar";
import { getAvatarProvider } from "./providers";

const Avatar = getAvatarProvider(AVATAR_PROVIDER);

/** The stage: ambient light, state ring and the (replaceable) avatar. */
export function AvatarPanel({ phase, lipRef, micLevelRef, cue, label, className }: {
  phase: Phase; lipRef: { current: LipLevel }; micLevelRef: { current: number }; cue?: AvatarCue | null; label: string; className?: string;
}) {
  const ring = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      ring.current?.style.setProperty("--lvl", String(micLevelRef.current));
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [micLevelRef]);

  const tone = phase === "LISTENING" ? "rgba(95,199,161,0.30)" : phase === "THINKING" ? "rgba(217,174,91,0.30)" : phase === "ERROR" ? "rgba(229,112,122,0.28)" : "rgba(232,132,63,0.30)";
  return (
    <div className={cn("relative mx-auto aspect-[4/5] w-full select-none", className)}>
      {/* ambient light behind the avatar */}
      <div aria-hidden className="absolute inset-[-12%] animate-drift rounded-full blur-3xl transition-colors duration-700" style={{ background: `radial-gradient(closest-side, ${tone}, transparent 72%)` }} />
      <div ref={ring} aria-hidden className="pointer-events-none absolute inset-0 flex items-center justify-center" style={{ ["--lvl" as string]: 0 }}>
        {phase === "LISTENING" && (
          <>
            <span className="absolute h-[78%] w-[78%] animate-pulseRing rounded-full border border-jade/40" />
            <span className="absolute h-[78%] w-[78%] animate-pulseRing rounded-full border border-jade/30 [animation-delay:0.6s]" />
            <span className="absolute h-[70%] w-[70%] rounded-full border border-jade/40 transition-transform duration-75" style={{ transform: "scale(calc(1 + var(--lvl) * 0.22))" }} />
          </>
        )}
        {phase === "THINKING" && <span className="absolute h-[74%] w-[74%] animate-spin rounded-full border border-dashed border-gold/40 [animation-duration:9s]" />}
      </div>
      <div className="relative h-full w-full overflow-hidden rounded-[2.2rem] border border-white/[0.08] bg-[radial-gradient(120%_90%_at_50%_0%,rgba(255,255,255,0.07),rgba(255,255,255,0.01)_60%)] shadow-glass">
        <div className="absolute inset-x-[-4%] bottom-0 top-[2%]"><Avatar phase={phase} lipRef={lipRef} cue={cue} /></div>
        <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-ink/70 to-transparent" />
        <div className="absolute inset-x-0 bottom-3 flex justify-center">
          <span role="status" aria-live="polite" className="glass flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs text-ivory-dim">
            <span className={cn("h-1.5 w-1.5 rounded-full", phase === "LISTENING" ? "bg-jade" : phase === "THINKING" ? "bg-gold" : phase === "SPEAKING" ? "bg-saffron" : phase === "ERROR" ? "bg-rose" : "bg-muted")} />
            {label}
          </span>
        </div>
      </div>
    </div>
  );
}
