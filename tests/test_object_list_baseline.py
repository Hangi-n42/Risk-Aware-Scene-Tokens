from rast.baselines.audit import object_list_audit
from rast.baselines.object_list import build_object_list
from rast.tokenizer.entity_tokenizer import build_entity_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_object_list_baseline_uses_same_visible_object_source_as_entity_tokens() -> None:
    snapshot = load_sample_snapshot()

    object_list = build_object_list(snapshot)
    entity_tokens = build_entity_tokens(snapshot)

    assert len(object_list) == len(entity_tokens) == 3
    assert {item.object_id for item in object_list} == {token.entity_id for token in entity_tokens}


def test_object_list_baseline_excludes_rast_only_fields() -> None:
    snapshot = load_sample_snapshot()

    object_list = build_object_list(snapshot)
    payload = object_list[0].to_dict()

    assert "risk_score" not in payload
    assert "recommended_policy" not in payload
    assert "risk_type" not in payload


def test_object_list_audit_declares_accessible_and_forbidden_fields() -> None:
    audit = object_list_audit()

    assert audit.baseline_type == "object_list"
    assert "object_id" in audit.accessible_fields
    assert "distance_to_agent" in audit.accessible_fields
    assert "risk_score" in audit.forbidden_fields
    assert "recommended_policy" in audit.forbidden_fields
