from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from abstention_experiment.layer2_export import (
    PROMPT_FORBIDDEN_FIELDS,
    load_input_feature_schema,
    serialized_input_record,
    validate_schema_snapshot,
)
from abstention_experiment.layer2_runtime import load_prompt_asset


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "configs/llm/e9_input_feature_schema.json"
PROMPT_PATH = REPO_ROOT / "configs/llm/e9_prompt_v1.json"


def test_schema_snapshot_matches_whitelist() -> None:
    schema = load_input_feature_schema(SCHEMA_PATH)

    validate_schema_snapshot(schema, REPO_ROOT)

    assert schema.schema_version == "e9-input-v1"
    assert len(schema.features) == 59
    assert not (set(schema.features) & PROMPT_FORBIDDEN_FIELDS)


def test_schema_snapshot_rejects_changed_whitelist(tmp_path: Path) -> None:
    schema = load_input_feature_schema(SCHEMA_PATH)
    changed = tmp_path / "configs/features_whitelist.json"
    changed.parent.mkdir(parents=True)
    changed.write_text('{"include": []}\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="source whitelist hash"):
        validate_schema_snapshot(schema, tmp_path)


def test_prompt_asset_and_rendered_payload_follow_leakage_contract() -> None:
    schema = load_input_feature_schema(SCHEMA_PATH)
    prompt = load_prompt_asset(PROMPT_PATH)
    values = {feature: index + 0.5 for index, feature in enumerate(schema.features)}
    values["Protocol"] = "TCP"
    row = pd.Series(
        {
            "input_index": 0,
            **values,
            "day": "monday",
            "id": 123,
            "binary_label": 1,
            "predicted_label": 0,
            "confidence": 0.51,
        }
    )

    record = serialized_input_record(row, schema)
    flow_features = record["payload"]["flow_features"]
    rendered = prompt.render(flow_features)
    rendered_payload = json.loads(
        rendered.split("<flow_features>\n", 1)[1].split("\n</flow_features>", 1)[0]
    )

    assert prompt.prompt_version == "e9-v1"
    assert prompt.placeholder not in rendered
    assert list(rendered_payload) == list(schema.features)
    assert not (set(rendered_payload) & PROMPT_FORBIDDEN_FIELDS)
    assert "monday" not in rendered
    assert "binary_label" not in rendered


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("prompt_version", "e9-v2"),
        ("flow_features_placeholder", "{{FLOW}}"),
    ],
)
def test_prompt_asset_rejects_contract_changes(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    payload = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))
    payload[field] = value
    path = tmp_path / "prompt.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        load_prompt_asset(path)
