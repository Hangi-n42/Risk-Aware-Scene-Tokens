import json
from pathlib import Path

from experiments.run_mvp0_vertical_slice import build_record_from_metadata


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_ai2thor_metadata.json"


def test_fixture_vertical_slice_builds_log_record() -> None:
    metadata = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    record = build_record_from_metadata(
        metadata=metadata,
        step=0,
        run_id="unit_fixture_run",
        episode_id="unit_fixture_episode",
        metadata_snapshot_ref=str(FIXTURE_PATH),
        risk_threshold=1.5,
        action_latency_ms=0.0,
    )

    assert record.scene_id == "FloorPlan1"
    assert record.baseline_type == "rast"
    assert record.selected_action != "MoveAhead"
    assert record.latency.perception == 0.0
    assert record.latency.token_generation >= 0.0
    assert record.latency.planning >= 0.0
    assert record.extra["phase"] == "oracle_tokenization"
    assert record.extra["entity_count"] == 3
    assert record.extra["risk_count"] == 1
    assert record.extra["object_list_count"] == 3
    assert len(record.tokens) == 4
