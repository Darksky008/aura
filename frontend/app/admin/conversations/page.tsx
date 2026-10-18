"use client";

import { useState } from "react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { Badge, EmptyState, Skeleton } from "@/components/ui";
import { adminRequest, useAdminData } from "@/lib/admin";
import { cn } from "@/lib/utils";

interface Row { id: string; language: string; channel: string; started_at: string; messages: number }
interface Detail { id: string; language: string; messages: { role: string; content: string; tools_used: string[]; latency_ms: number | null; at: string }[] }

export default function ConversationsPage() {
  const { data } = useAdminData<Row[]>("/conversations");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [active, setActive] = useState<string | null>(null);
  const load = async (id: string) => { setActive(id); setDetail(await adminRequest<Detail>(`/conversations/${id}`)); };
  return (
    <>
      <PageHeader title="Conversations" sub="Guest sessions, newest first. No personal details are collected." />
      {!data ? <Skeleton className="h-72" /> : data.length === 0 ? <EmptyState title="No conversations yet" hint="Talk to AURA on the customer screen and they will appear here." /> : (
        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <ul className="glass max-h-[70dvh] space-y-1 overflow-y-auto rounded-3xl p-2">
            {data.map((r) => (
              <li key={r.id}><button onClick={() => load(r.id)} className={cn("w-full rounded-2xl px-4 py-3 text-left text-sm transition", active === r.id ? "bg-gold/15" : "hover:bg-white/[0.06]")}>
                <div className="flex items-center justify-between"><span className="text-ivory">{new Date(r.started_at).toLocaleString()}</span><Badge>{r.language.toUpperCase()}</Badge></div>
                <p className="mt-0.5 text-xs text-muted">{r.messages} messages · {r.channel}</p></button></li>
            ))}
          </ul>
          <section className="glass min-h-72 space-y-3 rounded-3xl p-5">
            {!detail ? <p className="py-16 text-center text-sm text-muted">Select a conversation</p> : detail.messages.map((m, i) => (
              <div key={i} className={cn("max-w-[85%] rounded-2xl px-4 py-2.5 text-sm", m.role === "user" ? "ml-auto bg-gold/85 text-ink" : "border border-white/10 bg-white/[0.05]")}>
                <p>{m.content}</p>
                {m.role === "assistant" && <div className="mt-1.5 flex flex-wrap gap-1">{m.tools_used.map((t) => <Badge key={t}>{t}</Badge>)}{m.latency_ms != null && <Badge>{m.latency_ms} ms</Badge>}</div>}
              </div>
            ))}
          </section>
        </div>
      )}
    </>
  );
}
