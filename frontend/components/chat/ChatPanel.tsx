"use client";

import { useEffect, useRef, useState } from "react";
import { RotateCcw, Send, Trash2, Volume2, VolumeX, Mic } from "lucide-react";
import { Spinner } from "@/components/ui";
import type { Strings } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { ChatMessage, Phase } from "@/types";

/** Tiny safe renderer: **bold** and "• " bullet lines only (no HTML injection). */
function Formatted({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        const bullet = /^\s*[•\-*]\s+/.test(line);
        const parts = line.replace(/^\s*[•\-*]\s+/, "").split(/(\*\*[^*]+\*\*)/g);
        return (
          <p key={i} className={cn(bullet && "flex gap-2 pl-1 before:text-gold before:content-['•']")}>
            <span>{parts.map((p, j) => (p.startsWith("**") ? <strong key={j} className="font-semibold text-ivory">{p.slice(2, -2)}</strong> : p))}</span>
          </p>
        );
      })}
    </div>
  );
}

export function ChatPanel({ messages, phase, toolStatus, s, onSend, onRetry, onClear, onMic, speakReplies, onToggleSpeak, className }: {
  messages: ChatMessage[]; phase: Phase; toolStatus: string | null; s: Strings; onSend: (t: string) => void; onRetry: (t: string) => void;
  onClear: () => void; onMic: () => void; speakReplies: boolean; onToggleSpeak: (v: boolean) => void; className?: string;
}) {
  const [text, setText] = useState("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, toolStatus, phase]);
  const busy = phase === "THINKING";
  const submit = () => { if (!text.trim() || busy) return; onSend(text); setText(""); };

  return (
    <section aria-label="Conversation" className={cn("glass flex min-h-0 flex-col rounded-[2rem]", className)}>
      <div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-3">
        <h2 className="font-display text-xl text-ivory">AURA</h2>
        <div className="flex items-center gap-1">
          <button className="btn btn-ghost !p-2" aria-pressed={speakReplies} aria-label={s.voiceReplies} title={s.voiceReplies} onClick={() => onToggleSpeak(!speakReplies)}>
            {speakReplies ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </button>
          <button className="btn btn-ghost !p-2" aria-label={s.clear} title={s.clear} onClick={onClear}><Trash2 className="h-4 w-4" /></button>
        </div>
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4" role="log" aria-live="polite">
        {messages.map((m) => (
          <div key={m.id} className={cn("flex animate-rise", m.role === "user" ? "justify-end" : "justify-start")}>
            <div className={cn("max-w-[88%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed",
              m.role === "user" ? "rounded-br-md bg-gold/90 text-ink" : m.failed ? "rounded-bl-md border border-rose/30 bg-rose/10 text-ivory" : "rounded-bl-md border border-white/[0.08] bg-white/[0.06] text-ivory")}>
              <Formatted text={m.text} />
              {m.failed && m.retryText && (
                <button onClick={() => onRetry(m.retryText!)} className="mt-2 inline-flex items-center gap-1.5 text-xs text-gold-soft underline-offset-2 hover:underline"><RotateCcw className="h-3 w-3" />{s.retry}</button>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex animate-rise items-center gap-2 text-sm text-gold-soft"><Spinner />{toolStatus ? s.tools[toolStatus] ?? s.thinking : s.thinking}</div>
        )}
        <div ref={end} />
      </div>
      <div className="flex items-center gap-2 border-t border-white/[0.07] p-3">
        <button className="btn btn-ghost !p-3" onClick={onMic} aria-label={s.mic}><Mic className="h-5 w-5" /></button>
        <input className="input !rounded-full" value={text} onChange={(e) => setText(e.target.value)} placeholder={s.askPlaceholder} aria-label={s.askPlaceholder}
          maxLength={1000} onKeyDown={(e) => { if (e.key === "Enter" && !e.nativeEvent.isComposing) submit(); }} />
        <button className="btn btn-gold !p-3" onClick={submit} disabled={!text.trim() || busy} aria-label={s.send}><Send className="h-5 w-5" /></button>
      </div>
    </section>
  );
}
