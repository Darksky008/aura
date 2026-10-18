"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { MenuExplorer } from "@/components/menu/MenuExplorer";
import { LanguageSelector } from "@/components/voice/LanguageSelector";
import { STRINGS } from "@/lib/i18n";
import type { Lang } from "@/types";

export default function MenuPage() {
  const router = useRouter();
  const [language, setLanguage] = useState<Lang>("en");
  useEffect(() => { const l = localStorage.getItem("aura-lang") as Lang | null; if (l && ["en", "ta", "hi"].includes(l)) setLanguage(l); }, []);
  const s = STRINGS[language];
  return (
    <main className="mx-auto max-w-[1180px] px-4 py-6 sm:px-8">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <Link href="/" className="btn btn-ghost"><ArrowLeft className="h-4 w-4" />{s.backToConcierge}</Link>
        <LanguageSelector value={language} onChange={(l) => { localStorage.setItem("aura-lang", l); setLanguage(l); }} languages={["en", "ta", "hi"]} label={s.language} />
      </header>
      <div className="mb-8">
        <p className="text-sm text-gold-soft">Saffron Terrace · Aurelia Grand Hotel</p>
        <h1 className="font-display text-5xl font-semibold sm:text-6xl">{s.menuTitle}</h1>
        <p className="mt-2 text-ivory-dim">{s.menuSub}</p>
      </div>
      <MenuExplorer language={language} onAsk={(d) => router.push(`/?ask=${d.id}&lang=${language}`)} />
    </main>
  );
}
