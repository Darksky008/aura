"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { Badge, Skeleton, Spinner } from "@/components/ui";
import { useAdminData } from "@/lib/admin";
import { request } from "@/services/api";

interface Status { llm_provider: string; llm_model: string; stt: string | null; tts: string | null; tts_voices: Record<string, string>; avatar_provider: string; voice_provider: string; tools: string[]; environment: string; admin_protected: boolean }

export default function AssistantPage() {
  const { data } = useAdminData<Status>("/assistant");
  const [q, setQ] = useState("I want something vegetarian and not too spicy.");
  const [lang, setLang] = useState("en");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<{ reply: string; tools_used: string[]; provider: string; latency_ms: number } | null>(null);
  const [err, setErr] = useState("");

  const run = async () => {
    setBusy(true); setErr("");
    try { setOut(await request("/assistant/chat", { method: "POST", body: JSON.stringify({ message: q, language: lang }) })); }
    catch (e) { setErr(e instanceof Error ? e.message : "Failed"); }
    finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader title="AI Assistant" sub="Configuration is read-only here - it comes from backend environment variables." />
      {!data ? <Skeleton className="h-60" /> : (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="glass rounded-3xl p-5">
            <h2 className="mb-4 font-display text-2xl">Providers</h2>
            <dl className="space-y-3 text-sm">
              {[["Language model", `${data.llm_provider} · ${data.llm_model}`], ["Speech recognition", data.stt ?? "browser fallback only (set GROQ_API_KEY)"], ["Speech output", data.tts ?? "browser voices"],
                ["Voices (EN / TA / HI)", `${data.tts_voices.en} · ${data.tts_voices.ta} · ${data.tts_voices.hi}`], ["Avatar / voice adapters", `${data.avatar_provider} / ${data.voice_provider}`], ["Environment", `${data.environment}${data.admin_protected ? "" : " (admin open - set ADMIN_API_KEY)"}`]].map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-white/[0.05] pb-2 last:border-0"><dt className="text-muted">{k}</dt><dd className="text-right text-ivory">{v}</dd></div>
              ))}
            </dl>
            <h3 className="label mt-5">Tools the model can call</h3>
            <div className="flex flex-wrap gap-1.5">{data.tools.map((t) => <Badge key={t} tone="gold">{t}</Badge>)}</div>
          </section>
          <section className="glass rounded-3xl p-5">
            <h2 className="mb-4 font-display text-2xl">Test console</h2>
            <div className="mb-2 flex gap-2"><select className="input !w-28" value={lang} onChange={(e) => setLang(e.target.value)}><option value="en">English</option><option value="ta">தமிழ்</option><option value="hi">हिन्दी</option></select>
              <input className="input" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run()} aria-label="Test question" />
              <button className="btn btn-gold !px-4" onClick={run} disabled={busy || !q.trim()} aria-label="Run">{busy ? <Spinner /> : <Send className="h-4 w-4" />}</button></div>
            {err && <p className="text-sm text-rose">{err}</p>}
            {out && <div className="mt-3 space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm"><p className="leading-relaxed">{out.reply}</p>
              <div className="flex flex-wrap gap-1.5"><Badge>{out.provider}</Badge><Badge>{out.latency_ms} ms</Badge>{out.tools_used.map((t) => <Badge key={t} tone="gold">{t}</Badge>)}</div></div>}
          </section>
        </div>
      )}
    </>
  );
}
