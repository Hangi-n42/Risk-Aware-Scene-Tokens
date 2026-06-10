from rast.tokenizer.pipeline import tokenize_snapshot
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig

from tests.test_entity_tokenizer import load_sample_snapshot


def test_tokenize_snapshot_returns_entities_and_risks() -> None:
    snapshot = load_sample_snapshot()

    result = tokenize_snapshot(
        snapshot,
        risk_config=RiskTokenizerConfig(near_agent_threshold=1.6),
    )

    assert len(result.entities) == 3
    assert len(result.risks) == 1
    assert len(result.tokens) == 4
    assert result.tokens[0].type == "EntityToken"
    assert result.tokens[-1].type == "RiskToken"
