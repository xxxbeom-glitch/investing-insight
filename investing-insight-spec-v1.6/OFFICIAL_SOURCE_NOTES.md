# Official Source Notes — verified 2026-08-10

이 파일은 설계에 포함된 변동 가능 기술 사실을 구현 시 다시 확인하기 위한 메모다.

## OpenAI
- GPT-5.6 family: Sol / Terra / Luna
- Terra: intelligence/cost balance
- Luna: cost-sensitive high-volume
- Sol: frontier complex professional work
- GPT-5.6 supports reasoning.effort: none, low, medium, high, xhigh, max
- Responses API recommended for reasoning/tool workflows

Official docs:
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/docs/models/gpt-5.6-terra
- https://developers.openai.com/api/docs/models/gpt-5.6-sol
- https://developers.openai.com/api/docs/models/gpt-5.6-luna

## Supabase
- New projects should prefer publishable (`sb_publishable_...`) and secret (`sb_secret_...`) keys.
- Secret key is backend-only and bypasses RLS.

Official docs:
- https://supabase.com/docs/guides/getting-started/api-keys

## SEC EDGAR
- Automated requests should declare a User-Agent.
- Current fair-access max: 10 requests/second.

Official docs:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/developer-resources

Implementation must re-check official docs when each provider Layer begins.
