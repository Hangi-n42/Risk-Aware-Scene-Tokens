from rast.baselines.audit import flat_feature_table_audit
from rast.baselines.flat_feature_table import build_flat_feature_table
from rast.planner.actions import Action
from rast.planner.flat_feature_planner import plan_from_flat_features
from rast.tokenizer.entity_tokenizer import build_entity_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_flat_feature_table_uses_same_visible_object_source_as_entity_tokens() -> None:
    snapshot = load_sample_snapshot()

    rows = build_flat_feature_table(snapshot, risk_threshold=1.5)
    entity_tokens = build_entity_tokens(snapshot)

    assert len(rows) == len(entity_tokens) == 3
    assert {row.object_id for row in rows} == {token.entity_id for token in entity_tokens}


def test_flat_feature_table_includes_scalar_features_without_token_contract_fields() -> None:
    snapshot = load_sample_snapshot()

    rows = build_flat_feature_table(snapshot, risk_threshold=1.5)
    payload = rows[0].to_dict()

    assert "risk_score_scalar" in payload
    assert "distance_to_path_proxy" in payload
    assert "within_risk_threshold" in payload
    assert "recommended_policy" not in payload
    assert "risk_type" not in payload
    assert "severity" not in payload
    assert "token_type" not in payload


def test_flat_feature_planner_uses_common_action_enum() -> None:
    snapshot = load_sample_snapshot()
    rows = build_flat_feature_table(snapshot, risk_threshold=1.5)

    decision = plan_from_flat_features(rows)

    assert isinstance(decision.action, Action)
    assert decision.reason_code in {"within_risk_threshold", "high_risk_score_scalar", "no_risk_scalar_move_ahead"}


def test_flat_feature_audit_forbids_token_contract_fields() -> None:
    audit = flat_feature_table_audit(input_unit_count=3)

    assert audit.baseline_type == "flat_feature_table"
    assert audit.input_unit_count == 3
    assert "risk_score_scalar" in audit.accessible_fields
    assert "recommended_policy" in audit.forbidden_fields
    assert "risk_type" in audit.forbidden_fields
    assert "severity" in audit.forbidden_fields
    assert "token_type" in audit.forbidden_fields
