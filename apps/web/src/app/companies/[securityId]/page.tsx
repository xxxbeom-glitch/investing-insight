import Link from "next/link";
import { apiGet } from "@/lib/api";

type Company = {
  identity: { ticker: string; exchange: string; name: string | null; security_id: string };
  run_id: string;
  quant: null | { total_score: number; components: Record<string, number>; rank_market: number; rule_version: string; input_hash: string };
  judgment: null | Record<string, unknown>;
  research: null | { qa_status: string | null; failed_claims: unknown; output: unknown };
  packet: null | { evidence: unknown; input_hash: string; price_metrics: unknown; financial_trends: unknown };
};

export default async function CompanyPage({
  params,
  searchParams,
}: {
  params: Promise<{ securityId: string }>;
  searchParams: Promise<{ run_id?: string }>;
}) {
  const { securityId } = await params;
  const { run_id } = await searchParams;
  if (!run_id) {
    return <main><h1>Company</h1><p className="bad">run_id query required</p></main>;
  }
  const res = await apiGet<Company>(`/v1/companies/${securityId}?run_id=${run_id}`);
  if (!res.ok || !res.data) {
    return <main><h1>Company</h1><p className="bad">{res.error}</p></main>;
  }
  const d = res.data;
  const qaFail = d.research?.qa_status === "FAIL";
  return (
    <main>
      <h1>
        {d.identity.ticker} <span style={{ color: "var(--muted)", fontSize: "1rem" }}>{d.identity.exchange}</span>
      </h1>
      <p className="lead">
        {d.identity.name ?? "—"} · <Link href={`/runs/${d.run_id}`}>run</Link>
        {qaFail && <span className="bad"> · Research QA FAIL</span>}
      </p>
      <div className="grid">
        <div className="row">
          <div className="label">Quant</div>
          <div className="mono">{d.quant ? JSON.stringify(d.quant, null, 2) : "—"}</div>
        </div>
        <div className="row">
          <div className="label">Judgment</div>
          <div className="mono">{d.judgment ? JSON.stringify(d.judgment, null, 2) : "—"}</div>
        </div>
        <div className="row">
          <div className="label">AI Research / QA</div>
          <div className="mono">{d.research ? JSON.stringify(d.research, null, 2) : "—"}</div>
        </div>
        <div className="row">
          <div className="label">Evidence / packet</div>
          <div className="mono">
            hash {d.packet?.input_hash ?? "—"}
            <pre>{JSON.stringify(d.packet?.evidence ?? [], null, 2)}</pre>
          </div>
        </div>
      </div>
    </main>
  );
}
