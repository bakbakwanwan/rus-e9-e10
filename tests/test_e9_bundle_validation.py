from __future__ import annotations

import json
import shutil
from pathlib import Path

from abstention_experiment.data import sha256_file
from abstention_experiment.layer2_runtime import validate_transfer_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_bundle(root: Path) -> Path:
    transfer = root / "transfer"
    transfer.mkdir(parents=True)
    schema_path = transfer / "e9_input_feature_schema.json"
    prompt_path = transfer / "e9_prompt_v1.json"
    input_path = transfer / "llm_inputs.jsonl"
    shutil.copyfile(REPO_ROOT / "configs/llm/e9_input_feature_schema.json", schema_path)
    shutil.copyfile(REPO_ROOT / "configs/llm/e9_prompt_v1.json", prompt_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    row = {
        "input_index": 0,
        "payload": {
            "flow_features": {
                feature: "TCP" if feature == "Protocol" else 0.0
                for feature in schema["features"]
            }
        },
    }
    input_path.write_text(json.dumps(row, separators=(",", ":")) + "\n", encoding="utf-8")
    manifest = {
        "counts": {"exported_rows": 1},
        "artifacts": {
            "llm_inputs": {
                "path": "transfer/llm_inputs.jsonl",
                "sha256": sha256_file(input_path),
                "rows": 1,
            },
            "feature_schema": {
                "path": "transfer/e9_input_feature_schema.json",
                "sha256": sha256_file(schema_path),
                "version": "e9-input-v1",
            },
            "prompt": {
                "path": "transfer/e9_prompt_v1.json",
                "sha256": sha256_file(prompt_path),
                "version": "e9-v1",
            },
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return input_path


def test_transfer_bundle_validator_accepts_valid_contract(tmp_path: Path) -> None:
    _write_bundle(tmp_path)

    result = validate_transfer_bundle(tmp_path)

    assert result["passed"] is True
    assert result["summary"]["failed_count"] == 0
    assert result["checks"]["forbidden_fields"]["passed"] is True
    assert result["checks"]["feature_rows"]["passed"] is True


def test_transfer_bundle_validator_reports_tampered_input(tmp_path: Path) -> None:
    input_path = _write_bundle(tmp_path)
    input_path.write_text('{"input_index":0,"payload":{"flow_features":{"binary_label":1}}}\n', encoding="utf-8")

    result = validate_transfer_bundle(tmp_path)

    assert result["passed"] is False
    assert result["checks"]["input_jsonl_sha256"]["passed"] is False
    assert result["checks"]["feature_rows"]["passed"] is False
    assert result["checks"]["forbidden_fields"]["passed"] is False
