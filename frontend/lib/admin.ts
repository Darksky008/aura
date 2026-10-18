"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, request } from "@/services/api";

const KEY = "aura-admin-key";
export const getAdminKey = () => (typeof window === "undefined" ? "" : sessionStorage.getItem(KEY) ?? "");
export const setAdminKey = (k: string) => sessionStorage.setItem(KEY, k);
export const clearAdminKey = () => sessionStorage.removeItem(KEY);

export function adminRequest<T>(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const key = getAdminKey();
  if (key) headers.set("X-Admin-Key", key);
  return request<T>(`/admin${path}`, { ...init, headers });
}
export const adminJson = <T,>(path: string, method: "POST" | "PUT" | "PATCH" | "DELETE", body?: unknown) =>
  adminRequest<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });

/** Fetch-on-mount with reload + error state. */
export function useAdminData<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const reload = useCallback(async () => {
    setLoading(true);
    try { setData(await adminRequest<T>(path)); setError(null); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Could not load."); }
    finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}
