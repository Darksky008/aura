import { Flame, Star } from "lucide-react";
import { Badge, VegMark } from "@/components/ui";
import type { Strings } from "@/lib/i18n";
import type { Dish } from "@/types";

const LEVEL = { none: 0, mild: 1, medium: 2, high: 3 } as const;

export function SpiceMeter({ level, label }: { level: Dish["spice_level"]; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-ivory-dim" title={label}>
      <span className="flex" aria-hidden>{[1, 2, 3].map((i) => <Flame key={i} className={i <= LEVEL[level] ? "h-3.5 w-3.5 fill-saffron text-saffron" : "h-3.5 w-3.5 text-white/20"} />)}</span>
      {label}
    </span>
  );
}

export function DietBadges({ dish, s }: { dish: Dish; s: Strings }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <VegMark value={dish.dietary.vegetarian ?? "unknown"} />
      {dish.dietary.vegan === "yes" && <Badge tone="jade">{s.vegan}</Badge>}
      {dish.dietary.gluten_free === "yes" && <Badge>{s.glutenFree}</Badge>}
      {dish.is_chef_special && <Badge tone="gold"><Star className="h-3 w-3 fill-current" />{s.chefSpecial}</Badge>}
      {!dish.is_available && <Badge tone="rose">{s.unavailable}</Badge>}
    </div>
  );
}
