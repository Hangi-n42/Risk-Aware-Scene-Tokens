"""Metadata 기반 EvidenceToken 생성 유틸리티입니다."""

from __future__ import annotations

from typing import Any, Iterable

from rast.schemas.decision import PlannerDecision
from rast.schemas.observation import ObjectMetadata, ObservationSnapshot
from rast.schemas.tokens import EvidenceToken, EventToken, RiskToken, UncertaintyToken


def build_evidence_tokens(
    snapshot: ObservationSnapshot,
    *,
    risks: Iterable[RiskToken] | None = None,
    uncertainties: Iterable[UncertaintyToken] | None = None,
    events: Iterable[EventToken] | None = None,
    decisions: Iterable[PlannerDecision | dict[str, Any]] | None = None,
    source: str = "windows_metadata_sim_metadata",
) -> list[EvidenceToken]:
    """Risk, uncertainty, event, planner decision의 metadata evidence pointer를 생성합니다."""

    object_by_id = {item.object_id: item for item in snapshot.objects}
    snapshot_ref = snapshot.metadata_snapshot_ref or f"{source}:{snapshot.scene_id}:step:{snapshot.step}"
    evidence: list[EvidenceToken] = []

    for index, risk in enumerate(risks or []):
        obj = object_by_id.get(risk.entity_id)
        evidence.append(
            EvidenceToken(
                token_id=f"ev_risk_{snapshot.step}_{index}_{_safe_id(risk.entity_id)}",
                evidence_type="risk_feature",
                source=source,
                pointer=_object_pointer(snapshot, risk.entity_id, source=source),
                timestamp=snapshot.step,
                entity_id=risk.entity_id,
                related_token_ids=[risk.token_id],
                bbox_2d=obj.bbox_2d if obj is not None else None,
                metadata_path=f"objects[{risk.entity_id}].risk_features",
                snapshot_ref=snapshot_ref,
                confidence_source="oracle_metadata",
                evidence_features={
                    "risk_type": risk.risk_type,
                    "severity": risk.severity,
                    "risk_score": risk.risk_score,
                    "affected_area": risk.affected_area,
                    "risk_features": risk.risk_features,
                },
            )
        )

    for index, uncertainty in enumerate(uncertainties or []):
        obj = object_by_id.get(uncertainty.entity_id)
        evidence.append(
            EvidenceToken(
                token_id=f"ev_uncertainty_{snapshot.step}_{index}_{_safe_id(uncertainty.entity_id)}",
                evidence_type="uncertainty_feature",
                source=source,
                pointer=_object_pointer(snapshot, uncertainty.entity_id, source=source),
                timestamp=snapshot.step,
                entity_id=uncertainty.entity_id,
                related_token_ids=[uncertainty.token_id],
                bbox_2d=obj.bbox_2d if obj is not None else None,
                metadata_path=f"objects[{uncertainty.entity_id}].uncertainty_features",
                snapshot_ref=snapshot_ref,
                confidence_source="synthetic_metadata_uncertainty",
                evidence_features={
                    "uncertainty_type": uncertainty.uncertainty_type,
                    "level": uncertainty.level,
                    "variance": uncertainty.variance,
                    "possible_categories": uncertainty.possible_categories,
                    "occluded_by": uncertainty.occluded_by,
                    "sensor_agreement": uncertainty.sensor_agreement,
                    "recommended_action": uncertainty.recommended_action,
                    "uncertainty_features": uncertainty.uncertainty_features,
                },
            )
        )

    for index, event in enumerate(events or []):
        obj = object_by_id.get(event.entity_id)
        evidence.append(
            EvidenceToken(
                token_id=f"ev_event_{snapshot.step}_{index}_{_safe_id(event.entity_id)}",
                evidence_type="event_diff",
                source=source,
                pointer=f"{snapshot_ref}/events/{event.token_id}",
                timestamp=snapshot.step,
                entity_id=event.entity_id,
                related_token_ids=[event.token_id],
                bbox_2d=obj.bbox_2d if obj is not None else None,
                metadata_path=f"diff.objects[{event.entity_id}]",
                snapshot_ref=snapshot_ref,
                confidence_source="semantic_metadata_diff",
                evidence_features={
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "previous_state": event.previous_state,
                    "current_state": event.current_state,
                },
            )
        )

    for index, decision in enumerate(decisions or []):
        payload = _decision_payload(decision)
        planner_name = str(payload.get("planner_name") or "planner")
        reason_code = str(payload.get("reason_code") or "")
        action = str(payload.get("action") or "")
        trigger_token_ids = list(payload.get("trigger_token_ids") or [])
        trigger_object_ids = list(payload.get("trigger_object_ids") or [])
        entity_id = trigger_object_ids[0] if trigger_object_ids else None
        obj = object_by_id.get(entity_id) if entity_id is not None else None
        evidence_id = f"ev_decision_{snapshot.step}_{index}_{_safe_id(planner_name)}"
        evidence.append(
            EvidenceToken(
                token_id=evidence_id,
                evidence_type="planner_decision",
                source=source,
                pointer=f"{snapshot_ref}/decisions/{planner_name}/{reason_code or action}",
                timestamp=snapshot.step,
                entity_id=entity_id,
                related_token_ids=trigger_token_ids,
                related_decision_ids=[f"{planner_name}:{action}:{reason_code}"],
                bbox_2d=obj.bbox_2d if obj is not None else None,
                metadata_path=f"decisions[{planner_name}]",
                snapshot_ref=snapshot_ref,
                confidence_source="rule_based_planner",
                evidence_features={
                    "planner_name": planner_name,
                    "action": action,
                    "reason_code": reason_code,
                    "trigger_object_ids": trigger_object_ids,
                    "trigger_features": payload.get("trigger_features") or {},
                },
            )
        )

    return evidence


def attach_decision_evidence_ids(
    decisions: Iterable[PlannerDecision],
    evidence_tokens: Iterable[EvidenceToken],
) -> list[PlannerDecision]:
    """PlannerDecision별로 연결 가능한 EvidenceToken id를 채워 새 decision list로 반환합니다."""

    evidence_by_decision: dict[str, list[str]] = {}
    for token in evidence_tokens:
        if token.evidence_type != "planner_decision":
            continue
        planner_name = str(token.evidence_features.get("planner_name") or "")
        if planner_name:
            evidence_by_decision.setdefault(planner_name, []).append(token.token_id)

    attached: list[PlannerDecision] = []
    for decision in decisions:
        ids = evidence_by_decision.get(decision.planner_name, [])
        if hasattr(decision, "model_copy"):
            attached.append(decision.model_copy(update={"evidence_token_ids": ids}))
        else:
            attached.append(decision.copy(update={"evidence_token_ids": ids}))
    return attached


def count_evidence_types(tokens: Iterable[EvidenceToken]) -> dict[str, int]:
    """EvidenceToken type별 count를 계산합니다."""

    counts: dict[str, int] = {}
    for token in tokens:
        counts[token.evidence_type] = counts.get(token.evidence_type, 0) + 1
    return counts


def _object_pointer(snapshot: ObservationSnapshot, entity_id: str, *, source: str) -> str:
    return f"{source}:{snapshot.scene_id}:step:{snapshot.step}:objects:{entity_id}"


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value)[:80]


def _decision_payload(decision: PlannerDecision | dict[str, Any]) -> dict[str, Any]:
    if isinstance(decision, PlannerDecision):
        return decision.to_dict()
    return dict(decision)
