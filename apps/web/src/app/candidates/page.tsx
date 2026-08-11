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

function finalLabel(status: string | null) {
  if (status === "SELECTED") return "선정";
  if (status === "WATCH") return "관찰";
  if (status === "REJECT") return "기각";
  return status ?? "—";
}

export default async function CandidatesPage({
  searchParams,
}: {
  searchParams: Promise<{ run_id?: string }>;
}) {
  const sp = await searchParams;
  const dash = await apiGet<Dash>("/v1/dashboard");
  const runId = sp.run_id ?? dash.data?.latest_run?.run_id;
  if (!runId) {
    return <main><h1>후보 종목</h1><p className="lead">아직 리서치 실행이 없습니다.</p></main>;
  }
  const res = await apiGet<Cands>(`/v1/runs/${runId}/candidates`);
  const rows = res.data?.candidates ?? [];
  return (
    <main>
      <h1>후보 종목</h1>
      <p className="lead">
        실행 <Link href={`/runs/${runId}`}>{runId.slice(0, 8)}…</Link> · 퀀트 순위 숏리스트
      </p>
      {!res.ok && <p className="bad">{res.error}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>순위</th>
            <th>티커</th>
            <th>거래소</th>
            <th>점수</th>
            <th>리서치 QA</th>
            <th>최종</th>
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
              <td className={r.research_qa === "FAIL" ? "bad" : undefined}>
                {r.research_qa === "FAIL" ? "실패" : r.research_qa === "PASS" ? "통과" : r.research_qa ?? "—"}
              </td>
              <td>{finalLabel(r.final_status)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
