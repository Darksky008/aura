export type Lang = "en" | "ta" | "hi";
export type Phase = "IDLE" | "LISTENING" | "THINKING" | "SPEAKING" | "ERROR";
export type Mode = "voice" | "chat";
export interface LipLevel { open: number; wide: number }

export interface Category { id: string; slug: string; name: string; names: Record<string, string> }
export type Tri = "yes" | "no" | "unknown";
export interface Dish {
  id: string; slug: string; name: string; names: Record<string, string>; aliases: string[]; description: string | null;
  category: Category | null; cuisine: string | null; spice_level: "none" | "mild" | "medium" | "high";
  calories_kcal: number | null; price: number | null; ingredients: string[];
  allergens: { code: string; label: string }[]; dietary: Record<string, Tri>;
  preparation_notes: string | null; image_url: string | null; is_chef_special: boolean; is_available: boolean;
}
export interface Special { id: string; type: string; title: string; description: string | null; dish: Dish | null }
export interface HotelInfo {
  slug: string; name: string; tagline: string | null; assistant_name: string; default_language: Lang;
  languages: { code: Lang; name: string; locale: string }[];
  restaurant: { id: string; name: string; description: string | null; positioning: string | null; currency: string };
}
export interface ChatMessage {
  id: string; role: "user" | "assistant"; text: string; tools?: string[]; failed?: boolean; retryText?: string; lang?: Lang;
}
export interface FinalEvent {
  type: "final"; session_id: string; reply: string; language: Lang; tools_used: string[]; dishes: string[]; provider: string; latency_ms: number;
}
export type StreamEvent = { type: "tool"; name: string } | FinalEvent | { type: "error"; message: string };
export interface VoiceCaps { stt: boolean; stt_model: string | null; tts: boolean; tts_provider: string | null; languages: string[] }
