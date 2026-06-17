import pytest

from rast.schemas.common import SCHEMA_VERSION, Vector3
from rast.schemas.tokens import EntityToken, EventToken, EvidenceToken, RiskToken, UncertaintyToken


def test_entity_token_defaults_and_round_trip() -> None:
    token = EntityToken(
        token_id="ent_1",
        entity_id="Chair|1",
        category="chair",
        position=Vector3(x=1.0, y=0.0, z=2.0),
        distance_to_agent=2.2,
    )

    payload = token.to_dict()
    restored = EntityToken(**payload)

    assert restored.schema_version == SCHEMA_VERSION
    assert restored.type == "EntityToken"
    assert restored.confidence == 1.0
    assert restored.entity_id == "Chair|1"


def test_risk_token_serializes_required_contract() -> None:
    token = RiskToken(
        token_id="risk_1",
        risk_type="near_path_obstacle",
        severity="high",
        entity_id="Chair|1",
        affected_area={"radius": 0.5},
        risk_score=0.8,
        recommended_policy="slow_down_or_replan",
    )

    payload = token.to_dict()

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["type"] == "RiskToken"
    assert payload["affected_area"]["radius"] == 0.5
    assert payload["confidence"] == 1.0


def test_event_token_serializes_required_contract() -> None:
    token = EventToken(
        token_id="evt_1",
        event_type="object_moved",
        entity_id="Box|1",
        previous_state={"position": {"x": 0.0, "y": 0.0, "z": 1.0}},
        current_state={"position": {"x": 0.0, "y": 0.0, "z": 1.3}},
        severity="medium",
        timestamp=2,
    )

    payload = token.to_dict()

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["type"] == "EventToken"
    assert payload["event_type"] == "object_moved"
    assert payload["confidence"] == 1.0


def test_uncertainty_token_serializes_required_contract() -> None:
    token = UncertaintyToken(
        token_id="unc_1",
        uncertainty_type="partial_occlusion",
        entity_id="Box|uncertain",
        level="high",
        recommended_action="inspect_before_passing",
        occluded_by="Chair|1",
        timestamp=3,
    )

    payload = token.to_dict()

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["type"] == "UncertaintyToken"
    assert payload["uncertainty_type"] == "partial_occlusion"
    assert payload["level"] == "high"
    assert payload["confidence"] == 1.0


def test_evidence_token_serializes_metadata_pointer_contract() -> None:
    token = EvidenceToken(
        token_id="ev_1",
        evidence_type="risk_feature",
        source="windows_metadata_sim_metadata",
        pointer="metadata://WindowsRoom1/step/1/objects/Box|1",
        entity_id="Box|1",
        related_token_ids=["risk_1"],
        snapshot_ref="windows_metadata_sim:WindowsRoom1:step:1",
        evidence_features={"risk_score": 0.8},
        timestamp=1,
    )

    payload = token.to_dict()

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["type"] == "EvidenceToken"
    assert payload["evidence_type"] == "risk_feature"
    assert payload["related_token_ids"] == ["risk_1"]


def test_entity_token_requires_distance_to_agent() -> None:
    with pytest.raises(Exception):
        EntityToken(
            token_id="ent_missing_distance",
            entity_id="Chair|1",
            category="chair",
            position=Vector3(x=1.0, y=0.0, z=2.0),
        )
