import { AdminShell } from "@/components/dashboard/AdminShell";

export const metadata = { title: "AURA Admin | Aurelia Grand Hotel" };
export default function AdminLayout({ children }: { children: React.ReactNode }) { return <AdminShell>{children}</AdminShell>; }
