import type { Lang, LipLevel } from "@/types";

export type RecognitionResult =
  | { status: "ok"; text: string; confidence?: number }
  | { status: "no_speech" }                      // nothing was said
  | { status: "unclear"; text?: string }         // something was said but we could not trust the transcript
  | { status: "aborted" }
  | { status: "error"; code: "denied" | "unsupported" | "network" | "unknown"; message: string };

export interface RecognizeOptions {
  language: Lang;
  onLevel?: (level01: number) => void;           // live microphone level for the UI ring
  onSpeechStart?: () => void;
  onInterim?: (text: string) => void;
}

/** Turns speech into text. Implementations: ServerSpeechRecognizer (Groq Whisper), BrowserSpeechRecognizer. */
export interface SpeechRecognizer {
  readonly kind: "server" | "browser";
  start(opts: RecognizeOptions): Promise<RecognitionResult>;
  /** Stop recording now and transcribe what was captured (tap-to-send). */
  finish(): void;
  abort(): void;
  /** Release the microphone completely. */
  release(): void;
}

export interface SpeechSynthesizerEvents {
  onStart?: () => void;
  onEnd?: () => void;
}

/** Turns text into audible speech and reports a live mouth shape for lip-sync. */
export interface SpeechSynthesizer {
  unlock(): Promise<void>;                       // must be called from a user gesture (autoplay policies)
  speak(text: string, lang: Lang, lip: { current: LipLevel }, events?: SpeechSynthesizerEvents): Promise<void>;
  stop(): void;
}

export class TtsUnavailable extends Error {
  constructor(public remainingText: string) { super("tts unavailable"); }
}
export class NoVoiceError extends Error {}

export interface VoiceProvider {
  recognizer: SpeechRecognizer;
  synthesizer: SpeechSynthesizer;
}
