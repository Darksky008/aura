export const cn = (...parts: (string | false | null | undefined)[]) => parts.filter(Boolean).join(" ");
export const clamp = (v: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const rand = (lo: number, hi: number) => lo + Math.random() * (hi - lo);
export const uid = () => Math.random().toString(36).slice(2, 10);
