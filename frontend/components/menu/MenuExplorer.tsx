"use client";

import { useEffect, useMemo, useState } from "react";
import { MessageCircle } from "lucide-react";
import { Dialog, EmptyState, Skeleton, Tabs } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { localName, STRINGS } from "@/lib/i18n";
import { ApiError, api } from "@/services/api";
import type { Category, Dish, Lang } from "@/types";
import { DietBadges, SpiceMeter } from "./Badges";
import { DishArt } from "./DishArt";

type Filter = "all" | "chef" | "vegetarian" | "vegan" | string;

export function MenuExplorer({ language, onAsk, sessionId }: { language: Lang; onAsk: (dish: Dish, question: string) => void; sessionId?: string | null }) {
  const s = STRINGS[language];
  const toast = useToast();
  const [data, setData] = useState<{ categories: Category[]; dishes: Dish[] } | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [selected, setSelected] = useState<Dish | null>(null);

  useEffect(() => { api.menu().then(setData).catch((e) => toast(e instanceof ApiError ? e.message : s.serviceDown, "error")); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const tabs = useMemo(() => {
    const cats = (data?.categories ?? []).map((c) => ({ id: c.slug, label: s.filters[c.slug] ?? localName(c.names, c.name, language) }));
    return [{ id: "all", label: s.filters.all }, ...cats, { id: "chef", label: s.filters.chef }, { id: "vegetarian", label: s.filters.vegetarian }, { id: "vegan", label: s.filters.vegan }];
  }, [data, s, language]);

  const dishes = useMemo(() => (data?.dishes ?? []).filter((d) => {
    if (filter === "all") return true;
    if (filter === "chef") return d.is_chef_special;
    if (filter === "vegetarian") return d.dietary.vegetarian === "yes";
    if (filter === "vegan") return d.dietary.vegan === "yes";
    return d.category?.slug === filter;
  }), [data, filter]);

  const open = (d: Dish) => { setSelected(d); void api.event("dish_viewed", sessionId ?? null, { dishes: [d.name], via: "menu" }); };

  return (
    <div>
      <Tabs items={tabs} value={filter} onChange={setFilter} className="mb-5" />
      {!data ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-72" />)}</div>
      ) : dishes.length === 0 ? <EmptyState title={s.nothingHere} /> : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {dishes.map((d) => (
            <article key={d.id} className={`glass group flex flex-col overflow-hidden rounded-3xl transition hover:-translate-y-0.5 hover:border-gold/30 ${d.is_available ? "" : "opacity-60"}`}>
              <button onClick={() => open(d)} className="text-left" aria-label={localName(d.names, d.name, language)}>
                <div className="flex justify-center bg-[radial-gradient(70%_70%_at_50%_40%,rgba(217,174,91,0.14),transparent)] px-6 pt-5">
                  <DishArt slug={d.slug} name={d.name} className="h-36 w-36 transition duration-500 group-hover:scale-105" />
                </div>
                <div className="space-y-2.5 p-5">
                  <h3 className="font-display text-2xl font-semibold leading-tight">{localName(d.names, d.name, language)}</h3>
                  <p className="line-clamp-2 text-sm text-muted">{d.description}</p>
                  <div className="flex items-center justify-between gap-2"><SpiceMeter level={d.spice_level} label={s.spice[d.spice_level]} />
                    <span className="text-xs text-muted">{d.price != null ? `₹${d.price}` : s.priceOnRequest}</span></div>
                  <DietBadges dish={d} s={s} />
                </div>
              </button>
            </article>
          ))}
        </div>
      )}

      <Dialog open={!!selected} onClose={() => setSelected(null)} title={selected ? localName(selected.names, selected.name, language) : ""} wide>
        {selected && (
          <div className="grid gap-6 sm:grid-cols-[180px_1fr]">
            <div className="flex flex-col items-center gap-3">
              <DishArt slug={selected.slug} name={selected.name} className="h-40 w-40" />
              <SpiceMeter level={selected.spice_level} label={s.spice[selected.spice_level]} />
            </div>
            <div className="space-y-4 text-sm">
              <DietBadges dish={selected} s={s} />
              <p className="text-base leading-relaxed text-ivory-dim">{selected.description}</p>
              <dl className="grid grid-cols-2 gap-3">
                <div className="glass rounded-2xl p-3"><dt className="label !mb-0.5">{s.calories}</dt><dd>{selected.calories_kcal ? `≈ ${selected.calories_kcal} kcal` : s.unknown}</dd></div>
                <div className="glass rounded-2xl p-3"><dt className="label !mb-0.5">{s.available}</dt><dd>{selected.is_available ? s.yes : s.no}</dd></div>
                <div className="glass col-span-2 rounded-2xl p-3"><dt className="label !mb-0.5">{s.allergens}</dt>
                  <dd>{selected.allergens.length ? selected.allergens.map((a) => a.label).join(", ") : s.none}</dd></div>
              </dl>
              <div><h4 className="label">{s.ingredients}</h4><p className="leading-relaxed text-ivory-dim">{selected.ingredients.join(" · ")}</p></div>
              <p className="text-xs text-muted">{s.confirmWithTeam}</p>
              <div className="flex flex-wrap gap-2 pt-1">
                <button className="btn btn-gold" onClick={() => { onAsk(selected, s.askWhy); setSelected(null); }}><MessageCircle className="h-4 w-4" />{s.askAbout}</button>
              </div>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
