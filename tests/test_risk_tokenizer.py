from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig, build_risk_tokens

from tests.test_entity_tokenizer import load_sample_snapshot


def test_risk_tokenizer_creates_risk_for_near_object_only() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    config = RiskTokenizerConfig(near_agent_threshold=1.6)

    risks = build_risk_tokens(entities, config=config)

    assert len(risks) == 1
    assert risks[0].entity_id.startswith("Chair|near")
    assert risks[0].risk_type == "near_agent_obstacle"
    assert risks[0].severity == "high"
    assert risks[0].risk_score is not None
    assert risks[0].risk_score > 0.0


def test_risk_tokenizer_does_not_create_risk_for_far_object() -> None:
    snapshot = load_sample_snapshot()
    entities = build_entity_tokens(snapshot)
    config = RiskTokenizerConfig(near_agent_threshold=1.6)

    risks = build_risk_tokens(entities, config=config)
    risk_entity_ids = {risk.entity_id for risk in risks}

    assert not any(entity_id.startswith("Sofa|far") for entity_id in risk_entity_ids)
    assert not any(entity_id.startswith("Mug|target") for entity_id in risk_entity_ids)
