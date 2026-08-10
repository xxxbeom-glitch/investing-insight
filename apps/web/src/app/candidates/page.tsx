import Link from "next/link";
import { apiGet } from "@/lib/api";

type Dash = { latest_run: null | { run_id: string } };
type Cands = {
  run_id: string;
  candidates: Array<{
    security_id: string;
    ticker: string;
    exchange: string;
    rank: number | null;
    total_score: number;
    research_qa: string | null;
    final_status: string | null;
  }>;
};

export default async function CandidatesPage({
  searchParams,
}: {
  searchParams: Promise<{ run_id?: string }>;
}) {
  const sp = await searchParams;
  const dash = await apiGet<Dash>("/v1/dashboard");
  const runId = sp.run_id ?? dash.data?.latest_run?.run_id;
  if (!runId) {
    return <main><h1>Candidates</h1><p className="lead">No research run yet.</p></main>;
  }
  const res = await apiGet<Cands>(`/v1/runs/${runId}/candidates`);
  const rows = res.data?.candidates ?? [];
  return (
    <main>
      <h1>Candidates</h1>
      <p className="lead">
        Run <Link href={`/runs/${runId}`}>{runId.slice(0, 8)}…</Link> · quant rank shortlist
      </p>
      {!res.ok && <p className="bad">{res.error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>rank</th>
            <th>ticker</th>
            <th>exchange</th>
            <th>score</th>
            <th>research QA</th>
            <th>final</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.security_id}>
              <td>{r.rank}</td>
              <td>
                <Link href={`/companies/${r.security_id}?run_id=${runId}`}>{r.ticker}</Link>
              </td>
              <td>{r.exchange}</td>
              <td>{r.total_score.toFixed(1)}</td>
              <td className={r.research_qa === "FAIL" ? "bad" : undefined}>{r.research_qa ?? "—"}</td>
              <td>{r.final_status ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
