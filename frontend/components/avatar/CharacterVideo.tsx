"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import type { Phase } from "@/types";

interface CharacterVideoProps {
  phase: Phase;
  className?: string;
}

export function CharacterVideo({ phase, className }: CharacterVideoProps) {
  const idleRef = useRef<HTMLVideoElement>(null);
  const speakingRef = useRef<HTMLVideoElement>(null);
  const isSpeaking = phase === "SPEAKING";
  const pauseTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [idleError, setIdleError] = useState(false);
  const [speakingError, setSpeakingError] = useState(false);

  // Preload and start idle playback on mount; prime speaking video buffer
  useEffect(() => {
    const idleEl = idleRef.current;
    const speakingEl = speakingRef.current;

    if (idleEl) {
      idleEl.play().catch(() => {
        // Will auto-resume on first user gesture per browser autoplay policies
      });
    }

    if (speakingEl) {
      // Warm up decoder buffer for speaking video so the first frame renders instantaneously
      speakingEl.load();
    }

    return () => {
      if (pauseTimeoutRef.current) {
        clearTimeout(pauseTimeoutRef.current);
      }
    };
  }, []);

  // Seamless layered transition synchronized strictly with audio playback (phase === "SPEAKING")
  useEffect(() => {
    const speakingEl = speakingRef.current;
    const idleEl = idleRef.current;

    if (pauseTimeoutRef.current) {
      clearTimeout(pauseTimeoutRef.current);
      pauseTimeoutRef.current = null;
    }

    if (isSpeaking) {
      // Audio started playing: play speaking video immediately
      if (speakingEl) {
        try {
          speakingEl.currentTime = 0;
        } catch {
          /* ignore seeking error if not ready */
        }
        speakingEl.play().catch((err) => {
          console.warn("Speaking video playback error:", err);
        });
      }
    } else {
      // Audio finished or interrupted: fade out speaking video, then pause after fade
      if (speakingEl) {
        pauseTimeoutRef.current = setTimeout(() => {
          if (!speakingEl.paused) {
            speakingEl.pause();
          }
        }, 220); // allow 200ms opacity transition to finish smoothly
      }
      // Ensure idle video is playing continuously underneath
      if (idleEl && idleEl.paused) {
        idleEl.play().catch(() => {});
      }
    }
  }, [isSpeaking]);

  return (
    <div
      className={cn(
        "relative flex h-full w-full items-center justify-center overflow-hidden bg-black",
        className
      )}
    >
      {/* 
        Base layer (z-0): Idle character video.
        Always visible at 100% opacity underneath. Eliminates black frames, flickering,
        and visible pauses during any speaking transition or seeking delay.
      */}
      <video
        ref={idleRef}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        onError={() => setIdleError(true)}
        className="absolute inset-0 z-0 h-full w-full object-cover object-center pointer-events-none opacity-100"
      >
        <source src="/videos/idle.mp4" type="video/mp4" />
        <source src="/videos/chef-idle.mp4" type="video/mp4" />
      </video>

      {/* 
        Top layer (z-10): Speaking character video.
        Layered directly over the idle video with fast, subtle opacity crossfade (200ms).
        Only visible while actual audio speech playback is active.
      */}
      <video
        ref={speakingRef}
        loop
        muted
        playsInline
        preload="auto"
        onError={() => setSpeakingError(true)}
        className={cn(
          "absolute inset-0 z-10 h-full w-full object-cover object-center pointer-events-none transition-opacity duration-200 ease-out",
          isSpeaking ? "opacity-100" : "opacity-0"
        )}
      >
        <source src="/videos/speaking.mp4" type="video/mp4" />
        <source src="/videos/chef-speaking.mp4" type="video/mp4" />
      </video>

      {/* Fallback indicator if neither video can be loaded */}
      {idleError && speakingError && (
        <div className="relative z-20 text-center text-sm text-purple-300/60 p-4">
          Character videos not found. Place <code className="text-purple-200">idle.mp4</code> and{" "}
          <code className="text-purple-200">speaking.mp4</code> in{" "}
          <code className="text-purple-200">frontend/public/videos/</code>.
        </div>
      )}
    </div>
  );
}
