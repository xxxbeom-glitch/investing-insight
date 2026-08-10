const API_BASE = (process.env.API_BASE_URL ?? "http://127.0.0.1:8000").trim().replace(/\/$/, "");

export async function apiGet<T>(path: string): Promise<{ ok: boolean; status: number; data: T | null; error?: string }> {
  try {
    const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
    const data = (await res.json().catch(() => null)) as T | null;
    return { ok: res.ok, status: res.status, data, error: res.ok ? undefined : JSON.stringify(data) };
  } catch (e) {
    return { ok: false, status: 0, data: null, error: e instanceof Error ? e.message : "fetch failed" };
  }
}
