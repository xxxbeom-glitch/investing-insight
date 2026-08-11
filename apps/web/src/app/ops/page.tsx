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

function jobStatus(status: string) {
  if (status === "success") return "성공";
  if (status === "running") return "실행 중";
  if (status === "failed") return "실패";
  return status;
}

export default async function OpsPage() {
  const ops = await apiGet<OpsHealth>("/v1/ops/health");
  const d = ops.data;
  const jobs = d?.recent_jobs ?? [];

  return (
    <main>
      <h1>운영 상태</h1>
      <p className="lead">스케줄 작업 · 백업 준비 · 공급자 플래그 (비밀키 없음)</p>
      <div className="stats">
        <div className="stat">
          <div className="k">API</div>
          <div className={ops.ok ? "v ok" : "v bad"}>{ops.ok ? "정상" : "실패"}</div>
        </div>
        <div className="stat">
          <div className="k">백업</div>
          <div className={d?.backup_ready ? "v ok" : "v bad"}>
            {d?.backup_ready ? "준비됨" : "대기"}
          </div>
        </div>
        <div className="stat">
          <div className="k">시점복구(PITR)</div>
          <div className="v bad">{d?.pitr_available ? "켜짐" : "없음 (Free)"}</div>
        </div>
        <div className="stat">
          <div className="k">스케줄러</div>
          <div className="v bad">
            {d?.scheduler_enable_allowed ? "허용" : "차단"}
          </div>
        </div>
      </div>
      <div className="stats">
        <div className="stat">
          <div className="k">24시간 실패</div>
          <div className={`v ${(d?.failed_jobs_24h ?? 0) > 0 ? "bad" : "ok"}`}>
            {d?.failed_jobs_24h ?? "—"}
          </div>
        </div>
      </div>
      <div className="grid">
        <div className="row">
          <div className="label">공급자</div>
          <div className="mono">
            {d?.providers
              ? Object.entries(d.providers)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(" · ")
              : "—"}
          </div>
        </div>
      </div>
      <h2>최근 작업</h2>
      {jobs.length === 0 ? (
        <p className="lead">아직 운영 작업이 없습니다. 마이그레이션 0010 이후 CLI로 실행하세요.</p>
      ) : (
        <div className="grid">
          {jobs.map((j) => (
            <div className="row" key={j.job_id}>
              <div className="label">
                {j.job_type} · <span className="mono">{j.job_id.slice(0, 8)}</span>
              </div>
              <div>
                <span className={j.status === "success" ? "ok" : j.status === "running" ? "" : "bad"}>
                  {jobStatus(j.status)}
                </span>
                <div className="mono">
                  {j.stage}
                  {j.error_code ? ` · ${j.error_code}` : ""} · 재시도={j.retry_count}
                </div>
                <div className="mono">{j.started_at}</div>
              </div>
            </div>
          ))}
        </div>
      )}
      <p className="lead">
        <Link href="/">← 대시보드</Link>
      </p>
    </main>
  );
}
