"""MVP-0 tokenization pipeline입니다."""

from __future__ import annotations

from dataclasses import dataclass, field

from rast.schemas.metrics import GoalSpec
from rast.schemas.observation import ObservationSnapshot
from rast.schemas.tokens import AffordanceToken, EntityToken, EventToken, RelationToken, RiskToken, UncertaintyToken
from rast.token_memory.diff import state_from_tokens
from rast.token_memory.incremental_update import UpdateMode, compute_update_stats
from rast.token_memory.memory import TokenMemory
from rast.tokenizer.affordance_tokenizer import AffordanceTokenizerConfig, build_affordance_tokens
from rast.tokenizer.entity_tokenizer import build_entity_tokens
from rast.tokenizer.event_tokenizer import EventTokenizerConfig, build_event_tokens
from rast.tokenizer.relation_tokenizer import RelationTokenizerConfig, build_relation_tokens
from rast.tokenizer.risk_tokenizer import RiskTokenizerConfig, build_risk_tokens
from rast.tokenizer.uncertainty_tokenizer import UncertaintyTokenizerConfig, build_uncertainty_tokens


@dataclass(frozen=True)
class TokenizationResult:
    """EntityToken, RiskToken, optional EventToken을 명확히 분리해 반환합니다."""

    entities: list[EntityToken]
    risks: list[RiskToken]
    relations: list[RelationToken] = field(default_factory=list)
    uncertainties: list[UncertaintyToken] = field(default_factory=list)
    affordances: list[AffordanceToken] = field(default_factory=list)
    events: list[EventToken] = field(default_factory=list)
    update_mode: UpdateMode = "full_recompute"
    changed_object_count: int = 0
    affected_token_count: int = 0

    @property
    def tokens(self) -> list[EntityToken | RiskToken | RelationToken | UncertaintyToken | AffordanceToken | EventToken]:
        """Planner/logging에서 사용할 수 있는 평탄화된 token list입니다."""

        return [*self.entities, *self.relations, *self.risks, *self.uncertainties, *self.affordances, *self.events]


def tokenize_snapshot(
    snapshot: ObservationSnapshot,
    *,
    risk_config: RiskTokenizerConfig,
    visible_only: bool = True,
    token_memory: TokenMemory | None = None,
    event_config: EventTokenizerConfig | None = None,
    relation_config: RelationTokenizerConfig | None = None,
    uncertainty_config: UncertaintyTokenizerConfig | None = None,
    affordance_config: AffordanceTokenizerConfig | None = None,
    goal: GoalSpec | None = None,
    enable_relations: bool = False,
    enable_events: bool = False,
    enable_uncertainty: bool = False,
    enable_affordances: bool = False,
    update_mode: UpdateMode = "full_recompute",
) -> TokenizationResult:
    """ObservationSnapshot을 EntityToken, RiskToken, optional EventToken으로 변환합니다.

    token_generation latency는 runner나 외부 timer가 측정할 수 있도록
    이 함수 내부에서는 timer/logging side effect를 만들지 않습니다.
    """

    event_config = event_config or EventTokenizerConfig()
    entities = build_entity_tokens(snapshot, visible_only=visible_only)
    risks = build_risk_tokens(entities, config=risk_config)
    uncertainties = (
        build_uncertainty_tokens(
            snapshot,
            config=uncertainty_config or UncertaintyTokenizerConfig(risk_threshold=risk_config.near_agent_threshold),
            visible_only=visible_only,
        )
        if enable_uncertainty
        else []
    )
    relations = (
        build_relation_tokens(
            snapshot,
            entities,
            config=relation_config or RelationTokenizerConfig(near_agent_threshold=risk_config.near_agent_threshold),
            goal=goal,
        )
        if enable_relations
        else []
    )
    affordances = (
        build_affordance_tokens(
            snapshot,
            entities,
            risks,
            relations,
            uncertainties,
            config=affordance_config
            or AffordanceTokenizerConfig(
                path_lateral_threshold=relation_config.near_path_lateral_threshold
                if relation_config is not None
                else 0.5
            ),
        )
        if enable_affordances
        else []
    )
    events: list[EventToken] = []
    current_state = state_from_tokens(entities, risks)
    previous_state = token_memory.get_previous_state() if token_memory is not None else None
    if enable_events and token_memory is not None:
        events = build_event_tokens(
            previous_state,
            current_state,
            config=event_config,
            timestamp=snapshot.step,
        )
    update_stats = compute_update_stats(
        previous_state=previous_state,
        current_state=current_state,
        entities=entities,
        risks=risks,
        events=events,
        update_mode=update_mode,
        movement_threshold=event_config.movement_threshold,
        risk_score_delta_threshold=event_config.risk_score_delta_threshold,
    )
    if token_memory is not None and (enable_events or update_mode == "incremental"):
        token_memory.update(current_state)
    return TokenizationResult(
        entities=entities,
        risks=risks,
        relations=relations,
        uncertainties=uncertainties,
        affordances=affordances,
        events=events,
        update_mode=update_stats.update_mode,
        changed_object_count=update_stats.changed_object_count,
        affected_token_count=update_stats.affected_token_count,
    )
