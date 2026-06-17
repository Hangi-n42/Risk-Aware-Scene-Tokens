from rast.planner.actions import Action
from rast.schemas.decision import PlannerDecision
from rast.schemas.tokens import EventToken, UncertaintyToken
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.evidence_tokenizer import attach_decision_evidence_ids, build_evidence_tokens, count_evidence_types
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig, build_risk_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_evidence_tokenizer_links_risk_uncertainty_event_and_decision() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    risks = build_risk_tokens(entities, config=RiskTokenizerConfig(near_agent_threshold=1.6))
    uncertainty = UncertaintyToken(
        token_id="unc_test",
        uncertainty_type="unknown_object",
        entity_id=entities[0].entity_id,
        level="high",
        recommended_action="treat_as_risk",
        timestamp=snapshot.step,
    )
    event = EventToken(
        token_id="evt_test",
        event_type="risk_changed",
        entity_id=entities[0].entity_id,
        previous_state={"risk": False},
        current_state={"risk": True},
        severity="high",
        timestamp=snapshot.step,
    )
    decision = PlannerDecision(
        planner_name="rast",
        action=Action.ROTATE_RIGHT,
        reason_code="high_risk_token",
        reason_text="RiskToken is present.",
        trigger_object_ids=[risks[0].entity_id],
        trigger_token_ids=[risks[0].token_id],
        trigger_features={"risk_score": risks[0].risk_score},
    )

    evidence = build_evidence_tokens(
        snapshot,
        risks=risks[:1],
        uncertainties=[uncertainty],
        events=[event],
        decisions=[decision],
    )
    counts = count_evidence_types(evidence)

    assert counts["risk_feature"] == 1
    assert counts["uncertainty_feature"] == 1
    assert counts["event_diff"] == 1
    assert counts["planner_decision"] == 1
    assert any(risks[0].token_id in token.related_token_ids for token in evidence)
    assert any(uncertainty.token_id in token.related_token_ids for token in evidence)
    assert any(event.token_id in token.related_token_ids for token in evidence)


def test_attach_decision_evidence_ids_adds_planner_evidence_reference() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    risks = build_risk_tokens(entities, config=RiskTokenizerConfig(near_agent_threshold=1.6))
    decision = PlannerDecision(
        planner_name="rast",
        action=Action.ROTATE_RIGHT,
        reason_code="high_risk_token",
        reason_text="RiskToken is present.",
        trigger_object_ids=[risks[0].entity_id],
        trigger_token_ids=[risks[0].token_id],
        trigger_features={"risk_score": risks[0].risk_score},
    )
    evidence = build_evidence_tokens(snapshot, risks=risks[:1], decisions=[decision])

    attached = attach_decision_evidence_ids([decision], evidence)

    assert attached[0].evidence_token_ids
    assert attached[0].evidence_token_ids[0].startswith("ev_decision_")
