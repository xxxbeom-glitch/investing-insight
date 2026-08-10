# Playwright browser acceptance (ER-P1-03)

Method: Playwright headless Chromium @ 1440x900
Target run: 89064263-8b6c-4a58-aeb4-0704ab539d9a
Path: Dashboard → Runs → Run Detail → Candidates → Company/Evidence → Audit → Settings
Generated: 2026-08-10T21:42:25.748Z

- [x] dashboard_brand: brand present
- [x] dashboard_latest_run: latest run label
- [x] dashboard_llm_profile: profile/model on dashboard
- [x] dashboard_latest_link: href=/runs/9e0896c5-7513-4e11-938f-427c53fc6462
- [x] runs_historical_list: run_detail_links=50
- [x] runs_shows_versions: version columns
- [x] latest_vs_historical: latest=/runs/9e0896c5-7513-4e11-938f-427c53fc6462 list_n=50
- [x] run_detail_id: 89064263-8b6c-4a58-aeb4-0704ab539d9a
- [x] run_model_visible: requested/resolved model
- [x] run_effort_visible: reasoning effort
- [x] run_profile_visible: profile version
- [x] run_hashes_visible: hash columns
- [x] candidates_page: candidates
- [x] candidates_qa_fail_visible: QA FAIL in candidates table
- [x] candidate_company_links: n=1
- [x] company_evidence_section: evidence
- [x] company_qa_fail_visible: QA FAIL on company
- [x] company_quant_or_research: sections
- [x] audit_page: audit
- [x] audit_qa_fail_or_status: qa statuses
- [x] settings_profile_visible: profile
- [x] settings_model_effort_visible: model+effort
- [x] settings_provider_flags: flags only
- [x] settings_no_raw_secret_text: body text scan
- [x] settings_no_raw_secret_html: html scan
- [x] settings_no_leak_banner: leak banner absent
- [x] viewport_1280_plus: width=1440

Overall: PASS