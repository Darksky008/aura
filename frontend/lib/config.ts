/** Only NEXT_PUBLIC_* values reach the browser. Secrets (Groq key, DB URL) live exclusively on the backend. */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
export const HOTEL_SLUG = process.env.NEXT_PUBLIC_HOTEL_SLUG || "";
export const AVATAR_PROVIDER = process.env.NEXT_PUBLIC_AVATAR_PROVIDER || "demo";
export const VOICE_PROVIDER = process.env.NEXT_PUBLIC_VOICE_PROVIDER || "server";
