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
      <h1>감사·QA</h1>
      <p className="lead">리서치 QA · LLM 실행 · 격리 · 데이터 점검</p>
      {!res.ok && <p className="bad">API 오류: {res.error}</p>}
      <div className="grid">
        <div className="row">
          <div className="label">리서치 QA</div>
          <div className="mono">{JSON.stringify(res.data?.research_qa ?? {}, null, 2)}</div>
        </div>
        <div className="row">
          <div className="label">격리</div>
          <div>{res.data?.quarantine ?? "—"}</div>
        </div>
      </div>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>LLM 실행 기록</h2>
      <table className="table">
        <thead><tr><th>역할</th><th>상태</th><th>건수</th></tr></thead>
        <tbody>
          {(res.data?.llm_executions ?? []).map((e, i) => (
            <tr key={`${e.agent_role}-${e.status}-${i}`}>
              <td>{e.agent_role}</td>
              <td className={e.status === "failed" ? "bad" : "ok"}>
                {e.status === "failed" ? "실패" : e.status === "success" ? "성공" : e.status}
              </td>
              <td>{e.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>최근 데이터 점검</h2>
      <table className="table">
        <thead><tr><th>점검</th><th>상태</th></tr></thead>
        <tbody>
          {(res.data?.recent_checks ?? []).map((c, i) => (
            <tr key={`${c.check_name}-${i}`}>
              <td>{c.check_name}</td>
              <td className={c.status === "FAIL" ? "bad" : "ok"}>
                {c.status === "FAIL" ? "실패" : c.status === "PASS" ? "통과" : c.status}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
