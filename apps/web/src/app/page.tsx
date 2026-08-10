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
      <h1>Dashboard</h1>
      <p className="lead">Latest research run · counts · provider/config health</p>
      <div className="stats">
        <div className="stat"><div className="k">Universe</div><div className="v">{c.universe ?? "—"}</div></div>
        <div className="stat"><div className="k">Eligible</div><div className="v">{c.eligible ?? "—"}</div></div>
        <div className="stat"><div className="k">Shortlist</div><div className="v">{c.shortlist ?? "—"}</div></div>
        <div className="stat"><div className="k">QA FAIL</div><div className={`v ${c.research_qa_fail ? "bad" : "ok"}`}>{c.research_qa_fail ?? "—"}</div></div>
      </div>
      <div className="stats">
        <div className="stat"><div className="k">SELECTED</div><div className="v">{c.selected ?? 0}</div></div>
        <div className="stat"><div className="k">WATCH</div><div className="v">{c.watch ?? 0}</div></div>
        <div className="stat"><div className="k">REJECT</div><div className="v">{c.reject ?? 0}</div></div>
        <div className="stat"><div className="k">Quarantine</div><div className="v">{c.quarantine ?? 0}</div></div>
      </div>
      <div className="grid">
        <div className="row">
          <div className="label">API health</div>
          <div className={health.ok ? "ok" : "bad"}>{health.ok ? "PASS" : "FAIL"}</div>
        </div>
        <div className="row">
          <div className="label">Latest run</div>
          <div>
            {latest ? (
              <>
                <Link href={`/runs/${latest.run_id}`}>{latest.run_id}</Link>
                <div className="mono">
                  {latest.status} · cutoff {latest.cutoff_at}
                  <br />
                  quant {latest.quant_rule_version} · llm {latest.llm_profile_version}
                  <br />
                  commit {latest.code_commit_hash ?? "—"}
                </div>
              </>
            ) : (
              <span className="muted">no runs yet</span>
            )}
          </div>
        </div>
        <div className="row">
          <div className="label">LLM profiles</div>
          <div className="mono">
            {cfg.ok ? cfg.data?.llm_profile_version : "config FAIL"}
            <pre>{JSON.stringify(cfg.data?.llm_profiles ?? {}, null, 2)}</pre>
          </div>
        </div>
      </div>
    </main>
  );
}
