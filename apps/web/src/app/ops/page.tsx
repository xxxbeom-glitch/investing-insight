import Link from "next/link";
import { apiGet } from "@/lib/api";

type OpsHealth = {
  status?: string;
  pitr_available?: boolean;
  pitr_confirmed?: boolean;
  backup_ready?: boolean;
  scheduler_enable_allowed?: boolean;
  failed_jobs_24h?: number;
  recent_jobs?: Array<{
    job_id: string;
    job_type: string;
    stage: string;
    status: string;
    error_code: string | null;
    retry_count: number;
    started_at: string;
    finished_at: string | null;
  }>;
  providers?: Record<string, boolean>;
};

export default async function OpsPage() {
  const ops = await apiGet<OpsHealth>("/v1/ops/health");
  const d = ops.data;
  const jobs = d?.recent_jobs ?? [];

  return (
    <main>
      <h1>Ops Health</h1>
      <p className="lead">Scheduler jobs · Free-plan backup readiness · provider flags (no secrets)</p>
      <div className="stats">
        <div className="stat">
          <div className="k">API</div>
          <div className={ops.ok ? "v ok" : "v bad"}>{ops.ok ? "PASS" : "FAIL"}</div>
        </div>
        <div className="stat">
          <div className="k">Backup</div>
          <div className={d?.backup_ready ? "v ok" : "v bad"}>
            {d?.backup_ready ? "READY" : "PENDING"}
          </div>
        </div>
        <div className="stat">
          <div className="k">PITR</div>
          <div className="v bad">{d?.pitr_available ? "ON" : "N/A (Free)"}</div>
        </div>
        <div className="stat">
          <div className="k">Schedulers</div>
          <div className="v bad">
            {d?.scheduler_enable_allowed ? "ALLOWED" : "BLOCKED"}
          </div>
        </div>
      </div>
      <div className="stats">
        <div className="stat">
          <div className="k">Failed 24h</div>
          <div className={`v ${(d?.failed_jobs_24h ?? 0) > 0 ? "bad" : "ok"}`}>
            {d?.failed_jobs_24h ?? "—"}
          </div>
        </div>
      </div>
      <div className="grid">
        <div className="row">
          <div className="label">Providers</div>
          <div className="mono">
            {d?.providers
              ? Object.entries(d.providers)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(" · ")
              : "—"}
          </div>
        </div>
      </div>
      <h2>Recent jobs</h2>
      {jobs.length === 0 ? (
        <p className="lead">No ops_jobs yet. Run daily/biweekly CLIs after migration 0010.</p>
      ) : (
        <div className="grid">
          {jobs.map((j) => (
            <div className="row" key={j.job_id}>
              <div className="label">
                {j.job_type} · <span className="mono">{j.job_id.slice(0, 8)}</span>
              </div>
              <div>
                <span className={j.status === "success" ? "ok" : j.status === "running" ? "" : "bad"}>
                  {j.status}
                </span>
                <div className="mono">
                  {j.stage}
                  {j.error_code ? ` · ${j.error_code}` : ""} · retry={j.retry_count}
                </div>
                <div className="mono">{j.started_at}</div>
              </div>
            </div>
          ))}
        </div>
      )}
      <p className="lead">
        <Link href="/">← Dashboard</Link>
      </p>
    </main>
  );
}
