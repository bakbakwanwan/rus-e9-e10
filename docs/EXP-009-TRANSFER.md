# EXP-009 Environment Transfer Guide

> 기준일: 2026-09-18  
> 범위: EXP-009 100-flow pilot 완료 시점의 Git 및 비-Git artifact 이관

## 1. 현재 보존 지점

현재 환경에서는 full E9 run을 실행하지 않았다.

| 구분 | run ID | 상태 | 보존 위치 |
|---|---|---|---|
| 1-flow smoke | `e9-pilot-20260918T101014Z-2d96f10f` | completed | `results/pilots/e9-json-llm/` |
| 첫 100-flow run | `e9-pilot-20260918T101300Z-eafa7419` | OOM, 28/100 incomplete | `results/pilots/e9-json-llm/` |
| 복구 후 100-flow pilot | `e9-pilot-20260918T105813Z-5179ebd6` | completed, evaluated | `results/pilots/e9-json-llm/` |

성공 pilot의 기준 metrics는 다음 파일에 있다.

```text
results/pilots/e9-json-llm/e9-pilot-20260918T105813Z-5179ebd6/evaluation/metrics.json
```

## 2. Git으로 이동하는 항목

다음은 repository clone/pull로 복원한다.

- `configs/`
- `docs/`
- `scripts/`
- `src/`
- `tests/`
- `index.md`
- `requirement.txt`
- `.gitignore`
- `AGENTS.md`

`.venv/`는 복사하지 않는다.

## 3. 직접 이동해야 하는 항목

### 3.1 Data

```text
data/                                             약 1.1GB
├── CICIDS2017_improved_2022ver/                  원본 5일 CSV
└── pilots/e9-json-llm/e9-pilot-20260918T051044Z-fc63bbad/
    └── export/group_seed42.parquet, metrics.json 및 source bundle
```

가장 안전한 방법은 `data/` 전체를 새 repository root의 `data/`로 복사하는 것이다.

### 3.2 Results

```text
results/pilots/e9-json-llm/                       약 888KB
```

성공 결과만 고르지 말고 디렉토리 전체를 복사한다. OOM 실패 run의 partial response도 연구 기록이다.

### 3.3 Exact Ollama Model

```text
/usr/share/ollama/.ollama/models/                 약 4.7GB
model tag: gemma:7b-instruct
model ID: a72c7f4d0a15
base blob SHA-256: ef311de6af9db043d51ca4b1e766c28e0a1ac41d60420fed5e001dc470c64b77
```

같은 tag를 새로 pull하면 registry의 대상이 바뀔 가능성이 있으므로, 동일 artifact가 필요하면 model store를 직접 보존한다. 새 환경에 복사할 때는 Ollama 서비스를 중지하고 파일 소유권을 새 환경의 Ollama service user에 맞춰야 한다.

## 4. 복사 예시

`<TRANSFER_ROOT>`는 외장 디스크, 공유 스토리지 또는 새 환경에서 접근 가능한 경로로 교체한다.

현재 환경에서:

```bash
rsync -a --info=progress2 /home/user1/RUS-EXP-009/data/ <TRANSFER_ROOT>/data/
rsync -a --info=progress2 /home/user1/RUS-EXP-009/results/ <TRANSFER_ROOT>/results/
sudo rsync -a --info=progress2 /usr/share/ollama/.ollama/models/ <TRANSFER_ROOT>/ollama-models/
```

새 환경의 repository root에서:

```bash
rsync -a --info=progress2 <TRANSFER_ROOT>/data/ ./data/
rsync -a --info=progress2 <TRANSFER_ROOT>/results/ ./results/
```

Ollama model store 복원은 새 환경의 설치 방식과 service user를 확인한 뒤 수행한다. 경로와 user가 현재 환경과 같을 때의 예시는 다음과 같다.

```bash
sudo systemctl stop ollama
sudo rsync -a --info=progress2 <TRANSFER_ROOT>/ollama-models/ /usr/share/ollama/.ollama/models/
sudo chown -R ollama:ollama /usr/share/ollama/.ollama/models
sudo systemctl start ollama
```

## 5. 무결성 검증

Repository root에서 data와 results를 검증한다.

```bash
sha256sum -c configs/artifacts/exp009_data_results.sha256
```

Ollama model store를 검증한다.

```bash
cd /usr/share/ollama/.ollama/models
sha256sum -c /path/to/repository/configs/artifacts/exp009_ollama_model.sha256
```

## 6. 새 환경 Bootstrap

```bash
git clone https://github.com/bakbakwanwan/rus-e9-e10.git
cd rus-e9-e10
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirement.txt
python -m pytest -q
```

그다음 data/results/model을 복사하고 SHA-256을 검증한다.

## 7. Full Run 전 필수 재확인

- 새 환경의 OS, Python, GPU, VRAM, RAM, swap, driver를 `docs/environment.md`와 구분되는 새 기록으로 남긴다.
- Ollama version `0.34.1`과 exact model metadata를 확인한다.
- `ollama list`, `ollama ps`, `nvidia-smi`를 확인한다.
- data/results/model checksum을 모두 통과시킨다.
- `pytest -q`를 통과시킨다.
- full-run source population과 result directory convention을 확정한다.
- 장시간 실행 구조는 아직 확정하지 않았다. monolithic/chunked/resume 중 하나를 별도 결정한다.
- 공식 full run 직전 worktree가 clean인지 확인한다.

현재 환경의 `.wslconfig`는 `memory=12GB`, `swap=8GB`였지만 새 환경에 그대로 강제하지 않는다. 새 hardware에 맞게 정하고 실제 값을 기록한다.
