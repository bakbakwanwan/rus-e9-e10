# EXP-009 Full Run Spec

> 상태: full E9 run 실행 확정 스펙 (`docs/e9_json_llm_verification_decisions.md` 5-8절 WP6 완료)
> 작성일: 2026-09-19
> 근거 문서: `docs/EXP-009-DECISIONS.MD`, `docs/EXP-009-PLAN.MD`, `docs/e9_json_llm_verification_decisions.md`, `docs/environment-fullrun-2026-09-19.md`

100-flow pilot(`e9-pilot-20260919T113156Z-093066da`, completed, schema valid 100%, timeout 0%)이 D-EXP009-016 기술 성공 기준을 통과했으므로, WP6에 따라 다음을 확정한다.

## 1. Experiment ID와 질문

- Experiment ID: **EXP-009**
- 질문: 같은 abstained flow 집합에서 `gate_forced`와 `end_to_end`(LLM fallback 포함) 중 어느 쪽이 오류를 덜 내는가 (`docs/EXP-009-DECISIONS.MD` D-EXP009-001, D-EXP009-011).

## 2. Abstention budget과 전체 대상 flow

- source experiment: `EXP-007`
- method: `group_seed42`
- target_abstention_rate: `0.01`
- 실제 대상 행 수: **4,816행** (`n_abstained`, `data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/metrics.json`)
- selection rule: 대상 abstained set 전체 (100-flow pilot처럼 hash 상위 N행으로 자르지 않음)
- 다른 budget(0.02/0.05/0.10)은 이번 EXP-009 full run 범위에 포함하지 않는다. 필요 시 별도 experiment로 분리한다.

## 3. 성공·실패·판정불가 기준

**실행 성공 (technical)**

- `runner_status.json`의 `run_status == completed`
- 모든 `input_index`(0~4815)에 정확히 하나의 응답 행
- schema valid rate ≥95%, timeout rate ≤5%, OOM/crash 0건

**실행 실패**

- OOM/crash 발생
- model metadata mismatch (`EXPECTED_MODEL`과 불일치)
- LLM input leakage 발견
- input/response/evaluation sidecar row mismatch

**판정불가 (연구 결론 보류)**

- 기술적으로 completed이지만 timeout/generation_failure rate가 pilot 대비 비정상적으로 높아 표본이 왜곡됐다고 판단되는 경우
- 이 경우 원인을 문서화하고 재실행 여부를 별도로 결정한다 (기존 결과는 보존, 새 `run_id`로 재실행)

**연구 결론(성능 비교)**은 이 실행 성공 기준을 만족한 뒤에만 4절 지표로 판단한다. 100-flow pilot 수치는 이 판단에 사용하지 않는다 (`D-EXP009-017`).

## 4. 지표 구분과 해석 한계

- Primary: `gate_forced.error_rate` vs `end_to_end.error_rate`, `gate_correct_final_error` / `gate_error_final_correct` 전이 수
- Secondary: precision/recall/F1/FPR/FNR (세 결과 각각), override rate, fallback rate, indeterminate rate, generation failure rate, latency p50/p95
- `llm_valid_only`는 보조 분석이며 primary comparison에 쓰지 않는다

**해석 한계**

- 단일 seed(`group_seed42`), 단일 budget(`0.01`)의 결과다. 다른 seed/budget에 일반화하지 않는다
- attack-type 분류, LLM confidence calibration, RAG/groundedness는 이 실험 범위 밖이다 (`docs/EXP-009-DECISIONS.MD` 5절)
- zero-day/LOAO 일반화를 주장하지 않는다 (`AGENTS.md` 22절)
- 이 실행은 `docs/environment-fullrun-2026-09-19.md`에 기록된 하드웨어(RTX 3050, VRAM 4GB, CUDA 부분 offload)에서 수행됐다. latency는 이 환경 고유의 값이며 다른 하드웨어에 일반화하지 않는다

## 5. 실행 자원·시간 상한, artifact 계약

- 예상 소요 시간: 4,816행 × pilot warm p50(4.71초) ≈ **약 6.3시간** (순차 실행, `concurrency=1` 고정 계약)
- 시간 상한: 명시적 hard timeout은 두지 않는다. 진행 중 100행 단위 checkpoint로 진행 상황을 관찰하며, 비정상적으로 느려지거나 멈추면 상태를 보고 중단 여부를 사용자와 상의한다
- 중단 시: `llm_responses.partial.jsonl`, `runner_status.json`(`run_status=incomplete`), `run_manifest.json`을 보존하고 같은 `run_id`로 재개하지 않는다 (D-EXP009-019)
- 결과 디렉토리: `results/EXP-009/<run_id>/` — pilot과 동일한 내부 구조(`export/{transfer,local}`, `checks`, `returned`, `evaluation`)를 사용하고 루트만 `results/pilots/e9-json-llm/`에서 분리한다
- `run_id`는 기존과 동일한 `e9-pilot-YYYYMMDDTHHMMSSZ-xxxxxxxx` 형식을 그대로 쓴다. pilot과 full run의 구분은 `run_id` 문자열이 아니라 디렉토리 루트로만 한다 (`RUN_ID_PATTERN`이 코드에 고정되어 있어 접두사 변경 불가)
- 최종 artifact 계약은 pilot과 동일: `export/manifest.json`, `export/transfer/*`, `export/local/evaluation_sidecar.jsonl`, `checks/bundle_validation.preflight.json`, `returned/{run_manifest.json, runner_status.json, llm_responses.jsonl}`, `evaluation/{evaluation_manifest.json, evaluation_records.jsonl, metrics.json}`
