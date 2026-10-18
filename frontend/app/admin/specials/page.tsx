"use client";

import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { Badge, Dialog, EmptyState, Field, Skeleton, Switch } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { adminJson, useAdminData } from "@/lib/admin";
import { ApiError } from "@/services/api";
import type { Dish } from "@/types";

interface SpecialRow { id: string; type: string; title: string; description: string | null; is_active: boolean; starts_on: string | null; ends_on: string | null; dish: { id: string; name: string } | null }
const TYPES: Record<string, string> = { today: "Today's Special", weekend: "Weekend Special", chef_recommendation: "Chef Recommendation", seasonal: "Seasonal Item" };

export default function SpecialsPage() {
  const toast = useToast();
  const { data, reload } = useAdminData<SpecialRow[]>("/specials");
  const { data: dishes } = useAdminData<Dish[]>("/dishes");
  const [edit, setEdit] = useState<Partial<SpecialRow> & { open: boolean } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const open = (s?: SpecialRow) => { setErrors({}); setEdit({ open: true, id: s?.id, type: s?.type ?? "today", title: s?.title ?? "", description: s?.description ?? "", dish: s?.dish ?? null, is_active: s?.is_active ?? true, starts_on: s?.starts_on, ends_on: s?.ends_on }); };
  const save = async () => {
    if (!edit) return;
    if ((edit.title ?? "").trim().length < 2) return setErrors({ title: "Give this special a title." });
    const body = { special_type: edit.type, title: edit.title!.trim(), description: edit.description || null, dish_id: edit.dish?.id ?? null, is_active: edit.is_active, starts_on: edit.starts_on || null, ends_on: edit.ends_on || null };
    try { await (edit.id ? adminJson(`/specials/${edit.id}`, "PUT", body) : adminJson("/specials", "POST", body)); toast("Special saved", "success"); setEdit(null); await reload(); }
    catch (e) { toast(e instanceof ApiError ? e.message : "Could not save", "error"); }
  };
  const remove = async (s: SpecialRow) => { try { await adminJson(`/specials/${s.id}`, "DELETE"); await reload(); toast("Special removed", "success"); } catch { toast("Could not delete", "error"); } };

  return (
    <>
      <PageHeader title="Specials" sub="AURA announces whatever is active here when guests ask about specials." action={<button className="btn btn-gold" onClick={() => open()}><Plus className="h-4 w-4" />New special</button>} />
      {!data ? <Skeleton className="h-60" /> : data.length === 0 ? <EmptyState title="No specials yet" hint="Create today's special so AURA can recommend it." /> : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((s) => (
            <article key={s.id} className="glass rounded-3xl p-5">
              <div className="flex items-start justify-between gap-3"><div><Badge tone="gold">{TYPES[s.type] ?? s.type}</Badge><h2 className="mt-2 font-display text-2xl">{s.title}</h2></div>{!s.is_active && <Badge tone="rose">Inactive</Badge>}</div>
              <p className="mt-1 text-sm text-gold-soft">{s.dish?.name ?? "No dish linked"}</p>
              {s.description && <p className="mt-2 text-sm text-muted">{s.description}</p>}
              <div className="mt-4 flex justify-end gap-1.5"><button className="btn btn-ghost !p-2" aria-label="Edit special" onClick={() => open(s)}><Pencil className="h-4 w-4" /></button><button className="btn btn-danger !p-2" aria-label="Delete special" onClick={() => remove(s)}><Trash2 className="h-4 w-4" /></button></div>
            </article>
          ))}
        </div>
      )}
      <Dialog open={!!edit?.open} onClose={() => setEdit(null)} title={edit?.id ? "Edit special" : "New special"}>
        {edit && (
          <div className="space-y-4">
            <Field label="Type"><select className="input" value={edit.type} onChange={(e) => setEdit({ ...edit, type: e.target.value })}>{Object.entries(TYPES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Field>
            <Field label="Title *" error={errors.title}><input className="input" value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} /></Field>
            <Field label="Dish"><select className="input" value={edit.dish?.id ?? ""} onChange={(e) => setEdit({ ...edit, dish: dishes?.find((d) => d.id === e.target.value) ? { id: e.target.value, name: dishes!.find((d) => d.id === e.target.value)!.name } : null })}><option value="">- none -</option>{dishes?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></Field>
            <Field label="Note for guests"><textarea className="input min-h-20" value={edit.description ?? ""} onChange={(e) => setEdit({ ...edit, description: e.target.value })} /></Field>
            <div className="grid grid-cols-2 gap-3"><Field label="Starts"><input type="date" className="input" value={edit.starts_on ?? ""} onChange={(e) => setEdit({ ...edit, starts_on: e.target.value })} /></Field>
              <Field label="Ends"><input type="date" className="input" value={edit.ends_on ?? ""} onChange={(e) => setEdit({ ...edit, ends_on: e.target.value })} /></Field></div>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 px-4 py-3 text-sm">Active <Switch checked={!!edit.is_active} onChange={(v) => setEdit({ ...edit, is_active: v })} label="Active" /></label>
            <div className="flex justify-end gap-2"><button className="btn btn-ghost" onClick={() => setEdit(null)}>Cancel</button><button className="btn btn-gold" onClick={save}>Save</button></div>
          </div>
        )}
      </Dialog>
    </>
  );
}
