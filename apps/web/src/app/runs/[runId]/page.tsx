import Link from "next/link";
import { apiGet } from "@/lib/api";

type Detail = {
  run: Record<string, string | null>;
  snapshot: null | Record<string, string>;
  llm_executions: Array<Record<string, string | null>>;
};

export default async function RunDetailPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const res = await apiGet<Detail>(`/v1/runs/${runId}`);
  if (!res.ok || !res.data) {
    return <main><h1>실행 상세</h1><p className="bad">{res.error ?? "찾을 수 없음"}</p></main>;
  }
  const { run, snapshot, llm_executions } = res.data;
  return (
    <main>
      <h1>실행 상세</h1>
      <p className="lead mono">{run.run_id}</p>
      <div className="grid">
        <div className="row"><div className="label">상태</div><div>{run.status}</div></div>
        <div className="row"><div className="label">기준시각</div><div className="mono">{run.cutoff_at}</div></div>
        <div className="row"><div className="label">버전</div>
          <div className="mono">
            유니버스 {run.universe_rule_version}<br />
            퀀트 {run.quant_rule_version}<br />
            LLM {run.llm_profile_version}<br />
            커밋 {run.code_commit_hash}
          </div>
        </div>
        <div className="row"><div className="label">스냅샷</div>
          <div className="mono">{snapshot ? JSON.stringify(snapshot, null, 2) : "없음"}</div>
        </div>
      </div>
      <p style={{ marginTop: 28 }}>
        <Link href={`/candidates?run_id=${runId}`}>후보 종목 보기 →</Link>
      </p>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>LLM 실행 기록</h2>
      <table className="table">
        <thead>
          <tr>
            <th>역할</th>
            <th>요청 모델</th>
            <th>실제 모델</th>
            <th>추론 강도</th>
            <th>상태</th>
            <th>입력 해시</th>
            <th>출력 해시</th>
          </tr>
        </thead>
        <tbody>
          {llm_executions.map((e) => (
            <tr key={e.execution_id ?? Math.random()}>
              <td>{e.agent_role}</td>
              <td className="mono">{e.requested_model}</td>
              <td className="mono">{e.resolved_model}</td>
              <td>{e.reasoning_effort}</td>
              <td className={e.status === "failed" ? "bad" : "ok"}>{e.status === "failed" ? "실패" : e.status === "success" ? "성공" : e.status}</td>
              <td className="mono">{(e.input_hash ?? "").slice(0, 10)}</td>
              <td className="mono">{(e.output_hash ?? "").slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
