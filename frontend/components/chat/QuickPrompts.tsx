"use client";

export function QuickPrompts({ prompts, title, onPick, disabled }: { prompts: string[]; title: string; onPick: (p: string) => void; disabled?: boolean }) {
  return (
    <div>
      <p className="mb-2.5 text-center text-xs text-muted">{title}</p>
      <div className="flex flex-wrap justify-center gap-2">
        {prompts.map((p) => <button key={p} className="chip" disabled={disabled} onClick={() => onPick(p)}>{p}</button>)}
      </div>
    </div>
  );
}
