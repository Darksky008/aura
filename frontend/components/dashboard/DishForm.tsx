"use client";

import { useEffect, useState } from "react";
import { Dialog, Field, Spinner, Switch } from "@/components/ui";
import { useToast } from "@/components/ui/Toast";
import { adminJson } from "@/lib/admin";
import { ApiError } from "@/services/api";
import type { Dish, Tri } from "@/types";

export interface Reference { allergens: { code: string; label: string }[]; dietary_tags: { code: string; label: string }[]; categories: { id: string; name: string }[] }

interface FormState {
  name: string; ta: string; hi: string; aliases: string; description: string; category_id: string; cuisine: string; spice_level: string;
  calories: string; price: string; ingredients: string; allergens: string[]; dietary: Record<string, Tri>; preparation_notes: string; is_chef_special: boolean; is_available: boolean;
}
const DIET = ["vegetarian", "vegan", "gluten_free", "halal", "jain"];
const empty = (cat: string): FormState => ({ name: "", ta: "", hi: "", aliases: "", description: "", category_id: cat, cuisine: "", spice_level: "mild", calories: "", price: "", ingredients: "", allergens: [],
  dietary: { vegetarian: "unknown", vegan: "unknown", gluten_free: "unknown", halal: "unknown", jain: "unknown" }, preparation_notes: "", is_chef_special: false, is_available: true });

const fromDish = (d: Dish): FormState => ({
  name: d.name, ta: d.names.ta ?? "", hi: d.names.hi ?? "", aliases: d.aliases.join(", "), description: d.description ?? "", category_id: d.category?.id ?? "", cuisine: d.cuisine ?? "",
  spice_level: d.spice_level, calories: d.calories_kcal?.toString() ?? "", price: d.price?.toString() ?? "", ingredients: d.ingredients.join("\n"), allergens: d.allergens.map((a) => a.code),
  dietary: { ...empty("").dietary, ...d.dietary }, preparation_notes: d.preparation_notes ?? "", is_chef_special: d.is_chef_special, is_available: d.is_available });

function validate(f: FormState): Record<string, string> {
  const e: Record<string, string> = {};
  if (f.name.trim().length < 2) e.name = "Enter the dish name (at least 2 characters).";
  if (f.calories && (!/^\d+$/.test(f.calories) || +f.calories > 5000)) e.calories = "Whole number between 0 and 5000.";
  if (f.price && (isNaN(+f.price) || +f.price < 0)) e.price = "Enter a positive price, or leave blank if unknown.";
  if (!f.category_id) e.category_id = "Choose a category.";
  if (!f.ingredients.trim()) e.ingredients = "List at least one ingredient - the assistant only quotes listed ingredients.";
  return e;
}

export function DishFormDialog({ open, dish, reference, onClose, onSaved }: { open: boolean; dish: Dish | null; reference: Reference | null; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const [f, setF] = useState<FormState>(empty(""));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  useEffect(() => { if (open) { setF(dish ? fromDish(dish) : empty(reference?.categories[0]?.id ?? "")); setErrors({}); } }, [open, dish, reference]);
  const set = <K extends keyof FormState>(k: K, v: FormState[K]) => setF((p) => ({ ...p, [k]: v }));

  const save = async () => {
    const e = validate(f);
    setErrors(e);
    if (Object.keys(e).length) return;
    const split = (s: string) => s.split(/[\n,]/).map((x) => x.trim()).filter(Boolean);
    const body = {
      name: f.name.trim(), name_translations: Object.fromEntries([["ta", f.ta.trim()], ["hi", f.hi.trim()]].filter(([, v]) => v)), aliases: split(f.aliases), description: f.description.trim() || null,
      category_id: f.category_id, cuisine: f.cuisine.trim() || null, spice_level: f.spice_level, calories_kcal: f.calories ? +f.calories : null, price: f.price ? +f.price : null,
      ingredients: split(f.ingredients), allergens: f.allergens, dietary: f.dietary, preparation_notes: f.preparation_notes.trim() || null, is_chef_special: f.is_chef_special, is_available: f.is_available,
    };
    setSaving(true);
    try {
      await (dish ? adminJson(`/dishes/${dish.id}`, "PUT", body) : adminJson("/dishes", "POST", body));
      toast(dish ? "Dish updated" : "Dish added", "success");
      onSaved(); onClose();
    } catch (err) {
      if (err instanceof ApiError && err.fields) setErrors(Object.fromEntries(err.fields.map((x) => [x.field, x.message])));
      toast(err instanceof ApiError ? err.message : "Could not save.", "error");
    } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onClose={onClose} title={dish ? `Edit ${dish.name}` : "Add dish"} wide>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name *" error={errors.name}><input className="input" value={f.name} onChange={(e) => set("name", e.target.value)} /></Field>
        <Field label="Category *" error={errors.category_id}>
          <select className="input" value={f.category_id} onChange={(e) => set("category_id", e.target.value)}>{reference?.categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
        </Field>
        <Field label="Name in Tamil" hint="Spoken by AURA in Tamil replies"><input className="input" value={f.ta} onChange={(e) => set("ta", e.target.value)} /></Field>
        <Field label="Name in Hindi" hint="Spoken by AURA in Hindi replies"><input className="input" value={f.hi} onChange={(e) => set("hi", e.target.value)} /></Field>
        <Field label="Other names guests may say" hint="Comma separated, e.g. chicken biryani, dum biryani"><input className="input" value={f.aliases} onChange={(e) => set("aliases", e.target.value)} /></Field>
        <Field label="Cuisine"><input className="input" value={f.cuisine} onChange={(e) => set("cuisine", e.target.value)} placeholder="North Indian" /></Field>
        <div className="sm:col-span-2"><Field label="Description"><textarea className="input min-h-20" value={f.description} onChange={(e) => set("description", e.target.value)} /></Field></div>
        <Field label="Spice level"><select className="input" value={f.spice_level} onChange={(e) => set("spice_level", e.target.value)}>{["none", "mild", "medium", "high"].map((s) => <option key={s}>{s}</option>)}</select></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Calories (approx.)" error={errors.calories}><input className="input" inputMode="numeric" value={f.calories} onChange={(e) => set("calories", e.target.value)} /></Field>
          <Field label="Price (₹)" error={errors.price} hint="Blank = never quoted"><input className="input" inputMode="decimal" value={f.price} onChange={(e) => set("price", e.target.value)} /></Field>
        </div>
        <div className="sm:col-span-2"><Field label="Ingredients * (one per line)" error={errors.ingredients}><textarea className="input min-h-28 font-mono text-[13px]" value={f.ingredients} onChange={(e) => set("ingredients", e.target.value)} /></Field></div>
        <div className="sm:col-span-2">
          <span className="label">Allergens declared</span>
          <div className="flex flex-wrap gap-2">
            {reference?.allergens.map((a) => {
              const on = f.allergens.includes(a.code);
              return <button key={a.code} type="button" aria-pressed={on} onClick={() => set("allergens", on ? f.allergens.filter((x) => x !== a.code) : [...f.allergens, a.code])}
                className={`chip ${on ? "!border-gold/60 !bg-gold/20 !text-gold-soft" : ""}`}>{a.label}</button>;
            })}
          </div>
        </div>
        <div className="sm:col-span-2">
          <span className="label">Dietary status - "Unknown" means AURA will never claim it</span>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {DIET.map((d) => (
              <label key={d} className="block"><span className="mb-1 block text-[11px] capitalize text-ivory-dim">{d.replace("_", " ")}</span>
                <select className="input !py-2" value={f.dietary[d]} onChange={(e) => set("dietary", { ...f.dietary, [d]: e.target.value as Tri })}><option value="unknown">Unknown</option><option value="yes">Yes</option><option value="no">No</option></select></label>
            ))}
          </div>
        </div>
        <div className="sm:col-span-2"><Field label="Preparation notes"><textarea className="input min-h-16" value={f.preparation_notes} onChange={(e) => set("preparation_notes", e.target.value)} /></Field></div>
        <label className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 px-4 py-3 text-sm">Chef special <Switch checked={f.is_chef_special} onChange={(v) => set("is_chef_special", v)} label="Chef special" /></label>
        <label className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 px-4 py-3 text-sm">Available now <Switch checked={f.is_available} onChange={(v) => set("is_available", v)} label="Available" /></label>
      </div>
      <div className="mt-6 flex justify-end gap-2"><button className="btn btn-ghost" onClick={onClose}>Cancel</button><button className="btn btn-gold" disabled={saving} onClick={save}>{saving && <Spinner />}{dish ? "Save changes" : "Add dish"}</button></div>
    </Dialog>
  );
}
