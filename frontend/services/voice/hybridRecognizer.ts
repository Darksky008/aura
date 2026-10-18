import type { Lang } from "@/types";
import { BrowserSpeechRecognizer } from "./browserRecognizer";
import { ServerSpeechRecognizer } from "./serverRecognizer";
import type { RecognitionResult, RecognizeOptions, SpeechRecognizer } from "./types";

/**
 * Hybrid speech recognizer:
 * Uses server Groq Whisper when configured and available;
 * automatically and seamlessly falls back to the browser's native Web Speech API
 * when server speech recognition is unavailable or unconfigured (503).
 */
export class HybridSpeechRecognizer implements SpeechRecognizer {
  readonly kind = "server" as const;
  private server: ServerSpeechRecognizer;
  private browser: BrowserSpeechRecognizer;
  private serverAvailable: boolean | null = null;
  private activeRecognizer: SpeechRecognizer | null = null;
  private healthCheckPromise: Promise<boolean> | null = null;

  constructor(
    private transcribe: (
      blob: Blob,
      lang: Lang
    ) => Promise<{ text: string; status: "ok" | "empty" | "unclear"; confidence: number }>,
    private onFallback?: (r: "browser" | "none") => void
  ) {
    this.server = new ServerSpeechRecognizer(transcribe);
    this.browser = new BrowserSpeechRecognizer();

    if (BrowserSpeechRecognizer.supported()) {
      this.healthCheckPromise = this.checkServerHealth();
    } else {
      this.serverAvailable = true;
    }
  }

  private async checkServerHealth(): Promise<boolean> {
    if (this.serverAvailable !== null) return this.serverAvailable;
    try {
      // Probe the transcription endpoint with a test chunk
      // If Groq key is invalid/missing, backend returns 503
      const res = await this.transcribe(
        new Blob([new Uint8Array(2000)], { type: "audio/webm" }),
        "en"
      );
      this.serverAvailable = res.status === "ok" || res.status === "empty" || res.status === "unclear";
    } catch {
      this.serverAvailable = false;
    }
    return this.serverAvailable ?? false;
  }

  async start(opts: RecognizeOptions): Promise<RecognitionResult> {
    const browserOk = BrowserSpeechRecognizer.supported();

    // If browser recognition is available and server is known to be unavailable, use browser
    if (browserOk && this.serverAvailable === false) {
      this.activeRecognizer = this.browser;
      return this.browser.start(opts);
    }

    // If health check is pending, wait up to 400ms for it before deciding
    if (browserOk && this.serverAvailable === null && this.healthCheckPromise) {
      try {
        const serverOk = await Promise.race([
          this.healthCheckPromise,
          new Promise<boolean>((r) => setTimeout(() => r(false), 400)),
        ]);
        if (!serverOk) {
          this.serverAvailable = false;
          this.activeRecognizer = this.browser;
          return this.browser.start(opts);
        }
      } catch {
        this.serverAvailable = false;
        this.activeRecognizer = this.browser;
        return this.browser.start(opts);
      }
    }

    // If browser is not supported, use server recognizer directly
    this.activeRecognizer = this.server;
    const result = await this.server.start(opts);

    // If server succeeded or was aborted/silent, return result
    if (result.status === "ok" || result.status === "no_speech" || result.status === "aborted") {
      this.serverAvailable = true;
      return result;
    }

    // If server failed (e.g. 503 network error) and browser is supported, record failure for next turns
    if (result.status === "error" && result.code !== "denied" && browserOk) {
      this.serverAvailable = false;
      this.activeRecognizer = this.browser;
    }

    return result;
  }

  finish() {
    this.activeRecognizer?.finish();
  }

  abort() {
    this.activeRecognizer?.abort();
  }

  release() {
    this.server.release();
    this.browser.release();
  }
}

