# RUS 연구 계획 초안

> 상태: **연구 설계 초안 / 변경 가능**
>
> 이 문서는 현재까지 합의된 연구 방향과 E9–E10 실험의 목적, 통제 조건, 평가 지표를 정리하기 위한 작업 문서다.  
> 아직 모델, 데이터셋 세부 구성, 임계값, 프롬프트, RAG corpus 등은 최종 확정되지 않았으며, 실험 과정에서 수정될 수 있다.

---

## 1. 연구 배경

네트워크 트래픽 규모가 증가하고 공격 기법이 정교해지면서 침입 탐지 시스템(IDS)은 속도, 정확도, 설명가능성 사이의 트레이드오프를 가진다.

- 규칙 기반 IDS는 빠르지만 알려지지 않은 변종이나 새로운 패턴에 취약하다.
- 기계학습 기반 IDS(ML-IDS)는 미지의 패턴을 포착할 수 있지만, 결정 경계 부근에서 오탐과 미탐이 증가할 수 있으며 판정 근거를 충분히 제공하지 못한다.
- LLM 기반 분석은 문맥적 추론과 설명을 제공할 수 있으나, 전체 트래픽을 대상으로 사용하기에는 추론 지연과 계산 비용이 크다.

본 연구는 이 문제를 해결하기 위해 전체 트래픽에 LLM을 적용하는 대신, 1차 ML-IDS가 **판정하기 어려운 트래픽만 유보(abstention)** 하고, 이 유보된 트래픽에 대해서만 LLM 기반 심층 검증을 수행하는 계층형 하이브리드 IDS를 연구한다.

---

## 2. 전체 아키텍처 개념

현재 연구 방향은 다음 세 계층으로 구성된다.

### Layer 1 — Confidence-Calibrated Selective IDS

LightGBM 기반 ML-IDS가 전체 트래픽을 처리한다.

1. ML-IDS가 각 flow에 대해 예측 확률을 생성한다.
2. 확률 보정을 통해 confidence를 보정한다.
3. 신뢰도가 충분히 높은 flow는 즉시 판정한다.
4. 결정 경계 부근의 불확실한 flow는 강제 판정하지 않고 abstain 한다.
5. abstained flow만 다음 계층으로 전달한다.

핵심 목적은 전체 트래픽 중 소수만 LLM으로 보내면서도 위험을 낮추는 것이다.

### Layer 2 — LLM Verification / Retrieval-Augmented Verification

Layer 1이 abstain한 flow를 LLM이 재검증한다.

두 단계로 실험한다.

- **E9:** LLM-only verification
- **E10:** RAG + LLM verification

E9는 외부 보안 지식을 검색하지 않고 LLM 단독으로 재판정하는 baseline이다.

E10은 MITRE ATT&CK, CTI, CVE 등 외부 보안 지식을 검색한 뒤 검색 근거를 LLM 입력에 추가하여 재판정한다.

### Layer 3 — XAI / Evidence Critic

향후 실험에서는 Layer 1의 XAI 결과를 LLM 입력에 추가하고, Critic Agent가 LLM 출력과 근거 문서를 다시 대조하는 구조를 고려한다.

현재 E9–E10 단계에서는 Layer 3를 구현의 필수 범위로 두지 않는다.

---

## 3. 연구 질문

### RQ1

> 전체 트래픽 대비 유보 구간 비율에 따라 판정 위험이 어떻게 변화하며, 소수 비율의 심층 검증만으로 유의미한 위험 저감이 가능한가?

RQ1은 Layer 1 실험에 해당한다.

현재 E9/E10 실험은 Layer 1 실험이 어느 정도 완료되었고, **동일한 abstained flow test set이 확보되어 있다는 가정**에서 시작한다.

### RQ2

> Layer 1이 abstain한 flow에 대해 LLM 기반 심층 검증이 Gate의 강제 판정보다 정확한가?  
> 그리고 retrieval evidence를 제공한 RAG + LLM이 LLM-only보다 분류 정확도와 근거 신뢰성을 개선하는가?

RQ2는 E9와 E10의 핵심 질문이다.

---

# 4. E9 — Local LLM-only Verification

## 4.1 목적

E9의 목적은 다음을 확인하는 것이다.

> Layer 1이 판정을 유보한 어려운 flow에 대해, local LLM이 외부 검색 지식 없이도 Gate의 강제 판정보다 더 정확한 재판정을 할 수 있는가?

즉 E9는 RAG의 효과를 평가하기 위한 **LLM-only baseline** 역할을 한다.

---

## 4.2 기본 비교

동일한 abstained flow test set을 사용한다.

### Baseline A — Gate Forced Decision

Layer 1이 abstain한 flow에 대해 기존 ML 모델의 prediction을 그대로 강제 판정으로 간주한다.

### Baseline B — Local LLM-only

동일한 flow를 구조화된 텍스트로 변환한 뒤 local LLM에 입력하고 재분류한다.

핵심 비교는 다음과 같다.

```text
Gate Forced Decision
        vs
Local LLM-only Verification
```

---

## 4.3 E9에서 고정해야 하는 조건

다음 변수는 가능한 한 고정한다.

- 동일한 abstained test flow
- 동일한 ground-truth label
- 동일한 flow serializer
- 동일한 prompt template
- 동일한 few-shot examples
- 동일한 generation parameter
- 동일한 model version
- 동일한 quantization
- 동일한 context length
- 동일한 hardware
- 동일한 Ollama version

모델이나 prompt를 변경한 경우 반드시 별도의 experiment ID로 관리한다.

---

## 4.4 현재 Local LLM 환경

현재 실험 환경의 기본 가정은 다음과 같다.

```text
OS              : WSL2 Ubuntu 24.04
GPU             : NVIDIA GeForce GTX 1660 Ti
GPU VRAM        : 6 GB
System RAM      : 16 GB
LLM Runtime     : Ollama
Model class     : 7B / 8B급 instruct model 후보
Primary interest: Gemma 7B 계열
Quantization    : Q4 계열 우선 검토
Concurrency     : 1
```

모델은 아직 최종 확정하지 않는다.

GPU 메모리 제약 때문에 다음을 우선한다.

- Q4 수준 quantization
- context 2K–4K에서 시작
- single request
- sequential inference
- CPU offload 허용
- latency와 GPU/CPU 비율 기록

---

## 4.5 Flow Serialization

tabular network flow feature를 LLM이 읽을 수 있는 의미 보존 구조화 텍스트로 변환한다.

예시:

```text
Network Flow
- Protocol: TCP
- Destination Port: 80
- Flow Duration: 1.42 seconds
- Forward Packets: 6
- Backward Packets: 2
- Mean Forward Inter-arrival Time: ...
- SYN Flag Count: 3
- ACK Flag Count: 1
```

### 요구사항

- feature order는 모든 flow에서 동일하게 유지
- feature name abbreviation은 가능한 한 사람이 읽을 수 있는 이름으로 정규화
- 값 단위가 명확한 경우 단위 포함
- NaN/Inf 처리 규칙 고정
- test label은 serializer에 절대 포함하지 않음
- Gate prediction도 기본 LLM 입력에는 넣지 않음
- 필요 시 별도 ablation에서 Gate prediction 제공 여부를 비교

---

## 4.6 Prompt 설계

초기 E9 prompt는 다음 목표를 가져야 한다.

- flow를 benign / attack으로 분류
- 가능하면 attack type 반환
- 고정 JSON schema 준수
- 불필요한 자유서술 최소화
- 재현성을 위해 temperature는 0 또는 매우 낮은 값 사용

예상 schema:

```json
{
  "decision": "BENIGN | ATTACK",
  "attack_type": "string | UNKNOWN",
  "confidence": 0.0,
  "observed_indicators": [
    "..."
  ],
  "reason": "..."
}
```

주의:

- LLM이 출력한 `confidence`는 calibrated probability로 간주하지 않는다.
- confidence는 보조 분석값이다.
- JSON parsing failure는 별도 실패 유형으로 기록한다.

---

## 4.7 Zero-shot / Few-shot

초기에는 다음 두 조건을 비교하는 것이 유용하다.

```text
E9-A: Zero-shot LLM
E9-B: Few-shot LLM
```

Few-shot 사용 시:

- train 또는 validation partition에서 example 선택
- test flow 사용 금지
- 모든 test flow에 동일 example 사용
- class balance 고려
- example 변경 시 experiment ID 변경

---

## 4.8 E9 평가 지표

### Binary intrusion verification

- Accuracy
- Precision
- Recall
- F1
- FPR
- FNR
- confusion matrix

핵심 비교:

```text
Gate Forced Decision vs LLM-only
```

예:

\[
\Delta F1 = F1_{LLM} - F1_{Gate}
\]

\[
\Delta Error = Error_{Gate} - Error_{LLM}
\]

### Attack-type classification

공격 유형까지 출력하는 경우 binary task와 별도로 평가한다.

- Macro-F1
- Weighted-F1
- Per-class Precision
- Per-class Recall

예:

```text
Ground truth : PortScan
LLM output   : ATTACK / DoS

Binary detection  : Correct
Attack type       : Incorrect
```

두 평가는 혼합하지 않는다.

---

## 4.9 Operational Metrics

local LLM의 실행 가능성을 확인하기 위해 다음을 반드시 기록한다.

- total latency per flow
- mean latency
- median latency
- p95 latency
- model load time
- prompt tokens
- completion tokens
- generation tokens/sec
- GPU memory usage
- CPU/GPU processor distribution
- system RAM usage
- parsing failure rate
- invalid schema rate
- timeout rate

---

## 4.10 E9 결과 로그

각 flow별 결과를 JSONL 형태로 저장하는 것을 권장한다.

예:

```json
{
  "experiment_id": "e9_gemma7b_q4_fs_v1",
  "flow_id": "12345",
  "ground_truth": "ATTACK",
  "ground_truth_attack_type": "PortScan",
  "gate_prediction": "BENIGN",
  "gate_confidence": 0.53,
  "llm_decision": "ATTACK",
  "llm_attack_type": "PortScan",
  "llm_confidence": 0.81,
  "observed_indicators": [],
  "reason": "...",
  "raw_response": "...",
  "valid_schema": true,
  "latency_ms": 2143
}
```

---

# 5. E10 — Retrieval-Augmented LLM Verification

## 5.1 목적

E10은 E9 pipeline에 retrieval을 추가한다.

핵심 질문:

> 외부 보안 근거를 제공하면, LLM-only보다 abstained flow의 재분류 정확도가 개선되는가?

그리고:

> LLM의 판단이 실제 외부 근거에 의해 더 잘 지지되는가?

---

## 5.2 E9와 E10의 통제 원칙

E10은 가능한 한 E9와 동일한 조건을 유지한다.

동일하게 유지해야 하는 것:

- abstained flow
- serializer
- LLM model
- quantization
- generation parameter
- few-shot examples
- output schema
- hardware

변경되는 핵심 요소는:

```text
E9  : Flow -> LLM
E10 : Flow -> Retrieval -> Evidence -> LLM
```

즉 E10에서 성능 향상이 발생했을 때 가능한 한 retrieval evidence의 효과로 해석할 수 있도록 한다.

---

## 5.3 RAG 기본 구성

예상 pipeline:

```text
Abstained Flow
      |
      v
Flow Serializer
      |
      v
Query Construction
      |
      v
Retriever
      |
      v
Security Knowledge Base
      |
      v
Top-k Evidence
      |
      v
Prompt + Evidence
      |
      v
Local LLM
      |
      v
Structured Output
```

---

## 5.4 Security Knowledge Base 후보

초기 corpus는 과도하게 확장하지 않는다.

우선순위:

1. MITRE ATT&CK
2. 공개 CTI report
3. 필요 시 CVE / advisory

초기 E10에서는 MITRE ATT&CK 중심 corpus만으로 시작해도 된다.

---

## 5.5 Retrieval Query

raw flow 숫자를 그대로 vector search에 넣는 방식은 semantic gap이 클 수 있다.

따라서 다음 두 방식을 검토한다.

### Template-based Query

flow feature를 deterministic rule로 network behavior description으로 변환한다.

장점:

- 재현성
- 낮은 hallucination 위험
- 실험 통제가 쉬움

### LLM Query Rewriting

LLM이 flow를 retrieval query로 변환한다.

장점:

- 풍부한 semantic 표현

단점:

- retrieval 이전에 LLM 추론이 개입
- 실험 변수가 늘어남

초기 E10에서는 template-based query를 우선 고려한다.

---

## 5.6 E10 Output Schema

E10부터는 evidence attribution을 포함한다.

예:

```json
{
  "decision": "ATTACK",
  "attack_type": "PortScan",
  "confidence": 0.83,
  "observed_indicators": [
    "high SYN activity",
    "multiple destination ports"
  ],
  "evidence": [
    {
      "claim": "behavior is consistent with network service scanning",
      "document_id": "MITRE-T1046"
    }
  ],
  "reason": "..."
}
```

---

## 5.7 E10 평가

### Classification

E9와 동일:

- Accuracy
- Precision
- Recall
- F1
- FPR
- FNR

비교:

```text
Gate Forced
vs
LLM-only
vs
RAG + LLM
```

### Retrieval

정답 relevant document annotation이 가능한 subset에 대해:

- Hit@k
- Recall@k
- Precision@k
- MRR / nDCG (필요 시)

### Groundedness / Evidence Support

RAG의 핵심 평가 지표다.

예:

\[
EvidenceSupportRate =
\frac{\text{retrieved evidence로 실제 지지되는 claims}}
{\text{전체 evidence-dependent claims}}
\]

필요 시 각 claim을 다음으로 annotation한다.

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
```

---

# 6. E9–E10 실험에서 확인하고자 하는 것

최종적으로 다음 질문에 답할 수 있어야 한다.

### Q1

Layer 1이 abstain한 어려운 flow에서 Gate forced decision의 오류율은 어느 정도인가?

### Q2

Local LLM-only가 동일 flow에서 Gate forced decision보다 나은가?

### Q3

Local LLM의 개선이 특정 attack class에만 집중되는가, 아니면 전반적으로 발생하는가?

### Q4

LLM-only가 새로운 오류를 생성하는 경우는 어떤 feature pattern에서 발생하는가?

### Q5

RAG evidence를 제공하면 LLM-only보다 정확도가 개선되는가?

### Q6

RAG가 분류 정확도를 크게 높이지 못하더라도 evidence support / groundedness는 개선되는가?

### Q7

성능 개선 대비 latency와 계산비용은 어느 정도인가?

---

# 7. 실험 단계

## Phase 0 — Environment

- WSL2 Ubuntu 24.04
- Ollama 설치
- local model 실행
- Python venv
- GPU inference 확인

상태: **기본 구축 완료**

## Phase 1 — E9 Pilot

- abstained flow loader
- serializer
- prompt
- JSON schema
- Ollama client
- 50–100 flow pilot
- latency / JSON validity 확인

## Phase 2 — E9 Full Experiment

- zero-shot
- few-shot
- Gate forced baseline
- 전체 abstained test set inference
- classification metrics
- operational metrics

## Phase 3 — E9 Analysis

- error analysis
- class-wise performance
- latency distribution
- model feasibility
- prompt/schema 안정성

## Phase 4 — E10 Retrieval

- security corpus
- preprocessing
- embedding
- vector index
- query construction
- top-k retrieval

## Phase 5 — E10 Full Experiment

- 동일 abstained flow
- 동일 LLM
- 동일 prompt 기본 구조
- retrieval evidence만 추가
- E9 vs E10 비교

## Phase 6 — Groundedness Evaluation

- evidence support annotation
- unsupported claim 분석
- retrieval quality 분석

---

# 8. 현재 확정하지 않은 사항

다음은 아직 결정하지 않는다.

- 최종 local LLM
- 최종 quantization
- 최종 context length
- final prompt wording
- few-shot 개수
- retrieval embedding model
- vector database
- chunk size
- top-k
- CTI corpus 범위
- CVE 포함 여부
- XAI 입력 구조
- Critic Agent 구조

이러한 요소는 pilot 결과를 보고 결정한다.

---

# 9. 연구 범위 제한

본 연구에서 다루는 불확실성은 기본적으로:

> 훈련 시점에 존재한 공격 범주 내에서 결정 경계 부근에 위치해 Layer 1이 판정을 유보한 flow

이다.

엄밀한 의미의 unseen attack / zero-day generalization을 측정하는 LOAO(Leave-One-Attack-Out) 프로토콜은 현재 핵심 실험 범위에 포함하지 않는다.

---

# 10. 연구 재현성 원칙

모든 experiment는 최소한 다음 정보를 기록한다.

```text
experiment_id
git commit
dataset version
test split identifier
abstention threshold
model name
model hash/tag
quantization
Ollama version
prompt version
few-shot version
context length
temperature
seed
hardware
run date
```

연구 결과를 비교할 때 한 번에 가능한 한 하나의 실험 변수만 변경한다.

---

# 11. 핵심 원칙

E9와 E10의 가장 중요한 원칙은 다음과 같다.

> **동일한 abstained flows에 대해 동일한 local LLM을 사용하고, E9와 E10 사이에서 retrieval evidence의 존재 여부를 주된 차이로 유지한다.**

이 원칙이 유지되어야 다음 비교가 의미를 가진다.

```text
Gate Forced Decision
        ↓
LLM-only
        ↓
RAG + LLM
```

향후 XAI와 Critic을 추가할 경우 다음과 같은 ablation chain으로 확장할 수 있다.

```text
Gate Forced
→ LLM-only
→ RAG + LLM
→ RAG + XAI + LLM
→ RAG + XAI + LLM + Critic
```
