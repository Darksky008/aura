"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, AlertTriangle, X } from "lucide-react";
import { uid } from "@/lib/utils";

type Kind = "success" | "error" | "info";
interface Toast { id: string; kind: Kind; text: string }
const Ctx = createContext<(text: string, kind?: Kind) => void>(() => undefined);
export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((text: string, kind: Kind = "info") => {
    const id = uid();
    setItems((p) => [...p, { id, kind, text }]);
    window.setTimeout(() => setItems((p) => p.filter((t) => t.id !== id)), 4200);
  }, []);
  return (
    <Ctx.Provider value={push}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-[100] flex flex-col items-center gap-2 px-4">
        {items.map((t) => (
          <div key={t.id} role="status" className="glass-strong pointer-events-auto flex max-w-md animate-rise items-center gap-3 rounded-2xl px-4 py-3 text-sm">
            {t.kind === "error" ? <AlertTriangle className="h-4 w-4 shrink-0 text-rose" /> : <CheckCircle2 className="h-4 w-4 shrink-0 text-jade" />}
            <span>{t.text}</span>
            <button aria-label="Dismiss" className="ml-1 text-muted hover:text-ivory" onClick={() => setItems((p) => p.filter((x) => x.id !== t.id))}><X className="h-4 w-4" /></button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
