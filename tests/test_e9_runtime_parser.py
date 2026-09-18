from __future__ import annotations

from http.client import RemoteDisconnected
import json
from pathlib import Path
import shutil

import pytest

from abstention_experiment.data import sha256_file
from abstention_experiment.layer2_common import read_json, read_jsonl
from abstention_experiment.layer2_runtime import (
    EXPECTED_MODEL,
    RunIncompleteError,
    _parse_api_response,
    run_ollama_bundle,
)


RUN_ID = "e9-pilot-20260918T120000Z-1234abcd"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _api(content: str, *, done: bool = True, done_reason: str = "stop") -> dict[str, object]:
    return {
        "model": "gemma:7b-instruct",
        "created_at": "2026-09-18T12:00:00Z",
        "done": done,
        "done_reason": done_reason,
        "message": {"content": content},
    }


@pytest.mark.parametrize(("decision", "status"), [("BENIGN", "completed"), ("ATTACK", "completed"), ("INDETERMINATE", "indeterminate")])
def test_strict_parser_accepts_contract_decisions(decision: str, status: str) -> None:
    row = _parse_api_response(
        RUN_ID,
        input_index=2,
        http_status=200,
        api=_api(f'{{"decision":"{decision}"}}'),
        latency=0.25,
    )

    assert row["status"] == status
    assert row["parsed_decision"] == decision
    assert row["generation_failure"] is None
    assert row["raw_content"] == f'{{"decision":"{decision}"}}'


@pytest.mark.parametrize(
    ("content", "failure_code"),
    [
        ("not-json", "decision_json_invalid"),
        ('{"decision":"ATTACK","reason":"extra"}', "decision_schema_invalid"),
        ('{"decision":"attack"}', "decision_schema_invalid"),
        ('["ATTACK"]', "decision_schema_invalid"),
    ],
)
def test_strict_parser_records_invalid_output(content: str, failure_code: str) -> None:
    row = _parse_api_response(RUN_ID, 0, 200, _api(content), 0.5)

    assert row["status"] == "generation_failure"
    assert row["parsed_decision"] is None
    assert row["generation_failure"]["code"] == failure_code
    assert row["raw_content"] == content


def test_strict_parser_records_generation_failure() -> None:
    row = _parse_api_response(
        RUN_ID,
        input_index=0,
        http_status=200,
        api=_api('{"decision":"ATTACK"}', done=False, done_reason="length"),
        latency=1.5,
    )

    assert row["status"] == "generation_failure"
    assert row["generation_failure"]["code"] == "generation_incomplete"
    assert row["parsed_decision"] is None


def _write_one_row_bundle(root: Path) -> None:
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
        "run_id": RUN_ID,
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


def test_runner_records_remote_disconnect_as_systemic_failure(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle"
    output_dir = tmp_path / "returned"
    _write_one_row_bundle(bundle_root)

    def disconnected(_: dict[str, object]) -> tuple[int, dict[str, object]]:
        raise RemoteDisconnected("server closed connection")

    with pytest.raises(RunIncompleteError, match="connection_error"):
        run_ollama_bundle(
            bundle_root=bundle_root,
            output_dir=output_dir,
            run_id=RUN_ID,
            repo_root=REPO_ROOT,
            chat=disconnected,
            model_metadata=EXPECTED_MODEL,
        )

    status = read_json(output_dir / "runner_status.json")
    responses = read_jsonl(output_dir / "llm_responses.partial.jsonl")
    assert status["run_status"] == "incomplete"
    assert status["reason"] == "connection_error"
    assert status["written_rows"] == 1
    assert responses[0]["generation_failure"] == {
        "code": "connection_error",
        "detail": "RemoteDisconnected",
    }
