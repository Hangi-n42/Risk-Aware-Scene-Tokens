# RAST: Risk-Aware Scene Tokens PRD v0.2

## 1. 기존 PRD의 주요 문제점 요약

기존 v0.1 PRD는 RAST의 핵심 아이디어, token 종류, MVP 범위, baseline 비교의 큰 방향을 잘 담고 있었습니다. 특히 AS-IS와 TO-BE의 기본 대비, AI2-THOR 기반 MVP, rule-based planner, token schema 초안은 연구형 프로토타입을 시작하기에 충분한 골격을 제공했습니다.

다만 연구 검토나 지도교수/심사자 피드백을 견디기 위해서는 다음 약점이 보강되어야 합니다.

| 문제 영역 | 기존 약점 | v0.2에서 필요한 보강 |
|---|---|---|
| Latency accounting | planning latency 중심으로 서술되어 token generation overhead가 전체 지연을 상쇄할 가능성이 충분히 분리되지 않았습니다. | `T_total = T_observation + T_perception + T_token_generation + T_planning + T_action` 기준으로 end-to-end latency를 분해해 측정해야 합니다. |
| Oracle tokenization의 한계 | simulator metadata 기반 tokenization이 MVP에 적합하다는 점은 설명했지만, 실제 perception latency와 generalization을 증명하지 않는다는 caveat가 약했습니다. | Phase 1 Oracle Tokenization과 Phase 2 Perception-Bound Tokenization을 명확히 분리해야 합니다. |
| Baseline 공정성 | raw, object list, scene graph, RAST 비교는 있었지만, RAST가 더 많은 정보를 받아서 유리해지는 문제를 막는 protocol이 부족했습니다. | 동일 observation source와 동일 accessible information에서 시작하는 Information-Bound Evaluation Protocol이 필요합니다. |
| 구조화 효과 분리 | RAST의 성능 향상이 token 구조 때문인지, 단순히 더 많은 scalar feature 때문인지 분리하기 어려웠습니다. | RAST와 동일 scalar feature를 flat table로 제공하는 Baseline D를 추가해야 합니다. |
| Token 범용성 | RiskToken과 AffordanceToken이 simulator/task-specific heuristic으로 보일 위험이 있었습니다. | Token Schema와 Token Extractor를 분리하고, schema는 planner-facing interface로 정의해야 합니다. |
| Incremental update | EventToken의 필요성은 있었지만, 매 frame 전체 token 재계산 대신 Token Memory 기반 incremental update를 핵심 구조로 충분히 강조하지 않았습니다. | semantic event-driven update와 incremental update benefit metric을 포함해야 합니다. |
| Generalization 검증 | seen/unseen scene, unknown object, noise, occlusion scenario가 평가 protocol로 충분히 분리되지 않았습니다. | seen/unseen, noise, unknown, occlusion을 evaluation axis로 명시해야 합니다. |

## 2. v0.2에서 강화한 핵심 변경사항

v0.2는 기존 구조를 유지하되, 연구적 약점을 방어할 수 있도록 다음을 강화했습니다.

| 변경사항 | 설명 |
|---|---|
| Latency Accounting Protocol 추가 | planning latency와 end-to-end latency를 분리하고, token별 generation latency까지 기록하는 protocol을 추가했습니다. |
| Phase 1/Phase 2 분리 | metadata 기반 oracle tokenization은 representation 검증용, perception-bound tokenization은 실제 overhead 검증용으로 구분했습니다. |
| Information-Bound Evaluation Protocol 추가 | 모든 baseline이 동일 observation source와 동일 accessible information에서 시작하도록 비교 조건을 명시했습니다. |
| Baseline D: Flat Feature Table 추가 | RAST와 동일 scalar feature를 쓰되 token contract 없이 제공하여, 정보량 효과와 구조화 효과를 분리합니다. |
| Ablation Study Plan 강화 | Risk, Event, Uncertainty, Relation, EvidenceToken 제거 실험을 포함했습니다. |
| Token Schema와 Extractor 분리 | RAST를 고정 heuristic이 아니라 planner-facing token schema로 정의했습니다. |
| RiskToken 설계 일반화 | object class 중심이 아니라 geometry, path relevance, uncertainty, time-to-collision 중심 risk score를 제안했습니다. |
| AffordanceToken MVP 범위 제한 | MVP에서는 indoor navigation affordance로 제한하고 manipulation affordance는 후속 확장으로 분리했습니다. |
| Generalization axis 추가 | seen/unseen scene, unknown object, noise injection, occlusion scenario를 평가 축으로 포함했습니다. |
| Success Criteria 재정의 | latency, safety metric, explainability, incremental update benefit을 성공 기준에 추가했습니다. |

## 3. 수정된 PRD 전체본

### 3.1 제목

RAST: Risk-Aware Scene Tokens

### 3.2 문서 버전

- 버전: v0.2
- 작성일: 2026-06-09
- 문서 상태: 연구 검토용 PRD 초안
- 임시 프로젝트명: RAST, Risk-Aware Scene Tokens
- MVP 기준 simulator: AI2-THOR 우선 검토

### 3.3 Executive Summary

RAST는 Physical AI, Embodied AI, Robotics 환경에서 raw sensor data와 planner 사이의 명시적 중간 표현을 설계하기 위한 연구형 프로토타입입니다. 현재 로봇 perception pipeline은 RGB-D, LiDAR, segmentation, detection, dense feature처럼 풍부하지만 무거운 데이터를 다루는 반면, planner가 실제로 필요로 하는 정보는 위험, 관계, 변화, 불확실성, 행동 가능성 등 action-relevant subset인 경우가 많습니다. RAST는 raw observation을 Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence token stream으로 변환하여 planner가 바로 사용할 수 있는 planning-facing scene representation을 제공합니다. 이 표현의 목적은 단순 압축이 아니라 safety-critical information을 보존하는 risk-aware representation을 설계하는 것입니다. MVP는 AI2-THOR 기반 indoor navigation 환경에서 simulator metadata 기반 oracle tokenization, Token Memory, incremental update, rule-based planner, baseline 비교, 실험 logging, 간단한 시각화를 구현합니다. 다만 Phase 1은 실제 perception latency를 검증했다고 주장하지 않고, representation과 planner interface의 유효성을 검증하는 단계로 제한합니다. Phase 2에서는 RGB-D, segmentation, detector output 등을 이용한 perception-bound tokenization으로 확장하여 token generation overhead를 포함한 end-to-end latency를 검증합니다.

### 3.4 Problem Statement

현재 로봇의 perception-to-planning pipeline은 센서 입력을 풍부하게 유지하는 방향으로 발전해 왔습니다. RGB image, depth image, LiDAR point cloud, segmentation mask, object detection result, dense visual feature는 장면 정보를 많이 담지만 planner 입장에서는 매 step마다 처리하기에 계산량과 memory cost가 큽니다.

문제는 planner가 항상 전체 픽셀이나 dense feature를 필요로 하지는 않는다는 점입니다. 예를 들어 navigation planner가 필요한 정보는 "앞에 의자가 있다", "경로 근처에 unknown object가 있다", "방금 장애물이 등장했다", "저 영역은 occlusion 때문에 불확실하다", "이 통로는 지나갈 수 있지만 여유가 좁다" 같은 구조화된 action-relevant information입니다.

단순 object list는 객체의 존재와 위치를 표현할 수 있지만 위험도, 경로 관련성, 불확실성, 시간적 변화, affordance를 충분히 제공하지 못합니다. 일반 scene graph는 객체 간 관계 표현에는 강점이 있으나, planner가 직접 소비할 수 있는 risk contract, update semantics, evidence pointer가 명확하지 않은 경우가 많습니다. 결과적으로 raw perception과 planning 사이의 interface가 불명확해지고, 정보 압축 과정에서 safety-critical information이 손실될 수 있습니다.

RAST는 이 문제를 "planner-facing scene token contract"로 다룹니다. 즉, perception 결과를 단순히 줄이는 것이 아니라 planner decision에 필요한 정보와 다시 확인해야 할 evidence를 명시적으로 남기는 중간 표현을 설계하고, simulation benchmark에서 그 장단점을 검증합니다.

동시에 RAST의 성능 주장은 신중해야 합니다. token generation이 느리면 planning latency가 줄어도 전체 시스템 latency는 줄지 않을 수 있습니다. 또한 RAST가 scene graph보다 좋은 결과를 보이더라도, 단순히 더 많은 정보를 받았기 때문일 수 있습니다. 따라서 v0.2 PRD는 latency accounting, information-bound comparison, ablation study, seen/unseen generalization을 평가 설계의 핵심으로 둡니다.

### 3.5 AS-IS

현재 구조는 대체로 raw observation 또는 perception 결과를 planner가 직접 또는 간접적으로 소비하는 형태입니다. 이 구조는 정보량은 풍부하지만, planner가 매번 많은 정보를 해석해야 하고 safety-critical cue가 명시적으로 분리되지 않는 한계가 있습니다.

| 항목 | 현재 상태 | 한계 |
|---|---|---|
| 현재 입력 데이터 형태 | RGB, Depth, semantic segmentation, instance segmentation, object detection, simulator metadata, point cloud | 입력 차원이 크고 step마다 처리 비용이 큽니다. |
| 현재 perception pipeline | sensor -> detection/segmentation -> object list 또는 map update -> planner | 위험, 불확실성, event, affordance가 별도 contract로 보존되지 않을 수 있습니다. |
| 현재 planner가 받는 정보 | occupancy grid, object list, scene graph, waypoint, local map | planner가 필요한 정보와 perception 출력 사이에 semantic mismatch가 있습니다. |
| 병목 지점 | dense image processing, map update, graph construction, repeated full-scene processing | latency, memory footprint, planning complexity가 증가합니다. |
| 안전성 측면 한계 | unknown object, occlusion, low confidence, near-path object가 암묵적으로 처리될 수 있음 | safety-critical signal이 누락되거나 후순위 feature로 취급될 수 있습니다. |
| 변화 감지 | 매 step full update 또는 task-specific diff | 방금 변한 객체와 위험도가 증가한 객체를 planner-facing event로 주지 못할 수 있습니다. |
| baseline 비교 관행 | raw/object list/scene graph를 단순 비교 | 각 방법이 받은 정보량이 달라지면 공정한 비교가 어렵습니다. |
| 개인 연구자의 현실적 한계 | 실제 로봇, 센서 calibration, embedded deployment, real-time inference 환경 구축이 어렵습니다. | MVP 단계에서는 simulator metadata와 rule-based evaluation으로 시작하되, generalization을 증명했다고 주장하면 안 됩니다. |

AS-IS의 핵심 메시지는 다음과 같습니다. 로봇은 너무 많은 raw sensory data를 처리하지만 planner가 실제로 필요한 정보는 그중 일부입니다. 기존 object list나 scene graph는 구조화된 장면 이해에는 유용하지만, 위험, 불확실성, 시공간 변화, 행동 가능성을 planner-facing interface로 충분히 제공하지 못합니다.

### 3.6 TO-BE

RAST는 raw observation을 action-relevant token stream으로 변환하여 planner가 직접 사용할 수 있는 scene interface를 제공합니다. 이 token stream은 객체, 관계, 사건, 위험, 행동 가능성, 불확실성, 근거 포인터를 분리해 표현합니다.

| 항목 | AS-IS | TO-BE: RAST |
|---|---|---|
| perception interface | raw image, object list, scene graph 중심 | Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence token stream |
| planner 입력 | dense 또는 task별 ad hoc structure | planner가 직접 사용할 수 있는 token contract |
| 위험 표현 | collision check 또는 cost map에 암묵적으로 반영 | RiskToken으로 risk type, severity, affected path segment를 명시 |
| 장면 변화 처리 | 매 step full perception 또는 map update | Token Memory와 EventToken 기반 semantic event-driven update |
| 불확실성 처리 | confidence score 일부만 사용 | UncertaintyToken으로 classification, position, occlusion, sensor disagreement 보존 |
| 압축 방식 | feature reduction 또는 object extraction | safety-critical information을 보존하는 risk-aware compression |
| token 생성 방식 | pipeline 내부 구현에 종속 | Token Schema와 Token Extractor를 분리하여 oracle, rule-based, learned extractor로 확장 |
| latency 주장 | planning time만 비교할 위험 | end-to-end latency와 token generation overhead를 함께 측정 |
| 실험 방식 | task별 pipeline 비교가 어려움 | information-bound baseline, ablation, seen/unseen scenario를 동일 protocol로 비교 |

TO-BE의 핵심 메시지는 다음과 같습니다. RAST는 raw observation을 Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence token으로 변환하여 planner가 바로 사용할 수 있는 action-relevant scene representation을 제공합니다. 이 표현은 단순 압축이 아니라 safety-critical information을 보존하는 risk-aware representation입니다.

RAST가 raw observation을 완전히 대체한다고 주장하지는 않습니다. MVP에서는 planner-facing representation이 latency, memory, safety-related metric에서 어떤 장단점을 가지는지 검증합니다. 특히 Phase 1은 oracle tokenization 기반 representation 검증이고, Phase 2가 되어야 perception-bound overhead까지 포함한 시스템 주장을 할 수 있습니다.

### 3.7 Vision

RAST가 성공하면 로봇 perception과 planning 사이에 더 명확한 interface를 둘 수 있는 가능성을 실험적으로 확인할 수 있습니다. 장기적으로는 raw sensory representation과 symbolic planning 사이의 중간 지점에서, 위험과 불확실성을 보존하는 planning-facing representation의 근거를 축적하는 것이 목표입니다.

이 프로젝트는 새로운 로봇 perception interface의 가능성을 검증하고, simulation 기반 embodied planning benchmark를 구축하는 데 의미가 있습니다. 이후 real robot 또는 embedded inference로 확장할 수 있는 구조를 마련하되, MVP에서는 실제 배포 가능성을 단정하지 않습니다.

### 3.8 Goals

#### 정량적 목표

| 목표 | 측정 방식 | MVP 성공 기준 예시 |
|---|---|---|
| token count reduction | raw pixel/input unit 대비 token 수 | object/navigation scenario에서 입력 단위 수 감소 |
| planning latency reduction | `T_planning` 평균, median, p95 | baseline 대비 median 또는 p95 planning latency 감소 |
| end-to-end latency accounting | `T_total` 구성요소별 기록 | token overhead가 전체 지연에 미치는 영향 분리 |
| token generation latency | `T_token_generation` 및 token type별 시간 | RiskToken, EventToken 등 token별 overhead 보고 |
| memory footprint reduction | serialized input size, per-step memory | raw/object graph 대비 memory 감소 |
| collision rate reduction | episode당 collision count | risk scenario에서 baseline 대비 감소 |
| task success 유지 또는 개선 | success rate | object navigation 성공률 유지 또는 개선 |
| unknown object recall | unknown object가 Risk/UncertaintyToken으로 잡힌 비율 | 지정 scenario에서 recall 측정 |
| occlusion risk recall | occlusion 상황을 risk로 감지한 비율 | occlusion scenario에서 recall 측정 |
| emergency replanning time | event 발생부터 새 action 결정까지 시간 | sudden object scenario에서 full reprocessing 대비 감소 |
| incremental update benefit | full token recomputation 대비 incremental update 시간 절감 | event-driven update의 latency/memory 이점 보고 |

#### 정성적 목표

| 목표 | 설명 |
|---|---|
| 해석 가능한 representation | planner decision을 token log로 사후 설명할 수 있어야 합니다. |
| 위험과 불확실성 보존 | 위험하거나 불확실한 정보를 버리지 않고 명시적 token으로 남깁니다. |
| 중간 표현 제공 | object list보다 풍부하고 raw image보다 가벼운 representation을 제공합니다. |
| 구조화 효과 검증 | flat feature table baseline을 통해 단순 정보량 효과와 token contract 효과를 분리합니다. |
| 연구 재현성 | 동일 seed, 동일 scenario, 동일 token schema로 반복 실험이 가능해야 합니다. |

### 3.9 Non-Goals

이번 MVP에서 하지 않을 일은 다음과 같습니다.

| 항목 | 설명 |
|---|---|
| 실제 임베디드 장비 성능 검증 | Jetson, NPU, MCU 등 실제 embedded device latency는 측정하지 않습니다. |
| 실제 로봇 배포 | 물리 로봇 제어, 센서 calibration, real-time control loop는 다루지 않습니다. |
| 상용 자율주행 수준 safety guarantee | collision-free guarantee나 formal safety proof는 제공하지 않습니다. |
| end-to-end deep learning 학습 | 처음부터 token generator를 학습하지 않고 rule/metadata 기반으로 시작합니다. |
| simulator metadata 결과를 generalization 증거로 주장 | Phase 1 oracle tokenization은 representation 검증용이며 실제 perception 성능을 증명하지 않습니다. |
| sim-to-real transfer | 후속 연구 주제로 분리합니다. |
| 범용 VLA 통합 | P2 확장 후보로 두며 MVP 필수 범위에서 제외합니다. |
| manipulation affordance 전체 구현 | MVP의 AffordanceToken은 indoor navigation affordance로 제한합니다. |

### 3.10 Target Users

| 사용자 | 필요 |
|---|---|
| Embodied AI 연구자 | simulator에서 planning-facing representation을 실험하고자 합니다. |
| Robotics perception/planning 연구자 | perception 결과와 planner interface를 분리해 평가하고자 합니다. |
| Simulation 기반 알고리즘 개발자 | AI2-THOR 또는 Habitat에서 반복 가능한 benchmark가 필요합니다. |
| Physical AI representation 연구자 | raw/dense representation과 symbolic representation 사이의 중간 표현을 탐색합니다. |
| 개인 연구자 또는 대학생 개발자 | Python 기반으로 구현 가능한 연구형 prototype 범위가 필요합니다. |

### 3.11 Core Concept: Risk-Aware Scene Tokens

RAST는 고정된 heuristic rule set이 아니라 planner-facing token schema입니다. Token Schema는 planner에게 어떤 정보를 줄 것인지 정의하고, Token Extractor는 그 정보를 어떻게 추출할지 정의합니다. MVP에서는 simulator metadata 기반 extractor를 허용하지만, 같은 schema는 rule-based geometry, learned perception model, foundation-model-assisted extraction으로 확장될 수 있어야 합니다.

#### 3.11.1 EntityToken

Purpose: 장면 내 객체 또는 agent-relevant entity의 위치, 상태, confidence를 표현합니다.

Required fields: `token_id`, `type`, `entity_id`, `category`, `position`, `distance_to_agent`, `confidence`, `timestamp`

Optional fields: `velocity`, `bbox_2d`, `bbox_3d`, `semantic_attributes`, `is_visible`, `source`, `size`

Example JSON:

```json
{
  "token_id": "ent_0007",
  "type": "EntityToken",
  "entity_id": "Chair|+01.2|+00.0|-02.4",
  "category": "chair",
  "position": {"x": 1.2, "y": 0.0, "z": -2.4},
  "size": {"x": 0.7, "y": 0.9, "z": 0.7},
  "distance_to_agent": 1.8,
  "confidence": 0.98,
  "timestamp": 42
}
```

Planner usage: planner는 `distance_to_agent`, `position`, `category`, `size`를 이용해 obstacle, target object, interactable object를 판단합니다.

#### 3.11.2 RelationToken

Purpose: 객체 간 관계와 agent/path와 객체의 관계를 표현합니다.

Required fields: `token_id`, `type`, `subject_id`, `relation`, `object_id`, `confidence`, `timestamp`

Optional fields: `path_segment_id`, `distance_margin`, `source_rule`, `relation_frame`

Example JSON:

```json
{
  "token_id": "rel_0012",
  "type": "RelationToken",
  "subject_id": "agent",
  "relation": "near_path",
  "object_id": "Chair|+01.2|+00.0|-02.4",
  "path_segment_id": "seg_02",
  "distance_margin": 0.35,
  "confidence": 0.94,
  "timestamp": 42
}
```

Planner usage: planner는 `near_path`, `blocking`, `left_of`, `on_top_of`, `inside` 같은 relation을 이용해 route cost나 interaction precondition을 계산합니다.

#### 3.11.3 EventToken

Purpose: 시간적으로 의미 있는 장면 변화를 표현합니다.

Required fields: `token_id`, `type`, `event_type`, `entity_id`, `previous_state`, `current_state`, `timestamp`

Optional fields: `severity`, `trigger`, `affected_tokens`, `update_scope`

Example JSON:

```json
{
  "token_id": "evt_0003",
  "type": "EventToken",
  "event_type": "new_object_appeared",
  "entity_id": "Box|+00.6|+00.0|-01.1",
  "previous_state": null,
  "current_state": {"visible": true, "distance_to_agent": 1.1},
  "severity": "medium",
  "update_scope": ["ent_tmp_03", "risk_0009"],
  "timestamp": 43
}
```

Planner usage: planner는 EventToken을 보고 full scene reprocessing 대신 affected region 중심으로 replanning을 수행합니다.

#### 3.11.4 RiskToken

Purpose: collision, occlusion, unknown object, near-path obstacle 같은 safety-related cue를 명시적으로 표현합니다.

Required fields: `token_id`, `type`, `risk_type`, `severity`, `entity_id`, `affected_area`, `confidence`, `timestamp`

Optional fields: `risk_score`, `recommended_policy`, `time_to_collision`, `path_segment_id`, `evidence_token_id`, `risk_features`

RiskToken은 object class 중심이 아니라 geometry, uncertainty, path relevance 중심으로 설계합니다. 예시 함수는 다음과 같습니다.

```text
risk_score = f(
  distance_to_agent,
  distance_to_planned_path,
  relative_velocity,
  object_size,
  occlusion_ratio,
  position_uncertainty,
  classification_uncertainty,
  time_to_collision
)
```

unknown object라도 near path, large enough, low confidence 조건을 만족하면 RiskToken을 생성할 수 있어야 합니다.

Example JSON:

```json
{
  "token_id": "risk_0005",
  "type": "RiskToken",
  "risk_type": "near_path_obstacle",
  "severity": "high",
  "risk_score": 0.82,
  "entity_id": "UnknownObject|tmp_03",
  "affected_area": {"path_segment_id": "seg_02", "radius": 0.5},
  "risk_features": {
    "distance_to_planned_path": 0.22,
    "object_size": 0.6,
    "classification_uncertainty": 0.71,
    "position_uncertainty": 0.18
  },
  "recommended_policy": "slow_down_or_replan",
  "confidence": 0.91,
  "timestamp": 42
}
```

Planner usage: planner는 RiskToken을 cost map, action filter, speed policy, replanning trigger로 사용합니다.

#### 3.11.5 AffordanceToken

Purpose: 객체 또는 공간이 제공하는 행동 가능성을 표현합니다.

MVP의 AffordanceToken은 indoor navigation affordance로 제한합니다. manipulation affordance는 후속 확장으로 둡니다.

MVP affordance set:

| affordance | 의미 |
|---|---|
| `passable` | agent가 통과할 수 있는 공간 또는 영역입니다. |
| `blocking` | 현재 path를 막거나 path cost를 크게 높이는 객체입니다. |
| `narrow_passage` | 통과 가능하지만 margin이 작은 영역입니다. |
| `target_reachable` | target object 또는 target region에 접근 가능합니다. |
| `support_surface` | 다른 물체를 지지하는 표면입니다. MVP에서는 navigation context 설명용으로만 사용합니다. |
| `recheck_required` | 불확실성 또는 occlusion 때문에 재확인이 필요한 영역입니다. |

Required fields: `token_id`, `type`, `entity_id`, `affordance`, `confidence`, `timestamp`

Optional fields: `preconditions`, `action_hint`, `interaction_pose`, `failure_risk`, `navigation_margin`

Example JSON:

```json
{
  "token_id": "aff_0002",
  "type": "AffordanceToken",
  "entity_id": "Passage|seg_04",
  "affordance": "narrow_passage",
  "preconditions": ["slow_down", "keep_clearance"],
  "action_hint": "reduce_speed_and_center_path",
  "navigation_margin": 0.28,
  "confidence": 0.87,
  "timestamp": 42
}
```

Planner usage: planner는 passable/blocking/narrow passage 여부를 이용해 path 선택, 감속, 재확인을 결정합니다.

#### 3.11.6 UncertaintyToken

Purpose: classification uncertainty, position uncertainty, occlusion, sensor disagreement를 명시적으로 표현합니다.

Required fields: `token_id`, `type`, `uncertainty_type`, `entity_id`, `level`, `confidence`, `timestamp`

Optional fields: `variance`, `possible_categories`, `occluded_by`, `recommended_action`, `sensor_agreement`

Example JSON:

```json
{
  "token_id": "unc_0004",
  "type": "UncertaintyToken",
  "uncertainty_type": "partial_occlusion",
  "entity_id": "UnknownObject|tmp_03",
  "level": "high",
  "possible_categories": ["box", "bag", "unknown"],
  "recommended_action": "inspect_before_passing",
  "confidence": 0.76,
  "timestamp": 42
}
```

Planner usage: planner는 high uncertainty 영역에서 속도를 줄이거나, inspect action 또는 wider path를 선택합니다.

#### 3.11.7 EvidenceToken

Purpose: token 판단의 근거가 되는 raw observation region 또는 simulator metadata pointer를 보존합니다.

Required fields: `token_id`, `type`, `evidence_type`, `source`, `pointer`, `timestamp`

Optional fields: `bbox_2d`, `frame_id`, `metadata_path`, `related_token_ids`, `confidence_source`

Example JSON:

```json
{
  "token_id": "evd_0011",
  "type": "EvidenceToken",
  "evidence_type": "image_region",
  "source": "rgb_frame",
  "pointer": "episode_03/frame_0042.png",
  "bbox_2d": {"x": 210, "y": 144, "w": 56, "h": 72},
  "related_token_ids": ["risk_0005", "unc_0004"],
  "timestamp": 42
}
```

Planner usage: planner가 판단을 보류하거나 재확인이 필요할 때 EvidenceToken을 통해 원본 frame, bbox, metadata를 다시 조회합니다.

### 3.12 Token Generalization and Extraction Strategy

RAST의 연구적 가치는 특정 simulator heuristic이 아니라 planner-facing token schema에 있습니다. 따라서 v0.2에서는 Token Schema와 Token Extractor를 명확히 분리합니다.

| 구분 | 정의 | MVP/확장 |
|---|---|---|
| Token Schema | planner에게 어떤 정보를 줄 것인가에 대한 일반화 가능한 interface | Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence |
| Token Extractor | token을 어떻게 추출할 것인가에 대한 구현 방식 | oracle metadata, rule-based geometry, learned perception, foundation-model-assisted extraction |

Extractor 단계:

| 단계 | 이름 | 입력 | 목적 | 주장 가능한 범위 |
|---|---|---|---|---|
| Phase 1 | Oracle Tokenization | simulator metadata | representation과 planner interface 유효성 검증 | 실제 perception latency 또는 real-world generalization을 주장하지 않음 |
| Phase 2 | Perception-Bound Tokenization | RGB-D, segmentation, detector output | token generation overhead 포함 end-to-end 평가 | perception error와 token robustness를 제한적으로 검증 |
| Phase 3 | Learned/Hybrid Extraction | learned model, foundation model, multimodal feature | schema의 extractor-independent 확장성 평가 | 후속 연구 |

일반화 검증 축:

| 축 | 설명 |
|---|---|
| seen scene | tuning에 사용한 scene에서 반복 평가합니다. |
| unseen scene | tuning에 사용하지 않은 scene에서 schema와 planner robustness를 평가합니다. |
| unknown object | 학습 또는 rule table에 없는 object label을 unknown으로 주입합니다. |
| noise injection | position, class confidence, depth, visibility에 noise를 주입합니다. |
| occlusion | 부분 가림과 low visibility 상황에서 Uncertainty/RiskToken recall을 평가합니다. |

### 3.13 System Architecture

전체 pipeline은 다음과 같습니다.

```text
Simulator
-> Raw Observation
-> Perception Adapter
-> Scene Tokenizer
-> Token Memory
-> Incremental Token Update
-> Token-based Planner
-> Action
-> Evaluation Logger
```

| 모듈 | 책임 |
|---|---|
| Simulator | AI2-THOR 또는 Habitat 환경 실행, agent action 적용, observation/metadata 반환 |
| Raw Observation | RGB, depth, segmentation, metadata를 step 단위로 저장 |
| Perception Adapter | Phase 1에서는 metadata adapter, Phase 2에서는 detector/segmentation/depth output adapter 역할 |
| Scene Tokenizer | adapter output을 RAST token stream으로 변환 |
| Token Memory | 이전 step token과 현재 token을 비교해 state history 관리 |
| Incremental Token Update | 변한 객체, 새 객체, 사라진 객체, risk가 변한 객체만 업데이트 |
| Token-based Planner | token stream을 입력으로 next action 또는 replanning decision 생성 |
| Action | simulator action으로 변환 가능한 discrete/continuous command |
| Evaluation Logger | latency, memory, collision, near-miss, token count, decision trace 저장 |

제안 디렉토리 구조:

```text
simulator/
  ai2thor_env.py
  scenarios.py
tokenizer/
  entity_tokenizer.py
  relation_tokenizer.py
  risk_tokenizer.py
  event_tokenizer.py
  uncertainty_tokenizer.py
  incremental_update.py
schemas/
  tokens.py
  token_schema.json
planner/
  rule_based_planner.py
  baselines.py
experiments/
  run_episode.py
  configs/
evaluation/
  latency.py
  information_bound.py
  metrics.py
  logger.py
  ablation.py
  analyze_results.py
dashboard/
  app.py
  views.py
```

### 3.14 MVP Scope

MVP simulator는 AI2-THOR를 우선 선택합니다. 이유는 Python 기반 접근성이 좋고, indoor navigation, object metadata, visibility, object state/action loop를 활용해 개인 개발자가 metadata 기반 tokenization을 빠르게 구현하기에 적합하기 때문입니다. Habitat은 고성능 embodied AI benchmark 확장 후보로 P2에 둡니다.

MVP 범위:

| 범위 | 내용 |
|---|---|
| Simulator | AI2-THOR |
| Task | indoor navigation |
| Phase | Phase 1 Oracle Tokenization 중심 |
| Token source | simulator metadata 기반 token 생성 |
| Planner | rule-based token planner |
| Baseline | raw observation, object list, scene graph, flat feature table |
| Logging | episode metrics, latency breakdown, token logs, planner decision trace |
| Visualization | top-down path, token overlay, risk timeline, event timeline |

MVP task 예시:

| Task | 설명 |
|---|---|
| Object navigation | "컵 찾기"처럼 target object 근처까지 이동합니다. |
| Obstacle avoidance | 의자, 테이블 등 장애물을 피해 이동합니다. |
| Risk-aware navigation | unknown object 또는 near-path obstacle 근처에서 감속/우회합니다. |
| Semantic event reaction | 새 객체 등장 또는 위치 변화 발생 시 EventToken으로 replanning합니다. |
| Occlusion-aware navigation | partially occluded object 근처에서 recheck 또는 우회를 선택합니다. |

### 3.15 Functional Requirements

| Priority | 요구사항 | 설명 |
|---|---|---|
| P0 | simulator environment 실행 | AI2-THOR scene load, reset, step action을 지원합니다. |
| P0 | object metadata 수집 | object id, type, position, visibility, distance 정보를 수집합니다. |
| P0 | EntityToken 생성 | visible/relevant object를 EntityToken으로 변환합니다. |
| P0 | RiskToken 생성 | near-path obstacle, collision risk, unknown risk를 rule 기반으로 생성합니다. |
| P0 | Token Memory 구현 | 이전 step token state를 저장하고 diff를 계산합니다. |
| P0 | token-based planner 실행 | token stream을 입력으로 next action을 선택합니다. |
| P0 | baseline planner와 비교 | object list, scene graph, flat feature table baseline과 동일 scenario에서 비교합니다. |
| P0 | latency breakdown logging | `T_observation`, `T_perception`, `T_token_generation`, `T_planning`, `T_action`을 저장합니다. |
| P0 | metric logging | latency, token count, memory, collision, near-miss, success를 저장합니다. |
| P1 | RelationToken 생성 | agent-object, object-object, path-object 관계를 생성합니다. |
| P1 | EventToken 생성 | 등장, 사라짐, 이동, 위험 증가를 step diff로 감지합니다. |
| P1 | UncertaintyToken 생성 | occlusion, unknown, low confidence를 rule 또는 noise injection으로 표현합니다. |
| P1 | incremental update | full recomputation과 incremental update를 비교할 수 있게 합니다. |
| P1 | visualization dashboard | token stream, path, risk timeline, event timeline을 시각화합니다. |
| P1 | scenario replay | 저장된 episode를 다시 재생하고 decision trace를 확인합니다. |
| P2 | perception model 연결 | metadata 대신 detector/segmenter output을 token source로 사용합니다. |
| P2 | noise injection | position/classification noise를 주입해 robustness를 평가합니다. |
| P2 | occlusion simulation | partial visibility와 occluded obstacle scenario를 구성합니다. |
| P2 | Habitat 확장 | 동일 token schema를 Habitat adapter에 연결합니다. |
| P2 | VLA 또는 LLM planner 연결 | structured JSON 또는 language prompt로 token을 전달합니다. |

### 3.16 Non-Functional Requirements

| 항목 | 요구사항 |
|---|---|
| Latency | planning latency와 end-to-end latency를 모두 측정해야 합니다. |
| Token overhead visibility | token별 generation latency를 가능하면 분리해야 합니다. |
| Memory usage | raw/object list/scene graph/flat table/RAST 입력 크기를 동일 기준으로 저장해야 합니다. |
| Reproducibility | scene id, seed, episode config, token schema version을 log에 포함해야 합니다. |
| Modularity | simulator adapter, perception adapter, tokenizer, planner, evaluator를 분리해야 합니다. |
| Extensibility | AI2-THOR 이후 Habitat 또는 real perception adapter를 붙일 수 있어야 합니다. |
| Interpretability | planner decision이 어떤 token에 의해 유발됐는지 trace해야 합니다. |
| Safety-awareness | 위험과 불확실성을 별도 token으로 보존해야 합니다. |
| Experiment repeatability | scenario별 repeated run과 aggregate metric 계산을 지원해야 합니다. |
| Information-bound fairness | baseline 간 accessible information 차이를 명시적으로 통제해야 합니다. |

### 3.17 Latency Accounting Protocol

RAST의 latency 주장은 planning latency만으로 평가하지 않습니다. 전체 시스템 지연은 다음과 같이 분해합니다.

```text
T_total = T_observation
        + T_perception
        + T_token_generation
        + T_planning
        + T_action
```

| 구성요소 | 정의 | Phase 1 측정 | Phase 2 측정 |
|---|---|---|---|
| `T_observation` | simulator step 후 observation/metadata를 받는 시간 | 측정 | 측정 |
| `T_perception` | raw observation에서 object/segmentation/depth feature를 얻는 시간 | metadata adapter time으로 별도 기록하되 실제 perception latency로 주장하지 않음 | detector/segmentation/depth pipeline latency 측정 |
| `T_token_generation` | adapter output을 token으로 변환하는 시간 | oracle token generation latency | perception-bound token generation latency |
| `T_planning` | planner가 next action을 결정하는 시간 | 측정 | 측정 |
| `T_action` | action command 생성 및 simulator step request overhead | 측정 | 측정 |
| `T_total` | end-to-end decision loop latency | 측정하되 oracle-bound로 표기 | 실제 token pipeline overhead 포함 측정 |

Token generation latency는 가능하면 다음처럼 token type별로 분리합니다.

| Token type | 측정 항목 |
|---|---|
| EntityToken | object count 대비 생성 시간 |
| RelationToken | relation pair 수 대비 생성 시간 |
| EventToken | Token Memory diff 시간 |
| RiskToken | path relevance, geometry, uncertainty feature 계산 시간 |
| AffordanceToken | passable/blocking/narrow_passage 판단 시간 |
| UncertaintyToken | confidence/noise/occlusion 판단 시간 |
| EvidenceToken | raw pointer 또는 metadata pointer 생성 시간 |

Incremental update 측정:

| 비교 | 목적 |
|---|---|
| full token recomputation | 매 step 전체 객체와 관계를 재계산하는 기준 |
| incremental token update | 변한 객체, 새 객체, 사라진 객체, risk가 변한 객체만 업데이트 |
| metric | `incremental_update_benefit = 1 - T_incremental_update / T_full_recompute` |

Phase 1에서는 `T_perception`을 실제 perception latency로 주장하지 않습니다. Phase 2에서만 raw RGB-D, segmentation, detector output을 포함한 end-to-end latency를 주장할 수 있습니다.

### 3.18 Information-Bound Evaluation Protocol

RAST baseline 비교는 "같은 정보, 다른 구조" 원칙을 따릅니다. 즉, 모든 비교 방법은 동일한 observation source와 동일한 accessible information에서 시작해야 합니다.

| 원칙 | 설명 |
|---|---|
| 동일 observation source | 같은 simulator episode, 같은 frame, 같은 metadata 또는 같은 perception output을 사용합니다. |
| 동일 accessible information | RAST만 추가 정보를 받지 않도록 object 위치, confidence, relation, risk feature의 접근 범위를 명시합니다. |
| 동일 planner budget | planner decision time budget 또는 search depth를 가능한 한 동일하게 둡니다. |
| 동일 action space | 모든 방법은 같은 discrete action set 또는 같은 navigation action interface를 사용합니다. |
| 동일 scenario seed | scene, target, obstacle placement, noise seed를 동일하게 고정합니다. |
| 정보량 보고 | 각 baseline의 input unit 수와 serialized memory footprint를 함께 보고합니다. |

비교군:

| 접근 | 입력 | 공정성 조건 |
|---|---|---|
| Baseline A: Raw Observation | raw RGB-D 또는 dense observation | 같은 frame과 sensor stream을 사용합니다. MVP에서는 raw input size와 simple dense proxy planner를 구분해 기록합니다. |
| Baseline B: Object List | 동일한 객체, 위치, confidence 정보 | RAST의 EntityToken과 동일 object source를 사용하되 risk/event/uncertainty contract는 제공하지 않습니다. |
| Baseline C: Scene Graph | 동일한 객체와 relation 정보 | RAST의 RelationToken과 동일 relation source를 사용하되 risk/event/uncertainty/evidence contract는 제공하지 않습니다. |
| Baseline D: Flat Feature Table | RAST와 동일 scalar feature | token type, semantic event, contract 없이 flat row table로 제공합니다. |
| Proposed: RAST | 동일 정보 범위의 token contract | Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence structure를 제공합니다. |

Oracle-Bound Evaluation과 Perception-Bound Evaluation은 분리합니다.

| 평가 단계 | 입력 | 목적 | 해석 제한 |
|---|---|---|---|
| Oracle-Bound Evaluation | simulator metadata | representation과 planner interface 비교 | 실제 perception robustness와 latency를 증명하지 않음 |
| Perception-Bound Evaluation | RGB-D, segmentation, detector output | perception/token overhead 포함 평가 | detector 품질에 따라 결과가 달라질 수 있음 |

### 3.19 Evaluation Plan

평가 지표:

| Metric | 정의 |
|---|---|
| task success rate | 목표 지점 또는 목표 객체 도달 성공률 |
| average planning latency | action decision에 걸린 평균 시간 |
| p95 planning latency | planning latency의 95 percentile |
| token generation latency | token 생성에 걸린 시간 |
| end-to-end latency | `T_total` 기준 전체 decision loop latency |
| number of input units | raw pixel 수, object 수, graph node/edge 수, flat row 수, token 수 |
| memory footprint | step별 serialized input byte size |
| collision count | episode당 collision 횟수 |
| near-miss count | agent와 장애물 간 거리가 threshold 이하인 횟수 |
| emergency replanning time | event 발생부터 새 action 결정까지 소요 시간 |
| unknown object recall | injected unknown object가 risk/uncertainty로 감지된 비율 |
| occlusion risk recall | occlusion 상황이 Risk/UncertaintyToken으로 감지된 비율 |
| incremental update benefit | full recomputation 대비 incremental update의 시간 절감률 |
| planner decision explainability | action decision에 연결된 token trace의 존재 여부와 사람이 검토 가능한 비율 |
| token generation overhead | `T_token_generation / T_total` 또는 baseline 대비 추가 overhead |

실험 시나리오:

| Scenario | 평가 목적 |
|---|---|
| normal navigation | 기본 성공률과 latency 측정 |
| cluttered room | 장애물이 많은 환경에서 path quality와 collision 측정 |
| sudden object appearance | EventToken 기반 replanning 성능 측정 |
| partially occluded object | occlusion risk recall 측정 |
| unknown object | unknown risk와 보수적 행동 측정 |
| narrow passage | near-miss와 path margin 측정 |
| noisy perception | position/classification/depth noise에 대한 robustness 측정 |
| seen scene | tuning에 사용한 scene에서 반복성 측정 |
| unseen scene | tuning에 사용하지 않은 scene에서 generalization 경향 측정 |
| moving obstacle | simulator 지원 범위 안에서 동적 위험 처리 평가 |

실험 설계는 scene별 seed를 고정하고, scenario당 최소 10~30 episode를 반복하는 방식이 적절합니다. 결과는 평균뿐 아니라 median, p95, 실패 사례 token log를 함께 보고합니다. 통계적 유의성까지 주장하기 어려운 MVP 단계에서는 effect size와 failure case analysis를 함께 제시합니다.

### 3.20 Ablation Study Plan

Ablation은 RAST의 성능 향상이 어떤 token contract에서 오는지 분리하기 위한 핵심 실험입니다.

| 실험군 | 제거/유지 조건 | 목적 |
|---|---|---|
| RAST-full | 모든 token 사용 | 제안 방식의 전체 성능 |
| RAST without RiskToken | RiskToken 제거 | safety metric 개선이 risk contract 때문인지 확인 |
| RAST without EventToken | EventToken 제거 | scene change 대응과 replanning time 기여도 확인 |
| RAST without UncertaintyToken | UncertaintyToken 제거 | unknown/occlusion scenario에서 보수적 행동 기여도 확인 |
| RAST without RelationToken | RelationToken 제거 | path-object/object-object relation의 planning 기여도 확인 |
| RAST without EvidenceToken | EvidenceToken 제거 | decision explainability와 recheck behavior 기여도 확인 |
| Object List only | Entity 중심 입력만 사용 | object list baseline과 직접 비교 |
| Scene Graph only | Entity + Relation 중심 입력만 사용 | 일반 scene graph 대비 차이 확인 |
| Flat Feature Table | 동일 scalar feature를 flat table로 제공 | 구조화 token contract의 효과 분리 |

권장 분석:

| 분석 | 설명 |
|---|---|
| Safety ablation | collision, near-miss, unknown recall, occlusion recall을 비교합니다. |
| Latency ablation | token별 overhead와 planning latency 변화를 비교합니다. |
| Explainability ablation | action decision에 연결된 근거 token trace 품질을 비교합니다. |
| Incremental update ablation | EventToken/Token Memory 유무에 따른 update latency를 비교합니다. |

### 3.21 Research Hypotheses

| 가설 | 검증 방법 | 성공 기준 |
|---|---|---|
| H1: RAST는 object list보다 낮은 collision 또는 near-miss rate를 보일 수 있습니다. | cluttered room, narrow passage, unknown object scenario에서 object list planner와 비교합니다. | collision 또는 near-miss가 실용적으로 감소합니다. |
| H2: RAST는 raw observation 기반 방식보다 planning latency를 줄일 수 있습니다. | raw proxy planner와 RAST planner의 `T_planning`을 비교합니다. | median 또는 p95 planning latency가 감소합니다. |
| H3: RAST의 end-to-end latency 이점은 token generation overhead에 의해 약화될 수 있습니다. | `T_total` breakdown으로 RAST와 baseline을 비교합니다. | Phase 1/2에서 overhead 비율을 정량 보고하고, 이점이 유지되는 조건을 제시합니다. |
| H4: RiskToken과 UncertaintyToken은 unknown/occluded object 상황에서 emergency replanning을 개선할 수 있습니다. | unknown object, partial occlusion scenario에서 ablation을 수행합니다. | Risk/Uncertainty 제거 버전 대비 collision, near-miss, replanning time이 개선됩니다. |
| H5: Semantic EventToken과 Token Memory는 scene 변화 발생 시 full recomputation보다 빠른 update를 가능하게 할 수 있습니다. | sudden object appearance scenario에서 full update와 incremental update를 비교합니다. | update latency가 감소하고 success rate가 유지됩니다. |
| H6: Flat Feature Table 대비 RAST가 개선된다면, 단순 정보량이 아니라 token contract 구조가 기여했을 가능성이 있습니다. | 동일 scalar feature를 flat table과 token contract로 각각 제공해 비교합니다. | 동일 정보 조건에서 RAST가 explainability 또는 safety/planning metric에서 개선됩니다. |

### 3.22 Key Differentiation

RAST는 기존 연구와 단절된 완전히 새로운 분야라기보다 scene graph, world model, VLA 입력 표현, compact scene token 연구와 연결되는 확장으로 정의하는 것이 적절합니다.

| 관점 | 차별점 |
|---|---|
| Scene graph 대비 | 단순 node-edge graph가 아니라 planner-facing token contract를 정의합니다. |
| Compression 대비 | 단순 정보량 축소가 아니라 risk-preserving compression을 목표로 합니다. |
| Event camera 대비 | low-level pixel event가 아니라 semantic event stream을 다룹니다. |
| Object detection 대비 | 객체 결과에 relation, risk, uncertainty, affordance, evidence를 추가합니다. |
| Planner interface | raw image와 planner 사이의 명시적 structured interface를 제공합니다. |
| Flat feature 대비 | 동일 scalar feature라도 semantic token type, event update, evidence pointer를 contract로 제공합니다. |
| Benchmark | simulation 기반으로 raw/object list/scene graph/flat table/RAST 비교 실험을 제공합니다. |

### 3.23 Risks and Mitigations

| 리스크 | 설명 | 대응 전략 |
|---|---|---|
| tokenization overhead가 latency 이점을 상쇄 | token 생성 비용이 planner latency 감소보다 클 수 있습니다. | latency accounting protocol로 `T_token_generation`, `T_planning`, `T_total`을 분리 측정합니다. |
| simulator metadata 과의존 | metadata 기반 token이 실제 perception error를 반영하지 못할 수 있습니다. | Phase 1 결과는 oracle-bound로 표기하고, Phase 2에서 perception-bound tokenization으로 확장합니다. |
| 실제 perception error 미반영 | occlusion, misclassification, false positive가 단순화될 수 있습니다. | synthetic uncertainty, confidence degradation, visibility-based occlusion rule, detector output adapter를 도입합니다. |
| token schema가 task-specific해짐 | 특정 navigation task에만 맞는 schema가 될 수 있습니다. | Token Schema와 Extractor를 분리하고, core fields와 task-specific extension fields를 분리합니다. |
| risk score 설계가 임의적 | rule-based score가 근거 부족으로 보일 수 있습니다. | risk feature와 formula를 공개하고 sensitivity analysis와 ablation을 수행합니다. |
| scene graph와 차별점 약화 | RelationToken만 강조하면 일반 scene graph와 유사해질 수 있습니다. | Risk, Uncertainty, Event, EvidenceToken과 flat feature baseline을 핵심 평가 축으로 둡니다. |
| RAST가 더 많은 정보를 받아 유리해짐 | baseline 공정성이 깨질 수 있습니다. | Information-Bound Evaluation Protocol로 accessible information을 통제합니다. |
| incremental update가 복잡도만 증가 | 작은 scene에서는 full recomputation이 더 단순하고 빠를 수 있습니다. | scene size와 changed object count별로 incremental update benefit을 측정합니다. |
| explainability metric이 주관적 | token trace가 실제로 설명 가능한지 평가가 모호할 수 있습니다. | decision-linked token coverage, evidence pointer availability, failure case review checklist를 정의합니다. |

### 3.24 Implementation Plan

| 기간 | 작업 |
|---|---|
| Week 1 | AI2-THOR 환경 구축, object navigation task 정의, scenario config 작성, token schema v0.1 작성 |
| Week 2 | EntityToken, RiskToken 생성기 구현, object list baseline planner 구현, latency logger 구현 |
| Week 3 | RelationToken, EventToken, Token Memory 구현, sudden object scenario 구성 |
| Week 4 | baseline A/B/C/D 비교 실험, information-bound input export, simple visualization |
| Week 5~6 | UncertaintyToken, noise injection, occlusion scenario, Risk/Uncertainty/Event ablation study |
| Week 7 | incremental update benchmark, latency accounting report, seen/unseen scene split 평가 |
| Week 8 | technical report 작성, PRD 업데이트, dashboard 정리, demo episode replay 구성 |

### 3.25 Success Criteria

MVP 성공 기준은 다음과 같습니다.

| 기준 | 설명 |
|---|---|
| 최소 3개 navigation scenario 동작 | normal, cluttered, sudden object 또는 unknown scenario에서 RAST planner가 action을 생성합니다. |
| baseline 대비 planning latency 또는 input size 감소 | raw/object list/scene graph/flat table 중 하나 이상 대비 `T_planning` 또는 input size가 감소합니다. |
| end-to-end latency breakdown 제공 | `T_total`과 구성요소별 latency가 기록되어 token overhead를 확인할 수 있습니다. |
| RiskToken 효과 확인 | RiskToken 포함 버전이 collision 또는 near-miss를 줄이는 경향을 보입니다. |
| unknown/occlusion 보수적 행동 | unknown 또는 occluded object 근처에서 slow down, inspect, replan 중 하나를 선택합니다. |
| incremental update benefit 보고 | full recomputation 대비 incremental update가 유리한 조건과 불리한 조건을 모두 보고합니다. |
| Flat Feature Table 대비 구조화 효과 검토 | 동일 scalar feature 조건에서 RAST token contract가 어떤 metric에 기여하는지 분석합니다. |
| decision trace 가능 | token log를 통해 planner decision의 근거를 사후 설명할 수 있습니다. |
| 재현 가능한 실험 | seed, scene, config, schema version이 저장되어 episode replay가 가능합니다. |

### 3.26 Open Questions

| 질문 | 현재 상태 |
|---|---|
| risk score는 rule-based인가 learned model인가? | MVP는 rule-based, 후속 연구에서 learned model 검토가 적절합니다. |
| token schema는 task-independent하게 유지 가능한가? | core schema와 task extension 분리가 필요합니다. |
| relation graph는 full update인가 incremental update인가? | MVP는 full update와 incremental update를 모두 구현해 비교합니다. |
| simulator metadata 결과가 실제 perception 기반 결과로 이어질 수 있는가? | noise injection과 perception adapter 실험이 필요합니다. |
| VLA 모델과 연결할 때 token은 language인가 JSON인가? | structured JSON을 기본으로 두고, language serialization은 별도 ablation으로 둡니다. |
| EvidenceToken은 얼마나 자세해야 하는가? | MVP는 frame id, bbox, metadata path 수준으로 시작합니다. |
| AffordanceToken은 navigation MVP에 필수인가? | P0에서는 navigation affordance만 다루고 manipulation affordance는 후속 확장으로 둡니다. |
| Flat Feature Table baseline의 planner는 어떻게 설계할 것인가? | RAST planner와 동일 feature를 쓰되 token type/event contract 없이 처리하는 rule-based variant가 필요합니다. |
| unknown object는 어떻게 주입할 것인가? | simulator object label masking, confidence degradation, synthetic obstacle insertion 중 하나를 선택해야 합니다. |
| explainability metric은 어떻게 정량화할 것인가? | decision-linked token coverage와 evidence availability를 우선 metric으로 둘 수 있습니다. |

### 3.27 Appendix: Example Token Schema

공통 token envelope 예시:

```json
{
  "schema_version": "rast.v0.2",
  "episode_id": "episode_0003",
  "scene_id": "FloorPlan1",
  "phase": "oracle_tokenization",
  "step": 42,
  "timestamp": 42,
  "latency_ms": {
    "observation": 8.4,
    "perception": 1.2,
    "token_generation": 3.7,
    "planning": 2.8,
    "action": 5.1,
    "total": 21.2
  },
  "agent_state": {
    "position": {"x": 0.0, "y": 0.0, "z": -1.2},
    "rotation": {"yaw": 90.0}
  },
  "tokens": []
}
```

예시 token stream:

```json
{
  "schema_version": "rast.v0.2",
  "episode_id": "episode_0003",
  "scene_id": "FloorPlan1",
  "step": 42,
  "tokens": [
    {
      "token_id": "ent_0007",
      "type": "EntityToken",
      "entity_id": "Chair|+01.2|+00.0|-02.4",
      "category": "chair",
      "position": {"x": 1.2, "y": 0.0, "z": -2.4},
      "size": {"x": 0.7, "y": 0.9, "z": 0.7},
      "distance_to_agent": 1.8,
      "confidence": 0.98,
      "timestamp": 42
    },
    {
      "token_id": "rel_0012",
      "type": "RelationToken",
      "subject_id": "agent",
      "relation": "near_path",
      "object_id": "Chair|+01.2|+00.0|-02.4",
      "path_segment_id": "seg_02",
      "distance_margin": 0.35,
      "confidence": 0.94,
      "timestamp": 42
    },
    {
      "token_id": "risk_0005",
      "type": "RiskToken",
      "risk_type": "near_path_obstacle",
      "severity": "high",
      "risk_score": 0.82,
      "entity_id": "UnknownObject|tmp_03",
      "affected_area": {"path_segment_id": "seg_02", "radius": 0.5},
      "risk_features": {
        "distance_to_planned_path": 0.22,
        "object_size": 0.6,
        "classification_uncertainty": 0.71,
        "position_uncertainty": 0.18
      },
      "recommended_policy": "slow_down_or_replan",
      "confidence": 0.91,
      "timestamp": 42
    },
    {
      "token_id": "aff_0002",
      "type": "AffordanceToken",
      "entity_id": "Passage|seg_04",
      "affordance": "narrow_passage",
      "preconditions": ["slow_down", "keep_clearance"],
      "action_hint": "reduce_speed_and_center_path",
      "navigation_margin": 0.28,
      "confidence": 0.87,
      "timestamp": 42
    },
    {
      "token_id": "evt_0003",
      "type": "EventToken",
      "event_type": "risk_increased",
      "entity_id": "UnknownObject|tmp_03",
      "previous_state": {"risk_score": 0.41},
      "current_state": {"risk_score": 0.82},
      "severity": "high",
      "update_scope": ["ent_tmp_03", "risk_0005", "unc_0004"],
      "timestamp": 42
    },
    {
      "token_id": "unc_0004",
      "type": "UncertaintyToken",
      "uncertainty_type": "partial_occlusion",
      "entity_id": "UnknownObject|tmp_03",
      "level": "high",
      "possible_categories": ["box", "bag", "unknown"],
      "recommended_action": "inspect_before_passing",
      "confidence": 0.76,
      "timestamp": 42
    },
    {
      "token_id": "evd_0011",
      "type": "EvidenceToken",
      "evidence_type": "image_region",
      "source": "rgb_frame",
      "pointer": "episode_0003/frame_0042.png",
      "bbox_2d": {"x": 210, "y": 144, "w": 56, "h": 72},
      "related_token_ids": ["risk_0005", "unc_0004"],
      "timestamp": 42
    }
  ]
}
```

## 4. 추가로 검토해야 할 Open Questions

v0.2에서 특히 추가 검토가 필요한 질문은 다음과 같습니다.

| 질문 | 이유 |
|---|---|
| Flat Feature Table baseline의 planner를 RAST planner와 얼마나 동일하게 유지할 것인가? | 구조화 효과와 planner 구현 차이를 분리해야 합니다. |
| Phase 2 perception-bound extractor는 어떤 perception output부터 시작할 것인가? | RGB-D, segmentation, detector 중 선택에 따라 overhead와 error profile이 달라집니다. |
| RiskToken threshold는 scenario별 tuning을 허용할 것인가? | 과도한 tuning은 unseen generalization 평가를 약화할 수 있습니다. |
| incremental update가 유리한 scene scale은 어느 정도인가? | 작은 scene에서는 full recomputation이 더 단순하고 빠를 수 있습니다. |
| explainability metric은 사람이 검토 가능한 수준으로 어떻게 표준화할 것인가? | decision trace가 있다는 사실만으로 설명 가능성을 보장하지 않습니다. |

## 5. 다음 액션 아이템

| 우선순위 | 액션 | 산출물 |
|---|---|---|
| P0 | token schema v0.2를 `schemas/token_schema.json`으로 구체화 | JSON Schema 초안 |
| P0 | latency logger 설계 | `T_total` breakdown log format |
| P0 | information-bound baseline input exporter 설계 | raw/object list/scene graph/flat table/RAST 공통 episode export |
| P0 | AI2-THOR normal/cluttered/sudden object scenario 정의 | scenario config |
| P1 | RiskToken formula와 threshold sensitivity plan 작성 | risk scoring note |
| P1 | ablation runner 설계 | RAST-full 및 token 제거 실험 config |
| P1 | simple dashboard 요구사항 정의 | token timeline, risk timeline, path view |
