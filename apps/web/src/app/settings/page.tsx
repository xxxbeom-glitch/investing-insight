import { apiGet } from "@/lib/api";

export default async function SettingsPage() {
  const res = await apiGet<{
    llm_profile_version: string;
    llm_profiles: unknown;
    registry: unknown;
    providers: Record<string, boolean>;
  }>("/v1/settings/summary");
  const providers = res.data?.providers ?? {};
  const leaked = JSON.stringify(res.data ?? {}).match(/sk-|eyJ|password|SECRET/i);
  return (
    <main>
      <h1>설정</h1>
      <p className="lead">설정 버전 · 공급자 존재 여부 (비밀키 원문 없음)</p>
      {!res.ok && <p className="bad">API 오류: {res.error}</p>}
      {leaked && <p className="bad">응답에 비밀값이 포함되어 있습니다</p>}
      <div className="grid">
        <div className="row">
          <div className="label">LLM 프로필</div>
          <div className="mono">{res.data?.llm_profile_version}
            <pre>{JSON.stringify(res.data?.llm_profiles, null, 2)}</pre>
          </div>
        </div>
        <div className="row">
          <div className="label">공급자 설정됨?</div>
          <div className="mono">{JSON.stringify(providers, null, 2)}</div>
        </div>
        <div className="row">
          <div className="label">레지스트리</div>
          <div className="mono"><pre>{JSON.stringify(res.data?.registry, null, 2)}</pre></div>
        </div>
      </div>
    </main>
  );
}
