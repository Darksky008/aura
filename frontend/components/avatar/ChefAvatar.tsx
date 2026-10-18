"use client";

import { useEffect, useRef, useState } from "react";
import type { LipLevel, Phase } from "@/types";
import { clamp, rand } from "@/lib/utils";
import { AvatarSvg } from "./AvatarSvg";
import { GESTURES, SPEAKING_GESTURES, initialPose, type ArmPose, type Fingers, type GestureName, type Pose } from "./pose";

export interface AvatarCue { name: GestureName; nonce: number; seconds?: number }
export interface AvatarProviderProps {
  phase: Phase;
  /** Live mouth shape (0..1) written by the speech synthesizer ~30x/s. Read-only here; never triggers React renders. */
  lipRef: { current: LipLevel };
  /** One-shot gesture (e.g. a wave on arrival). */
  cue?: AvatarCue | null;
}

const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const ease = (k: number, dt: number) => 1 - Math.exp(-k * dt);

function blendArm(cur: ArmPose, tgt: ArmPose, k: number) {
  cur.sh = lerp(cur.sh, tgt.sh, k);
  cur.el = lerp(cur.el, tgt.el, k);
  cur.wr = lerp(cur.wr, tgt.wr, k);
  cur.spread = lerp(cur.spread, tgt.spread, k);
  for (let i = 0; i < 5; i++) cur.fingers[i] = lerp(cur.fingers[i], tgt.fingers[i], k);
}

function pickGesture(prev: string): GestureName {
  const pool = SPEAKING_GESTURES.filter(([n]) => n !== prev);
  let r = Math.random() * pool.reduce((s, [, w]) => s + w, 0);
  for (const [name, w] of pool) { r -= w; if (r <= 0) return name; }
  return "presentR";
}

/** The demo avatar: a procedural chef concierge with gestures, gaze, blinking and audio-driven lip movement. */
export function ChefAvatar({ phase, lipRef, cue }: AvatarProviderProps) {
  const [pose, setPose] = useState<Pose>(initialPose);
  const wrapRef = useRef<HTMLDivElement>(null);
  const phaseRef = useRef(phase);
  const cueRef = useRef(cue);
  phaseRef.current = phase;
  cueRef.current = cue;

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const s = {
      pose: initialPose(), last: performance.now() / 1000, rendered: 0,
      gesture: "rest" as GestureName, gestureUntil: 0, cueNonce: -1, cueUntil: 0, cueGesture: "rest" as GestureName,
      nextBlink: 1.5, blinkStart: -1, doubleBlink: false,
      gaze: { x: 0, y: 0 }, glance: { x: 0, y: 0 }, glanceUntil: 0, nextGlance: 2, sacc: { x: 0, y: 0 }, nextSacc: 0.6,
      imp: 0, prevOpen: 0,
    };
    const pointer = { x: 0, y: 0, t: -99 };
    const onMove = (e: PointerEvent) => {
      const r = wrapRef.current?.getBoundingClientRect();
      if (!r) return;
      pointer.x = clamp((e.clientX - (r.left + r.width / 2)) / (r.width * 1.1), -1, 1);
      pointer.y = clamp((e.clientY - (r.top + r.height * 0.3)) / (r.height * 0.8), -1, 1);
      pointer.t = performance.now() / 1000;
    };
    window.addEventListener("pointermove", onMove, { passive: true });

    let raf = 0;
    const frame = (ms: number) => {
      raf = requestAnimationFrame(frame);
      const t = ms / 1000;
      const dt = Math.min(0.05, t - s.last);
      s.last = t;
      if (t - s.rendered < 0.022) return; // ~45 fps cap
      s.rendered = t;

      const ph = phaseRef.current;
      const lip = lipRef.current;
      const p = s.pose;

      // ---------- gesture director ----------
      const c = cueRef.current;
      if (c && c.nonce !== s.cueNonce && !reduce) {
        s.cueNonce = c.nonce; s.cueGesture = c.name; s.cueUntil = t + (c.seconds ?? 2.4);
      }
      let gName: GestureName = "rest";
      if (reduce) gName = "rest";
      else if (t < s.cueUntil) gName = s.cueGesture;
      else if (ph === "THINKING") gName = "moment";
      else if (ph === "SPEAKING") {
        if (t >= s.gestureUntil) {
          if (s.gesture !== "rest") { s.gesture = "rest"; s.gestureUntil = t + rand(0.3, 0.8); }
          else { s.gesture = pickGesture(s.gesture); s.gestureUntil = t + rand(1.3, 2.5); }
        }
        gName = s.gesture;
      } else { s.gesture = "rest"; s.gestureUntil = 0; }
      const g = GESTURES[gName];
      const ka = ease(6.5, dt);
      blendArm(p.armL, g.L, ka);
      blendArm(p.armR, g.R, ka);

      // emphasis "beats": a syllable peak nudges the arms, head and brows
      if (ph === "SPEAKING" && lip.open > 0.55 && s.prevOpen < 0.4) s.imp = 1;
      s.prevOpen = lip.open;
      s.imp = Math.max(0, s.imp - dt * 4.2);
      const sway = reduce ? 0 : Math.sin(t * 0.9) * 1.1;
      const wave = gName === "wave" ? Math.sin(t * 10) * 15 : 0;
      p.armL.sh += sway * 0.5;
      p.armR.sh -= sway * 0.5;
      if (ph === "SPEAKING" && gName !== "rest" && !reduce) {
        p.armL.el += s.imp * 6 * (g.L === GESTURES.rest.L ? 0 : 1);
        p.armR.el += s.imp * 6 * (g.R === GESTURES.rest.R ? 0 : 1);
      }
      p.armR.el += wave;

      // ---------- gaze ----------
      let tx = 0, ty = 0;
      if (ph === "THINKING") { tx = -0.55; ty = -0.65; }
      else if (ph === "SPEAKING") {
        if (t > s.nextGlance) { s.glance = { x: rand(-0.6, 0.6), y: rand(-0.5, 0.3) }; s.glanceUntil = t + rand(0.5, 1.1); s.nextGlance = t + rand(2.2, 4.6); }
        if (t < s.glanceUntil) { tx = s.glance.x; ty = s.glance.y; }
      } else if (ph === "ERROR") { ty = 0.3; }
      else if (t - pointer.t < 3) { tx = pointer.x * 0.8; ty = pointer.y * 0.6; }
      if (t > s.nextSacc) { s.sacc = { x: rand(-0.07, 0.07), y: rand(-0.05, 0.05) }; s.nextSacc = t + rand(0.5, 1.3); }
      const kg = ease(14, dt);
      s.gaze.x = lerp(s.gaze.x, clamp(tx + s.sacc.x, -1, 1), kg);
      s.gaze.y = lerp(s.gaze.y, clamp(ty + s.sacc.y, -1, 1), kg);
      p.gaze.x = s.gaze.x; p.gaze.y = s.gaze.y;

      // ---------- blink ----------
      if (t > s.nextBlink) { s.blinkStart = t; s.doubleBlink = Math.random() < 0.18; s.nextBlink = t + rand(2.2, 5.5); }
      const bp = (t - s.blinkStart) / 0.17;
      p.blink = bp >= 0 && bp < 1 ? Math.sin(Math.PI * bp) : 0;
      if (s.doubleBlink && bp >= 1.3 && bp < 2.3) p.blink = Math.sin(Math.PI * (bp - 1.3));

      // ---------- head + brows ----------
      const open = ph === "SPEAKING" ? lip.open : 0;
      const kh = ease(5, dt);
      const hRot = (ph === "LISTENING" ? 3 : ph === "ERROR" ? -3 : 0) + Math.sin(t * 0.6) * 0.8 + p.gaze.x * 2.5 + (ph === "SPEAKING" ? Math.sin(t * 2.3) * 1.3 + s.imp * 1.2 : 0);
      const hTy = (ph === "SPEAKING" ? open * 1.6 + s.imp * 2.5 : ph === "LISTENING" ? 1.5 : 0) + p.gaze.y * 2;
      p.head.rot = lerp(p.head.rot, hRot, kh);
      p.head.ty = lerp(p.head.ty, hTy, kh);
      p.head.tx = lerp(p.head.tx, p.gaze.x * 2.5, kh);
      const kb = ease(8, dt);
      const lift = ph === "LISTENING" ? 0.45 : ph === "SPEAKING" ? 0.15 + s.imp * 0.5 + open * 0.2 : ph === "ERROR" ? 0 : 0.05;
      p.brow.l = lerp(p.brow.l, ph === "THINKING" ? 0.65 : lift, kb);
      p.brow.r = lerp(p.brow.r, ph === "THINKING" ? 0.1 : lift, kb);
      p.brow.furrow = lerp(p.brow.furrow, ph === "ERROR" ? 0.8 : 0, kb);

      // ---------- mouth (lip-sync from the audio analyser) ----------
      const tOpen = ph === "SPEAKING" ? lip.open : 0;
      const tWide = ph === "SPEAKING" ? lip.wide : 0.3;
      p.mouth.open = lerp(p.mouth.open, tOpen, ease(tOpen > p.mouth.open ? 40 : 20, dt));
      p.mouth.wide = lerp(p.mouth.wide, tWide, ease(20, dt));
      const tSmile = ph === "ERROR" ? -0.6 : ph === "THINKING" ? 0.1 : ph === "SPEAKING" ? 0.35 : ph === "LISTENING" ? 0.45 : 0.55;
      p.mouth.smile = lerp(p.mouth.smile, tSmile, ease(6, dt));
      p.breath = Math.sin(t * 1.6);

      setPose({ ...p });
    };
    raf = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("pointermove", onMove); };
  }, [lipRef]);

  return (
    <div ref={wrapRef} className="h-full w-full">
      <AvatarSvg pose={pose} />
    </div>
  );
}
