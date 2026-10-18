import type { Lang, LipLevel } from "@/types";
import { clamp } from "@/lib/utils";
import { api } from "@/services/api";
import { NoVoiceError, TtsUnavailable, type SpeechSynthesizer, type SpeechSynthesizerEvents } from "./types";

const LOCALE: Record<Lang, string> = { en: "en-IN", ta: "ta-IN", hi: "hi-IN" };

/** Split into speakable chunks so the first sentence starts playing while the rest is still being synthesised. */
export function splitSentences(text: string): string[] {
  const clean = text.replace(/\*\*|__|`/g, "").replace(/^\s*[•\-*]\s+/gm, "").replace(/\n+/g, ". ").trim();
  const raw = clean.match(/[^.!?।]+[.!?।]*/g)?.map((s) => s.trim()).filter(Boolean) ?? [clean];
  const out: string[] = [];
  for (const s of raw) {
    if (out.length && (out[out.length - 1].length < 28 || s.length < 14)) out[out.length - 1] += " " + s;
    else out.push(s);
  }
  return out.flatMap((s) => (s.length > 230 ? (s.match(/.{1,200}(\s|$)/g) ?? [s]).map((x) => x.trim()) : [s]));
}

/** Natural neural voices from the backend (/api/voice/tts) + real audio analysis for lip-sync. */
export class ServerSpeechSynthesizer implements SpeechSynthesizer {
  private ctx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private runId = 0;
  private current: AudioBufferSourceNode | null = null;
  private abort: AbortController | null = null;

  private ensure(): AudioContext {
    if (!this.ctx) {
      const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AC();
      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 1024;
      this.analyser.smoothingTimeConstant = 0.3;
      this.analyser.connect(this.ctx.destination);
    }
    return this.ctx;
  }

  async unlock() {
    const ctx = this.ensure();
    if (ctx.state === "suspended") await ctx.resume();
    const s = ctx.createBufferSource(); // silent tick unlocks audio on iOS
    s.buffer = ctx.createBuffer(1, 1, 22050);
    s.connect(ctx.destination);
    s.start(0);
  }

  async speak(text: string, _lang: Lang, lip: { current: LipLevel }, events?: SpeechSynthesizerEvents) {
    const run = ++this.runId;
    this.abort?.abort();
    const ac = (this.abort = new AbortController());
    const ctx = this.ensure();
    if (ctx.state === "suspended") await ctx.resume();
    const parts = splitSentences(text);
    const jobs: Promise<AudioBuffer>[] = [];
    const load = (i: number) => (jobs[i] ??= api.tts(parts[i], ac.signal).then((buf) => new Promise<AudioBuffer>((res, rej) => ctx.decodeAudioData(buf, res, rej))));
    for (let i = 0; i < Math.min(2, parts.length); i++) load(i).catch(() => undefined);
    let hasStarted = false;
    for (let i = 0; i < parts.length; i++) {
      if (run !== this.runId) return;
      let buffer: AudioBuffer;
      try { buffer = await load(i); } catch { if (run !== this.runId) return; throw new TtsUnavailable(parts.slice(i).join(" ")); }
      if (run !== this.runId) return;
      if (i + 2 < parts.length) load(i + 2).catch(() => undefined);
      await this.play(buffer, lip, run, () => {
        if (!hasStarted) {
          hasStarted = true;
          events?.onStart?.();
        }
      });
    }
    if (run === this.runId) {
      lip.current = { open: 0, wide: 0.3 };
      events?.onEnd?.();
    }
  }

  private play(buffer: AudioBuffer, lip: { current: LipLevel }, run: number, onStart?: () => void) {
    const ctx = this.ctx!, analyser = this.analyser!;
    return new Promise<void>((resolve) => {
      const src = ctx.createBufferSource();
      src.buffer = buffer;
      src.connect(analyser);
      this.current = src;
      const td = new Uint8Array(analyser.fftSize), fd = new Uint8Array(analyser.frequencyBinCount);
      const hzPerBin = ctx.sampleRate / 2 / fd.length;
      const tick = window.setInterval(() => {
        if (run !== this.runId) return;
        analyser.getByteTimeDomainData(td);
        let sum = 0;
        for (let i = 0; i < td.length; i++) { const v = (td[i] - 128) / 128; sum += v * v; }
        const rms = Math.sqrt(sum / td.length);
        analyser.getByteFrequencyData(fd);
        let num = 0, den = 0;
        for (let i = 2; i < fd.length; i++) { num += i * fd[i]; den += fd[i]; }
        const centroid = den ? (num / den) * hzPerBin : 1200;
        // loudness -> jaw opening; spectral brightness -> lip width ("ee" wide, "oo" round)
        lip.current = { open: clamp((rms - 0.025) * 6.5), wide: clamp((centroid - 700) / 2300) };
      }, 33);
      src.onended = () => { window.clearInterval(tick); this.current = null; resolve(); };
      src.start();
      onStart?.();
    });
  }

  stop() {
    this.runId++;
    this.abort?.abort();
    try { this.current?.stop(); } catch { /* already stopped */ }
  }
}

/** Fallback: the device's own voices. Lip-sync is simulated (browsers expose no audio stream). */
export class BrowserSpeechSynthesizer implements SpeechSynthesizer {
  private timer: number | null = null;

  static supported() { return typeof window !== "undefined" && "speechSynthesis" in window; }
  async unlock() { if (BrowserSpeechSynthesizer.supported()) window.speechSynthesis.getVoices(); }

  private async voiceFor(lang: Lang): Promise<SpeechSynthesisVoice | null> {
    let voices = window.speechSynthesis.getVoices();
    if (!voices.length) {
      await new Promise<void>((r) => { window.speechSynthesis.onvoiceschanged = () => r(); setTimeout(r, 800); });
      voices = window.speechSynthesis.getVoices();
    }
    const exact = voices.filter((v) => v.lang.replace("_", "-").toLowerCase() === LOCALE[lang].toLowerCase());
    const loose = voices.filter((v) => v.lang.toLowerCase().startsWith(lang));
    return exact[0] ?? loose[0] ?? null;
  }

  async speak(text: string, lang: Lang, lip: { current: LipLevel }, events?: SpeechSynthesizerEvents) {
    if (!BrowserSpeechSynthesizer.supported()) throw new NoVoiceError();
    const voice = await this.voiceFor(lang);
    if (!voice) throw new NoVoiceError(); // never read Tamil/Hindi with an English voice
    this.stop();
    await new Promise<void>((resolve) => {
      const u = new SpeechSynthesisUtterance(splitSentences(text).join(" "));
      u.voice = voice; u.lang = voice.lang; u.rate = 0.95;
      const t0 = performance.now();
      let hasStarted = false;
      u.onstart = () => {
        if (!hasStarted) {
          hasStarted = true;
          events?.onStart?.();
        }
      };
      this.timer = window.setInterval(() => {
        const t = (performance.now() - t0) / 1000;
        lip.current = { open: clamp(0.42 + 0.34 * Math.sin(t * 13) + 0.2 * Math.sin(t * 5.3)), wide: clamp(0.5 + 0.4 * Math.sin(t * 7.1)) };
      }, 40);
      const finish = () => {
        if (this.timer) window.clearInterval(this.timer);
        this.timer = null;
        lip.current = { open: 0, wide: 0.3 };
        events?.onEnd?.();
        resolve();
      };
      u.onend = finish;
      u.onerror = finish;
      window.speechSynthesis.speak(u);
    });
  }

  stop() {
    if (BrowserSpeechSynthesizer.supported()) window.speechSynthesis.cancel();
    if (this.timer) window.clearInterval(this.timer);
    this.timer = null;
  }
}

/** Server neural voice first; automatically continues with the device voice if the server voice is unavailable. */
export class HybridSynthesizer implements SpeechSynthesizer {
  private server = new ServerSpeechSynthesizer();
  private browser = new BrowserSpeechSynthesizer();
  constructor(private onFallback?: (reason: "browser" | "none") => void) {}

  async unlock() { await Promise.all([this.server.unlock(), this.browser.unlock()]); }

  async speak(text: string, lang: Lang, lip: { current: LipLevel }, events?: SpeechSynthesizerEvents) {
    try {
      await this.server.speak(text, lang, lip, events);
    } catch (e) {
      if (!(e instanceof TtsUnavailable)) throw e;
      try { this.onFallback?.("browser"); await this.browser.speak(e.remainingText, lang, lip, events); }
      catch (err) { if (err instanceof NoVoiceError) this.onFallback?.("none"); else throw err; }
    }
  }
  stop() { this.server.stop(); this.browser.stop(); }
}
