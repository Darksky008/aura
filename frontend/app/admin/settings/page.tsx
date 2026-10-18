"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/dashboard/AdminShell";
import { Field, Skeleton, Spinner } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { adminJson, useAdminData } from "@/lib/admin";
import { ApiError } from "@/services/api";

interface S { hotel_name: string; tagline: string | null; assistant_name: string; supported_languages: string[]; restaurant_name: string; restaurant_description: string | null; slug: string }
const LANGS = [["en", "English"], ["ta", "தமிழ்"], ["hi", "हिन्दी"]];

export default function SettingsPage() {
  const toast = useToast();
  const { data } = useAdminData<S>("/settings");
  const [f, setF] = useState<S | null>(null);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<Record<string, string>>({});
  useEffect(() => { if (data) setF(data); }, [data]);
  if (!f) return <Skeleton className="h-80" />;
  const set = <K extends keyof S>(k: K, v: S[K]) => setF({ ...f, [k]: v });
  const save = async () => {
    const e: Record<string, string> = {};
    if (f.hotel_name.trim().length < 2) e.hotel_name = "Required";
    if (f.restaurant_name.trim().length < 2) e.restaurant_name = "Required";
    if (f.assistant_name.trim().length < 2) e.assistant_name = "Required";
    if (!f.supported_languages.length) e.languages = "Choose at least one language.";
    setErr(e);
    if (Object.keys(e).length) return;
    setSaving(true);
    try { await adminJson("/settings", "PUT", f); toast("Settings saved", "success"); } catch (x) { toast(x instanceof ApiError ? x.message : "Could not save", "error"); } finally { setSaving(false); }
  };
  return (
    <>
      <PageHeader title="Settings" sub={`Tenant: ${f.slug}`} />
      <div className="glass max-w-2xl space-y-4 rounded-3xl p-6">
        <Field label="Hotel name" error={err.hotel_name}><input className="input" value={f.hotel_name} onChange={(e) => set("hotel_name", e.target.value)} /></Field>
        <Field label="Tagline"><input className="input" value={f.tagline ?? ""} onChange={(e) => set("tagline", e.target.value)} /></Field>
        <Field label="Restaurant name" error={err.restaurant_name}><input className="input" value={f.restaurant_name} onChange={(e) => set("restaurant_name", e.target.value)} /></Field>
        <Field label="Restaurant description"><textarea className="input min-h-24" value={f.restaurant_description ?? ""} onChange={(e) => set("restaurant_description", e.target.value)} /></Field>
        <Field label="Assistant name" error={err.assistant_name}><input className="input" value={f.assistant_name} onChange={(e) => set("assistant_name", e.target.value)} /></Field>
        <div><span className="label">Languages offered to guests</span>
          <div className="flex gap-2">{LANGS.map(([c, l]) => { const on = f.supported_languages.includes(c); return <button key={c} type="button" aria-pressed={on} className={`chip ${on ? "!border-gold/60 !bg-gold/20 !text-gold-soft" : ""}`}
            onClick={() => set("supported_languages", on ? f.supported_languages.filter((x) => x !== c) : [...f.supported_languages, c])}>{l}</button>; })}</div>
          {err.languages && <p role="alert" className="mt-1 text-xs text-rose">{err.languages}</p>}</div>
        <div className="flex justify-end"><button className="btn btn-gold" onClick={save} disabled={saving}>{saving && <Spinner />}Save settings</button></div>
      </div>
    </>
  );
}
