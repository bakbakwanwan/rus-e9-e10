# EXP-009 Plan

> 상태: 실행 계획 확정  
> 작성일: 2026-09-18  
> 기준 결정 문서: `docs/EXP-009-DECISIONS.MD`  
> 범위: E9 local LLM-only verification pilot부터 full E9 진입 판단까지

## 1. 목적

EXP-009의 목적은 **Layer 1이 abstain한 network flow에 대해 local LLM-only verifier가 Gate forced decision보다 end-to-end 오류를 줄일 수 있는지 평가 가능한 baseline을 만드는 것**이다.

이 계획은 바로 full run을 실행하기 위한 문서가 아니다.  
먼저 100-flow pilot으로 pipeline, logging, validation, evaluator가 안정적인지 확인하고, 그 결과를 바탕으로 full E9 진입 여부를 결정한다.

## 2. 핵심 질문

EXP-009가 최종적으로 답하려는 질문은 다음이다.

```text
같은 abstained test flow 집합에서
Gate forced decision과
LLM fallback 포함 end-to-end decision 중
어느 쪽이 오류를 덜 내는가?
```

주 비교는 다음으로 고정한다.

```text
gate_forced
vs
end_to_end
```

`llm_valid_only`는 보조 분석으로만 사용한다.

## 3. 실험 범위

### 포함

- Layer 1 abstained flow export
- 59-feature label-free JSON serialization
- transfer bundle validation
- local Ollama LLM-only inference
- strict JSON parsing
- fallback 포함 end-to-end evaluation
- Gate forced vs LLM end-to-end 비교 가능 artifact 생성

### 제외

- RAG
- MITRE ATT&CK / CTI / CVE evidence retrieval
- attack type classification
- LLM confidence analysis
- prompt optimization against full test set
- zero-day 또는 LOAO 주장

## 4. 고정 조건

EXP-009 pilot에서 아래 조건은 고정한다.

| 항목 | 값 |
|---|---|
| Prompt version | `e9-v1` |
| Feature schema | `e9-input-v1` |
| Feature count | 59 |
| Output schema | `{ "decision": "BENIGN | ATTACK | INDETERMINATE" }` |
| Model tag | `gemma:7b-instruct` |
| Quantization | `Q4_0` |
| `num_ctx` | `4096` |
| `temperature` | `0` |
| `top_p` | `1.0` |
| `num_predict` | `64` |
| `seed` | `42` |
| `concurrency` | `1` |
| `timeout_seconds` | `60` |
| Retry | 없음 |
| RAG | 없음 |

변경이 필요한 경우 새 run/config/version으로 기록하고 기존 결과를 덮어쓰지 않는다.

## 5. 기본 Pilot Source

100-flow pilot의 기본 source 조건은 다음으로 둔다.

| 항목 | 값 |
|---|---|
| source experiment | `EXP-007` |
| method | `group_seed42` |
| target abstention rate | `0.01` |
| sample size | `100` |
| selection rule | selected abstained set에서 `sha256(day\0id)` 오름차순 첫 100행 |

단, 실제 파일 경로는 실행 환경마다 다를 수 있으므로 계획 문서에 고정하지 않는다. 실행 전 아래 값을 명시적으로 채워야 한다.

- predictions parquet path
- metrics json path
- source CSV data directory
- output root

파일명이나 경로만으로 source를 신뢰하지 않고, manifest의 source metadata와 SHA-256으로 검증한다.

## 6. 결과 디렉토리 Convention

Pilot 결과는 공식 full EXP 결과와 분리한다.

권장 구조:

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

중단 run은 `returned/llm_responses.partial.jsonl`과 `runner_status.json`을 보존하고, 공식 evaluation을 생성하지 않는다.

## 7. 실행 단계

### Phase 0 — Preflight

목표: 실험을 시작할 수 있는 최소 환경인지 확인한다.

확인 항목:

- `git status --short`
- Python venv
- `pytest -q`
- package import
- feature whitelist SHA
- Ollama binary/server/model
- GPU 확인 가능 여부

권장 명령:

```bash
cd /home/user1/RUS-EXP-009
source .venv/bin/activate
python -m pytest -q
PYTHONPATH=src python -c "from abstention_experiment.layer2_common import new_pilot_run_id; print(new_pilot_run_id())"
sha256sum configs/features_whitelist.json
which ollama
ollama list
nvidia-smi
```

진입 기준:

- `pytest -q` 통과
- package import 통과
- `configs/features_whitelist.json` hash가 `configs/llm/e9_input_feature_schema.json`의 source hash와 일치
- 공식 실험 실행 전에는 clean worktree 확보

현재 상태 메모:

- pytest는 설치되었지만 아직 테스트 파일이 없어 `no tests ran` 상태였다.
- 최소 테스트 스위트 추가가 Phase 1의 선행 작업이다.

### Phase 1 — Minimal Test Suite

목표: 실험 실행 전에 깨지면 안 되는 계약을 테스트로 고정한다.

추가할 테스트 범위:

- schema snapshot validation
- prompt asset validation
- prompt rendering에 forbidden field가 들어가지 않는지 확인
- strict parser 정상/`INDETERMINATE`/schema violation/failure 처리
- evaluator fallback logic
- transfer bundle validator 정상/실패 케이스

권장 테스트 파일:

```text
tests/
├── test_e9_schema_prompt.py
├── test_e9_runtime_parser.py
├── test_e9_bundle_validation.py
└── test_e9_evaluation.py
```

완료 기준:

- `python -m pytest -q` 통과
- 테스트가 외부 Ollama 서버를 요구하지 않음
- 테스트가 실제 대용량 dataset을 요구하지 않음

### Phase 2 — Export Dry Run

목표: Layer 1 artifact에서 100-flow label-free transfer bundle을 생성한다.

필수 입력:

```text
PREDICTIONS_PARQUET=data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/group_seed42.parquet
METRICS_JSON=data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/metrics.json
SOURCE_DATA_DIR=data/CICIDS2017_improved_2022ver
OUTPUT_ROOT=results/pilots/e9-json-llm
METHOD=group_seed42
TARGET_RATE=0.01
SAMPLE_SIZE=100
```

확인된 입력 artifact:

| 항목 | 경로 / 값 |
|---|---|
| predictions parquet | `data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/group_seed42.parquet` |
| predictions SHA-256 | `e27f1a5edbd305605923685fe4f9203f9ed1f6c269b6f0169cf2d4d1634898dc` |
| metrics json | `data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/metrics.json` |
| metrics SHA-256 | `122093a73f4d4b71c0173d5e72c23405e2010e4db129534c5ca1d794a0da5fb9` |
| source CSV data dir | `data/CICIDS2017_improved_2022ver` |
| parquet rows | `652829` |
| source experiment | `EXP-007` |
| method | `group_seed42` |
| target abstention rate | `0.01` |
| confidence threshold | `0.9993377811093735` |
| source days | `friday`, `monday`, `thursday`, `tuesday`, `wednesday` |

`SOURCE_DATA_DIR`의 5개 CSV SHA-256은 `METRICS_JSON`의 `dataset` 항목과 일치해야 한다. 2026-09-18 확인 결과 일치했다.

권장 명령 형태:

```bash
python scripts/Layer2-E9-Pilot/export_abstained_flows.py \
  --predictions "$PREDICTIONS_PARQUET" \
  --metrics "$METRICS_JSON" \
  --data-dir "$SOURCE_DATA_DIR" \
  --method group_seed42 \
  --target-rate 0.01 \
  --sample-size 100 \
  --output-root results/pilots/e9-json-llm
```

성공 기준:

- `export/manifest.json` 생성
- `export/transfer/llm_inputs.jsonl` 생성
- `export/local/evaluation_sidecar.jsonl` 생성
- `llm_inputs.jsonl`에 forbidden field 없음
- export manifest에 source metadata와 artifact SHA-256 기록

실패 시:

- 출력 디렉토리를 덮어쓰지 않는다.
- 원인 수정 후 새 `run_id`로 재실행한다.

### Phase 3 — Transfer Package

목표: LLM 환경으로 넘길 label-free artifact만 package한다.

권장 명령 형태:

```bash
python scripts/Layer2-E9-Pilot/package_e9_transfer.py \
  --export-dir results/pilots/e9-json-llm/<run_id>/export \
  --archive results/pilots/e9-json-llm/<run_id>/package/<run_id>.zip
```

성공 기준:

- ZIP에 `local/evaluation_sidecar.jsonl`이 포함되지 않음
- package manifest에 archive SHA-256과 member list 기록

### Phase 4 — Bundle Validation Preflight

목표: LLM 호출 전에 transfer bundle이 계약을 만족하는지 검증한다.

권장 명령 형태:

```bash
python scripts/Layer2-E9-Pilot/validate_e9_bundle.py \
  --bundle-dir results/pilots/e9-json-llm/<run_id>/export \
  --output results/pilots/e9-json-llm/<run_id>/checks/bundle_validation.preflight.json
```

성공 기준:

- `passed=true`
- manifest, input JSONL, feature schema, prompt SHA-256 일치
- `input_index`가 0부터 연속
- feature order가 schema와 일치
- forbidden field 없음

실패 시:

- Ollama runner를 시작하지 않는다.
- validation artifact를 보존한다.

주의:

- `returned/`는 runner output directory로 비워 둔다.
- 현재 runner는 `output_dir`가 이미 있으면 실패하며, 실행 중 `returned/bundle_validation.json`을 다시 생성한다.

### Phase 5 — 1-flow Ollama Smoke Test

목표: 100-flow pilot 전에 Ollama/model/structured output 계약을 확인한다.

권장 방식:

- 별도 1-row test bundle을 만들거나, 100-flow bundle을 사용하되 runner 입력 제한 기능이 없다면 아직 runner를 직접 수정하지 않는다.
- runner 수정 없이 진행해야 한다면 Phase 6의 100-flow pilot 전에 Ollama metadata만 별도로 확인한다.

확인 항목:

- Ollama server reachable
- `gemma:7b-instruct` installed
- metadata가 code contract와 일치
- response content가 strict JSON parser를 통과

결정 필요:

- 현재 runner에 `--limit 1` 기능을 추가할지 여부
- 추가한다면 실험 조건 변경이 아니라 smoke-test 편의 기능으로 문서화한다.

### Phase 6 — 100-flow Pilot Run

목표: 100개 flow에서 E9 LLM-only pipeline의 운영 가능성을 확인한다.

권장 명령 형태:

```bash
python scripts/Layer2-E9-Pilot/run_e9_ollama.py \
  --bundle-dir results/pilots/e9-json-llm/<run_id>/export \
  --output-dir results/pilots/e9-json-llm/<run_id>/returned \
  --run-id <run_id>
```

성공 기준:

- `run_manifest.json` 생성
- `bundle_validation.json` 생성
- `runner_status.json`의 `run_status=completed`
- `llm_responses.jsonl` 생성
- 모든 `input_index`에 정확히 하나의 response row 존재

기술 성공 기준:

- schema valid rate >= 95%
- timeout rate <= 5%
- OOM/crash 0
- latency p50/p95 기록 가능

중단 기준:

- model metadata mismatch
- bundle validation failure
- systemic connection/http/ollama/api failure
- runner unexpected exception

중단 시:

- partial response와 status를 보존한다.
- 같은 output directory에서 재개하지 않는다.
- 새 `run_id`로 재실행한다.

### Phase 7 — Pilot Evaluation

목표: completed response와 local sidecar를 결합해 metrics를 생성한다.

권장 명령 형태:

```bash
python scripts/Layer2-E9-Pilot/evaluate_e9_run.py \
  --export-manifest results/pilots/e9-json-llm/<run_id>/export/manifest.json \
  --evaluation-sidecar results/pilots/e9-json-llm/<run_id>/export/local/evaluation_sidecar.jsonl \
  --run-manifest results/pilots/e9-json-llm/<run_id>/returned/run_manifest.json \
  --runner-status results/pilots/e9-json-llm/<run_id>/returned/runner_status.json \
  --responses results/pilots/e9-json-llm/<run_id>/returned/llm_responses.jsonl \
  --output-dir results/pilots/e9-json-llm/<run_id>/evaluation
```

성공 기준:

- `evaluation_records.jsonl` 생성
- `metrics.json` 생성
- `evaluation_manifest.json` 생성
- `gate_forced`, `llm_valid_only`, `end_to_end`가 분리 산출됨
- transition counts가 산출됨

Pilot 해석 규칙:

- pilot accuracy/F1으로 성능 우위를 주장하지 않는다.
- technical readiness만 판단한다.
- `gate_error_final_correct`와 `gate_correct_final_error`는 full run 전 위험 신호로 검토한다.

### Phase 8 — Full Run Readiness Review

목표: full E9로 넘어갈지 결정한다.

검토 항목:

- JSON schema valid rate
- timeout/generation failure rate
- fallback rate
- latency p50/p95
- malformed output 유형
- LLM override rate
- Gate 정답을 오답으로 바꾸는 전이 수
- runner stability
- GPU/RAM 안정성

Full run 진입 조건:

- Phase 1-7 완료
- pilot이 technical success 기준 충족
- source abstained set과 selection rule 확정
- full run 결과 디렉토리 convention 확정
- partial resume 정책 결정
- git worktree clean

## 8. 지표 계획

### Primary

- `gate_forced.error_count`
- `gate_forced.error_rate`
- `end_to_end.error_count`
- `end_to_end.error_rate`
- `gate_error_final_correct`
- `gate_correct_final_error`

### Secondary

- precision
- recall
- F1
- FPR
- FNR
- confusion matrix counts
- override rate
- fallback rate
- indeterminate rate
- generation failure rate
- timeout rate
- schema valid rate
- latency p50/p95

### 보조 분석

`llm_valid_only`는 유효 LLM 이진 응답만 분모로 하므로 primary comparison으로 사용하지 않는다.

## 9. Artifact Checklist

EXP-009 pilot에서 보존해야 하는 파일:

- `export/manifest.json`
- `export/transfer/llm_inputs.jsonl`
- `export/transfer/e9_input_feature_schema.json`
- `export/transfer/e9_prompt_v1.json`
- `export/local/evaluation_sidecar.jsonl`
- package ZIP
- package manifest
- `returned/bundle_validation.json`
- `checks/bundle_validation.preflight.json`
- `returned/run_manifest.json`
- `returned/runner_status.json`
- `returned/llm_responses.jsonl`
- `evaluation/evaluation_manifest.json`
- `evaluation/evaluation_records.jsonl`
- `evaluation/metrics.json`

중단 run에서는 다음을 보존한다.

- `returned/llm_responses.partial.jsonl`
- `returned/runner_status.json`
- 가능한 경우 `returned/run_manifest.json`
- failure log 또는 terminal output summary

## 10. Open Decisions Before Execution

실행 전에 아래를 확정한다.

| 항목 | 상태 |
|---|---|
| predictions parquet path | 확정: `data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/group_seed42.parquet` |
| metrics json path | 확정: `data/pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/export/metrics.json` |
| source CSV data dir | 확정: `data/CICIDS2017_improved_2022ver` |
| pilot output root | 확정: `results/pilots/e9-json-llm` |
| 1-flow smoke test 방식 | 확정: `sample_size=1` 별도 bundle/run |
| runner `--limit` option 추가 여부 | 확정: 추가하지 않음 |
| full run partial resume policy | 확정: in-place resume 금지, 새 `run_id`로 재실행 |
| full run EXP/result directory | 확정: `results/EXP-009/<run_id>/`, pilot과 동일 내부 구조 (`experiments/EXP-009-full-run.md`) |

## 11. Immediate Next Work — 완료 (2026-09-20)

계획된 작업은 모두 실행됐다.

1. 최소 테스트 스위트 작성 — 완료 (`pytest -q` 17 passed)
2. `pytest -q` 통과 확인 — 완료
3. source artifact 경로 확정 — 완료
4. 100-flow export dry run — 완료
5. bundle validation — 완료
6. Ollama smoke test 방식 결정 — 완료
7. 100-flow pilot 실행 — 완료 (신 환경: `e9-pilot-20260919T113156Z-093066da`)
8. Full E9 run 실행 — 완료 (`e9-pilot-20260919T115818Z-768f24f8`, 4,816/4,816, `docs/EXP-009-DECISIONS.MD` D-EXP009-023)

결과와 해석은 `docs/EXP-009-DECISIONS.MD` D-EXP009-023, 위치 색인은 `index.md` 13절 참조.
