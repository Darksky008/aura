"use client";

import { useState } from "react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { AreaLine, HBars } from "@/components/dashboard/charts";
import { Skeleton, Tabs } from "@/components/ui";
import { useAdminData } from "@/lib/admin";
import type { Analytics } from "../page";

const LABELS: Record<string, string> = { conversation_started: "Conversations started", question_asked: "Questions asked", dish_viewed: "Dish views", dish_recommended: "Dishes recommended",
  special_viewed: "Specials viewed", ingredient_question: "Ingredient questions", allergen_question: "Allergen questions", dietary_question: "Dietary questions", voice_used: "Voice used", language_changed: "Language changes" };

export default function AnalyticsPage() {
  const [days, setDays] = useState("7");
  const { data } = useAdminData<Analytics & { events_by_type: Record<string, number> }>(`/analytics?days=${days}`);
  return (
    <>
      <PageHeader title="Analytics" sub="Structured events only - guest messages are never stored in analytics." action={<Tabs value={days} onChange={setDays} items={[{ id: "7", label: "7 days" }, { id: "30", label: "30 days" }, { id: "90", label: "90 days" }]} />} />
      {!data ? <Skeleton className="h-72" /> : (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="glass rounded-3xl p-5 lg:col-span-2"><h2 className="mb-3 font-display text-2xl">Conversations per day</h2><AreaLine points={data.conversations_per_day.map((d) => ({ label: d.date, value: d.conversations }))} /></section>
          <section className="glass rounded-3xl p-5"><h2 className="mb-4 font-display text-2xl">Topics</h2><HBars items={data.topics.map((t) => ({ label: t.label, value: t.count }))} /></section>
          <section className="glass rounded-3xl p-5"><h2 className="mb-4 font-display text-2xl">Most discussed dishes</h2><HBars items={data.top_dishes.map((d) => ({ label: d.name, value: d.count }))} /></section>
          <section className="glass rounded-3xl p-5 lg:col-span-2"><h2 className="mb-4 font-display text-2xl">All events</h2>
            <HBars items={Object.entries(data.events_by_type).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({ label: LABELS[k] ?? k, value: v }))} /></section>
        </div>
      )}
    </>
  );
}
