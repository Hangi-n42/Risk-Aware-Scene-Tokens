from rast.schemas.common import SCHEMA_VERSION, Vector3
from rast.schemas.observation import AgentState, ObjectMetadata, ObservationSnapshot


def test_observation_snapshot_serializes_minimal_metadata() -> None:
    agent = AgentState(position=Vector3(x=0.0, y=0.0, z=0.0))
    obj = ObjectMetadata(
        object_id="Chair|1",
        category="chair",
        position=Vector3(x=1.0, y=0.0, z=2.0),
        distance_to_agent=2.2,
    )

    snapshot = ObservationSnapshot(
        scene_id="FloorPlan1",
        step=3,
        episode_id="episode_001",
        agent_state=agent,
        objects=[obj],
        raw_observation_ref="frames/episode_001_step_003.png",
    )

    payload = snapshot.to_dict()

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["objects"][0]["confidence"] == 1.0
    assert payload["objects"][0]["object_id"] == "Chair|1"
    assert payload["raw_observation_ref"].endswith(".png")
