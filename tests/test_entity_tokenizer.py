import json
from pathlib import Path

from rast.schemas.common import BBox2D, Vector3
from rast.schemas.observation import AgentState, ObjectMetadata, ObservationSnapshot
from rast.tokenizer.entity_tokenizer import build_entity_tokens


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_ai2thor_metadata.json"


def load_sample_snapshot() -> ObservationSnapshot:
    metadata = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    agent = metadata["agent"]
    objects = []
    for item in metadata["objects"]:
        bbox = item.get("bbox2D")
        objects.append(
            ObjectMetadata(
                object_id=item["objectId"],
                category=item["objectType"],
                position=Vector3(**item["position"]),
                visible=item.get("visible"),
                distance_to_agent=item.get("distance"),
                bbox_2d=BBox2D(**bbox) if bbox else None,
            )
        )

    return ObservationSnapshot(
        scene_id=metadata["sceneName"],
        step=0,
        episode_id="fixture_episode",
        agent_state=AgentState(
            position=Vector3(**agent["position"]),
            rotation=Vector3(**agent["rotation"]),
            horizon=agent.get("cameraHorizon"),
        ),
        objects=objects,
        metadata_snapshot_ref=str(FIXTURE_PATH),
        source="oracle_metadata",
    )


def test_entity_tokenizer_uses_visible_objects_only() -> None:
    snapshot = load_sample_snapshot()

    tokens = build_entity_tokens(snapshot)

    assert len(snapshot.objects) == 4
    assert len(tokens) == 3
    assert {token.category for token in tokens} == {"Chair", "Sofa", "Mug"}
    assert all(token.is_visible is True for token in tokens)


def test_entity_tokenizer_fills_required_fields() -> None:
    snapshot = load_sample_snapshot()

    tokens = build_entity_tokens(snapshot)
    near = next(token for token in tokens if token.category == "Chair")

    assert near.entity_id.startswith("Chair|near")
    assert near.distance_to_agent == 0.5
    assert near.confidence == 1.0
    assert near.source == "oracle_metadata"
    assert near.bbox_2d is not None
