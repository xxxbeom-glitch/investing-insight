# config/

비-secret · Git versioned 실험 설정. Secret은 `.env.local`만.

| 파일 | 역할 |
|------|------|
| `llm_profiles.v0.1.yaml` | 역할별 model / reasoning.effort |
| `quant_rules.v0.1.yaml` | Quant 규칙 (L0x에서 채움) |
| `research_limits.v0.1.yaml` | 리서치 한도 |
| `provider_policy.v0.1.yaml` | SEC rate 등 |

변경 시 version bump + 관련 Layer QA 재실행.
