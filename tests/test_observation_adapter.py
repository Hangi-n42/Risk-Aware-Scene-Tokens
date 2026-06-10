import json
from pathlib import Path

import pytest

from rast.simulator.observation_adapter import metadata_to_observation_snapshot


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_ai2thor_metadata.json"


def load_fixture_metadata() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_metadata_maps_to_observation_snapshot() -> None:
    snapshot = metadata_to_observation_snapshot(
        load_fixture_metadata(),
        step=7,
        episode_id="adapter_fixture_episode",
        metadata_snapshot_ref=str(FIXTURE_PATH),
    )

    assert snapshot.scene_id == "FloorPlan1"
    assert snapshot.step == 7
    assert snapshot.episode_id == "adapter_fixture_episode"
    assert snapshot.agent_state.position.x == 0.0
    assert snapshot.agent_state.rotation is not None
    assert snapshot.agent_state.rotation.y == 90.0
    assert len(snapshot.objects) == 4
    assert sum(obj.visible is True for obj in snapshot.objects) == 3

    near = next(obj for obj in snapshot.objects if obj.category == "Chair")
    assert near.object_id.startswith("Chair|near")
    assert near.position.x == 0.4
    assert near.position.z == 0.3
    assert near.distance_to_agent == 0.5
    assert near.bbox_2d is not None
    assert near.bbox_2d.width == 80
    assert near.raw["objectType"] == "Chair"


def test_adapter_raises_clear_error_for_missing_core_field() -> None:
    metadata = load_fixture_metadata()
    del metadata["agent"]

    with pytest.raises(ValueError, match="agent"):
        metadata_to_observation_snapshot(metadata)
