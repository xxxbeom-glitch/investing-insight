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
    return <main><h1>Run</h1><p className="bad">{res.error ?? "not found"}</p></main>;
  }
  const { run, snapshot, llm_executions } = res.data;
  return (
    <main>
      <h1>Run detail</h1>
      <p className="lead mono">{run.run_id}</p>
      <div className="grid">
        <div className="row"><div className="label">status</div><div>{run.status}</div></div>
        <div className="row"><div className="label">cutoff</div><div className="mono">{run.cutoff_at}</div></div>
        <div className="row"><div className="label">versions</div>
          <div className="mono">
            universe {run.universe_rule_version}<br />
            quant {run.quant_rule_version}<br />
            llm {run.llm_profile_version}<br />
            commit {run.code_commit_hash}
          </div>
        </div>
        <div className="row"><div className="label">snapshot</div>
          <div className="mono">{snapshot ? JSON.stringify(snapshot, null, 2) : "none"}</div>
        </div>
      </div>
      <p style={{ marginTop: 28 }}>
        <Link href={`/candidates?run_id=${runId}`}>View candidates →</Link>
      </p>
      <h2 style={{ marginTop: 28, fontSize: "1.1rem" }}>LLM executions</h2>
      <table className="table">
        <thead>
          <tr>
            <th>role</th>
            <th>requested</th>
            <th>resolved</th>
            <th>effort</th>
            <th>status</th>
            <th>input_hash</th>
            <th>output_hash</th>
          </tr>
        </thead>
        <tbody>
          {llm_executions.map((e) => (
            <tr key={e.execution_id ?? Math.random()}>
              <td>{e.agent_role}</td>
              <td className="mono">{e.requested_model}</td>
              <td className="mono">{e.resolved_model}</td>
              <td>{e.reasoning_effort}</td>
              <td className={e.status === "failed" ? "bad" : "ok"}>{e.status}</td>
              <td className="mono">{(e.input_hash ?? "").slice(0, 10)}</td>
              <td className="mono">{(e.output_hash ?? "").slice(0, 10)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
