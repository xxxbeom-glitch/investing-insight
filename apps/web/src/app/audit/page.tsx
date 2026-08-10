import { apiGet } from "@/lib/api";

export default async function AuditPage() {
  const res = await apiGet<{
    research_qa: Record<string, number>;
    llm_executions: Array<{ agent_role: string; status: string; count: number }>;
    quarantine: number;
    recent_checks: Array<{ check_name: string; status: string }>;
  }>("/v1/audit/summary");
  return (
    <main>
      <h1>Audit & QA</h1>
      <p className="lead">Research QA · LLM execution · quarantine · data checks</p>
      {!res.ok && <p className="bad">{res.error}</p>}
      <div className="grid">
        <div className="row">
          <div className="label">Research QA</div>
          <div className="mono">{JSON.stringify(res.data?.research_qa ?? {}, null, 2)}</div>
        </div>
        <div className="row">
          <div className="label">Quarantine</div>
          <div>{res.data?.quarantine ?? "—"}</div>
        </div>
      </div>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>LLM executions</h2>
      <table className="table">
        <thead><tr><th>role</th><th>status</th><th>count</th></tr></thead>
        <tbody>
          {(res.data?.llm_executions ?? []).map((e, i) => (
            <tr key={`${e.agent_role}-${e.status}-${i}`}>
              <td>{e.agent_role}</td>
              <td className={e.status === "failed" ? "bad" : "ok"}>{e.status}</td>
              <td>{e.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>Recent data checks</h2>
      <table className="table">
        <thead><tr><th>check</th><th>status</th></tr></thead>
        <tbody>
          {(res.data?.recent_checks ?? []).map((c, i) => (
            <tr key={`${c.check_name}-${i}`}>
              <td>{c.check_name}</td>
              <td className={c.status === "FAIL" ? "bad" : "ok"}>{c.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
