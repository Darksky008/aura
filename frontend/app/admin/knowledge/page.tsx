"use client";

import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { Badge, Dialog, EmptyState, Field, Skeleton, Switch } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { adminJson, useAdminData } from "@/lib/admin";
import { ApiError } from "@/services/api";

interface Doc { id: string; doc_type: string; title: string; content: string; is_published: boolean }
const TYPES = ["restaurant", "chef", "philosophy", "faq", "policy", "dish_story", "preparation"];

export default function KnowledgePage() {
  const toast = useToast();
  const { data, reload } = useAdminData<Doc[]>("/knowledge");
  const [edit, setEdit] = useState<(Partial<Doc> & { open: boolean }) | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const open = (d?: Doc) => { setErrors({}); setEdit({ open: true, id: d?.id, doc_type: d?.doc_type ?? "faq", title: d?.title ?? "", content: d?.content ?? "", is_published: d?.is_published ?? true }); };
  const save = async () => {
    if (!edit) return;
    const e: Record<string, string> = {};
    if ((edit.title ?? "").trim().length < 3) e.title = "Title needs at least 3 characters.";
    if ((edit.content ?? "").trim().length < 10) e.content = "Write at least a sentence so AURA has something to quote.";
    setErrors(e);
    if (Object.keys(e).length) return;
    const body = { doc_type: edit.doc_type, title: edit.title!.trim(), content: edit.content!.trim(), is_published: edit.is_published };
    try { await (edit.id ? adminJson(`/knowledge/${edit.id}`, "PUT", body) : adminJson("/knowledge", "POST", body)); toast("Saved", "success"); setEdit(null); await reload(); }
    catch (err) { toast(err instanceof ApiError ? err.message : "Could not save", "error"); }
  };

  return (
    <>
      <PageHeader title="Knowledge Base" sub="Chef stories, philosophy, FAQs and policies. AURA searches these when a question isn't about a specific dish." action={<button className="btn btn-gold" onClick={() => open()}><Plus className="h-4 w-4" />Add document</button>} />
      {!data ? <Skeleton className="h-60" /> : data.length === 0 ? <EmptyState title="Nothing here yet" /> : (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((d) => (
            <article key={d.id} className="glass flex flex-col rounded-3xl p-5">
              <div className="flex items-center justify-between"><Badge tone="gold">{d.doc_type.replace("_", " ")}</Badge>{!d.is_published && <Badge tone="rose">Draft</Badge>}</div>
              <h2 className="mt-2 font-display text-2xl">{d.title}</h2>
              <p className="mt-1 line-clamp-4 flex-1 text-sm text-muted">{d.content}</p>
              <div className="mt-4 flex justify-end gap-1.5"><button className="btn btn-ghost !p-2" aria-label="Edit" onClick={() => open(d)}><Pencil className="h-4 w-4" /></button>
                <button className="btn btn-danger !p-2" aria-label="Delete" onClick={async () => { await adminJson(`/knowledge/${d.id}`, "DELETE"); await reload(); }}><Trash2 className="h-4 w-4" /></button></div>
            </article>
          ))}
        </div>
      )}
      <Dialog open={!!edit?.open} onClose={() => setEdit(null)} title={edit?.id ? "Edit document" : "New document"}>
        {edit && (
          <div className="space-y-4">
            <Field label="Type"><select className="input" value={edit.doc_type} onChange={(e) => setEdit({ ...edit, doc_type: e.target.value })}>{TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}</select></Field>
            <Field label="Title *" error={errors.title}><input className="input" value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} /></Field>
            <Field label="Content *" error={errors.content} hint="Write facts only - AURA repeats this to guests."><textarea className="input min-h-40" value={edit.content} onChange={(e) => setEdit({ ...edit, content: e.target.value })} /></Field>
            <label className="flex items-center justify-between rounded-2xl border border-white/10 px-4 py-3 text-sm">Published <Switch checked={!!edit.is_published} onChange={(v) => setEdit({ ...edit, is_published: v })} label="Published" /></label>
            <div className="flex justify-end gap-2"><button className="btn btn-ghost" onClick={() => setEdit(null)}>Cancel</button><button className="btn btn-gold" onClick={save}>Save</button></div>
          </div>
        )}
      </Dialog>
    </>
  );
}
