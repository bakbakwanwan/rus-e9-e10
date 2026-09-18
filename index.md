# RUS E9 Repository Index

> 작성 시점: 2026-09-18  
> 목적: 현재 디렉토리에 추가된 코드와 문서의 위치, 역할, E9 맥락을 빠르게 찾기 위한 작업용 색인이다.  
> 주의: 이 색인은 현재 파일 상태를 설명한다. 연구 설계의 새 확정 사항을 만들지 않는다.

## 1. 현재 초점

이 저장소의 현재 구현 초점은 **E9: abstained network flow에 대한 local LLM-only verification pilot**이다.

핵심 비교는 동일한 Layer 1 유보 flow 집합에 대해 다음 둘을 비교하는 것이다.

```text
Gate Forced Decision
vs
Local LLM-only Verification
```

현재 E9 구현 범위는 RAG, CTI, MITRE ATT&CK, CVE, TreeSHAP를 포함하지 않는다. E10은 E9가 안정화된 뒤 retrieval evidence를 추가하는 후속 확장으로 남아 있다.

## 2. E9 현재 계약 요약

현재 문서와 코드가 가리키는 첫 E9 pilot 계약은 다음과 같다.

| 항목 | 현재 값 / 규칙 | 위치 |
|---|---|---|
| 입력 대상 | Layer 1이 abstain한 test flow | `docs/e9_json_llm_verification_decisions.md` |
| LLM 입력 | `payload.flow_features` 아래 59개 feature만 전달 | `configs/llm/e9_input_feature_schema.json` |
| 금지 입력 | `day`, `id`, `Label`, `binary_label`, `is_error`, `p_attack`, `confidence`, `predicted_label`, `abstained` 등 | `src/abstention_experiment/layer2_export.py` |
| Prompt version | `e9-v1` | `configs/llm/e9_prompt_v1.json` |
| 출력 schema | `{ "decision": "BENIGN | ATTACK | INDETERMINATE" }` 단일 key JSON | `src/abstention_experiment/layer2_runtime.py` |
| 모델 계약 | Ollama `gemma:7b-instruct`, Q4_0, `num_ctx=4096`, `temperature=0`, `seed=42` | `src/abstention_experiment/layer2_runtime.py` |
| pilot 크기 | 100 flows completed | `docs/EXP-009-TRANSFER.md` |
| fallback | `INDETERMINATE` 또는 generation failure는 Gate forced decision 사용 | `src/abstention_experiment/layer2_evaluation.py` |
| 공식 평가 입력 | completed `llm_responses.jsonl`만 허용 | `src/abstention_experiment/layer2_evaluation.py` |

## 3. 디렉토리 지도

```text
.
├── AGENTS.md
├── index.md
├── requirement.txt
├── configs/
│   └── llm/
├── docs/
├── scripts/
│   └── Layer2-E9-Pilot/
├── src/
│   └── abstention_experiment/
├── data/
├── results/
├── logs/
└── prompts/
```

## 4. 루트 파일

| 파일 | 역할 |
|---|---|
| `AGENTS.md` | 프로젝트 작업 규칙, E9/E10 연구 제약, 실행 환경 기대값, 재현성 원칙을 담은 지시문이다. |
| `index.md` | 현재 저장소 파일과 E9 맥락을 찾기 위한 색인이다. |
| `requirement.txt` | 현재 Python 의존성 목록이다. 파일명이 일반적인 `requirements.txt`가 아니라 `requirement.txt`임에 주의한다. |
| `.gitignore` | `.venv/`, `data/*`, `results/*`, `logs/*` 등 로컬 환경과 산출물을 git에서 제외한다. |

## 5. 문서

| 파일 | 역할 |
|---|---|
| `docs/RESEARCH_PLAN_E9_E10.md` | RUS hybrid IDS의 전체 연구 계획 초안이다. Layer 1, E9, E10의 연구 질문과 비교 구도를 설명한다. |
| `docs/EXP-009-DECISIONS.MD` | EXP-009가 확인하려는 것, 궁극적 도달점, 현재 결정 사항을 기록한다. |
| `docs/EXP-009-PLAN.MD` | EXP-009 E9 pilot부터 full run readiness review까지의 실행 계획을 정리한다. |
| `docs/e9_json_llm_verification_decisions.md` | E9 JSON LLM verification의 가장 구체적인 결정 기록이다. 입력 계약, 직렬화, prompt, output schema, runner, evaluator, transfer bundle 계약을 다룬다. |
| `docs/glossary.md` | 프로젝트 용어와 코드 식별자의 정의처다. `abstention`, `confidence_threshold`, `p_attack`, `binary_label` 등 주요 용어를 확인한다. |
| `docs/git-policy.md` | git 운영 정책이다. 실험 실행 전 clean worktree, 결과 불변성, 커밋 형식, 금지 명령을 정의한다. |
| `docs/environment.md` | 현재 작업 세션에서 확인한 실행 환경 기록이다. 설계상 기대 환경과 실제 관찰값을 분리한다. |
| `docs/EXP-009-TRANSFER.md` | Git과 별도 이관 artifact, checksum 검증, 새 환경 bootstrap을 한 번에 정리한다. |

## 6. 설정 파일

| 파일 | 역할 |
|---|---|
| `configs/llm/e9_input_feature_schema.json` | Layer 2 E9 입력 feature schema snapshot이다. 59개 feature 순서, `Protocol` mapping, NaN/Inf 직렬화 규칙, prompt 제외 필드를 정의한다. |
| `configs/llm/e9_prompt_v1.json` | `e9-v1` prompt asset이다. system prompt, user template, `{{FLOW_FEATURES_JSON}}` placeholder를 정의한다. |
| `configs/artifacts/exp009_data_results.sha256` | Git에서 제외된 EXP-009 data/results 핵심 artifact checksum이다. |
| `configs/artifacts/exp009_ollama_model.sha256` | exact Ollama model blob과 manifest checksum이다. |

주의: `e9_input_feature_schema.json`은 `configs/features_whitelist.json`의 SHA-256을 참조한다. 현재 두 파일의 SHA-256 관계는 일치한다.

## 7. 구현 코드

현재 E9 pilot 구현은 import 가능한 Python package인 `src/abstention_experiment/` 아래에 있다.

| 파일 | 역할 |
|---|---|
| `src/abstention_experiment/__init__.py` | `abstention_experiment` package marker다. |
| `src/abstention_experiment/data.py` | canonical day 순서, protocol mapping, file SHA-256 계산 유틸리티를 제공한다. |
| `src/abstention_experiment/layer2_common.py` | run ID 생성/검증, JSON/JSONL read/write, bundle-relative path 검증 등 공통 유틸리티를 제공한다. |
| `src/abstention_experiment/layer2_export.py` | Layer 1 예측 산출물에서 abstained rows를 선택하고, label-free `llm_inputs.jsonl`과 local `evaluation_sidecar.jsonl`을 생성한다. |
| `src/abstention_experiment/layer2_package.py` | export manifest의 transfer 허용 목록만 ZIP으로 묶고 package manifest를 생성한다. |
| `src/abstention_experiment/layer2_runtime.py` | transfer bundle 검증, prompt rendering, Ollama HTTP 호출, strict parser, partial response 보존, runner manifest/status 생성을 담당한다. |
| `src/abstention_experiment/layer2_evaluation.py` | completed response와 local sidecar를 결합해 `gate_forced`, `llm_valid_only`, `end_to_end` 지표와 전이표를 산출한다. |

관찰된 주의사항:

- CLI scripts는 `REPO_ROOT/src`를 `sys.path`에 추가한 뒤 `abstention_experiment.*`를 import한다.
- 이전 `src/Layer2-E9-Pilot/` 경로는 import 가능한 package가 아니므로 코드 위치로 사용하지 않는다.

## 8. CLI 스크립트

현재 E9 pilot 실행용 wrapper는 `scripts/Layer2-E9-Pilot/` 아래에 있다.

| 파일 | 역할 |
|---|---|
| `scripts/Layer2-E9-Pilot/export_abstained_flows.py` | predictions, metrics, source CSV에서 E9 transfer bundle과 local sidecar를 export한다. |
| `scripts/Layer2-E9-Pilot/validate_e9_bundle.py` | LLM 환경에서 transfer bundle을 추론 전에 검증한다. |
| `scripts/Layer2-E9-Pilot/run_e9_ollama.py` | local Ollama를 통해 strict E9 JSON classification을 실행한다. |
| `scripts/Layer2-E9-Pilot/evaluate_e9_run.py` | completed LLM response와 evaluation sidecar를 결합해 metrics를 생성한다. |
| `scripts/Layer2-E9-Pilot/package_e9_transfer.py` | label-free transfer member만 ZIP archive로 포장한다. |

## 9. 데이터와 산출물 디렉토리

| 경로 | 현재 용도 |
|---|---|
| `data/` | CICIDS2017 CSV와 EXP-007 Layer 1 source artifact가 있다. Git에서 제외되므로 별도 이관한다. |
| `results/` | smoke, OOM 실패 pilot, 성공 100-flow pilot artifact가 있다. Git에서 제외되므로 전체를 별도 이관한다. |
| `logs/` | 실행 로그 위치다. `.gitignore`상 내용물은 기본적으로 추적하지 않는다. |
| `prompts/` | prompt 관련 자산 위치로 보이나, 현재 파일은 없다. 현재 E9 prompt asset은 `configs/llm/e9_prompt_v1.json`에 있다. |

## 10. E9 실행 흐름

현재 코드 기준 의도된 흐름은 다음과 같다.

```text
Layer 1 predictions + metrics + source CSV
  -> export_abstained_flows.py
  -> export/
       transfer/llm_inputs.jsonl
       transfer/e9_input_feature_schema.json
       transfer/e9_prompt_v1.json
       manifest.json
       local/evaluation_sidecar.jsonl
  -> package_e9_transfer.py
  -> LLM environment
  -> validate_e9_bundle.py
  -> run_e9_ollama.py
  -> run_manifest.json + runner_status.json + llm_responses.jsonl
  -> Layer 1/evaluation environment
  -> evaluate_e9_run.py
  -> evaluation_records.jsonl + metrics.json + evaluation_manifest.json
```

## 11. 현재 상태 체크

작성 시점의 빠른 상태는 다음과 같다.

| 항목 | 상태 |
|---|---|
| Git HEAD | 이관 준비 커밋 전 `12c00f1`; 최신 값은 `git rev-parse HEAD`로 확인한다. |
| Worktree | 이관 커밋과 push 후 clean 상태로 전환한다. |
| 테스트 | `17 passed` |
| 1-flow smoke | completed |
| 100-flow pilot | completed, evaluated |
| Full E9 run | 현재 환경에서는 미실행, 새 환경으로 이관 |

## 12. 다음에 보기 좋은 순서

1. E9 연구 맥락: `docs/e9_json_llm_verification_decisions.md`
2. 입력 feature와 leakage 방지: `configs/llm/e9_input_feature_schema.json`
3. prompt/output 계약: `configs/llm/e9_prompt_v1.json`, `src/abstention_experiment/layer2_runtime.py`
4. export와 sidecar 분리: `src/abstention_experiment/layer2_export.py`
5. evaluator fallback/metrics: `src/abstention_experiment/layer2_evaluation.py`
6. 실행 환경 기록: `docs/environment.md`
