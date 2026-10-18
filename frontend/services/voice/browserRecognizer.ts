import type { Lang } from "@/types";
import type { RecognitionResult, RecognizeOptions, SpeechRecognizer } from "./types";

const LOCALE: Record<Lang, string> = { en: "en-IN", ta: "ta-IN", hi: "hi-IN" };

/* eslint-disable @typescript-eslint/no-explicit-any */
type Ctor = new () => any;
const getCtor = (): Ctor | null => (typeof window === "undefined" ? null : (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null);

/** Fallback recognizer using the browser's Web Speech API (best in Chrome/Edge/Android; unreliable in Firefox/Safari). */
export class BrowserSpeechRecognizer implements SpeechRecognizer {
  readonly kind = "browser" as const;
  private rec: any = null;

  static supported() { return !!getCtor(); }

  start(opts: RecognizeOptions): Promise<RecognitionResult> {
    const Ctor = getCtor();
    if (!Ctor) return Promise.resolve({ status: "error", code: "unsupported", message: "Speech recognition is not supported in this browser." });
    this.abort();
    return new Promise((resolve) => {
      const rec = new Ctor();
      this.rec = rec;
      rec.lang = LOCALE[opts.language];
      rec.interimResults = true;
      rec.continuous = false;
      rec.maxAlternatives = 3;
      let best = { text: "", confidence: 0 }, settled = false, aborted = false;
      let latestText = "";
      const settle = (r: RecognitionResult) => { if (!settled) { settled = true; this.rec = null; opts.onLevel?.(0); resolve(r); } };
      rec.onspeechstart = () => opts.onSpeechStart?.();
      rec.onresult = (e: any) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const res = e.results[i];
          const transcript = res[0]?.transcript?.trim() || "";
          if (transcript) latestText = transcript;
          if (res.isFinal) {
            for (let j = 0; j < res.length; j++) {
              if (res[j].confidence >= best.confidence || !best.text) {
                best = { text: res[j].transcript.trim(), confidence: res[j].confidence || 0.9 };
              }
            }
          } else {
            opts.onInterim?.(transcript);
          }
        }
      };
      rec.onerror = (e: any) => {
        if (e.error === "not-allowed" || e.error === "service-not-allowed") settle({ status: "error", code: "denied", message: "Microphone permission was denied." });
        else if (e.error === "no-speech") settle({ status: "no_speech" });
        else if (e.error === "aborted") settle({ status: "aborted" });
        else if (e.error === "network") settle({ status: "error", code: "network", message: "Speech recognition needs an internet connection." });
        else settle({ status: "unclear" });
      };
      rec.onend = () => {
        if (aborted) return settle({ status: "aborted" });
        const finalText = best.text || latestText;
        if (finalText) settle({ status: "ok", text: finalText, confidence: best.confidence || 0.85 });
        else settle({ status: "no_speech" });
      };
      (rec as any)._markAborted = () => { aborted = true; };
      try { rec.start(); } catch { settle({ status: "error", code: "unknown", message: "Could not start speech recognition." }); }
    });
  }

  finish() { try { this.rec?.stop(); } catch { /* ignore */ } }
  abort() { try { this.rec?._markAborted?.(); this.rec?.abort(); } catch { /* ignore */ } }
  release() { this.abort(); }
}
