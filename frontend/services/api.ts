import { API_URL, HOTEL_SLUG } from "@/lib/config";
import type { Dish, HotelInfo, Lang, Special, StreamEvent, VoiceCaps, Category } from "@/types";

export class ApiError extends Error {
  constructor(public status: number, message: string, public fields?: { field: string; message: string }[]) { super(message); }
}

function headers(extra?: HeadersInit): Headers {
  const h = new Headers(extra);
  if (HOTEL_SLUG) h.set("X-Hotel-Slug", HOTEL_SLUG);
  return h;
}

async function parse<T>(res: Response): Promise<T> {
  if (res.ok) return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
  let body: { error?: string; fields?: { field: string; message: string }[] } = {};
  try { body = await res.json(); } catch { /* non-JSON error */ }
  throw new ApiError(res.status, body.error || "Something went wrong. Please try again.", body.fields);
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const h = headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) h.set("Content-Type", "application/json");
  try {
    return await parse<T>(await fetch(`${API_URL}/api${path}`, { ...init, headers: h }));
  } catch (e) {
    if (e instanceof ApiError || (e instanceof DOMException && e.name === "AbortError")) throw e;
    throw new ApiError(0, "We can't reach the concierge service right now. Please check your connection.");
  }
}

export const api = {
  hotel: () => request<HotelInfo>("/hotels/current"),
  menu: () => request<{ categories: Category[]; dishes: Dish[] }>("/menu"),
  specials: () => request<Special[]>("/specials"),
  voiceCaps: () => request<VoiceCaps>("/voice/capabilities"),
  createSession: (language: Lang) => request<{ session_id: string }>("/assistant/session", { method: "POST", body: JSON.stringify({ language, channel: "web" }) }),
  event: (event_type: string, session_id: string | null, payload: Record<string, unknown> = {}) =>
    request("/analytics/events", { method: "POST", body: JSON.stringify({ event_type, session_id, payload }) }).catch(() => undefined),

  /** NDJSON stream: tool-status events while the assistant works, then one final event. */
  async chatStream(body: { message: string; session_id: string | null; language: Lang; dish_id?: string }, onEvent: (e: StreamEvent) => void, signal?: AbortSignal) {
    let res: Response;
    try {
      res = await fetch(`${API_URL}/api/assistant/chat/stream`, { method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify(body), signal });
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") throw e;
      throw new ApiError(0, "We can't reach the concierge service right now.");
    }
    if (!res.ok || !res.body) await parse(res);
    const reader = res.body!.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl: number;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (line) onEvent(JSON.parse(line) as StreamEvent);
      }
    }
  },

  async transcribe(blob: Blob, language: Lang) {
    const form = new FormData();
    const ext = blob.type.includes("mp4") ? "m4a" : blob.type.includes("ogg") ? "ogg" : "webm";
    form.append("audio", blob, `speech.${ext}`);
    form.append("language", language);
    return request<{ text: string; status: "ok" | "empty" | "unclear"; confidence: number; reason?: string }>("/voice/transcribe", { method: "POST", body: form });
  },

  async tts(text: string, signal?: AbortSignal): Promise<ArrayBuffer> {
    const res = await fetch(`${API_URL}/api/voice/tts`, { method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify({ text }), signal });
    if (!res.ok) throw new ApiError(res.status, "tts unavailable");
    return res.arrayBuffer();
  },
};
