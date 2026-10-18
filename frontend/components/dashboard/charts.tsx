import { cn } from "@/lib/utils";

export function KpiCard({ label, value, hint, icon, accent }: { label: string; value: React.ReactNode; hint?: string; icon?: React.ReactNode; accent?: boolean }) {
  return (
    <div className={cn("glass relative overflow-hidden rounded-3xl p-5", accent && "border-gold/30")}>
      {accent && <div aria-hidden className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gold/15 blur-2xl" />}
      <div className="flex items-center justify-between text-muted"><span className="text-xs">{label}</span>{icon}</div>
      <div className="mt-3 truncate font-display text-4xl font-semibold leading-none text-ivory">{value ?? "-"}</div>
      {hint && <p className="mt-2 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function HBars({ items, empty = "No data yet" }: { items: { label: string; value: number }[]; empty?: string }) {
  const max = Math.max(1, ...items.map((i) => i.value));
  if (!items.length) return <p className="py-6 text-center text-sm text-muted">{empty}</p>;
  return (
    <ul className="space-y-3">
      {items.map((i) => (
        <li key={i.label}>
          <div className="mb-1 flex justify-between text-sm"><span className="truncate text-ivory-dim">{i.label}</span><span className="tabular-nums text-muted">{i.value}</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]"><div className="h-full rounded-full bg-gradient-to-r from-saffron to-gold transition-all duration-700" style={{ width: `${(i.value / max) * 100}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}

export function AreaLine({ points }: { points: { label: string; value: number }[] }) {
  const W = 560, H = 170, pad = 22;
  const max = Math.max(1, ...points.map((p) => p.value));
  const x = (i: number) => pad + (i * (W - pad * 2)) / Math.max(1, points.length - 1);
  const y = (v: number) => H - pad - (v / max) * (H - pad * 2);
  const line = points.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.value)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Conversations per day">
      <defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#D9AE5B" stopOpacity="0.4" /><stop offset="1" stopColor="#D9AE5B" stopOpacity="0" /></linearGradient></defs>
      {[0.25, 0.5, 0.75, 1].map((g) => <line key={g} x1={pad} x2={W - pad} y1={y(max * g)} y2={y(max * g)} stroke="rgba(255,255,255,0.06)" />)}
      {points.length > 1 && <path d={`${line} L${x(points.length - 1)},${H - pad} L${x(0)},${H - pad} Z`} fill="url(#area)" />}
      <path d={line} fill="none" stroke="#D9AE5B" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
      {points.map((p, i) => (
        <g key={p.label}>
          <circle cx={x(i)} cy={y(p.value)} r={3.5} fill="#0B0910" stroke="#EBD3A0" strokeWidth={2} />
          <text x={x(i)} y={H - 4} textAnchor="middle" fontSize={10} fill="#A39DB0">{p.label.slice(5)}</text>
        </g>
      ))}
    </svg>
  );
}
