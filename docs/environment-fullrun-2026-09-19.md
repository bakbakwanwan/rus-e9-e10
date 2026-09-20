# Full-Run Environment Record (2026-09-19)

> 작성 시점: 2026-09-19  
> 목적: `docs/environment.md`는 2026-09-18 시점 환경(작업 경로 `/home/user1/RUS-EXP-009`, GPU GTX 1660 Ti)의 관찰 기록이며 수정하지 않는다. `docs/EXP-009-TRANSFER.md` 7절 지침("새 환경의 OS, Python, GPU, VRAM, RAM, swap, driver를 `docs/environment.md`와 구분되는 새 기록으로 남긴다")에 따라, 이관된 새 환경에서 확인한 값을 이 문서에 별도로 남긴다.  
> 주의: 이 문서는 관찰 기록이다. 확인할 수 없는 값은 추정하지 않는다.

## 1. 요약

| 항목 | 관찰값 |
|---|---|
| 작업 경로 | `/home/user1/RUS/rus-e9-e10` |
| 호스트명 | `LAPTOP1324` |
| 커널 | `Linux LAPTOP1324 6.18.33.2-microsoft-standard-WSL2` |
| OS | Ubuntu `26.04.1 LTS` (`resolute`) |
| Architecture | `x86_64` |
| project venv Python | `/home/user1/RUS/rus-e9-e10/.venv/bin/python`, `3.14.4` |
| Ollama binary | `/usr/local/bin/ollama` |
| Ollama version | `0.34.1` (설치 직후 `0.34.2`였으나 코드 계약값 `0.34.1`에 맞춰 재설치함) |
| Ollama model | `gemma:7b-instruct` (`a72c7f4d0a15`, 9B, Q4_0, context 8192) |
| GPU | NVIDIA GeForce **RTX 3050 Laptop GPU** |
| VRAM | **4096 MiB** |
| GPU Driver | `616.92` (최초 관찰값 `546.30`에서 사용자가 갱신, WSL 재시작으로 반영) |
| WSL memory | `11 GiB` (`.wslconfig`으로 상향 완료, `free -h` 재확인) |
| WSL swap | `8.0 GiB` (`/dev/sdc`, 재확인) |
| Git HEAD | `96a5c997974b15e57d3badcbe0b11f0eace0fc99` |
| Git worktree | clean |

## 2. `docs/environment.md` 대비 하드웨어 차이

| 항목 | 2026-09-18 환경 (`docs/environment.md`) | 이 환경 |
|---|---|---|
| GPU | GTX 1660 Ti | RTX 3050 Laptop GPU |
| VRAM | 6144 MiB | **4096 MiB** |
| WSL memory (OOM 복구 후) | 약 11 GiB (`.wslconfig`: 12GB) | 11 GiB (`.wslconfig`로 상향, 재확인 완료) |
| WSL swap | 8 GiB | 8.0 GiB (재확인 완료) |

**GPU/VRAM 차이는 사용자가 확인 후 "이 하드웨어 그대로 진행"으로 결정했다 (2026-09-19).** 이 장비의 VRAM(4096 MiB)은 현재 가용 범위 안에서 바꿀 수 없는 조건으로 받아들이고, `docs/environment.md`의 GTX 1660 Ti 관찰값은 덮어쓰지 않는다. `AGENTS.md` 6절의 통제 변수(dataset split, model, quantization, prompt 등)에는 실행 하드웨어가 포함되지 않으므로, 이 차이 자체가 E9 실험 설계를 무효화하지 않는다. 다만 full run 결과 해석 시 이 환경에서 실행됐음을 명시한다.

모델 크기(5.0GB)가 VRAM(4096 MiB)보다 크므로 이전 환경보다 CPU offload 비중이 더 큰 상태로 추론이 진행된다. `AGENTS.md` 10절은 CPU offload를 허용한다.

### 2-1. GPU 드라이버 문제와 해결 (2026-09-19)

최초 설치된 드라이버 `546.30`에서는 Ollama가 GPU를 전혀 인식하지 못했다.

```text
level=WARN msg="NVIDIA driver too old" device="NVIDIA GeForce RTX 3050 Laptop GPU" compute=8.6 driver=546 required_driver="550 or newer"
inference compute id=cpu library=cpu ...
```

이 상태에서 1-flow smoke test는 `ollama ps` 기준 100% CPU로 처리되어 wall latency `48.07초` (load 22.7초 + prompt_eval 23.15초, eval 2.06초)가 나왔다. 이는 VRAM 용량 부족이 아니라 드라이버 버전 문제였다.

사용자가 Windows 쪽 NVIDIA 드라이버를 `616.92`로 갱신했다. WSL2는 호스트 드라이버를 `/usr/lib/wsl/lib/`에 재마운트하므로, 갱신 직후에는 `nvidia-smi`가 segfault를 일으켰다 (`dmesg`: `nvidia-smi: potentially unexpected fatal signal 11`, 라이브러리 버전 불일치). `wsl --shutdown` 후 재기동하여 해결했다.

재기동 후 Ollama 로그에서 GPU 인식을 확인했다.

```text
level=INFO msg="inference compute" id=0 library=CUDA compute=8.6 name=CUDA0 description="NVIDIA GeForce RTX 3050 Laptop GPU" driver=13.4 total="4.0 GiB" available="3.2 GiB"
```

`ollama ps`는 `69%/31% CPU/GPU`를 보고했다. VRAM 4GB에 7.1GB 모델이 다 올라가지 않아 부분 CPU offload는 여전하지만, GPU가 실제로 사용된다.

**latency 실측 (2026-09-19, GPU 활성화 후)**

| 시도 | 결과 | wall latency | 비고 |
|---|---|---|---|
| cold load (드라이버 갱신 직후 첫 요청) | `generation_failure: timeout` | 60.05초 | 모델을 GPU/CPU에 처음 올리는 시간이 `timeout_seconds=60` 계약을 초과함 |
| warm (모델이 메모리에 남아있는 상태) | `completed`, `decision: BENIGN` | 4.95초 | `prompt_eval` 1.26초 + `eval` 3.66초 |

warm 상태 latency(4.95초)는 이전 GTX 1660 Ti 환경 pilot의 p50(2.86초)/p95(9.41초) 범위 안에 든다. 다만 **cold load는 `timeout_seconds=60` 계약을 넘긴다** — 이는 `AGENTS.md` 6절의 통제 변수(temperature, context length 등)를 바꾸지 않고는 없앨 수 없는 하드웨어 특성으로 받아들인다. 100-flow 이상 규모 run에서는 최초 1건(input_index=0) 정도가 `generation_failure: timeout`으로 기록될 가능성이 있으며, 이는 D-EXP009-016의 timeout rate ≤5% 기준 안에서 허용 범위로 본다.

**WSL memory/swap은 사용자가 `.wslconfig`로 상향 조치했다.** 최초 관찰값(`.wslconfig` 없음, 6.7 GiB / swap 2.0 GiB)은 2026-09-18 OOM 발생 조건(7.6 GiB)보다 낮아 위험 신호였으나, 조치 후 `free -h` / `swapon --show`로 11 GiB / swap 8.0 GiB를 재확인했다. 이전 OOM 복구값과 동일한 수준이므로 이 항목은 해결된 것으로 본다.

## 3. 모델 계약 검증

`src/abstention_experiment/layer2_runtime.py`의 `_verify_model_metadata()`를 실제 실행해 확인했다.

```text
actual: {
  'version': '0.34.1',
  'model_tag': 'gemma:7b-instruct',
  'model_id': 'a72c7f4d0a15',
  'base_blob_sha256': 'ef311de6af9db043d51ca4b1e766c28e0a1ac41d60420fed5e001dc470c64b77',
  'architecture': 'gemma',
  'parameters': '9B',
  'quantization': 'Q4_0',
  'model_context_length': 8192,
}
```

`EXPECTED_MODEL`과 전 항목 일치. Ollama 설치 직후 관찰된 `0.34.2`는 코드 계약(`0.34.1`)과 달라 `v0.34.1` 릴리스 바이너리(`ollama-linux-amd64.tar.zst`, GitHub `ollama/ollama` releases)로 재설치했다. 모델 blob은 재설치 과정에서 변경되지 않았다.

## 4. Python 의존성

`requirement.txt` 커밋 `96a5c99`에서 실제 import되지 않는 패키지(`httpx`, `ollama` 파이썬 클라이언트, `pydantic`, `scikit-learn`, `scipy`, `tqdm`)를 제거했다. Ollama 호출은 표준 라이브러리 `urllib`으로 구현되어 있어 `numpy`, `pandas`, `pyarrow`, `pytest`만 실제로 필요하다. `pytest -q` 17개 통과 확인.

## 5. Full run 진입 전 남은 확인 사항

- [x] WSL memory/swap 상향 (`.wslconfig`로 11 GiB / swap 8.0 GiB 적용, 2026-09-19 재확인)
- [x] GPU/VRAM 4096 MiB 제약을 하드웨어 조건으로 수용하고 이 환경에서 진행하기로 결정 (2026-09-19)
- [x] NVIDIA 드라이버를 `616.92`로 갱신해 GPU(CUDA) 인식 확보, `wsl --shutdown` 재기동으로 반영 확인 (2026-09-19)
- [x] GPU 활성화 후 latency 실측: warm 4.95초, cold load는 timeout(60초) 초과 — 100-flow 이상 규모에서 최초 1건 timeout 예상, 허용 범위로 판단
- [ ] 그 외 `docs/EXP-009-PLAN.MD` Phase 0 나머지 항목 (checksum 검증은 완료, `results/results/pilots` 중첩 오류를 `results/pilots`로 정정함)
