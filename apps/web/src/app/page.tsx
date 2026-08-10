async function fetchHealth(path: string): Promise<{ ok: boolean; status: number; body: unknown }> {
  const base = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${base}${path}`, { cache: "no-store" });
    const body = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, body };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      body: { error: error instanceof Error ? error.message : "fetch failed" },
    };
  }
}

export default async function HomePage() {
  const health = await fetchHealth("/health");
  const db = await fetchHealth("/health/db");
  const config = await fetchHealth("/health/config");

  return (
    <main>
      <h1>investing-insight</h1>
      <p className="lead">L00 foundation health — PC local lab</p>
      <div className="grid">
        <div className="row">
          <div className="label">API /health</div>
          <div className={health.ok ? "ok" : "bad"}>
            {health.ok ? "PASS" : "FAIL"} ({health.status})
            <pre>{JSON.stringify(health.body, null, 2)}</pre>
          </div>
        </div>
        <div className="row">
          <div className="label">API /health/db</div>
          <div className={db.ok ? "ok" : "bad"}>
            {db.ok ? "PASS" : "FAIL"} ({db.status})
            <pre>{JSON.stringify(db.body, null, 2)}</pre>
          </div>
        </div>
        <div className="row">
          <div className="label">API /health/config</div>
          <div className={config.ok ? "ok" : "bad"}>
            {config.ok ? "PASS" : "FAIL"} ({config.status})
            <pre>{JSON.stringify(config.body, null, 2)}</pre>
          </div>
        </div>
      </div>
    </main>
  );
}
