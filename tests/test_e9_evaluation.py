from __future__ import annotations

import json
from pathlib import Path

from abstention_experiment.data import sha256_file
from abstention_experiment.layer2_common import read_jsonl
from abstention_experiment.layer2_evaluation import evaluate_layer2_run
from abstention_experiment.layer2_runtime import _parse_api_response


RUN_ID = "e9-pilot-20260918T120000Z-1234abcd"


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _api(content: str) -> dict[str, object]:
    return {
        "model": "gemma:7b-instruct",
        "created_at": "2026-09-18T12:00:00Z",
        "done": True,
        "done_reason": "stop",
        "message": {"content": content},
    }


def test_evaluator_applies_fallback_and_computes_counts(tmp_path: Path) -> None:
    sidecar_path = tmp_path / "evaluation_sidecar.jsonl"
    sidecar_rows = [
        {"input_index": 0, "day": "monday", "id": 10, "binary_label": 0, "p_attack": 0.4, "confidence": 0.6, "predicted_label": 0, "is_error": 0},
        {"input_index": 1, "day": "tuesday", "id": 11, "binary_label": 1, "p_attack": 0.4, "confidence": 0.6, "predicted_label": 0, "is_error": 1},
        {"input_index": 2, "day": "wednesday", "id": 12, "binary_label": 1, "p_attack": 0.6, "confidence": 0.6, "predicted_label": 1, "is_error": 0},
        {"input_index": 3, "day": "thursday", "id": 13, "binary_label": 0, "p_attack": 0.6, "confidence": 0.6, "predicted_label": 1, "is_error": 1},
    ]
    _write_jsonl(sidecar_path, sidecar_rows)

    export_manifest_path = tmp_path / "manifest.json"
    _write_json(
        export_manifest_path,
        {
            "run_id": RUN_ID,
            "counts": {"exported_rows": 4},
            "integrity": {"evaluation_sidecar_sha256": sha256_file(sidecar_path)},
        },
    )
    run_manifest_path = tmp_path / "run_manifest.json"
    _write_json(
        run_manifest_path,
        {
            "run_id": RUN_ID,
            "run_manifest_schema_version": "e9-run-manifest-v1",
            "input_bundle": {"manifest_sha256": sha256_file(export_manifest_path)},
        },
    )
    runner_status_path = tmp_path / "runner_status.json"
    _write_json(
        runner_status_path,
        {
            "run_id": RUN_ID,
            "status_schema_version": "e9-runner-status-v1",
            "run_status": "completed",
            "expected_rows": 4,
            "written_rows": 4,
            "last_input_index": 3,
        },
    )
    responses = [
        _parse_api_response(RUN_ID, 0, 200, _api('{"decision":"ATTACK"}'), 0.1),
        _parse_api_response(RUN_ID, 1, 200, _api('{"decision":"ATTACK"}'), 0.2),
        _parse_api_response(RUN_ID, 2, 200, _api('{"decision":"INDETERMINATE"}'), 0.3),
        _parse_api_response(RUN_ID, 3, 200, _api("not-json"), 0.4),
    ]
    responses[3]["generation_failure"] = {"code": "timeout", "detail": "test timeout"}
    responses_path = tmp_path / "llm_responses.jsonl"
    _write_jsonl(responses_path, responses)

    output_dir = tmp_path / "evaluation"
    metrics = evaluate_layer2_run(
        export_manifest_path=export_manifest_path,
        evaluation_sidecar_path=sidecar_path,
        run_manifest_path=run_manifest_path,
        runner_status_path=runner_status_path,
        responses_path=responses_path,
        output_dir=output_dir,
    )

    assert metrics["counts"] == {
        "n_rows": 4,
        "llm_binary_decision_count": 2,
        "indeterminate_count": 1,
        "generation_failure_count": 1,
        "fallback_count": 2,
        "override_count": 2,
        "timeout_count": 1,
        "parsing_failure_count": 0,
        "schema_valid_count": 3,
    }
    assert metrics["gate_forced"]["error_count"] == 2
    assert metrics["end_to_end"]["error_count"] == 2
    assert metrics["llm_valid_only"]["n_rows"] == 2
    assert metrics["transitions"] == {
        "gate_correct_final_correct": 1,
        "gate_correct_final_error": 1,
        "gate_error_final_correct": 1,
        "gate_error_final_error": 1,
    }

    records = read_jsonl(output_dir / "evaluation_records.jsonl")
    assert records[2]["fallback_applied"] is True
    assert records[2]["fallback_reason"] == "indeterminate"
    assert records[2]["final_predicted_label"] == records[2]["gate_predicted_label"]
    assert records[3]["fallback_applied"] is True
    assert records[3]["fallback_reason"] == "generation_failure"
    assert records[3]["final_predicted_label"] == records[3]["gate_predicted_label"]
