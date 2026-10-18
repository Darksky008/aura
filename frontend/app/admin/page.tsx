"use client";

import { Bot, Flame, Leaf, MessagesSquare, Mic, Star, UtensilsCrossed } from "lucide-react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { AreaLine, HBars, KpiCard } from "@/components/dashboard/charts";
import { Skeleton } from "@/components/ui";
import { useAdminData } from "@/lib/admin";

export interface Analytics {
  total_menu_items: number; ai_conversations: number; most_asked_dish: string | null; most_asked_topic: string | null; vegetarian_requests: number; chef_special_searches: number;
  conversations_per_day: { date: string; conversations: number }[]; top_dishes: { name: string; count: number }[]; topics: { label: string; count: number }[]; voice_sessions: number; window_days: number;
}

export default function Dashboard() {
  const { data, error } = useAdminData<Analytics>("/analytics");
  const { data: ai } = useAdminData<{ llm_provider: string; llm_model: string; tts: string | null }>("/assistant");
  if (error) return <p className="text-rose">{error}</p>;
  if (!data) return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>;
  return (
    <>
      <PageHeader title="Dashboard" sub={`Last ${data.window_days} days · demo events are marked as seed data`} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard accent label="Total menu items" value={data.total_menu_items} icon={<UtensilsCrossed className="h-4 w-4" />} />
        <KpiCard label="AI conversations" value={data.ai_conversations} icon={<MessagesSquare className="h-4 w-4" />} hint={`${data.voice_sessions} voice questions`} />
        <KpiCard label="Most asked dish" value={<span className="text-3xl">{data.most_asked_dish ?? "-"}</span>} icon={<Star className="h-4 w-4" />} />
        <KpiCard label="Most asked topic" value={<span className="text-3xl">{data.most_asked_topic ?? "-"}</span>} icon={<Flame className="h-4 w-4" />} />
        <KpiCard label="Vegetarian requests" value={data.vegetarian_requests} icon={<Leaf className="h-4 w-4" />} />
        <KpiCard label="Chef special searches" value={data.chef_special_searches} icon={<Mic className="h-4 w-4" />} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-5">
        <section className="glass rounded-3xl p-5 lg:col-span-3"><h2 className="mb-3 font-display text-2xl">Conversations per day</h2><AreaLine points={data.conversations_per_day.map((d) => ({ label: d.date, value: d.conversations }))} /></section>
        <section className="glass rounded-3xl p-5 lg:col-span-2"><h2 className="mb-4 font-display text-2xl">Top dishes</h2><HBars items={data.top_dishes.slice(0, 5).map((d) => ({ label: d.name, value: d.count }))} /></section>
      </div>
      {ai && <section className="glass mt-4 flex flex-wrap items-center gap-3 rounded-3xl p-4 text-sm text-ivory-dim"><Bot className="h-4 w-4 text-gold" />Assistant: <b className="text-ivory">{ai.llm_provider}</b> · {ai.llm_model} · voice: {ai.tts ?? "browser"}</section>}
    </>
  );
}
