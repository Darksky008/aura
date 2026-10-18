"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, Bot, ChefHat, LayoutDashboard, LogOut, MessagesSquare, Settings, Sparkles, UtensilsCrossed } from "lucide-react";
import { Spinner } from "@/components/ui";
import { adminRequest, clearAdminKey, setAdminKey } from "@/lib/admin";
import { cn } from "@/lib/utils";
import { ApiError } from "@/services/api";

const NAV = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard }, { href: "/admin/menu", label: "Menu", icon: UtensilsCrossed },
  { href: "/admin/specials", label: "Specials", icon: Sparkles }, { href: "/admin/knowledge", label: "Knowledge Base", icon: BookOpen },
  { href: "/admin/assistant", label: "AI Assistant", icon: Bot }, { href: "/admin/conversations", label: "Conversations", icon: MessagesSquare },
  { href: "/admin/analytics", label: "Analytics", icon: BarChart3 }, { href: "/admin/settings", label: "Settings", icon: Settings },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [state, setState] = useState<"checking" | "locked" | "ready" | "disabled" | "down">("checking");
  const [key, setKey] = useState("");
  const [err, setErr] = useState("");

  const check = async () => {
    try { await adminRequest("/ping"); setState("ready"); setErr(""); }
    catch (e) {
      if (e instanceof ApiError && e.status === 401) { setState("locked"); if (key) setErr("That key isn't right."); }
      else if (e instanceof ApiError && e.status === 503) setState("disabled");
      else setState("down");
    }
  };
  useEffect(() => { void check(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (state === "checking") return <div className="flex min-h-dvh items-center justify-center"><Spinner className="h-6 w-6 text-gold" /></div>;
  if (state !== "ready") {
    return (
      <main className="flex min-h-dvh items-center justify-center p-6">
        <div className="glass-strong w-full max-w-sm space-y-4 rounded-3xl p-7 text-center">
          <ChefHat className="mx-auto h-9 w-9 text-gold" />
          <h1 className="font-display text-3xl font-semibold">Hotel Admin</h1>
          {state === "locked" && (
            <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); setAdminKey(key); void check(); }}>
              <label className="label text-left" htmlFor="k">Admin key</label>
              <input id="k" type="password" autoFocus className="input" value={key} onChange={(e) => setKey(e.target.value)} placeholder="ADMIN_API_KEY" />
              {err && <p role="alert" className="text-xs text-rose">{err}</p>}
              <button className="btn btn-gold w-full" disabled={!key}>Unlock</button>
            </form>
          )}
          {state === "disabled" && <p className="text-sm text-ivory-dim">Admin is disabled until <code>ADMIN_API_KEY</code> is set on the backend.</p>}
          {state === "down" && <><p className="text-sm text-ivory-dim">The backend can't be reached. If it just woke up on a free plan, wait a moment and retry.</p><button className="btn btn-ghost" onClick={() => void check()}>Retry</button></>}
          <Link href="/" className="block text-xs text-muted hover:underline">← Back to AURA</Link>
        </div>
      </main>
    );
  }
  return (
    <div className="mx-auto flex min-h-dvh max-w-[1400px] flex-col gap-6 px-4 py-5 lg:flex-row lg:px-6">
      <aside className="glass flex shrink-0 flex-col rounded-3xl p-3 lg:sticky lg:top-5 lg:h-[calc(100dvh-2.5rem)] lg:w-60">
        <div className="flex items-center gap-2.5 px-3 pb-3 pt-2"><ChefHat className="h-6 w-6 text-gold" /><div><p className="font-display text-xl font-semibold leading-none">AURA</p><p className="text-[11px] text-muted">Hotel admin</p></div></div>
        <nav className="flex gap-1 overflow-x-auto lg:flex-1 lg:flex-col lg:overflow-visible" aria-label="Admin">
          {NAV.map((n) => {
            const active = n.href === "/admin" ? path === "/admin" : path.startsWith(n.href);
            return <Link key={n.href} href={n.href} aria-current={active ? "page" : undefined}
              className={cn("flex shrink-0 items-center gap-2.5 rounded-2xl px-3.5 py-2.5 text-sm transition", active ? "bg-gold/15 text-gold-soft" : "text-ivory-dim hover:bg-white/[0.06]")}><n.icon className="h-4 w-4" />{n.label}</Link>;
          })}
        </nav>
        <div className="mt-2 flex gap-1 border-t border-white/[0.07] pt-2">
          <Link href="/" className="btn btn-ghost flex-1 !rounded-2xl !py-2 text-xs">Customer view</Link>
          <button className="btn btn-ghost !rounded-2xl !p-2" aria-label="Lock admin" onClick={() => { clearAdminKey(); setState("locked"); setKey(""); }}><LogOut className="h-4 w-4" /></button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 pb-10">{children}</main>
    </div>
  );
}

export function PageHeader({ title, sub, action }: { title: string; sub?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><h1 className="font-display text-4xl font-semibold">{title}</h1>{sub && <p className="mt-1 text-sm text-muted">{sub}</p>}</div>
      {action}
    </div>
  );
}
