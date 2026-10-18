import { Suspense } from "react";
import { ConciergeScreen } from "@/components/ConciergeScreen";

export default function Home() {
  return <Suspense fallback={null}><ConciergeScreen /></Suspense>;
}
