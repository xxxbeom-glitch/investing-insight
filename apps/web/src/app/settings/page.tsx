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
      <h1>Settings</h1>
      <p className="lead">Config versions · provider presence (no raw secrets)</p>
      {!res.ok && <p className="bad">{res.error}</p>}
      {leaked && <p className="bad">SECRET LEAK DETECTED IN RESPONSE</p>}
      <div className="grid">
        <div className="row">
          <div className="label">LLM profile</div>
          <div className="mono">{res.data?.llm_profile_version}
            <pre>{JSON.stringify(res.data?.llm_profiles, null, 2)}</pre>
          </div>
        </div>
        <div className="row">
          <div className="label">Providers set?</div>
          <div className="mono">{JSON.stringify(providers, null, 2)}</div>
        </div>
        <div className="row">
          <div className="label">Registry</div>
          <div className="mono"><pre>{JSON.stringify(res.data?.registry, null, 2)}</pre></div>
        </div>
      </div>
    </main>
  );
}
