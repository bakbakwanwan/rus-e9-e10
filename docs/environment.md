# Current Experiment Environment

> 작성 시점: 2026-09-18 14:25:26 +09:00  
> 목적: 현재 작업 세션에서 확인한 E9 실험 환경을 기록한다.  
> 주의: 이 문서는 관찰 기록이다. 확인할 수 없는 값은 추정하지 않는다.

## 1. 요약

| 항목 | 현재 관찰값 |
|---|---|
| 작업 경로 | `/home/user1/RUS-EXP-009` |
| 커널 | `Linux DESKTOP-DN39U59 6.18.33.2-microsoft-standard-WSL2` |
| OS | Ubuntu `26.04.1 LTS` |
| Architecture | `x86_64` |
| 기본 `python3` | `/usr/bin/python3` |
| project venv Python | `/home/user1/RUS-EXP-009/.venv/bin/python` |
| Python version | `3.14.4` |
| Ollama binary | `/usr/local/bin/ollama` |
| Ollama version | `0.34.1` |
| Ollama model | `gemma:7b-instruct` (`a72c7f4d0a15`, 9B, Q4_0) |
| GPU | NVIDIA GeForce GTX 1660 Ti |
| VRAM | 6144 MiB |
| WSL memory | 약 11 GiB (`.wslconfig`: 12GB) |
| WSL swap | 8 GiB |
| Git HEAD | `12c00f1` |
| Git worktree | clean 아님 |

## 2. 설계상 기대 환경과 현재 관찰값

`AGENTS.md`의 기대 환경과 현재 관찰값 사이에 차이가 있다.

| 항목 | 기대값 | 현재 관찰값 |
|---|---|---|
| Project root | `~/rus-e9` | `/home/user1/RUS-EXP-009` |
| Execution OS | WSL2 Ubuntu 24.04 | WSL2 Ubuntu 26.04.1 LTS |
| LLM runtime | Ollama | 사용자 WSL shell에서 server/API와 model 확인 |
| GPU | NVIDIA GeForce GTX 1660 Ti | 일치 |
| VRAM | 6 GB | 6144 MiB 확인 |
| Python | project-local virtual environment | `.venv` 존재, Python 3.14.4 |

이 차이는 곧바로 연구 설계 변경을 의미하지 않는다. 실험 manifest에는 실제 실행 환경에서 재확인한 값을 기록해야 한다.

## 3. 실행한 점검 명령과 결과

### Working Directory

```bash
pwd
```

```text
/home/user1/RUS-EXP-009
```

### Kernel

```bash
uname -a
```

```text
Linux DESKTOP-DN39U59 6.18.33.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 18 21:54:43 UTC 2026 x86_64 GNU/Linux
```

### OS Release

```bash
cat /etc/os-release
```

확인된 주요 값:

```text
PRETTY_NAME="Ubuntu 26.04.1 LTS"
VERSION_ID="26.04"
VERSION_CODENAME=resolute
```

### Python

```bash
which python3
python3 -c 'import sys; print(sys.version)'
.venv/bin/python -c 'import sys; print(sys.executable); print(sys.version)'
```

```text
/usr/bin/python3
3.14.4 (main, Aug 20 2026, 10:41:58) [GCC 15.2.0]
/home/user1/RUS-EXP-009/.venv/bin/python
3.14.4 (main, Aug 20 2026, 10:41:58) [GCC 15.2.0]
```

### Ollama

```bash
which ollama
ollama list
```

Codex sandbox에서는 local socket 접근이 차단됐지만, 사용자 WSL shell에서 다음을 확인했다.

```text
/usr/local/bin/ollama
Ollama version: 0.34.1
Model tag: gemma:7b-instruct
Model ID: a72c7f4d0a15
Model size: 5.0 GB
Architecture/parameters/quantization: gemma / 9B / Q4_0
Model context length: 8192
```

`/api/version`은 `0.34.1`을 반환했고 `/api/tags`의 모델 metadata도 코드에 고정된 E9 runtime contract와 일치했다.

### GPU

```bash
nvidia-smi
```

Codex sandbox에서는 NVML 접근이 차단됐지만, 사용자 WSL shell에서 다음을 확인했다.

```text
GPU: NVIDIA GeForce GTX 1660 Ti
VRAM: 6144 MiB
Driver: 591.86
NVIDIA-SMI: 590.57
CUDA reported by nvidia-smi: 13.1
```

### Git

```bash
git rev-parse --short HEAD
git status --short
```

```text
12c00f1
 D RESEARCH_PLAN_E9_E10.md
?? configs/
?? docs/
?? scripts/
?? src/
```

해석: 현재 작업 트리는 clean 상태가 아니다. `docs/git-policy.md` 기준, 공식 실험 실행 전에는 커밋 또는 별도 정리가 필요하다.

## 4. Python Dependencies

의존성 파일은 루트의 `requirement.txt`에 있다.

현재 `.venv/bin/pip list`에서 확인한 주요 패키지는 다음과 같다.

| Package | Version |
|---|---|
| numpy | 2.5.3 |
| pandas | 3.0.5 |
| scikit-learn | 1.9.1 |
| scipy | 1.18.1 |
| httpx | 0.28.1 |
| ollama | 0.6.2 |
| pydantic | 2.13.5 |
| tqdm | 4.70.1 |
| pytest | 9.1.1 |
| pyarrow | 25.0.1 |

전체 목록은 `requirement.txt`와 현재 venv가 대체로 일치한다. `pip list` 실행 시 pip cache directory 권한 경고가 있었지만 패키지 목록 조회는 성공했다.

## 5. E9 Runtime Contract in Code

현재 `src/abstention_experiment/layer2_runtime.py`에 고정된 E9 runner 계약은 다음과 같다.

| 항목 | 값 |
|---|---|
| Ollama endpoint | `http://127.0.0.1:11434/api/chat` |
| Expected Ollama version | `0.34.1` |
| Model tag | `gemma:7b-instruct` |
| Model ID | `a72c7f4d0a15` |
| Architecture | `gemma` |
| Parameters | `9B` |
| Quantization | `Q4_0` |
| Model context length | `8192` |
| `num_ctx` | `4096` |
| `temperature` | `0` |
| `top_p` | `1.0` |
| `num_predict` | `64` |
| `seed` | `42` |
| `concurrency` | `1` |
| `timeout_seconds` | `60` |
| `stream` | `false` |
| `keep_alive` | `5m` |

실제 실행 시 runner는 Ollama metadata를 조회해 이 값들과 맞는지 검증한다.

## 6. Pilot 실행 중 확인된 환경 문제

1-flow smoke test는 completed 상태로 종료됐고 Ollama base blob SHA-256도 runtime contract와 일치했다.

첫 100-flow pilot `e9-pilot-20260918T101300Z-eafa7419`는 28행 기록 후 WSL OOM으로 중단됐다.

```text
WSL memory: 7.6 GiB
WSL swap: 2.0 GiB
Ollama service memory peak: 6.4 GiB
Ollama service swap peak: 936.4 MiB
kernel event: OOM killer terminated llama-server
```

복구 결정에 따라 Windows `%UserProfile%\.wslconfig`에 `memory=12GB`, `swap=8GB`를 설정했다. WSL 재시작 후 `free -h`와 `swapon --show`에서 약 11 GiB RAM과 8 GiB swap이 적용된 것을 확인했다.

## 7. 실험 전 재확인 체크리스트

공식 E9 pilot 또는 full run 전에는 실제 실행 shell에서 아래를 다시 확인한다.

```bash
pwd
uname -a
cat /etc/os-release
source .venv/bin/activate
which python
python --version
pip list
which ollama
ollama list
ollama ps
curl http://localhost:11434/api/tags
nvidia-smi
git status --short
git rev-parse HEAD
```

공식 실험은 `git status`가 clean이고, 필요한 data/prediction/metrics artifact의 hash가 manifest에 기록될 수 있을 때 실행한다.
