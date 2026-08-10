import Link from "next/link";
import { apiGet } from "@/lib/api";

type Runs = {
  runs: Array<{
    run_id: string;
    status: string;
    cutoff_at: string;
    quant_rule_version: string | null;
    prompt_bundle_version: string | null;
    llm_profile_version: string | null;
    code_commit_hash: string | null;
    candidates: number;
    selected: number;
  }>;
};

export default async function RunsPage() {
  const res = await apiGet<Runs>("/v1/runs");
  const runs = res.data?.runs ?? [];
  return (
    <main>
      <h1>Research Runs</h1>
      <p className="lead">Cutoff · status · versions · candidate/selected counts</p>
      {!res.ok && <p className="bad">API FAIL: {res.error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>run_id</th>
            <th>status</th>
            <th>cutoff</th>
            <th>quant</th>
            <th>llm</th>
            <th>candidates</th>
            <th>selected</th>
            <th>commit</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.run_id}>
              <td className="mono"><Link href={`/runs/${r.run_id}`}>{r.run_id.slice(0, 8)}…</Link></td>
              <td>{r.status}</td>
              <td className="mono">{r.cutoff_at}</td>
              <td>{r.quant_rule_version}</td>
              <td>{r.llm_profile_version}</td>
              <td>{r.candidates}</td>
              <td>{r.selected}</td>
              <td className="mono">{r.code_commit_hash ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
