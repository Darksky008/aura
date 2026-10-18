"use client";

import { useEffect, useRef } from "react";
import { Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function Spinner({ className }: { className?: string }) { return <Loader2 className={cn("h-4 w-4 animate-spin", className)} aria-hidden />; }

export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: "neutral" | "gold" | "jade" | "rose" | "saffron"; className?: string }) {
  const tones = {
    neutral: "border-white/10 bg-white/[0.05] text-ivory-dim", gold: "border-gold/30 bg-gold/10 text-gold-soft",
    jade: "border-jade/30 bg-jade/10 text-jade", rose: "border-rose/30 bg-rose/10 text-rose", saffron: "border-saffron/30 bg-saffron/10 text-saffron",
  };
  return <span className={cn("inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium", tones[tone], className)}>{children}</span>;
}

export function Dialog({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title?: string; children: React.ReactNode; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    ref.current?.focus();
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", onKey); document.body.style.overflow = ""; prev?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-6" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title}
        className={cn("glass-strong animate-rise max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl p-5 outline-none sm:rounded-3xl sm:p-7", wide ? "sm:max-w-3xl" : "sm:max-w-xl")}>
        <div className="mb-4 flex items-start justify-between gap-4">
          {title && <h2 className="font-display text-2xl font-semibold text-ivory">{title}</h2>}
          <button aria-label="Close" onClick={onClose} className="btn btn-ghost ml-auto !p-2"><X className="h-4 w-4" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Tabs<T extends string>({ items, value, onChange, className }: { items: { id: T; label: string; icon?: React.ReactNode }[]; value: T; onChange: (v: T) => void; className?: string }) {
  return (
    <div role="tablist" className={cn("flex gap-1.5 overflow-x-auto pb-1", className)}>
      {items.map((it) => (
        <button key={it.id} role="tab" aria-selected={value === it.id} onClick={() => onChange(it.id)}
          className={cn("flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-sm transition", value === it.id ? "border-gold/50 bg-gold/15 text-gold-soft" : "border-white/10 bg-white/[0.03] text-ivory-dim hover:bg-white/[0.08]")}>
          {it.icon}{it.label}
        </button>
      ))}
    </div>
  );
}

export function Field({ label, error, children, hint }: { label: string; error?: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && !error && <span className="mt-1 block text-[11px] text-muted">{hint}</span>}
      {error && <span role="alert" className="mt-1 block text-xs text-rose">{error}</span>}
    </label>
  );
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: React.ReactNode }) {
  return (
    <div className="glass flex flex-col items-center gap-2 rounded-3xl px-6 py-14 text-center">
      <p className="font-display text-2xl text-ivory">{title}</p>
      {hint && <p className="max-w-sm text-sm text-muted">{hint}</p>}
      {action}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-shimmer rounded-2xl bg-[linear-gradient(110deg,rgba(255,255,255,0.04)_30%,rgba(255,255,255,0.1)_50%,rgba(255,255,255,0.04)_70%)] bg-[length:200%_100%]", className)} />;
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button role="switch" aria-checked={checked} aria-label={label} onClick={() => onChange(!checked)}
      className={cn("relative h-6 w-11 shrink-0 rounded-full border transition", checked ? "border-gold/60 bg-gold/70" : "border-white/15 bg-white/10")}>
      <span className={cn("absolute top-0.5 h-4.5 w-4.5 rounded-full bg-ivory transition-all", checked ? "left-[22px]" : "left-0.5")} style={{ height: 18, width: 18 }} />
    </button>
  );
}

/** Indian-convention food mark: green dot = vegetarian, red dot = non-vegetarian, nothing = not specified. */
export function VegMark({ value }: { value: "yes" | "no" | "unknown" }) {
  if (value === "unknown") return null;
  const c = value === "yes" ? "#5FC7A1" : "#E5707A";
  return (
    <span title={value === "yes" ? "Vegetarian" : "Non-vegetarian"} className="inline-flex h-4 w-4 items-center justify-center rounded-[4px] border-2" style={{ borderColor: c }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: c }} />
    </span>
  );
}
