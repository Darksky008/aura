import type { Lang } from "@/types";
import type { RecognitionResult, RecognizeOptions, SpeechRecognizer } from "./types";

/**
 * Hands-free, noise-aware microphone capture + server-side Whisper transcription.
 *
 * Why it is built this way (accuracy matters - guests only speak):
 *  - echoCancellation / noiseSuppression / autoGainControl on the capture stream
 *  - ~450 ms ambient-noise calibration -> adaptive speech/silence thresholds (lobbies are loud)
 *  - speech must stay above threshold for 140 ms before we call it speech (door slams, clinks ignored)
 *  - utterance ends after 1.3 s of silence, so natural pauses ("I want... something mild") aren't cut off
 *  - clips shorter than 300 ms of speech are discarded, 25 s hard cap, 10 s "nobody spoke" timeout
 *  - the server verifies confidence, drops Whisper's silence hallucinations and biases decoding with the menu vocabulary
 */
const CALIBRATE_MS = 450;
const START_HOLD_MS = 140;
const END_SILENCE_MS = 1300;
const MAX_SPEECH_MS = 25000;
const NO_SPEECH_TIMEOUT_MS = 10000;
const MIN_SPEECH_MS = 300;

type Transcriber = (blob: Blob, lang: Lang) => Promise<{ text: string; status: "ok" | "empty" | "unclear"; confidence: number }>;

function pickMime(): string | undefined {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
  return candidates.find((m) => typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(m));
}

export class ServerSpeechRecognizer implements SpeechRecognizer {
  readonly kind = "server" as const;
  private stream: MediaStream | null = null;
  private ctx: AudioContext | null = null;
  private current: { finish: () => void; abort: () => void } | null = null;

  constructor(private transcribe: Transcriber) {}

  private async acquire(): Promise<MediaStream> {
    if (this.stream && this.stream.getTracks().every((t) => t.readyState === "live")) return this.stream;
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
    });
    return this.stream;
  }

  async start(opts: RecognizeOptions): Promise<RecognitionResult> {
    this.current?.abort();
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      return { status: "error", code: "unsupported", message: "Recording is not supported in this browser." };
    }
    let stream: MediaStream;
    try {
      stream = await this.acquire();
    } catch (e) {
      const denied = e instanceof DOMException && (e.name === "NotAllowedError" || e.name === "SecurityError");
      return { status: "error", code: denied ? "denied" : "unknown", message: denied ? "Microphone permission was denied." : "No microphone was found." };
    }
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    this.ctx ??= new AC();
    if (this.ctx.state === "suspended") await this.ctx.resume();
    const source = this.ctx.createMediaStreamSource(stream);
    const analyser = this.ctx.createAnalyser();
    analyser.fftSize = 1024;
    source.connect(analyser);

    const mime = pickMime();
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };

    return new Promise<RecognitionResult>((resolve) => {
      const buf = new Float32Array(analyser.fftSize);
      const t0 = performance.now();
      const calib: number[] = [];
      let noise = 0.01, calibrated = false;
      let speechStart: number | null = null, aboveSince: number | null = null, lastLoud = 0, done = false;

      const end = async (mode: "send" | "abort") => {
        if (done) return;
        done = true;
        clearInterval(timer);
        try { source.disconnect(); } catch { /* already disconnected */ }
        const speechMs = speechStart ? lastLoud - speechStart : 0;
        const stopped = new Promise<void>((r) => { recorder.onstop = () => r(); });
        if (recorder.state !== "inactive") recorder.stop();
        await stopped;
        this.current = null;
        opts.onLevel?.(0);
        if (mode === "abort") return resolve({ status: "aborted" });
        if (!speechStart || speechMs < MIN_SPEECH_MS) return resolve({ status: "no_speech" });
        try {
          const r = await this.transcribe(new Blob(chunks, { type: recorder.mimeType || "audio/webm" }), opts.language);
          if (r.status === "ok" && r.text) resolve({ status: "ok", text: r.text, confidence: r.confidence });
          else resolve({ status: "unclear", text: r.text });   // speech was detected but the transcript can't be trusted
        } catch {
          resolve({ status: "error", code: "network", message: "Speech recognition is unavailable." });
        }
      };
      this.current = { finish: () => void end("send"), abort: () => void end("abort") };

      const timer = window.setInterval(() => {
        analyser.getFloatTimeDomainData(buf);
        let sum = 0;
        for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
        const rms = Math.sqrt(sum / buf.length);
        opts.onLevel?.(Math.min(1, rms * 7));
        const now = performance.now();
        if (now - t0 < CALIBRATE_MS) { calib.push(rms); return; }
        if (!calibrated) {
          calib.sort((a, b) => a - b);
          noise = calib[Math.floor(calib.length * 0.6)] ?? 0.01;
          calibrated = true;
        }
        const speechT = Math.max(0.02, noise * 3);
        const silenceT = Math.max(0.013, noise * 1.8);
        if (rms > speechT) {
          aboveSince ??= now;
          lastLoud = now;
          if (!speechStart && now - aboveSince >= START_HOLD_MS) { speechStart = aboveSince; opts.onSpeechStart?.(); }
        } else {
          aboveSince = null;
          if (!speechStart && rms < silenceT) noise = noise * 0.95 + rms * 0.05; // keep adapting to the room
        }
        if (speechStart) {
          if (rms > silenceT) lastLoud = now;
          if (now - lastLoud > END_SILENCE_MS || now - speechStart > MAX_SPEECH_MS) void end("send");
        } else if (now - t0 > NO_SPEECH_TIMEOUT_MS) {
          void end("send"); // resolves as no_speech
        }
      }, 30);
      recorder.start(100);
    });
  }

  finish() { this.current?.finish(); }
  abort() { this.current?.abort(); }
  release() {
    this.current?.abort();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
  }
}
