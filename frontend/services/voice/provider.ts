import { VOICE_PROVIDER } from "@/lib/config";
import { api } from "@/services/api";
import { BrowserSpeechRecognizer } from "./browserRecognizer";
import { HybridSpeechRecognizer } from "./hybridRecognizer";
import { BrowserSpeechSynthesizer, HybridSynthesizer } from "./synthesizers";
import type { VoiceProvider } from "./types";

/**
 * VOICE_PROVIDER=server  (default) Groq Whisper for listening + neural TTS from the backend; falls back to the browser.
 * VOICE_PROVIDER=browser            Web Speech API for both directions (no backend voice calls at all).
 * A realtime voice vendor (OpenAI Realtime, Deepgram, ElevenLabs ...) plugs in by implementing `VoiceProvider`.
 */
export function createVoiceProvider(opts: { serverStt: boolean; onFallback?: (r: "browser" | "none") => void }): VoiceProvider {
  const useServerStt = VOICE_PROVIDER !== "browser" && opts.serverStt;
  const recognizer =
    VOICE_PROVIDER === "browser"
      ? new BrowserSpeechRecognizer()
      : useServerStt && BrowserSpeechRecognizer.supported()
      ? new HybridSpeechRecognizer((blob, lang) => api.transcribe(blob, lang), opts.onFallback)
      : BrowserSpeechRecognizer.supported()
      ? new BrowserSpeechRecognizer()
      : new HybridSpeechRecognizer((blob, lang) => api.transcribe(blob, lang), opts.onFallback);

  const synthesizer =
    VOICE_PROVIDER === "browser" && BrowserSpeechSynthesizer.supported()
      ? new BrowserSpeechSynthesizer()
      : new HybridSynthesizer(opts.onFallback);

  return { recognizer, synthesizer };
}

