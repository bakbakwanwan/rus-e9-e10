# AGENTS.md

## Project

This repository contains experimental code for the **RUS hybrid intrusion detection research project**.

The immediate implementation target is:

```text
E9  : Local LLM-only verification of abstained network flows
E10 : Retrieval-Augmented Local LLM verification
```

The research design is still evolving.  
Do **not** silently convert tentative assumptions into permanent design decisions.

---

# 1. Execution Environment

Primary environment:

```text
Host OS         : Windows
Execution OS    : WSL2 Ubuntu 24.04
Project root    : ~/rus-e9
LLM Runtime     : Ollama
GPU             : NVIDIA GeForce GTX 1660 Ti
VRAM            : 6 GB
System RAM      : 16 GB
Python          : project-local virtual environment
```

Always perform project work inside the WSL Ubuntu environment.

Expected project root:

```bash
cd ~/rus-e9
```

Do not treat `/mnt/c/...` as the primary project workspace unless explicitly instructed.

---

# 2. Before Making Changes

Before editing or executing experiments, inspect the current environment.

Recommended checks:

```bash
pwd
uname -a
cat /etc/os-release
which python3
which ollama
nvidia-smi
ollama list
```

For Python work:

```bash
cd ~/rus-e9
source .venv/bin/activate
which python
python --version
pip list
```

Do not install a second NVIDIA Linux display driver inside WSL.

Do not install CUDA Toolkit unless the task explicitly requires CUDA development outside Ollama.

---

# 3. Research Intent

The system under study is a hybrid IDS.

Layer 1:

```text
LightGBM ML-IDS
→ confidence calibration
→ selective prediction
→ abstention
```

Only abstained flows are passed to the later layers.

Current focus:

```text
E9  = local LLM-only verification
E10 = RAG + local LLM verification
```

E9 is the baseline for E10.

---

# 4. E9 Objective

E9 asks:

> For the same flows that Layer 1 abstained on, can a local LLM produce more accurate decisions than forcing the Layer 1 classifier to decide?

Primary comparison:

```text
Gate Forced Decision
vs
Local LLM-only Verification
```

The same abstained test flow set must be used for both.

---

# 5. E10 Objective

E10 asks:

> Does adding retrieved external security evidence improve LLM verification accuracy and evidence support compared with E9?

Primary comparison:

```text
Gate Forced
vs
LLM-only
vs
RAG + LLM
```

E10 should reuse as much of the E9 pipeline as possible.

The main experimental difference between E9 and E10 should be:

```text
E9:
Flow → LLM

E10:
Flow → Retrieval → Evidence → LLM
```

---

# 6. Research Constraints

Do not silently change any of the following:

- dataset split
- abstention threshold
- test flow population
- ground-truth mapping
- label taxonomy
- flow serializer
- LLM model
- quantization
- prompt
- few-shot examples
- temperature
- context length
- output schema

If a change is necessary:

1. document the reason;
2. create a new experiment configuration;
3. preserve the previous result;
4. do not overwrite old results.

---

# 7. Experimental Reproducibility

Every experiment should have a unique `experiment_id`.

Suggested naming:

```text
e9_<model>_<quant>_<prompt>_<shot>_<version>
```

Example:

```text
e9_gemma7b_q4_promptv1_fewshot_v1
```

Every experiment should record:

```text
experiment_id
run_timestamp
git_commit
dataset_version
test_split
abstention_threshold
model
model_tag
quantization
ollama_version
prompt_version
fewshot_version
context_length
temperature
seed
hardware
```

Prefer machine-readable YAML/JSON config files.

---

# 8. Directory Convention

Preferred structure:

```text
~/rus-e9/
├── AGENTS.md
├── README.md
├── RESEARCH_PLAN.md
├── requirements.txt
│
├── configs/
│   ├── models/
│   ├── prompts/
│   └── experiments/
│
├── data/
│   ├── abstained/
│   ├── processed/
│   └── metadata/
│
├── prompts/
│
├── src/
│   ├── data/
│   ├── serialization/
│   ├── llm/
│   ├── evaluation/
│   └── utils/
│
├── experiments/
│   ├── e9/
│   └── e10/
│
├── results/
│   ├── raw/
│   ├── parsed/
│   ├── metrics/
│   └── figures/
│
└── logs/
```

Do not reorganize the repository aggressively without an explicit reason.

---

# 9. Python Environment

Use the existing virtual environment.

```bash
cd ~/rus-e9
source .venv/bin/activate
```

Use:

```bash
python
pip
```

from the activated environment.

When adding dependencies:

- add only necessary packages;
- update `requirements.txt`;
- avoid heavyweight frameworks unless required;
- do not add LangChain or LlamaIndex during E9 unless explicitly justified.

E9 should remain minimal.

---

# 10. Ollama

Ollama is the local inference runtime.

Check server availability:

```bash
curl http://localhost:11434/api/tags
```

Check installed models:

```bash
ollama list
```

Check active model allocation:

```bash
ollama ps
```

Monitor GPU:

```bash
watch -n 1 nvidia-smi
```

Current hardware is memory constrained.

Default assumptions:

```text
model class     : 7B / 8B instruct
quantization    : Q4-class preferred
context         : 2048–4096 initially
concurrency     : 1
inference       : sequential
CPU offload     : acceptable
```

Do not assume 100% GPU residency.

---

# 11. Model Selection

The final model is not yet fixed.

Gemma 7B-class models are currently of interest.

Do not replace the selected model because another model is newer or larger without an explicit experiment.

If benchmarking models, treat model identity as an experimental variable and log results separately.

---

# 12. Flow Serialization

Never send raw test labels to the LLM.

The serializer should:

- preserve network semantics;
- use consistent feature ordering;
- normalize cryptic feature names;
- preserve numeric values;
- include units where meaningful;
- handle NaN/Inf deterministically;
- avoid including ground truth;
- avoid accidental leakage.

Example target format:

```text
Network Flow
- Protocol: TCP
- Destination Port: 80
- Flow Duration: 1.42 seconds
- Forward Packets: 6
- Backward Packets: 2
- SYN Flag Count: 3
```

Serializer behavior must be unit-tested.

---

# 13. LLM Output

Prefer structured JSON.

Initial schema:

```json
{
  "decision": "BENIGN | ATTACK",
  "attack_type": "string | UNKNOWN",
  "confidence": 0.0,
  "observed_indicators": [],
  "reason": ""
}
```

Rules:

- validate output;
- store raw output;
- store parsed output separately;
- do not silently repair invalid output without logging it;
- count malformed JSON as an operational failure;
- do not interpret self-reported confidence as calibrated probability.

---

# 14. E9 Pilot First

Do not run the full dataset immediately.

Recommended order:

```text
1. Load abstained flows
2. Serialize flows
3. Test Ollama client
4. Test zero-shot prompt
5. Validate JSON
6. Run 50–100 flow pilot
7. Inspect failures
8. Add few-shot
9. Run full E9
10. Evaluate Gate vs LLM
```

Pilot checks:

- JSON validity
- unexpected labels
- prompt bias
- latency
- GPU/RAM use
- attack-type naming consistency
- obvious data leakage

---

# 15. Evaluation Rules

Binary detection and attack-type classification are separate tasks.

Example:

```text
Ground truth: PortScan
Prediction  : ATTACK / DoS
```

Interpretation:

```text
Binary detection = correct
Attack type      = incorrect
```

Binary metrics:

```text
Accuracy
Precision
Recall
F1
FPR
FNR
Confusion Matrix
```

Attack-type metrics:

```text
Macro-F1
Weighted-F1
Per-class Precision
Per-class Recall
```

---

# 16. Operational Metrics

Record at minimum:

```text
latency_ms
prompt_tokens
completion_tokens
tokens_per_second
schema_valid
parse_error
timeout
GPU memory
system RAM
```

Where practical, also record:

```text
mean latency
median latency
p95 latency
```

---

# 17. Result Preservation

Never overwrite previous experiment results.

Use directories such as:

```text
results/raw/<experiment_id>/
results/parsed/<experiment_id>/
results/metrics/<experiment_id>/
logs/<experiment_id>/
```

Raw LLM responses must be preserved.

If parsing logic changes, re-parse raw outputs rather than rerunning inference unless necessary.

---

# 18. E10 Extension Principle

E10 should build directly on E9.

Do not rewrite E9 from scratch.

Add modules for:

```text
knowledge preprocessing
embedding
indexing
query construction
retrieval
evidence formatting
grounded output
```

Keep the E9 serializer, LLM client, logging, and evaluation code reusable.

---

# 19. RAG Scope

Do not build an oversized RAG system initially.

Initial corpus priority:

```text
1. MITRE ATT&CK
2. selected public CTI
3. CVE/advisories if needed
```

Initial retrieval should favor simple, reproducible components.

Template-based query construction should be considered before LLM query rewriting.

---

# 20. Research Integrity

Do not optimize prompts directly against the full test set.

Do not select few-shot examples from test samples.

Do not expose ground-truth labels to the model.

Do not alter class mappings after seeing final test results unless the experiment is restarted under a new version.

Do not delete failed runs because they reduce apparent performance.

Do not report only successful LLM responses.

Operational failures are part of the result.

---

# 21. Statistical Discipline

When possible:

- preserve per-flow predictions;
- compute confidence intervals;
- use paired comparison methods because E9/E10 operate on the same flows;
- report sample size;
- report class distribution;
- avoid claiming improvement based only on aggregate accuracy.

Do not introduce statistical tests without documenting assumptions.

---

# 22. Zero-Day Scope

Do not describe the current experiment as strict zero-day detection.

Current scope:

```text
uncertain flows near the Layer 1 decision boundary
within attack categories represented during training
```

Leave-One-Attack-Out evaluation is currently outside the primary scope unless explicitly added later.

---

# 23. Code Quality

Prefer:

- small modules;
- explicit configuration;
- type hints where useful;
- deterministic functions;
- clear error handling;
- testable serializers/parsers;
- JSONL for per-flow records;
- CSV for aggregate tables where convenient.

Avoid:

- hidden global state;
- magic constants;
- notebook-only pipelines;
- manual result editing;
- hard-coded absolute user-specific paths;
- silently swallowing exceptions.

---

# 24. Change Management

If implementation reveals a conflict between the research design and the current code:

1. stop before making a conceptual change;
2. document the issue;
3. explain the options;
4. preserve the current implementation;
5. only then implement the chosen alternative.

Technical refactoring may proceed normally.

Research-design changes require explicit documentation.

---

# 25. Immediate Implementation Priority

Current recommended priority:

```text
P0  Environment sanity check
P1  Abstained-flow loader
P2  Flow serializer
P3  Ollama client
P4  Structured output validator
P5  E9 zero-shot pilot
P6  E9 few-shot pilot
P7  E9 full experiment
P8  Gate-vs-LLM evaluation
P9  Error analysis
P10 E10 retrieval extension
```

Do not start E10 before E9 produces stable, reproducible outputs unless explicitly instructed.

---

# 26. Definition of E9 Ready

E9 can be considered ready for full execution when all of the following are true:

```text
[ ] abstained test set is fixed
[ ] ground-truth mapping is verified
[ ] serializer is deterministic
[ ] Ollama model is fixed for the run
[ ] prompt is versioned
[ ] few-shot set is versioned
[ ] JSON schema validator works
[ ] raw response logging works
[ ] pilot JSON validity is acceptable
[ ] latency is measurable
[ ] Gate forced baseline is reproducible
```

---

# 27. Definition of E10 Ready

E10 can begin when:

```text
[ ] E9 pipeline is stable
[ ] E9 full-run results are preserved
[ ] security corpus version is fixed
[ ] retrieval index can be rebuilt reproducibly
[ ] retrieved evidence is logged per flow
[ ] E9 prompt structure can be reused
[ ] evidence attribution schema is defined
```

---

# 28. Default Decision Rule for Ambiguity

When requirements are unclear:

- preserve existing behavior;
- prefer the smallest change;
- make assumptions explicit;
- do not silently make research decisions;
- leave TODO notes where a research choice is required.

The codebase should support experimentation, not prematurely lock the research into one design.
