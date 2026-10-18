"use client";

import { Globe } from "lucide-react";
import { LANG_LABEL } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { Lang } from "@/types";

export function LanguageSelector({ value, onChange, languages, label }: { value: Lang; onChange: (l: Lang) => void; languages: Lang[]; label: string }) {
  return (
    <div role="radiogroup" aria-label={label} className="glass flex items-center gap-0.5 rounded-full p-1">
      <Globe className="mx-2 hidden h-4 w-4 text-muted sm:block" aria-hidden />
      {languages.map((l) => (
        <button key={l} role="radio" aria-checked={value === l} onClick={() => onChange(l)}
          className={cn("rounded-full px-3 py-1.5 text-sm transition", value === l ? "bg-gold text-ink font-medium" : "text-ivory-dim hover:bg-white/10")}>
          {LANG_LABEL[l]}
        </button>
      ))}
    </div>
  );
}
