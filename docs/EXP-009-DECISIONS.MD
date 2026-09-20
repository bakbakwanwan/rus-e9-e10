# EXP-009 Decisions

> 상태: EXP-009 실험 설계 결정 기록  
> 작성일: 2026-09-18  
> 범위: E9 local LLM-only verification 실험의 목적, 확인하려는 것, 궁극적 도달점, 현재 결정 사항  
> 주의: 이 문서는 현재 결정의 기록이다. 세부 실행 스펙, 명령어, artifact 경로, 결과 해석은 별도 실험 스펙/결과 문서에 둔다.

## 1. EXP-009의 위치

EXP-009는 RUS hybrid IDS 연구에서 **Layer 2 E9: local LLM-only verification**을 실험 가능한 형태로 확립하기 위한 실험이다.

현재 연구 구조는 다음과 같다.

```text
Layer 1:
LightGBM ML-IDS
-> confidence-based selective prediction
-> uncertain flows abstained

Layer 2 E9:
abstained flows
-> label-free JSON serialization
-> local LLM-only verification

Layer 2 E10:
abstained flows
-> retrieval
-> evidence-augmented LLM verification
```

EXP-009는 E10의 효과를 논하기 전에 필요한 **LLM-only baseline**을 세우는 역할을 한다.

## 2. 확인하고자 하는 것

EXP-009가 확인하려는 핵심 질문은 다음이다.

> Layer 1이 판정을 유보한 어려운 network flow에 대해, local LLM-only verifier가 Gate forced decision보다 end-to-end 오류를 줄일 수 있는가?

이를 위해 EXP-009는 같은 abstained flow 집합에서 아래 두 판정을 비교한다.

```text
Gate Forced Decision
vs
E9 Local LLM-only End-to-End Decision
```

여기서 `end-to-end`는 다음 규칙을 따른다.

```text
LLM이 BENIGN 또는 ATTACK을 유효하게 출력하면 LLM 판정을 사용한다.
LLM이 INDETERMINATE를 출력하거나 generation failure가 발생하면 Gate forced decision으로 fallback한다.
```

EXP-009는 다음을 분리해서 확인한다.

1. LLM이 실제로 엄격한 JSON 출력 계약을 안정적으로 지킬 수 있는가.
2. LLM이 유효한 이진 판정을 내린 경우 Gate와 다른 판단을 어느 정도 하는가.
3. LLM override가 Gate 오류를 교정하는 경우와 Gate 정답을 오답으로 바꾸는 경우의 균형은 어떤가.
4. fallback을 포함한 end-to-end 시스템이 Gate forced baseline보다 나은가.
5. latency, timeout, malformed output 같은 운영 실패가 실험 결과에 어느 정도 영향을 주는가.

## 3. 궁극적으로 도달할 것

EXP-009의 궁극적 목표는 단순히 100-flow pilot을 한 번 실행하는 것이 아니다.

EXP-009의 도달점은 다음 세 가지다.

### 3.1 E9 Full Experiment Readiness

E9 full run을 실행해도 되는 상태를 만든다.

최소 조건은 다음과 같다.

- abstained test set 선택 규칙이 재현 가능하다.
- LLM 입력에는 ground truth, Gate prediction, confidence가 들어가지 않는다.
- 59-feature serializer가 deterministic하다.
- prompt version, model, generation settings가 고정되어 있다.
- raw response와 parsed result가 분리 저장된다.
- fallback 규칙이 명시되어 있다.
- evaluator가 `gate_forced`, `llm_valid_only`, `end_to_end`를 분리 산출한다.
- pilot에서 JSON validity, timeout, crash 여부가 full run을 막지 않는 수준이다.

### 3.2 Gate-vs-LLM 비교 가능 상태

EXP-009는 다음 질문에 답할 수 있는 artifact를 남겨야 한다.

```text
같은 abstained flow 집합에서
Gate forced decision과
LLM fallback 포함 end-to-end decision 중
어느 쪽이 오류를 덜 내는가?
```

이를 위해 반드시 per-flow record를 남긴다.

필수 row-level 정보는 다음이다.

- `input_index`
- `day`
- `id`
- `binary_label`
- `gate_predicted_label`
- `llm_decision`
- `llm_predicted_label`
- `fallback_applied`
- `fallback_reason`
- `final_predicted_label`
- `gate_is_error`
- `final_is_error`
- `transition`
- `llm_override`
- `wall_latency_seconds`

Aggregate metric만 남겨서는 EXP-009의 목적을 충족하지 못한다.

### 3.3 E10 Baseline 확립

EXP-009는 E10과 비교 가능한 baseline을 만든다.

E10은 retrieval evidence를 추가하는 실험이어야 하며, EXP-009와 비교할 때 아래 요소를 가능한 한 유지해야 한다.

- 같은 abstained flow population
- 같은 feature serializer
- 같은 model/runtime 조건
- 같은 output schema 또는 명시적으로 versioned된 schema
- 같은 fallback/evaluation logic
- 같은 primary metric family

따라서 EXP-009의 결과는 E10에서 다음 비교의 기준점이 된다.

```text
Gate Forced
vs
E9 LLM-only
vs
E10 RAG + LLM
```

## 4. 현재 내리는 결정

### D-EXP009-001 — EXP-009의 1차 목적

EXP-009의 1차 목적은 **local LLM-only verifier가 abstained flow에서 Gate forced decision 대비 end-to-end 오류를 줄일 수 있는지 평가 가능한 baseline을 만드는 것**이다.

성능 향상 주장보다 먼저, 재현 가능한 비교 구조와 artifact 보존을 우선한다.

### D-EXP009-002 — Pilot의 의미

100-flow pilot은 성능 우위 입증용이 아니다.

Pilot은 다음 운영 가능성만 판단한다.

- bundle 생성 가능 여부
- prompt leakage 방지 여부
- Ollama 호출 가능 여부
- strict JSON validity
- timeout/failure rate
- latency p50/p95
- evaluator 연결 가능 여부

Pilot 결과의 accuracy, F1, error transition은 점검용으로 볼 수 있지만, 연구 결론으로 주장하지 않는다.

### D-EXP009-003 — Primary Comparison

EXP-009의 주 비교는 다음으로 고정한다.

```text
gate_forced
vs
end_to_end
```

`llm_valid_only`는 보조 분석이다.  
이유는 `llm_valid_only`가 LLM이 유효하게 응답한 부분집합만 평가하므로 운영 시스템 전체 성능을 대표하지 않기 때문이다.

### D-EXP009-004 — Fallback Rule

EXP-009의 end-to-end 판정은 다음 fallback 규칙을 사용한다.

```text
BENIGN or ATTACK:
  use LLM decision

INDETERMINATE:
  fallback to Gate forced decision

generation_failure:
  fallback to Gate forced decision
```

이 규칙은 운영 실패를 숨기기 위한 것이 아니다.  
`INDETERMINATE`, `generation_failure`, `fallback_applied`, `fallback_reason`은 모두 별도 지표로 기록한다.

### D-EXP009-005 — Leakage Boundary

LLM prompt에는 평가 전용 정보와 Layer 1 판단 정보를 넣지 않는다.

Prompt에서 제외하는 필드는 다음이다.

- `day`
- `id`
- `Label`
- `binary_label`
- `is_error`
- `Attempted Category`
- `p_attack`
- `confidence`
- `predicted_label`
- `abstained`

이 값들은 evaluation sidecar와 manifest에는 보존할 수 있지만, LLM 환경으로 전달되는 prompt payload에는 포함하지 않는다.

### D-EXP009-006 — Output Schema

첫 EXP-009 E9 조건의 LLM 출력은 다음 최소 schema로 고정한다.

```json
{ "decision": "BENIGN | ATTACK | INDETERMINATE" }
```

`attack_type`, self-reported confidence, free-form reason, observed indicators는 첫 EXP-009 조건에 포함하지 않는다.

이유:

- 첫 실험은 LLM의 설명 품질보다 binary verification 효과를 먼저 본다.
- 출력 자유도를 줄여 malformed output과 parser ambiguity를 낮춘다.
- E10 이전에 최소 baseline을 안정화한다.

### D-EXP009-007 — Model and Runtime as Controlled Variables

EXP-009에서는 모델과 generation setting을 실험 중간에 바꾸지 않는다.

현재 코드상 E9 runner 계약은 다음이다.

- Ollama model tag: `gemma:7b-instruct`
- quantization: `Q4_0`
- `num_ctx=4096`
- `temperature=0`
- `top_p=1.0`
- `num_predict=64`
- `seed=42`
- `concurrency=1`
- `timeout_seconds=60`

모델, prompt, output schema, generation setting 중 하나라도 바뀌면 같은 EXP-009 안에서도 별도 run/config/version으로 기록한다.

### D-EXP009-008 — Result Preservation

EXP-009는 실패한 run도 삭제하거나 덮어쓰지 않는다.

다음 artifact는 보존 대상이다.

- export manifest
- transfer input JSONL
- local evaluation sidecar
- bundle validation result
- run manifest
- runner status
- raw LLM responses
- parsed/evaluated records
- metrics

중단된 run의 partial response도 보존하되, 공식 평가에는 completed `llm_responses.jsonl`만 사용한다.

### D-EXP009-009 — Full Run 진입 조건

Full EXP-009는 pilot 이후에만 실행한다.

Full run 진입 최소 조건은 다음이다.

- `pytest -q`가 실행 가능하며 현재 테스트 스위트가 통과한다.
- schema/prompt/bundle validator가 통과한다.
- 100-flow pilot에서 runner crash 또는 OOM이 없다.
- JSON schema valid rate가 충분히 높다.
- timeout/failure rate가 full run을 막지 않는 수준이다.
- git worktree 상태와 commit이 manifest에 기록 가능하다.
- source abstained set과 selection rule이 명확히 기록되어 있다.

### D-EXP009-010 — 계획 확정 진행 순서

EXP-009 계획 확정은 한 번에 하나의 결정만 처리한다.

각 확정 대화의 첫머리에는 현재 확정 단계를 표시한다.

확정 단계는 다음 순서로 진행한다.

1. 확정 단계 목록과 진행 순서
2. EXP-009의 primary objective와 success definition
3. pilot source 조건
4. artifact/input 경로 convention
5. 최소 테스트 스위트 범위
6. 1-flow smoke test 방식
7. 100-flow pilot 실행 조건
8. pilot evaluation 기준
9. full run 진입 기준
10. partial/resume 정책
11. 최종 EXP-009 plan 확정

이 순서를 채택하는 이유는 연구 목적에서 시작해 입력 source, 실행 기반, pilot 판단, full run 조건으로 내려가는 흐름이 가장 적은 되돌림으로 실험 설계를 고정할 수 있기 때문이다.

각 단계에서는 다음을 명시한다.

- 무엇을 확정해야 하는지
- 확정 시 영향
- 선택지가 있다면 각 후보군의 의미와 trade-off
- 최종 확정 이유

확정된 결정은 `docs/EXP-009-DECISIONS.MD`에 기록해 아카이빙한다.

### D-EXP009-011 — Primary Objective and Success Definition

EXP-009의 1차 성공은 **재현 가능한 E9 local LLM-only baseline을 구축하는 것**으로 정의한다.

EXP-009는 pilot 단계에서 LLM이 Gate forced decision보다 성능이 좋다는 결론을 입증하려 하지 않는다.

EXP-009가 성공했다고 판단하려면 최소한 다음이 가능해야 한다.

- 같은 abstained flow 집합에서 `gate_forced`와 `end_to_end`를 비교할 수 있다.
- LLM 입력 bundle이 label-free임을 검증할 수 있다.
- raw LLM response와 parsed response가 분리 보존된다.
- `INDETERMINATE`, malformed output, timeout, connection failure 같은 운영 실패가 숨겨지지 않고 기록된다.
- fallback 규칙이 row-level record에 반영된다.
- `gate_forced`, `llm_valid_only`, `end_to_end` metrics가 분리 산출된다.
- pilot 결과를 근거로 full E9 run 진입 여부를 판단할 수 있다.

이렇게 확정하는 이유는 EXP-009가 E10의 비교 baseline 역할을 해야 하며, 성능 향상 주장보다 먼저 재현 가능한 비교 구조와 artifact 보존이 필요하기 때문이다.

성능 향상 여부는 full E9 run에서 `gate_forced`와 `end_to_end`를 비교해 판단한다. 100-flow pilot의 accuracy, F1, transition count는 운영 가능성 점검용으로만 사용한다.

### D-EXP009-012 — Pilot Source Condition

EXP-009의 첫 100-flow pilot source 조건은 다음으로 고정한다.

- source experiment: `EXP-007`
- method: `group_seed42`
- target abstention rate: `0.01`
- sample size: `100`
- selection rule: 대상 abstained set에서 `sha256(day\0id)` 오름차순 첫 100행

실제 artifact 경로는 실행 환경마다 다를 수 있으므로 이 결정에서 고정하지 않는다.

실행 시에는 다음 경로를 명시적으로 주입해야 한다.

- predictions parquet path
- metrics json path
- source CSV data directory
- output root

파일명이나 로컬 경로만으로 source를 신뢰하지 않는다. source experiment, method, target abstention rate, 실제 threshold, prediction artifact SHA-256, dataset file SHA-256은 export manifest에 기록해 검증한다.

이렇게 확정하는 이유는 첫 pilot의 목적이 여러 budget 비교가 아니라 E9 pipeline readiness 확인이기 때문이다. `EXP-007 / group_seed42 / 0.01`은 기존 E9 결정 기록과 일치하며, stable hash sampling은 prompt/model 변경 시 같은 flow 집합을 재사용하기 쉽다.

### D-EXP009-013 — Artifact and Input Path Convention

EXP-009 pilot의 source input 경로는 문서에 고정하지 않고 실행 시 명시적으로 주입한다.

필수 입력 경로는 다음 CLI argument로 전달한다.

- predictions parquet path
- metrics json path
- source CSV data directory
- output root

Pilot 결과의 기본 output root는 다음으로 둔다.

```text
results/pilots/e9-json-llm
```

각 pilot run은 `run_id` 아래에 결과를 분리한다.

```text
results/pilots/e9-json-llm/<run_id>/
├── export/
│   ├── manifest.json
│   ├── transfer/
│   │   ├── llm_inputs.jsonl
│   │   ├── e9_input_feature_schema.json
│   │   └── e9_prompt_v1.json
│   └── local/
│       └── evaluation_sidecar.jsonl
├── package/
│   ├── <run_id>.zip
│   └── <run_id>.manifest.json
├── checks/
│   └── bundle_validation.preflight.json
├── returned/
│   ├── bundle_validation.json
│   ├── run_manifest.json
│   ├── runner_status.json
│   └── llm_responses.jsonl
└── evaluation/
    ├── evaluation_manifest.json
    ├── evaluation_records.jsonl
    └── metrics.json
```

`export/transfer`에는 LLM 환경으로 전달 가능한 label-free artifact만 둔다.

`export/local`에는 evaluation sidecar를 둔다. 이 파일은 LLM 환경으로 전달하지 않는다.

`checks`에는 runner 실행 전 standalone validation 결과를 둔다.

`returned`는 runner output directory로 사용하며, runner 실행 전 비어 있어야 한다. 현재 runner는 `output_dir`가 이미 존재하면 실패하고, 실행 중 `returned/bundle_validation.json`을 생성한다.

기존 run directory나 output artifact를 덮어쓰지 않는다. 재실행이 필요하면 새 `run_id`를 사용한다.

이렇게 확정하는 이유는 source artifact 경로가 실행 환경마다 달라질 수 있는 반면, run별 결과 구조는 고정되어야 검증·전송·평가·보존을 일관되게 수행할 수 있기 때문이다. 또한 transfer artifact와 local evaluation sidecar를 물리적으로 분리해 prompt leakage 위험을 낮춘다.

### D-EXP009-014 — Minimal Test Suite Scope

EXP-009 pilot 전에 작성할 최소 테스트 스위트는 E9 계약 경계 검증에 집중한다.

최소 테스트 범위는 다음이다.

- schema snapshot validation
- prompt asset validation
- prompt rendering에서 forbidden field가 포함되지 않는지 확인
- strict response parser의 정상/`INDETERMINATE`/schema violation 처리
- transfer bundle validator의 정상/실패 케이스
- evaluator fallback logic
- metric/count 산출의 기본 일관성

권장 테스트 파일은 다음이다.

```text
tests/
├── test_e9_schema_prompt.py
├── test_e9_runtime_parser.py
├── test_e9_bundle_validation.py
└── test_e9_evaluation.py
```

이 최소 테스트 스위트는 외부 Ollama 서버와 실제 대용량 dataset을 요구하지 않아야 한다.

Fake CSV 또는 synthetic prediction artifact를 사용해 `export_abstained_flow_bundle()` 전체를 integration test하는 것은 이번 최소 범위에 포함하지 않는다.

그 이유는 임의 수치로 만든 fixture가 실제 abstained flow 분포나 연구적 source 타당성을 대표하지 못하기 때문이다. 그런 fixture는 코드 plumbing 확인에는 쓸 수 있지만, EXP-009의 실험적 근거로 오해될 여지가 있다.

Export 단계의 검증은 실제 `EXP-007 / group_seed42 / target_abstention_rate=0.01` artifact를 사용한 dry run에서 수행한다. 이때 manifest, SHA-256, row count, forbidden field 부재, transfer/local sidecar 분리를 확인한다.

필요하다면 이후 실제 artifact 구조가 확인된 뒤, representative sample 또는 artifact-derived fixture 기반 export test를 별도 범위로 추가한다.

이렇게 확정하는 이유는 EXP-009 pilot 전에 반드시 필요한 leakage/parser/evaluator 계약은 자동 테스트로 고정하되, 근거 없는 synthetic data를 연구 source 검증처럼 다루지 않기 위해서다.

### D-EXP009-015 — 1-flow Ollama Smoke Test Method

100-flow pilot 전에 1-flow Ollama smoke test를 별도 bundle과 별도 `run_id`로 실행한다.

Smoke test bundle은 같은 source 조건을 사용하되 `sample_size=1`로 export한다.

Smoke test source 조건은 다음과 같다.

- source experiment: `EXP-007`
- method: `group_seed42`
- target abstention rate: `0.01`
- sample size: `1`
- selection rule: 대상 abstained set에서 `sha256(day\0id)` 오름차순 첫 1행

Smoke test의 목적은 성능 확인이 아니라 다음 실행 계약 확인이다.

- Ollama server reachable
- expected model installed
- model metadata가 E9 runner contract와 일치
- prompt rendering과 structured output request가 실제 Ollama 호출에서 동작
- strict response parser가 실제 response를 처리
- runner가 completed status와 `llm_responses.jsonl`을 생성

Smoke test 결과는 공식 pilot evaluation으로 사용하지 않는다.

Runner에 `--limit 1` 옵션은 추가하지 않는다.

이렇게 확정하는 이유는 현재 runner가 입력 row 수와 response row 수의 일대일 대응을 completed run의 핵심 계약으로 삼고 있기 때문이다. Smoke test를 위해 runner의 row-count semantics를 흔들지 않고, 대신 `sample_size=1` 별도 bundle을 사용해 기존 runner/evaluator 계약을 그대로 유지한다.

### D-EXP009-016 — 100-flow Pilot Execution Gate

100-flow pilot은 엄격한 readiness gate를 통과한 뒤 실행한다.

100-flow pilot 실행 전에는 다음 조건이 모두 충족되어야 한다.

- 최소 테스트 스위트가 통과한다.
- 1-flow smoke test가 completed 상태로 종료된다.
- 100-flow export bundle이 생성되어 있다.
- standalone bundle validation preflight가 통과한다.
- Ollama model metadata가 E9 runner contract와 일치한다.
- runner output directory인 `returned/`가 존재하지 않거나 비어 있다.
- source artifact SHA-256과 source metadata가 export manifest에 기록되어 있다.
- `llm_inputs.jsonl`에 forbidden field가 없음을 확인했다.

100-flow pilot의 기술 성공 기준은 다음이다.

- `runner_status.json`의 `run_status`가 `completed`다.
- `llm_responses.jsonl` row 수가 100이다.
- 모든 `input_index`에 정확히 하나의 response row가 있다.
- schema valid rate가 95% 이상이다.
- timeout rate가 5% 이하이다.
- OOM 또는 runner crash가 0건이다.
- latency p50/p95를 산출할 수 있다.

다음 조건에서는 pilot을 중단하거나 실패로 기록한다.

- bundle validation failure
- model metadata mismatch
- systemic connection/http/ollama/api failure
- unexpected runner exception
- completed response row count mismatch

중단 run은 삭제하지 않는다. partial response, runner status, 가능한 manifest를 보존한다. 같은 output directory에서 재개하지 않고 새 `run_id`로 재실행한다.

이렇게 확정하는 이유는 EXP-009의 1차 성공이 재현 가능한 baseline 구축이기 때문이다. 예측 가능한 준비 부족으로 실패 run을 만들지 않도록, 첫 100-flow pilot부터 입력·모델·runner·validation 상태를 명확히 통제한다.

### D-EXP009-017 — Pilot Evaluation Criteria

100-flow pilot evaluation은 technical readiness 판단 전용으로 사용한다.

Pilot evaluation에서는 다음 metrics와 artifact를 산출한다.

- `gate_forced`
- `llm_valid_only`
- `end_to_end`
- transition counts
- schema valid rate
- `INDETERMINATE` rate
- generation failure rate
- timeout rate
- fallback rate
- override rate
- latency p50/p95

Pilot evaluation의 primary interpretation은 운영 가능성이다.

다음 항목을 중심으로 full run readiness를 판단한다.

- strict JSON output이 충분히 안정적인가
- timeout과 generation failure가 허용 범위 안인가
- fallback이 과도하게 발생하지 않는가
- runner가 completed 상태로 종료되는가
- row-level transition record가 정상 생성되는가
- `gate_correct_final_error`가 위험 신호로 볼 만큼 과도하지 않은가
- latency가 full run 실행 가능성을 막지 않는가

Pilot의 accuracy, F1, error rate, transition count는 evaluator 연결과 위험 신호 점검을 위해 산출하지만, 성능 우위 주장에는 사용하지 않는다.

`end_to_end`가 `gate_forced`보다 좋아 보이더라도 100-flow pilot만으로 EXP-009의 성능 결론을 내리지 않는다. 성능 비교 결론은 full E9 run에서 사전 지정된 abstained flow 집합에 대해 판단한다.

이렇게 확정하는 이유는 100-flow pilot이 표본 수와 목적상 readiness check이며, 연구 결론을 주장하기에는 대표성과 통계적 안정성이 부족하기 때문이다. 다만 evaluator와 transition logic을 검증하기 위해 classification metrics 자체는 산출한다.

### D-EXP009-018 — Full E9 Run Entry Criteria

Full E9 run은 100-flow pilot과 구분되는 본 실험이다.

100-flow pilot은 pipeline readiness 확인용이며, full E9 run은 사전 지정된 abstained flow 집합에서 `gate_forced`와 `end_to_end`를 비교해 EXP-009의 연구 질문에 답하기 위한 실행이다.

Full E9 run 진입 전에는 다음 조건이 모두 충족되어야 한다.

- 최소 테스트 스위트가 통과한다.
- 1-flow smoke test가 completed 상태로 종료된다.
- 100-flow pilot이 completed 상태로 종료된다.
- 100-flow pilot의 schema valid rate가 95% 이상이다.
- 100-flow pilot의 timeout rate가 5% 이하이다.
- 100-flow pilot에서 OOM 또는 runner crash가 없다.
- pilot evaluation artifact가 정상 생성된다.
- full run에 사용할 source abstained set 조건이 확정되어 있다.
- prompt version, feature schema, model, quantization, generation setting이 freeze되어 있다.
- full run 결과 디렉토리 convention이 확정되어 있다.
- partial/resume 정책이 확정되어 있다.
- 공식 full run 실행 전 git worktree가 clean 상태다.

다음 항목은 full run 진입 blocker다.

- model metadata mismatch
- prompt/schema 변경 필요
- LLM input leakage 발견
- input/response/evaluation sidecar row mismatch
- evaluator 결합 실패
- `llm_inputs.jsonl`에 forbidden field 발견
- full run 예상 latency가 현실적으로 실행 불가능한 수준임이 확인됨

다음 항목은 blocker는 아니지만 full run 전 검토해야 하는 warning이다.

- fallback rate가 과도함
- `gate_correct_final_error`가 위험 신호로 볼 만큼 많음
- latency p95가 큼
- parsing/generation failure가 기준 이하이지만 특정 패턴으로 반복됨

Pilot에서 Gate 대비 성능이 좋아 보이거나 나빠 보이는 것만으로 full run 진입 여부를 결정하지 않는다. Pilot은 readiness 판단용이고, 성능 결론은 full E9 run에서 판단한다.

이렇게 확정하는 이유는 full E9 run이 EXP-009의 연구 결론 기반이므로, 운영 성공뿐 아니라 source/config/result preservation 조건이 함께 고정되어야 하기 때문이다.

### D-EXP009-019 — Partial Run and Resume Policy

EXP-009 pilot과 첫 full E9 run에서는 in-place resume을 허용하지 않는다.

중단 run은 삭제하지 않고 보존한다.

보존 대상은 가능한 범위에서 다음을 포함한다.

- `llm_responses.partial.jsonl`
- `runner_status.json`
- `run_manifest.json`
- `bundle_validation.json`
- failure log 또는 terminal output summary

공식 evaluation은 다음 조건을 모두 만족할 때만 허용한다.

- `runner_status.json`의 `run_status`가 `completed`다.
- completed `llm_responses.jsonl`이 존재한다.
- response row 수가 expected input row 수와 일치한다.
- 모든 `input_index`에 정확히 하나의 response row가 있다.

중단 run은 같은 output directory에서 이어붙이지 않는다.

같은 `run_id`를 재사용하지 않는다.

재실행이 필요하면 새 `run_id`로 시작한다.

Full run 시간이 실제로 너무 길거나 실패 비용이 과도하다는 근거가 생기면, 후속 결정으로 chunked full run 또는 input-index 기반 resume 기능을 별도 설계한다.

이렇게 확정하는 이유는 EXP-009의 현재 목표가 재현 가능한 baseline 구축이며, resume 기능은 편의성이 있지만 input/output 정합성과 evaluator 연결을 복잡하게 만들어 첫 baseline 안정화 단계의 위험을 키우기 때문이다.

### D-EXP009-020 — Final Plan Confirmation and Staged Source Artifacts

`docs/EXP-009-PLAN.MD`를 EXP-009 실행 계획으로 확정한다.

최종 plan 확정 전 source artifact staging을 확인했다.

확인된 입력 artifact는 다음이다.

```text
predictions parquet:
data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/group_seed42.parquet

metrics json:
data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/metrics.json

source CSV data directory:
data/CICIDS2017_improved_2022ver
```

확인된 SHA-256은 다음이다.

```text
predictions parquet:
e27f1a5edbd305605923685fe4f9203f9ed1f6c269b6f0169cf2d4d1634898dc

metrics json:
122093a73f4d4b71c0173d5e72c23405e2010e4db129534c5ca1d794a0da5fb9
```

`metrics.json`에서 확인된 source 조건은 다음이다.

- source experiment: `EXP-007`
- method: `group_seed42`
- target abstention rate: `0.01`
- confidence threshold: `0.9993377811093735`

`data/CICIDS2017_improved_2022ver`의 5개 source CSV는 `metrics.json`의 dataset SHA-256과 일치함을 확인했다.

Parquet reader dependency로 `pyarrow`가 설치되어 있으며, 확인된 version은 `25.0.1`이다.

계획은 확정하지만, full run result directory는 pilot 이후 결정한다. 이는 full run이 100-flow pilot과 구분되는 본 실험이며, pilot readiness 결과를 보고 별도 full-run convention을 확정하는 것이 더 안전하기 때문이다.

이렇게 확정하는 이유는 EXP-009의 설계 결정 1-10단계가 완료되었고, 실제 source artifact path와 hash가 확인되어 이제 계획 확정보다 실행 준비 단계로 넘어갈 수 있기 때문이다.

### D-EXP009-021 — Pilot OOM Recovery by Expanding WSL Memory

첫 100-flow pilot run `e9-pilot-20260918T101300Z-eafa7419`는 28개 response를 기록한 뒤 `incomplete`로 종료됐다.

관찰된 직접 원인은 다음과 같다.

- WSL 할당 RAM: 약 `7.6 GiB`
- WSL swap: `2.0 GiB`
- Ollama service memory peak: 약 `6.4 GiB`
- Ollama service swap peak: 약 `936.4 MiB`
- 종료 원인: Linux OOM killer가 `llama-server`를 강제 종료
- runner reason: `unexpected_runner_exception:RemoteDisconnected`

중단 run의 `llm_responses.partial.jsonl`, `runner_status.json`, `run_manifest.json`, `bundle_validation.json`은 삭제하지 않는다. 이 run은 공식 pilot evaluation 대상으로 사용하지 않으며 같은 `run_id`로 재개하지 않는다.

복구 방식은 WSL 2 VM 자원 한도를 다음과 같이 확장하는 것으로 확정한다.

```text
WSL memory: 12GB
WSL swap:   8GB
```

다음 E9 통제 변수는 변경하지 않는다.

- Ollama version과 model artifact
- model quantization
- feature schema
- prompt
- output schema
- `num_ctx`
- temperature, seed, timeout 및 나머지 generation setting

검토했지만 이번 복구에 채택하지 않은 대안은 다음과 같다.

- Flash Attention과 quantized KV cache: memory 사용량을 줄일 수 있으나 cache precision/runtime 조건을 변경한다.
- `num_ctx` 축소: memory 사용량을 줄일 수 있으나 확정된 generation setting을 변경한다.
- in-place resume 또는 chunked execution: 현재 partial/resume 정책과 runner의 row-count 계약을 변경한다.

WSL 재시작 후 실제 RAM/swap, Ollama model metadata, GPU 접근, 테스트 통과 여부를 재확인한다. 재실행은 같은 source 조건으로 새 bundle과 새 `run_id`를 생성해 처음부터 수행한다.

이렇게 확정하는 이유는 첫 실패가 model/prompt/schema의 문제가 아니라 WSL 기본 memory 한도에서 발생한 운영 환경 OOM이며, WSL 자원 확장은 현재 E9의 모델·입력·generation 계약을 그대로 유지하는 가장 작은 복구이기 때문이다.

### D-EXP009-022 — Current Environment Handoff After the 100-Flow Pilot

현재 환경에서는 EXP-009 full E9 run을 실행하지 않는다.

성공한 100-flow pilot `e9-pilot-20260918T105813Z-5179ebd6`까지의 코드, 설정, 테스트, 결정 기록과 artifact를 보존하고, full run은 새로운 실행 환경에서 별도로 준비한다.

현재 환경에서 보존할 실행 이력은 다음과 같다.

- 1-flow smoke run: `e9-pilot-20260918T101014Z-2d96f10f`, completed
- 첫 100-flow run: `e9-pilot-20260918T101300Z-eafa7419`, WSL OOM으로 28행에서 incomplete
- 복구 후 100-flow pilot: `e9-pilot-20260918T105813Z-5179ebd6`, completed

성공 pilot의 기술 결과는 다음과 같다.

- response rows: `100/100`
- schema valid rate: `100%`
- timeout/generation failure/parsing failure: `0`
- fallback rate: `3%`
- latency p50/p95: 약 `2.86초 / 9.41초`
- OOM 또는 runner crash: `0`

Pilot 성능 수치는 readiness 점검용으로만 보존하며 EXP-009 성능 결론으로 사용하지 않는다.

Git에는 코드, 설정, 테스트, 문서, dependency 목록, 외부 artifact checksum을 커밋한다. `.gitignore` 대상인 다음 항목은 Git에 강제로 추가하지 않고 별도로 이관한다.

- `data/`
- `results/`
- exact Ollama model store

`.venv/`는 이관하지 않고 새 환경에서 `requirement.txt`로 재생성한다.

새 환경의 GPU, VRAM, system RAM, swap, OS, driver가 현재 환경과 달라질 수 있음을 허용한다. 단, full run 전에 실제 환경을 새 environment record와 run manifest에 기록해야 하며, model artifact, prompt, feature schema, output schema, source population, generation setting은 별도 결정 없이 변경하지 않는다.

이렇게 확정하는 이유는 현재 환경에서 예상 약 6.5시간의 monolithic full run을 안정적으로 수행하기 어렵고, pilot까지 확보한 재현 가능한 코드와 실패·성공 이력을 잃지 않은 채 더 적합한 환경으로 넘기는 것이 EXP-009의 연구 무결성을 보존하기 때문이다.

### D-EXP009-023 — Full E9 Run 완료와 결과

새 실행 환경(`LAPTOP1324`, RTX 3050 Laptop GPU 4GB, `docs/environment-fullrun-2026-09-19.md`)에서 EXP-009 full E9 run을 실행했다. 실행 조건은 `experiments/EXP-009-full-run.md`에서 확정한 그대로다.

- run_id: `e9-pilot-20260919T115818Z-768f24f8`
- source: `EXP-007` / `group_seed42` / `target_abstention_rate=0.01`
- 대상 행 수: 4,816 (abstained set 전체, 표본 추출 없음)
- 실행 시각: `2026-09-19T11:59:52Z` ~ `2026-09-19T21:46:43Z` (약 9.78시간)
- 저장 위치: `results/EXP-009/e9-pilot-20260919T115818Z-768f24f8/`

**기술 성공 기준(D-EXP009-018)을 모두 충족했다.**

- `run_status`: `completed`, 4,816/4,816 행 확보, 모든 `input_index`에 정확히 하나의 응답
- schema valid rate: 99.88% (4,810/4,816)
- timeout rate: 0.12% (6건, 전부 timeout), 그 외 generation_failure 0건
- OOM/crash: 0건
- latency: p50 3.84초, p95 24.81초

**주 비교(`gate_forced` vs `end_to_end`) 결과**

| | gate_forced | end_to_end |
|---|---|---|
| error_rate | 0.62% (30/4816) | 9.18% (442/4816) |
| precision | 0.965 | 0.926 |
| recall | 0.994 | 0.418 |
| F1 | 0.979 | 0.576 |

전이표:

```text
gate_correct_final_correct : 4350
gate_correct_final_error   : 436
gate_error_final_correct   : 24
gate_error_final_error     : 6
```

**결과 해석**

이 결과는 EXP-009의 연구 질문("Layer 1이 abstain한 flow에서 local LLM-only verifier가 Gate forced decision보다 end-to-end 오류를 줄일 수 있는가?")에 **아니오**로 답한다.

이 조건(zero-shot, RAG 없음, `gemma:7b-instruct` Q4_0, `e9-v1` prompt)에서 LLM override는 Gate 오류 24건을 교정했지만 Gate 정답 436건을 오답으로 바꿨다. `end_to_end` error rate(9.18%)는 `gate_forced`(0.62%)보다 약 14.7배 높다. `end_to_end` recall 41.8%는 실제 공격의 58.2%를 최종적으로 놓친다는 뜻이다. 100-flow pilot에서 관찰된 위험 신호(`gate_correct_final_error : gate_error_final_correct` = 8:1)가 노이즈가 아니라 전체 모집단(4,816행)에서 재현됐으며, 오히려 더 뚜렷하다(18:1).

이 결과는 성능 우위를 입증하는 결과가 아니라 **부정적(negative) baseline**이다. `AGENTS.md` 20절 원칙에 따라 있는 그대로 기록하며, 이 결과를 뒤집기 위해 prompt나 few-shot을 사후 조정하지 않는다. 조정이 필요하다면 별도 experiment version으로 관리한다. 이 수치가 향후 E10(RAG 추가) 비교의 기준선이 된다.

전체 지표 정본은 `results/EXP-009/e9-pilot-20260919T115818Z-768f24f8/evaluation/metrics.json`이며, 요약은 `index.md` 13절에도 있다.

이렇게 확정하는 이유는 EXP-009의 1차 목적(D-EXP009-011: 재현 가능한 E9 baseline 구축)이 pilot이 아니라 full run에서 달성됐고, 그 결과가 향후 E10 비교의 기준점이 되므로 해석을 덧붙이지 않고 사실 그대로 결정 기록에 남겨야 하기 때문이다.

## 5. EXP-009가 답하지 않는 것

EXP-009는 다음을 답하지 않는다.

1. RAG가 LLM-only보다 좋은가.
2. MITRE ATT&CK 또는 CTI evidence가 decision groundedness를 높이는가.
3. LLM이 attack type을 정확히 분류하는가.
4. LLM confidence가 calibrated probability로 쓸 수 있는가.
5. zero-day 또는 leave-one-attack-out generalization이 가능한가.
6. prompt 최적화를 통해 full test 성능을 최대화할 수 있는가.

이 질문들은 E10 또는 별도 후속 실험에서 다룬다.

## 6. 현재 미결 사항

EXP-009 계획 확정 단계에서 다루기로 한 항목은 대부분 확정되었다.

확정 완료:

1. 실제 Layer 1 source artifact 경로
   - predictions parquet
   - metrics json
   - source CSV data directory
2. Pilot source 조건
   - source experiment ID
   - method
   - target abstention rate
   - confidence threshold source
3. Pilot 결과 디렉토리 convention
   - export
   - package
   - checks
   - runner output
   - evaluation output
4. 최소 테스트 스위트 범위
   - schema snapshot validation
   - prompt validation
   - strict parser
   - evaluator fallback
   - transfer bundle validation
5. 1-flow smoke test 방식
6. 100-flow pilot 실행 gate
7. Pilot evaluation 기준
8. Full run 진입 기준
9. Partial/resume 정책

10. Full run result directory convention
    - `results/EXP-009/<run_id>/`로 확정, pilot 구조(`export/{transfer,local}`, `checks`, `returned`, `evaluation`)와 동일 (`experiments/EXP-009-full-run.md`, D-EXP009-023).
11. Full E9 run 실행과 결과
    - `e9-pilot-20260919T115818Z-768f24f8` 완료, evaluated. 결과는 D-EXP009-023.

남은 미결: 없음. EXP-009의 1차 목적(재현 가능한 E9 baseline 구축)은 D-EXP009-023로 달성됐다.

## 7. 다음 작업 순서

EXP-009 실행 자체는 D-EXP009-023로 완료됐다. 이후 후보 작업(우선순위 미정, 별도 확정 필요):

1. full run 442건 오류(특히 `gate_correct_final_error` 436건)에 대한 error analysis — 어떤 feature 패턴/attack class에서 override가 집중되는지
2. E10(RAG 추가) 착수 여부 결정 — `AGENTS.md` 25절 P10, 27절 "Definition of E10 Ready" 체크리스트 검토
3. few-shot 또는 prompt 개정을 별도 experiment version으로 시도할지 결정 (현재 결과를 덮어쓰지 않음)

완료된 이력(참고용):

1. 최소 테스트 스위트 작성
2. `pytest -q` 통과 확인
3. 1-flow smoke bundle export
4. 1-flow smoke bundle validation
5. 1-flow Ollama smoke test
6. 100-flow export dry run
7. 100-flow transfer bundle validation
8. 100-flow pilot
9. pilot evaluation
10. full run 진입 여부 결정 → 진입
11. full E9 run 실행 → 완료, evaluated (D-EXP009-023)
