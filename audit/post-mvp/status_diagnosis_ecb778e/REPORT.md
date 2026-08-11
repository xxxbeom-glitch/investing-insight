# Dual Diagnosis Report — investing-insight Post-MVP

| 항목 | 값 |
|------|-----|
| as_of | 2026-08-11 (UTC 14:30–14:45 수집) |
| branch | `post-mvp/phase-1` |
| HEAD (진단 대상) | `ecb778e98d8f168b20594324e5b4bcf1ca819c42` |
| 본 보고서 commit | `063077c` |
| 1차 | 구현 에이전트 (facts + live API) |
| 2차 | `research_qa_agent` · `gpt-5.6-terra` · `reasoning.effort=high` |
| 2차 response_id | `resp_09224397166453b1006a7b322208a481989fd82582f27a1007` |
| 2차 tokens | in 1457 / out 2768 (reasoning 913) / total 4225 |
| 제품 GO | **하지 않음** |
| cron | **DISABLED** (`scheduler_enable_allowed=false`) |
| Post-MVP tag | **없음** |

원본: `facts.json` · `live_snapshot.json` · `llm_qa.json`

---

## 0. 한 줄 결론 (교차)

**LAB_ONLY_OK / NO-GO.**  
MVP L00–L10과 Post-MVP G00–M06 코드는 PASS다. 로컬 PC Web은 켜서 볼 수 있다. 그러나 상시 제품(seal · scheduler · hosted)은 닫히지 않았고, 화면에 보이는 AAPL 1건은 Research QA FAIL → REJECT다. 자체 grounding QA PASS ≠ 제품 GO.

1차와 2차는 이 결론에 **사실 불일치가 없다.** 차이는 분류 체계뿐이다(§6).

---

## 1. 무엇이 “완성된 제품”인가

설계서 기준, 사용자가 브라우저로 보는 **완성 제품**까지는 세 스위치가 남는다.

| # | 게이트 | 현재 | 근거 |
|---|--------|------|------|
| 1 | Post-MVP seal (GO + tag) | 안 함 | tag는 `mvp-v0.1-pass` @ `e98ff33`, `mvp-v0.1-review-pass` @ `c1a6692`만. Post-MVP tag null. `go_declared=false` |
| 2 | daily / biweekly scheduler enable | 차단 | cron DISABLED. G00-P2-01: PITR 전에 scheduler 금지. `pitr_available=false` |
| 3 | hosted PC Web | 로컬만 | `localhost:3000` + `127.0.0.1:8000` |

범위 밖: Long-Term Optional (매매·브로커·타이밍). 이번 진단에서도 **시작하지 않음**.

G00 HANDOFF는 원래 M01에 hosted + scheduler를 넣었지만, M01 PASS(`61107c3`)는 **schedulers DISABLED**로 닫혔다. hosted는 이후 마일스톤에서도 live가 아니다. 즉 “M01 PASS”는 패키징·잡 골격 PASS이지 상시 운영 PASS가 아니다.

---

## 2. 1차 진단 (구현 에이전트)

### 2.1 제품 완성도

| 축 | 상태 | 해석 |
|----|------|------|
| MVP Layers L00–L10 | PASS | 로컬 연구 콘솔의 기반 |
| Post-MVP G00 | PASS (review gate) | Free 플랜 PITR 없음. 가짜 CONFIRMED 안 함 |
| M01 | PASS | deploy packaging + jobs. scheduler는 의도적 비활성 |
| M02 | PASS | top-down/FRED. web page deferred P3 |
| M03 | PASS (audit) + live 재실행 | 8-role. SELECTED+empty invalidation이면 `GateBlockedError` (fail-closed) |
| M04 | 코드 PASS | lab eval 다수 INCOMPLETE (horizon 미경과, SPY/QQQ history P2) |
| M05 | PASS | 수동 error DB. auto-class P2 |
| M06 | PASS | replay/holdout 8-role, freeze 기록 |
| P1-01 grounding self-QA | exit 0 | replay 160/160, Red-Team 20/20, FP=0. **pass ≠ GO** |
| UI | 한글 라벨 (`071e9ff`) | JSON payload는 영어 |
| 로컬 데모 리서치 | 1회 성공 실행 | 결과물은 QA FAIL / REJECT |

Layer audit 관점 **open P0/P1 = 0**. 열려 있는 것은 P2 backlog와 **아직 켜지 않은 릴리스 게이트**.

### 2.2 자체 QA가 막아 온 것 (P1-01 이력)

외부 rereview가 반복해서 뚫은 구멍 → 코드 fail-closed로 막음. 사용자는 이후 외부 리뷰를 중단하고 자체 QA를 게이트로 둠.

| 커밋 | 내용 |
|------|------|
| `1a82cea` | control/Cf, 잘못된 as_of copula bind |
| `28b1890` | copula 목적어만 bind |
| `08d184d` | equality-only, `!=` `>` `<` 등 fail-closed |
| `3199db3` | value-copula-value 교차쌍 fail-closed |
| `d2fe744` | structural_attacks를 payload에서 **매 런 생성** (LLM luck 제거) |

현재 self-QA: `self_remediate` exit 0. Judge 호출 0 (replay-only 구조 공격이 커버). 이것은 **M03 `claim_support.py` 경로**의 보증이다.

### 2.3 두 개의 grounding 구현 (GO blocker)

| 경로 | 파일 | 하는 일 | 쓰이는 곳 |
|------|------|---------|-----------|
| M03 / 멀티에이전트 | `apps/api/app/agents/claim_support.py` | field / operator(equals만) / value triple. 비지원 연산자·control·value-copula fail-closed | 자체 QA 160 seeds, M03 gate |
| L08 / 바이위클리 | `apps/api/app/research/claim_check.py` | packet evidence+quant에서 숫자 bag을 만들고, claim 숫자가 bag에 없으면 `numeric_not_in_packet_evidence` | 로컬 데모 AAPL |

동등성 테스트 없음. 한쪽 PASS가 다른 쪽 보호를 증명하지 않는다.

### 2.4 로컬 데모 — 화면에 보이는 실제 결과

| 항목 | 값 |
|------|-----|
| script | `run_biweekly_research.py --limit 5` (priced security 1건만 반환) |
| job | `e5f98040-49e5-442e-aa9d-8a936cb01678` success |
| run | `31835b24-8823-4306-be7a-c48b43a4b66d` |
| ticker | AAPL / XNAS · Apple Inc. |
| security_id | `2c3f9b93-d40c-5266-b54b-3fb355525f64` |
| quant | 88.77 (growth/quality/cashflow/momentum 100, health 28.05, valuation 97.07) |
| research_qa | **FAIL** |
| judgment | **REJECT** |
| warning | `research_declared_unsupported_or_missing` |
| dashboard counts | universe 8804 · eligible 8724 · shortlist 1 · selected 0 · watch 0 · reject 1 · qa_fail 1 |
| run.llm_profile_version | `llm-profile-v0.1` (M03 프로파일은 v0.2) |
| run.code_commit_hash | `m01-biweekly` (git HEAD가 아님) |

화면: http://localhost:3000/candidates  
상세: http://localhost:3000/companies/2c3f9b93-d40c-5266-b54b-3fb355525f64?run_id=31835b24-8823-4306-be7a-c48b43a4b66d

Thesis (judgment):  
> Reject: the packet is not eligible for selection because Research QA status is FAIL. The evidence set is insufficiently reliable for an investable conclusion.

Fail-closed는 정상이다. 다만 **운영자가 볼 수 있는 PASS-QA 종목 예시가 아직 없다.**

### 2.5 FAIL 6건의 메커니즘 (라이브 재조회)

`claim_evidence_map`에는 evidence_id가 있다. 그런데 `claim_check`는 **숫자 문자열 bag**만 본다. LLM은 “$383.266 **billion**”처럼 단위 변환된 숫자를 썼고, packet 쪽 raw 값(보통 원단위)과 `_norm("383.266")`이 불일치한다.

| # | claim (요약) | 추출 숫자 | reason |
|---|--------------|-----------|--------|
| 1 | Assets were $383.266 billion at 2026-06-27 | 383.266 | `numeric_not_in_packet_evidence` |
| 2 | Stockholders' equity was $107.520 billion at 2026-06-27 | 107.520 | 동일 |
| 3 | Reported NetIncomeLoss was $101.464 billion at 2026-06-27 | 101.464 | 동일 |
| 4 | Assets were $359.241 billion at 2025-09-27 | 359.241 | 동일 |
| 5 | Stockholders' equity was $73.733 billion at 2025-09-27 | 73.733 | 동일 |
| 6 | Reported NetIncomeLoss was $112.010 billion at 2025-09-27 | 112.010 | 동일 |

같은 map의 **가격 claim** (`$294.38`, `$315.32` 등)은 통과한 것으로 보인다 — packet close와 단위가 같기 때문.

즉 이 FAIL은 “날조된 숫자”라기보다 **billion 스케일 vs raw 스케일**. 게이트를 느슨히 하면 안 된다. 고치려면 packet 표기·claim 생성·checker 중 하나를 **단위를 포함해** 맞추고, 회귀 테스트를 넣어야 한다.

### 2.6 운영 헬스

| 항목 | 값 |
|------|-----|
| API / DB | ok |
| backup_ready | true (G00 dump/restore 증거) |
| pitr_available | **false** (코드가 항상 false를 반환 + Free 플랜) |
| scheduler_enable_allowed | **false** |
| providers set | supabase_db, openai, massive, sec_ua, fred (키 값은 기록하지 않음) |
| failed_jobs_24h | 13 |

최근 20건 중 실패 3건은 모두 `multi_agent` / `error_code=GateBlockedError`. 성공 건도 다수 있다. 24h 카운트 13의 **전체 원인 목록은 20건 윈도우 밖**이라 전부 확정하지 못한다.

해석: 숫자 13을 “장애 폭주”로 단정하지 않되, “전부 양성”이라고도 하지 않는다. 확인된 샘플은 fail-closed 게이트 차단이다.

### 2.7 1차가 본 GO 차단 목록

1. Post-MVP tag / GO 없음 (설계상 아직)
2. cron disabled + PITR 없음
3. hosted URL 없음
4. biweekly 경로가 AAPL에서 QA FAIL (단위 불일치)
5. `claim_support` vs `claim_check` 동등성 미입증
6. self-QA PASS를 제품 GO로 바꾸면 안 됨

---

## 3. 2차 진단 (연결된 LLM QA)

호출 계약: facts-only, structured schema, silent fallback 없음. resolved model = 요청 모델.

### 3.1 판정

| 필드 | 2차 값 |
|------|--------|
| verdict | `LAB_ONLY_OK` |
| go_recommendation | `NO-GO` |
| confidence | `high` |
| severity_counts | P0=0 · **P1=4** · P2=5 · P3=1 |

2차 요약(원문 `summary_ko`):

> 판정: LAB_ONLY_OK, 권고: NO-GO. MVP 및 일부 Post-MVP 마일스톤 PASS는 로컬/통제된 실험 사용을 뒷받침하지만, Post-MVP GO·태그가 없고 호스팅은 localhost뿐이며 cron은 비활성화·허용 금지 상태입니다. 또한 AAPL 바이위클리 실행은 6개 숫자 근거 불일치로 QA FAIL/REJECT였고, M03와 L08의 근거 검증 구현도 서로 달라 동등성이 입증되지 않았습니다. PITR 부재와 최근 실패 작업 13건의 미분석도 남아 있습니다. 따라서 태그·GO·cron·공개 배포는 진행하지 말고, 먼저 근거 검증 경로 정합성, PASS-QA 실행 증거, 복구/운영 및 배포 증거를 닫아야 합니다.

### 3.2 2차 findings

**P1 (2차가 GO blocker로 올린 것)**

| ID | 제목 | 함의 |
|----|------|------|
| RQA-P1-01 | Post-MVP release authorization is not closed | tag/GO 없이 제품 출시 선언 근거 없음 |
| RQA-P1-02 | Production serving and scheduled operation are not authorized | localhost + cron DISABLED = lab only |
| RQA-P1-03 | Biweekly research path has a current failed end-to-end example | fail-closed는 긍정. 그러나 운영 가능 PASS-QA 예시 없음 |
| RQA-P1-04 | Two grounding implementations lack demonstrated equivalence | 한쪽 self-QA가 다른 쪽을 보증하지 않음 |

**P2**

| ID | 제목 |
|----|------|
| RQA-P2-01 | PITR unavailable — scheduler 전제 미충족. backup_ready ≠ PITR |
| RQA-P2-02 | failed_jobs_24h=13 원인/임계값 증거 없음 |
| RQA-P2-03 | M04 lab eval 일부 INCOMPLETE |
| RQA-P2-04 | Docker image CI 증거 없음. hosting local |
| RQA-P2-05 | industry map / batch load / auto-class 등 알려진 능력 공백 |

**P3**

| ID | 제목 |
|----|------|
| RQA-P3-01 | UI 한글 vs JSON 영어 |

### 3.3 2차가 1차에 동의한 점

- 제품 미완성, GO 불가
- lab/local only
- seal / scheduler / hosted 미닫힘
- AAPL은 fail-closed REJECT이지 자격 있는 PASS가 아님
- 두 grounding 경로 정렬 필요
- self-QA PASS ≠ product GO

### 3.4 2차가 1차와 “다른” 점 (2차 원문)

> No material factual disagreement. For independent readiness accounting, the unclosed release/operation gates and the currently failed demonstrated biweekly run are classified as P1 GO blockers even though the supplied open_p0_p1 list is empty.

> The 13 failed jobs in 24 hours cannot be characterized as benign, transient, or product-breaking from the supplied facts; only missing triage evidence is established.

### 3.5 2차 next_actions (축약)

1. lab-only 유지, NO-GO 유지. MVP tag를 제품 승인으로 포장하지 말 것.
2. AAPL 6건을 packet→claim→claim_check까지 추적. fail-closed 유지. 우회로 PASS 만들지 말 것.
3. `claim_support.py`와 `claim_check.py` 정합 또는 범위 문서화 + 교차 회귀.
4. scheduler 전에 PITR + 실패 잡 트리아지.
5. Docker CI·hosted는 **별도** 배포 증거. localhost를 live proof로 쓰지 말 것.

---

## 4. 교차검증 (1차가 2차를 재심사)

### 4.1 사실 검증 — 통과

2차 모델이 facts 밖의 메트릭을 만들지 않았다. 인용한 run_id / job_id / 6 claims / PITR / cron / tag 부재는 1차·라이브와 일치한다.

### 4.2 Taxonomy 차이 — 혼동 금지

| 체계 | P0/P1 의미 | 이 스냅샷 |
|------|------------|-----------|
| Layer audit (`25-layer-audit`) | 완료된 Layer의 **결함**. 미착수 게이트는 P2 또는 “아직 안 함” | open P0/P1 = 0 |
| 2차 독립 readiness | **출시에 막히는 조건**이면 P1 | P1 = 4 |

둘 다 맞다. 합치면:

- **지금 다음 Layer/코드를 막는 P0 장애는 없다** (audit 의미).
- **지금 제품 GO를 막는 조건은 있다** (readiness 의미). 2차가 그걸 P1로 부른 것.

이 보고서의 운영 권고는 2차와 같이 **NO-GO**다. audit 문서의 `open_p0_p1: []`를 “출시 가능”으로 읽으면 안 된다.

### 4.3 2차 이후 1차가 보강한 사실

2차 호출 시점의 `facts.json`에는 6 claim 원문과 실패 job 원인이 없었다. 라이브 재조회로 보강:

1. **단위 불일치**가 AAPL FAIL의 직접 원인 후보다 (billion vs raw). evidence_id는 map에 존재.
2. 최근 실패 샘플 3/20 = `GateBlockedError` (M03 fail-closed). 13건 전부라고 단정하지 않음 → 2차 RQA-P2-02는 **부분 해소, 완전 해소 아님**.
3. biweekly run이 `llm-profile-v0.1` / `code_commit_hash=m01-biweekly`를 심음 → 관측 가능성 P2 (2차는 이 항목을 못 봄; facts에 없었음).

### 4.4 1차가 2차 severity에 동의하는가

| 2차 ID | 1차 동의 | 메모 |
|--------|----------|------|
| RQA-P1-01 | 동의 (readiness P1) | audit P0/P1 리스트에는 안 넣음. 미선언 게이트 |
| RQA-P1-02 | 동의 (readiness P1) | 동일 |
| RQA-P1-03 | 동의 | FAIL은 올바른 차단. 가시 PASS 부재는 제품 경험 공백 |
| RQA-P1-04 | 동의 | 최우선 코드 정합 후보 |
| RQA-P2-01 | 동의 | scheduler 전제 |
| RQA-P2-02 | 부분 | 샘플은 GateBlockedError. 24h=13 전체 미트리아지 |
| RQA-P2-03–05 | 동의 | 기존 backlog |
| RQA-P3-01 | 동의 | UX |

**P0 = 0** 양쪽 일치. 데이터 손실·비밀 노출·매매 경로 활성화는 없음.

---

## 5.  Milestones 세부 공백 (P2 샘플)

기존 audit에 이미 적힌 것. 새로 만든 결함이 아니다.

- G00-P2-01 PITR before enabling schedulers
- M01-P2-03 production scheduler enable is separate ops decision
- M01-P2-01 Docker image not CI-evidenced
- M02-P2-01 industry-ticker maps config-limited
- M03-P2-02 multi-security batch not load-tested
- M04-P2-01 SPY/QQQ history missing in lab
- M05-P2-01 auto-classification not wired
- M06-P2-01 구이슈: replay notes manual (evaluator는 이후 존재)

이번 진단에서 **추가된 관측**:

- L08 vs M03 grounding dual-path
- AAPL billion-scale numeric FAIL
- biweekly `llm-profile-v0.1` vs M03 `v0.2`
- `code_commit_hash=m01-biweekly` 비-git
- `--limit 5`인데 priced universe 1건

---

## 6. 사용자가 지금 할 수 있는 것 / 없는 것

**가능 (lab)**

- http://localhost:3000 한글 콘솔
- 후보 1건(AAPL REJECT) 상세
- 감사/ops 화면 (PITR false, scheduler 허용 안 함 표시)

**불가능 / 하면 안 됨**

- “완성된 상시 제품”으로 쓰기
- Post-MVP tag · GO 선언
- cron 켜기
- 공개 URL 배포를 PASS로 간주
- QA FAIL를 화면용으로 PASS처럼 보이게 우회
- Long-Term Optional 착수

---

## 7. 권고 순서 (코드 다음 작업 — 이번 커밋에서 실행하지 않음)

우선순위는 2차 next_actions와 맞고, 1차가 AAPL 원인을 더 구체화했다.

| 순위 | 할 일 | 하지 말 것 |
|------|-------|------------|
| 1 | NO-GO / lab-only 유지. 이 보고서를 검증 흔적으로 둔다 | tag, GO, cron, 공개 배포 |
| 2 | L08 `claim_check` ↔ packet 단위(billion/raw) 정합. 회귀 테스트. 그 다음 **한 종목 PASS-QA**를 다시 돌려 화면에 남긴다 | 게이트 완화, FAIL를 PASS로 위장 |
| 3 | `claim_support`와 `claim_check` 정책 공유 또는 범위 문서 + 교차 공격 회귀 | 한쪽 self-QA로 양쪽 동등 주장 |
| 4 | failed_jobs_24h 13 전체 원인 표 (GateBlocked vs 그 외) | 카운트만 보고 scheduler 논의 |
| 5 | PITR 가능한 플랜/증거 후에만 scheduler 검토 | Free에서 PITR CONFIRMED 위조 |
| 6 | hosted + Docker CI는 **별도 ops**. 사람이 화면을 본 뒤 명시할 때만 | localhost를 production proof로 사용 |

---

## 8. 신뢰 한계

- 2차는 `facts.json`만 봤다. 라이브 보강(§4.3)은 1차 후속이다.
- 패킷 raw 값은 secret/대량이라 `live_snapshot`에 넣지 않았다. billion 가설은 claim 텍스트와 checker 코드로 추론 — packet leaf를 이 폴더에 dump하지 않음.
- grounding FP=0은 **당시 self_remediate 스냅샷**. 이후 claim_check를 바꾸면 M03 점수가 자동으로 따라가지 않는다.
- 로컬 서버가 떠 있다는 것은 lab usability이지 availability SLA가 아니다.

---

## 9. 최종 서명

| 역할 | 판정 |
|------|------|
| 1차 (구현 에이전트) | 제품 미완성. lab 사용 가능. **NO-GO**. 다음 실질 작업은 L08 숫자 단위 정합 + 가시 PASS-QA 1건 |
| 2차 (`research_qa_agent` / gpt-5.6-terra high) | `LAB_ONLY_OK` · **NO-GO** · confidence high |
| 교차 | 사실 일치. severity 라벨만 다름. 운영 권고 동일 |

**이 문서는 진단이다. PASS Layer가 아니고, Post-MVP seal이 아니다.**
