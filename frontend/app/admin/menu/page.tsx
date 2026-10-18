"use client";

import { useState } from "react";
import { Pencil, Plus, Star, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { DishFormDialog, type Reference } from "@/components/dashboard/DishForm";
import { Badge, Dialog, EmptyState, Skeleton, Switch, VegMark } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { adminJson, useAdminData } from "@/lib/admin";
import { ApiError } from "@/services/api";
import type { Dish } from "@/types";

export default function AdminMenu() {
  const toast = useToast();
  const { data: dishes, reload, error } = useAdminData<Dish[]>("/dishes");
  const { data: reference } = useAdminData<Reference>("/reference");
  const [editing, setEditing] = useState<Dish | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [deleting, setDeleting] = useState<Dish | null>(null);

  const patch = async (d: Dish, path: string) => {
    try { await adminJson(`/dishes/${d.id}/${path}`, "PATCH"); await reload(); } catch (e) { toast(e instanceof ApiError ? e.message : "Update failed", "error"); }
  };
  const remove = async () => {
    if (!deleting) return;
    try { await adminJson(`/dishes/${deleting.id}`, "DELETE"); toast(`${deleting.name} deleted`, "success"); setDeleting(null); await reload(); }
    catch (e) { toast(e instanceof ApiError ? e.message : "Delete failed", "error"); }
  };

  return (
    <>
      <PageHeader title="Menu" sub="Everything AURA knows about a dish comes from here." action={<button className="btn btn-gold" onClick={() => { setEditing(null); setFormOpen(true); }}><Plus className="h-4 w-4" />Add dish</button>} />
      {error && <p className="text-rose">{error}</p>}
      {!dishes ? <Skeleton className="h-80" /> : dishes.length === 0 ? <EmptyState title="No dishes yet" hint="Add your first dish and AURA can start answering questions about it." /> : (
        <div className="glass overflow-x-auto rounded-3xl">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-xs text-muted"><tr className="border-b border-white/[0.07]"><th className="p-4 font-medium">Dish</th><th className="p-4 font-medium">Category</th><th className="p-4 font-medium">Spice</th><th className="p-4 font-medium">Kcal</th>
              <th className="p-4 font-medium">Chef special</th><th className="p-4 font-medium">Available</th><th className="p-4" /></tr></thead>
            <tbody>
              {dishes.map((d) => (
                <tr key={d.id} className="border-b border-white/[0.05] last:border-0 hover:bg-white/[0.03]">
                  <td className="p-4"><div className="flex items-center gap-2"><VegMark value={d.dietary.vegetarian ?? "unknown"} /><span className="font-medium text-ivory">{d.name}</span></div>
                    <div className="mt-1 flex gap-1.5">{d.allergens.map((a) => <Badge key={a.code}>{a.label}</Badge>)}</div></td>
                  <td className="p-4 text-ivory-dim">{d.category?.name}</td>
                  <td className="p-4 capitalize text-ivory-dim">{d.spice_level}</td>
                  <td className="p-4 tabular-nums text-ivory-dim">{d.calories_kcal ?? "-"}</td>
                  <td className="p-4"><button aria-label="Toggle chef special" aria-pressed={d.is_chef_special} onClick={() => patch(d, `chef-special?special=${!d.is_chef_special}`)}><Star className={d.is_chef_special ? "h-5 w-5 fill-gold text-gold" : "h-5 w-5 text-white/25"} /></button></td>
                  <td className="p-4"><Switch checked={d.is_available} label={`${d.name} available`} onChange={(v) => patch(d, `availability?available=${v}`)} /></td>
                  <td className="p-4"><div className="flex justify-end gap-1.5">
                    <button className="btn btn-ghost !p-2" aria-label={`Edit ${d.name}`} onClick={() => { setEditing(d); setFormOpen(true); }}><Pencil className="h-4 w-4" /></button>
                    <button className="btn btn-danger !p-2" aria-label={`Delete ${d.name}`} onClick={() => setDeleting(d)}><Trash2 className="h-4 w-4" /></button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <DishFormDialog open={formOpen} dish={editing} reference={reference} onClose={() => setFormOpen(false)} onSaved={reload} />
      <Dialog open={!!deleting} onClose={() => setDeleting(null)} title="Delete this dish?">
        <p className="text-sm text-ivory-dim">“{deleting?.name}” will be removed from the menu and AURA will stop mentioning it. This cannot be undone.</p>
        <div className="mt-5 flex justify-end gap-2"><button className="btn btn-ghost" onClick={() => setDeleting(null)}>Keep it</button><button className="btn btn-danger" onClick={remove}>Delete dish</button></div>
      </Dialog>
    </>
  );
}
