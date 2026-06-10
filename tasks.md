# tasks.md — RAST MVP-0 Vertical Slice Implementation Plan

## 1. 문서 목적

이 문서는 `prd.md` v0.2와 `stack.md`를 기준으로 RAST MVP-0 vertical slice의 구현 계획을 파일 단위 작업 목록으로 정의합니다. 아직 구현하지 않고, 다음 구현 단계에서 어떤 파일을 만들고 어떤 완료 조건을 만족해야 하는지 명확히 정리합니다.

MVP-0의 목표는 전체 RAST 연구 시스템을 한 번에 만드는 것이 아니라, AI2-THOR에서 하나의 observation을 받아 최소 token representation으로 변환하고, latency를 기록하며, Object List baseline과 최소 token planner를 같은 입력 source에서 비교할 수 있는 가장 얇은 end-to-end slice를 만드는 것입니다.

## 2. Source of Truth

| 문서 | 반영한 핵심 요구 |
|---|---|
| `prd.md` | AI2-THOR 우선, Phase 1 Oracle Tokenization, EntityToken/RiskToken, latency accounting, information-bound baseline, JSONL logging, object list baseline |
| `stack.md` | Python 중심, Pydantic schema, AI2-THOR smoke test, JSONL logger, pytest, YAML/CLI는 후속 확장 가능, simulator와 tokenizer 분리 |

## 3. MVP-0 Scope

### 포함 범위

| 범위 | 설명 |
|---|---|
| AI2-THOR smoke test | 최소 scene reset/step이 가능한지 확인하는 실행 경로를 둡니다. |
| ObservationSnapshot | AI2-THOR event/metadata를 공통 snapshot 형태로 정리합니다. |
| EntityToken | simulator metadata 기반 object token을 생성합니다. |
| RiskToken | near-path 또는 near-agent obstacle 중심의 최소 risk token을 생성합니다. |
| LatencyRecord | `T_observation`, `T_perception`, `T_token_generation`, `T_planning`, `T_action`, `T_total`을 기록합니다. |
| JSONL logger | step-level snapshot/token/action/latency log를 append-only로 저장합니다. |
| Object List baseline | 같은 ObservationSnapshot에서 object list representation을 생성합니다. |
| 최소 token planner | RiskToken/EntityToken을 입력으로 `MoveAhead`, `RotateLeft`, `RotateRight`, `Stop` 중 하나를 선택하는 rule-based planner를 둡니다. |

### 제외 범위

| 제외 항목 | 이유 |
|---|---|
| RelationToken/EventToken/UncertaintyToken/AffordanceToken/EvidenceToken 전체 구현 | MVP-0 이후 vertical slice가 안정화된 뒤 확장합니다. |
| Token Memory와 incremental update 실제 구현 | MVP-0에서는 파일 구조와 latency field만 준비하고 실제 diff/update는 후속으로 둡니다. |
| Scene Graph baseline, Flat Feature Table baseline | MVP-0에서는 Object List baseline까지만 구현합니다. |
| Habitat, FastAPI, Next.js, dashboard | 초기 vertical slice 범위를 벗어납니다. |
| Docker, CI, 대형 실험 runner | smoke test 성공 후 P1로 둡니다. |
| learned perception extractor | Phase 1 Oracle Tokenization 범위에서는 simulator metadata를 사용합니다. |

## 4. Proposed File-Level Work Plan

아래 파일은 다음 구현 단계에서 생성 또는 수정할 후보입니다. 이번 문서 작성 단계에서는 실제 파일을 만들지 않습니다.

### 4.1 Project and Package Skeleton

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T0.1 | `pyproject.toml` | 최소 Python package metadata와 dependency group을 정의합니다. | 없음 | `pytest`, `pydantic`, `numpy`, `ai2thor` 후보 dependency가 명시됩니다. 실제 버전은 구현 시점 공식 문서 확인 후 고정합니다. |
| T0.2 | `rast/__init__.py` | `rast` 패키지 루트를 정의합니다. | T0.1 | import 가능한 빈 패키지로 동작합니다. |
| T0.3 | `tests/__init__.py` | pytest test package를 정의합니다. | T0.1 | 테스트 discovery에 방해되지 않습니다. |

### 4.2 Schemas

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T1.1 | `rast/schemas/common.py` | `Vector3`, `BBox2D`, 공통 timestamp/step type 등 shared schema를 정의합니다. | T0.2 | EntityToken, RiskToken, ObservationSnapshot에서 중복 없이 재사용됩니다. |
| T1.2 | `rast/schemas/observation.py` | `ObservationSnapshot`, `AgentState`, `ObjectMetadata`를 정의합니다. | T1.1 | AI2-THOR event metadata에서 필요한 최소 필드가 표현됩니다: scene id, step, agent pose, objects, raw observation reference. |
| T1.3 | `rast/schemas/tokens.py` | `EntityToken`, `RiskToken`을 정의합니다. | T1.1 | `schema_version="rast.v0.2"`를 포함하고 JSON serialization이 가능합니다. |
| T1.4 | `rast/schemas/latency.py` | `LatencyRecord`를 정의합니다. | T1.1 | observation, perception, token_generation, planning, action, total latency field를 포함합니다. |

### 4.3 Simulator Smoke and Observation Adapter

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T2.1 | `rast/simulator/ai2thor_env.py` | AI2-THOR controller 생성, scene reset, single step wrapper를 정의합니다. | T1.2 | 지정 scene에서 reset과 1-step action을 호출할 수 있는 함수가 존재합니다. |
| T2.2 | `rast/simulator/observation_adapter.py` | AI2-THOR event를 `ObservationSnapshot`으로 변환합니다. | T1.2, T2.1 | 같은 event에서 deterministic한 snapshot이 생성됩니다. |
| T2.3 | `experiments/smoke_ai2thor.py` | AI2-THOR smoke test CLI entry를 둡니다. | T2.1, T2.2 | `FloorPlan1` 같은 기본 scene을 reset하고 snapshot summary를 출력 또는 JSONL로 기록하는 흐름이 정의됩니다. |

### 4.4 Tokenizers

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T3.1 | `rast/tokenizer/entity_tokenizer.py` | `ObservationSnapshot.objects`에서 visible/relevant object를 `EntityToken`으로 변환합니다. | T1.2, T1.3 | object id, category, position, distance_to_agent, confidence가 채워집니다. |
| T3.2 | `rast/tokenizer/risk_tokenizer.py` | EntityToken과 agent/path proxy를 사용해 최소 `RiskToken`을 생성합니다. | T1.3 | near-agent 또는 near-path threshold 기반 `near_path_obstacle` risk가 생성됩니다. |
| T3.3 | `rast/tokenizer/pipeline.py` | snapshot -> EntityToken -> RiskToken 순서의 MVP-0 tokenization pipeline을 제공합니다. | T3.1, T3.2 | token generation latency 측정 boundary를 넣을 수 있는 단일 함수가 존재합니다. |

### 4.5 Latency and Logging

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T4.1 | `rast/evaluation/latency.py` | `time.perf_counter()` 기반 context manager timer를 정의합니다. | T1.4 | stage별 elapsed ms를 기록하고 `LatencyRecord`로 변환할 수 있습니다. |
| T4.2 | `rast/evaluation/jsonl_logger.py` | append-only JSONL writer를 정의합니다. | T1.3, T1.4 | snapshot ref, tokens, baseline type, selected action, latency가 한 줄 JSON으로 저장됩니다. |
| T4.3 | `rast/evaluation/records.py` | MVP-0 step log record schema를 정의합니다. | T1.2, T1.3, T1.4 | log record에 run_id, episode_id, step, schema_version, baseline_type이 포함됩니다. |

### 4.6 Baseline

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T5.1 | `rast/baselines/object_list.py` | `ObservationSnapshot`에서 Object List baseline representation을 생성합니다. | T1.2 | RAST EntityToken과 동일 object source를 사용합니다. |
| T5.2 | `rast/baselines/audit.py` | Object List baseline의 accessible fields를 기록하는 최소 audit helper를 둡니다. | T5.1 | object list가 RiskToken-only field나 planner recommendation을 보지 않았음을 log로 남길 수 있습니다. |

### 4.7 Minimal Token Planner

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T6.1 | `rast/planner/token_planner.py` | EntityToken/RiskToken 기반 최소 rule-based planner를 정의합니다. | T1.3 | high risk가 있으면 회전 또는 정지, risk가 낮으면 전진하는 deterministic policy가 존재합니다. |
| T6.2 | `rast/planner/actions.py` | MVP-0 action enum 또는 literal set을 정의합니다. | 없음 | `MoveAhead`, `RotateLeft`, `RotateRight`, `Stop`이 공통 action contract로 사용됩니다. |
| T6.3 | `rast/planner/object_list_planner.py` | Object List baseline용 최소 planner를 정의합니다. | T5.1, T6.2 | 같은 action space를 사용하고, RiskToken 없이 object distance만으로 action을 고릅니다. |

### 4.8 MVP-0 Runner

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T7.1 | `experiments/run_mvp0_vertical_slice.py` | smoke -> snapshot -> tokenization -> baseline -> planner -> JSONL logging을 연결합니다. | T2, T3, T4, T5, T6 | 단일 episode 또는 단일 step vertical slice가 한 번 실행되는 흐름이 정의됩니다. |
| T7.2 | `configs/mvp0.yaml` | scene, seed, max_steps, risk threshold, logging path를 정의합니다. | T7.1 | config만 바꿔 scene/log path를 바꿀 수 있습니다. |

### 4.9 Tests

| ID | 파일 | 작업 내용 | 의존성 | Definition of Done |
|---|---|---|---|---|
| T8.1 | `tests/test_observation_snapshot.py` | fixture metadata에서 ObservationSnapshot 생성 테스트를 작성합니다. | T1.2 | simulator 없이 pure unit test로 통과합니다. |
| T8.2 | `tests/test_tokens.py` | EntityToken/RiskToken serialization과 required field validation을 테스트합니다. | T1.3 | token JSON round-trip이 통과합니다. |
| T8.3 | `tests/test_risk_tokenizer.py` | near object가 RiskToken을 생성하고 far object는 생성하지 않는지 테스트합니다. | T3.2 | threshold 기반 risk behavior가 deterministic합니다. |
| T8.4 | `tests/test_latency.py` | timer가 stage별 latency와 total latency를 기록하는지 테스트합니다. | T4.1 | `T_total`이 stage 합과 일관됩니다. |
| T8.5 | `tests/test_jsonl_logger.py` | JSONL logger가 한 줄 JSON record를 append하는지 테스트합니다. | T4.2 | 임시 디렉토리에서 log write/read가 통과합니다. |
| T8.6 | `tests/test_object_list_baseline.py` | Object List baseline이 ObservationSnapshot과 같은 object source를 쓰는지 테스트합니다. | T5.1 | input object count가 snapshot과 일치합니다. |
| T8.7 | `tests/test_token_planner.py` | RiskToken 유무에 따른 action selection을 테스트합니다. | T6.1 | high risk case와 no risk case가 deterministic합니다. |

## 5. Execution Order

| 순서 | 묶음 | 완료 후 확인 |
|---|---|---|
| 1 | T0 Project skeleton | package import와 pytest discovery가 가능합니다. |
| 2 | T1 Schemas | snapshot, token, latency schema가 JSON 직렬화됩니다. |
| 3 | T4 Latency/Logging | simulator 없이 latency와 JSONL logger unit test가 통과합니다. |
| 4 | T2 Simulator smoke | AI2-THOR reset/step으로 ObservationSnapshot이 생성됩니다. |
| 5 | T3 Tokenizers | snapshot에서 EntityToken/RiskToken이 생성됩니다. |
| 6 | T5 Object List baseline | 같은 snapshot에서 baseline representation이 생성됩니다. |
| 7 | T6 Minimal planners | RAST planner와 Object List planner가 같은 action space를 사용합니다. |
| 8 | T7 MVP-0 runner | 단일 vertical slice가 JSONL log를 남깁니다. |
| 9 | T8 Tests | pure unit test와 가능한 smoke test가 통과합니다. |

## 6. Global Definition of Done

MVP-0 vertical slice는 다음 조건을 만족하면 완료로 봅니다.

| DoD | 설명 |
|---|---|
| AI2-THOR smoke path 존재 | 기본 scene reset과 최소 action step을 실행하는 경로가 있습니다. |
| ObservationSnapshot 생성 | AI2-THOR metadata가 simulator-independent snapshot으로 변환됩니다. |
| EntityToken 생성 | snapshot object에서 최소 EntityToken list가 생성됩니다. |
| RiskToken 생성 | near-agent 또는 near-path rule로 최소 RiskToken이 생성됩니다. |
| LatencyRecord 기록 | observation, perception, token_generation, planning, action, total latency가 분리 기록됩니다. |
| JSONL log 생성 | 한 step 또는 짧은 episode 결과가 append-only JSONL로 저장됩니다. |
| Object List baseline 생성 | RAST와 같은 ObservationSnapshot source에서 object list baseline이 생성됩니다. |
| 최소 token planner 동작 | EntityToken/RiskToken을 입력으로 deterministic action을 반환합니다. |
| baseline action space 일치 | RAST planner와 Object List planner가 같은 action set을 사용합니다. |
| unit test 통과 | simulator가 없어도 schema/tokenizer/logger/planner 핵심 unit test가 통과합니다. |
| smoke test 분리 | AI2-THOR 설치가 필요한 test는 별도 marker 또는 script로 분리됩니다. |
| scope 준수 | RelationToken, EventToken, UncertaintyToken, dashboard, Habitat, learned extractor는 구현하지 않습니다. |

## 7. MVP-0 Non-Goals

| 항목 | 이유 |
|---|---|
| full experiment runner | MVP-0는 vertical slice 검증이 목적입니다. |
| ablation runner | RiskToken 제거 실험 등은 MVP-1 이후로 둡니다. |
| Token Memory incremental update | PRD 핵심 요구지만 MVP-0에서는 schema와 latency 설계만 준비합니다. |
| Scene Graph/Flat Feature Table baseline | Object List baseline이 먼저 안정화되어야 합니다. |
| visualization dashboard | JSONL log가 먼저 안정화되어야 합니다. |
| perception-bound extractor | Phase 1 Oracle Tokenization이 먼저입니다. |

## 8. Implementation Notes for Next Step

| 주제 | 결정 |
|---|---|
| schema 구현 | Pydantic을 우선 사용하되, 버전은 구현 시점 공식 문서를 확인합니다. |
| confidence 기본값 | simulator metadata 기반 Phase 1에서는 기본 confidence를 `1.0`으로 둘 수 있습니다. 단, 이 값은 실제 perception confidence가 아님을 주석과 log에 명시해야 합니다. |
| path relevance | MVP-0에서는 planned path 전체 대신 agent forward direction 또는 next action corridor를 단순 proxy로 사용할 수 있습니다. |
| risk threshold | 기본값을 config로 빼고, 코드에 magic number로 고정하지 않습니다. |
| latency 측정 | `time.perf_counter()` context manager를 사용합니다. |
| logging | JSONL 한 줄은 schema_version, run_id, episode_id, step, baseline_type, latency, selected_action을 반드시 포함합니다. |
| tests | AI2-THOR 없이 가능한 pure unit test를 먼저 만들고, simulator smoke는 optional로 둡니다. |
