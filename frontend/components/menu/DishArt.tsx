/** Local, offline "plate" artwork - no remote images that can disappear. Colour is derived from the dish slug. */
const PALETTES: [string, string][] = [["#E8843F", "#7A2E12"], ["#D9AE5B", "#6B4A12"], ["#C4552D", "#4A1A0C"], ["#5FC7A1", "#10463A"], ["#E5A1A6", "#5A2230"], ["#B8873E", "#3E2A0E"]];

export function DishArt({ slug, name, className }: { slug: string; name: string; className?: string }) {
  let h = 0;
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const [a, b] = PALETTES[h % PALETTES.length];
  const dots = Array.from({ length: 9 }, (_, i) => ({ x: 100 + 54 * Math.cos((i / 9) * Math.PI * 2 + (h % 7)), y: 100 + 54 * Math.sin((i / 9) * Math.PI * 2 + (h % 7)), r: 3 + ((h >> i) % 4) }));
  return (
    <svg viewBox="0 0 200 200" className={className} role="img" aria-label={name}>
      <defs>
        <radialGradient id={`pl-${slug}`} cx="40%" cy="35%"><stop offset="0" stopColor={a} /><stop offset="1" stopColor={b} /></radialGradient>
        <radialGradient id={`rim-${slug}`} cx="50%" cy="50%"><stop offset="0.82" stopColor="#FBF9F5" stopOpacity="0.95" /><stop offset="1" stopColor="#CFC8BA" /></radialGradient>
      </defs>
      <circle cx="100" cy="104" r="86" fill="rgba(0,0,0,0.35)" />
      <circle cx="100" cy="100" r="86" fill={`url(#rim-${slug})`} />
      <circle cx="100" cy="100" r="68" fill={`url(#pl-${slug})`} />
      <circle cx="100" cy="100" r="68" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="1.5" />
      {dots.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r={d.r} fill="#FBF9F5" opacity={0.55} />)}
      <text x="100" y="116" textAnchor="middle" fontSize="48" fontFamily="Georgia, serif" fill="#FBF9F5" opacity="0.92">{name.trim().charAt(0)}</text>
    </svg>
  );
}
