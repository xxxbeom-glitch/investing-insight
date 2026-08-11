import Link from "next/link";
import { apiGet } from "@/lib/api";

type Dashboard = {
  latest_run: null | {
    run_id: string;
    status: string;
    cutoff_at: string;
    quant_rule_version: string | null;
    llm_profile_version: string | null;
    code_commit_hash: string | null;
  };
  counts: Record<string, number>;
};

export default async function HomePage() {
  const health = await apiGet<Record<string, unknown>>("/health");
  const dash = await apiGet<Dashboard>("/v1/dashboard");
  const cfg = await apiGet<{ llm_profile_version?: string; llm_profiles?: unknown }>("/health/config");
  const c = dash.data?.counts ?? {};
  const latest = dash.data?.latest_run;

  return (
    <main>
      <h1>대시보드</h1>
      <p className="lead">최근 리서치 실행 · 건수 · API/설정 상태</p>
      <div className="stats">
        <div className="stat"><div className="k">유니버스</div><div className="v">{c.universe ?? "—"}</div></div>
        <div className="stat"><div className="k">적격 종목</div><div className="v">{c.eligible ?? "—"}</div></div>
        <div className="stat"><div className="k">숏리스트</div><div className="v">{c.shortlist ?? "—"}</div></div>
        <div className="stat"><div className="k">QA 실패</div><div className={`v ${c.research_qa_fail ? "bad" : "ok"}`}>{c.research_qa_fail ?? "—"}</div></div>
      </div>
      <div className="stats">
        <div className="stat"><div className="k">선정</div><div className="v">{c.selected ?? 0}</div></div>
        <div className="stat"><div className="k">관찰</div><div className="v">{c.watch ?? 0}</div></div>
        <div className="stat"><div className="k">기각</div><div className="v">{c.reject ?? 0}</div></div>
        <div className="stat"><div className="k">격리</div><div className="v">{c.quarantine ?? 0}</div></div>
      </div>
      <div className="grid">
        <div className="row">
          <div className="label">API 상태</div>
          <div className={health.ok ? "ok" : "bad"}>{health.ok ? "정상" : "실패"}</div>
        </div>
        <div className="row">
          <div className="label">최근 실행</div>
          <div>
            {latest ? (
              <>
                <Link href={`/runs/${latest.run_id}`}>{latest.run_id}</Link>
                <div className="mono">
                  {latest.status} · 기준시각 {latest.cutoff_at}
                  <br />
                  퀀트 {latest.quant_rule_version} · LLM {latest.llm_profile_version}
                  <br />
                  커밋 {latest.code_commit_hash ?? "—"}
                </div>
              </>
            ) : (
              <span className="muted">아직 실행 없음</span>
            )}
          </div>
        </div>
        <div className="row">
          <div className="label">LLM 프로필</div>
          <div className="mono">
            {cfg.ok ? cfg.data?.llm_profile_version : "설정 실패"}
            <pre>{JSON.stringify(cfg.data?.llm_profiles ?? {}, null, 2)}</pre>
          </div>
        </div>
      </div>
    </main>
  );
}
