# stack.md — RAST Technical Stack

## 1. Document Purpose

이 문서는 RAST: Risk-Aware Scene Tokens 연구 MVP를 어떤 기술 스택으로 구현하고, 실험하고, 후속 확장할지 결정하기 위한 기술 스택 설계 문서입니다.

`prd.md`는 연구 목표, 문제 정의, AS-IS/TO-BE, 평가 가설, baseline 공정성, latency accounting 요구사항의 source of truth입니다. `stack.md`는 그 요구사항을 실제 구현 가능한 Python 연구 시스템, 실험 자동화 구조, 데이터 로깅 방식, 개발 환경 선택으로 번역합니다.

따라서 이 문서는 단순 dependency list가 아니라 architecture decision document입니다. 각 기술 선택은 다음 기준으로 판단합니다.

| 기준 | 설명 |
|---|---|
| MVP 구현 가능성 | 개인 개발자가 4~8주 안에 로컬에서 구현 가능한가 |
| 연구 재현성 | seed, scenario, config, schema version, metric이 반복 가능하게 관리되는가 |
| latency accounting | observation, perception, token generation, planning, action latency를 분리 측정할 수 있는가 |
| baseline fairness | object list, scene graph, flat feature table, RAST를 같은 information bound에서 비교할 수 있는가 |
| 확장 가능성 | Phase 2 perception-bound tokenization, Habitat, dashboard, learned extractor로 확장 가능한가 |

## 2. Project Constraints

| 제약 | 결정 |
|---|---|
| 개인 개발자 기준 로컬 개발 가능 | 초기 스택은 Python 중심, 단일 머신, 단순 CLI runner 위주로 설계합니다. |
| 초기 MVP는 simulation 기반 | 실제 로봇 제어보다 AI2-THOR indoor navigation 실험을 우선합니다. |
| 실제 로봇/임베디드 장비는 Non-Goal | ROS2, real robot bridge, embedded inference는 P2 이후로 둡니다. |
| AI2-THOR 우선 | object metadata와 indoor scene 접근성을 활용해 Phase 1 oracle tokenization을 빠르게 검증합니다. |
| Habitat은 후속 또는 비교 후보 | 대량 benchmark와 더 복잡한 navigation 확장 단계에서 검토합니다. |
| Python 중심 | simulator API, token schema, experiment runner, metric analysis를 Python으로 통합합니다. |
| Docker 사용 권장 | 환경 재현성과 headless 실행을 위해 권장하되, AI2-THOR 렌더링 이슈를 고려해 local venv 경로도 열어 둡니다. |
| GPU 의존성 낮춤 | MVP는 metadata 기반 tokenization과 rule-based planner라 GPU 없이도 가능한 구성을 우선합니다. |
| Windows 가능성 | 현재 작업 환경은 Windows이지만, 안정적인 simulator/headless 개발은 Ubuntu 또는 Linux 기반을 우선 고려합니다. |
| 재현성과 latency 측정 중요 | config, logging, timing utility, baseline input export를 P0로 둡니다. |

## 3. Recommended Stack Summary

| Layer | Recommended Technology | Role | Reason | MVP Priority | Alternatives |
|---|---|---|---|---|---|
| Programming Language | Python | 전체 연구 시스템 중심 언어 | AI2-THOR API, 데이터 처리, 실험 자동화에 적합합니다. | P0 | C++, Julia |
| Simulator | AI2-THOR | MVP indoor navigation simulator | metadata, RGB-D, segmentation 접근성이 좋고 개인 연구에 현실적입니다. | P0 | Habitat |
| Token Schema | Pydantic 또는 dataclasses | RAST token schema 정의와 validation | schema versioning, JSON serialization, validation에 적합합니다. | P0 | JSON Schema 단독, TypedDict |
| Configuration | YAML + argparse/Typer | scenario, baseline, seed, logging path 관리 | 단순하고 설치 부담이 낮습니다. | P0 | Hydra |
| Planner | rule-based Python planner | token 기반 action policy와 baseline policy | representation 검증 단계에 충분하고 해석 가능합니다. | P0 | RL planner, LLM planner |
| Experiment Runner | Python CLI runner | episode 반복 실행과 ablation 자동화 | 실험 재현성과 batch 실행에 적합합니다. | P0 | notebooks, Airflow |
| Logging / Metrics | custom JSONL/SQLite logger | latency, token, action, metric 기록 | 외부 서비스 의존 없이 재현 가능한 로그를 남깁니다. | P0 | MLflow, Weights & Biases |
| Data Storage | JSONL + SQLite | step log와 episode summary 저장 | JSONL은 append-friendly, SQLite는 query-friendly입니다. | P0 | CSV, DuckDB, Parquet |
| Visualization | matplotlib + simple replay plots | metric plot, path plot, risk timeline | 빠른 분석과 보고서 그림 생성에 충분합니다. | P1 | Plotly, Streamlit |
| Backend API | FastAPI | dashboard backend와 token stream 조회 | 실험 결과가 쌓인 뒤 viewer API로 확장합니다. | P2 | Flask, Django |
| Frontend Dashboard | Next.js | experiment viewer, token memory viewer | 상호작용형 demo dashboard에 적합합니다. | P2 | Streamlit, Dash |
| Testing | pytest | token schema, tokenizer, planner, metric 테스트 | 연구 코드라도 회귀 방지에 필요합니다. | P0 | unittest |
| Packaging | pyproject.toml + uv 권장 | 의존성 관리와 실행 환경 고정 | 개인 연구 프로젝트에서 빠르고 단순합니다. | P0 | requirements.txt, Poetry, conda |
| Containerization | Docker / Docker Compose | 재현 가능한 실행 환경 | headless, GPU, local 환경 차이를 문서화할 수 있습니다. | P1 | local venv only |
| Dev Environment | Ubuntu/WSL2 또는 Linux 우선 | simulator 안정 실행 | 렌더링, headless, Docker 연동이 상대적으로 안정적입니다. | P0 | native Windows |
| CI | GitHub Actions | schema/test/lint 자동 검증 | simulator 없이 가능한 unit test부터 자동화합니다. | P2 | local-only test |
| Documentation | Markdown docs | PRD, stack, protocol, report 관리 | 연구 의사결정과 실험 protocol을 추적하기 쉽습니다. | P0 | Notion, Google Docs |

## 4. Core Stack Decisions

### 4.1 Python

Python을 MVP의 중심 언어로 선택합니다.

선택 이유:

| 이유 | 설명 |
|---|---|
| simulator 접근성 | AI2-THOR, Habitat 등 embodied AI simulator의 Python API와 잘 맞습니다. |
| 연구 생산성 | token schema, tokenizer, planner, metric aggregation을 빠르게 작성할 수 있습니다. |
| 데이터 처리 | NumPy, pandas, Polars, SQLite, DuckDB 등 실험 분석 도구와 연결이 쉽습니다. |
| 테스트와 자동화 | pytest, argparse/Typer, YAML config로 실험 runner를 단순하게 구성할 수 있습니다. |

대안:

| 대안 | 판단 |
|---|---|
| C++ | real-time robotics에는 유리하지만 MVP의 representation 검증에는 개발 비용이 큽니다. |
| Julia | 수치 실험에는 장점이 있으나 AI2-THOR/Habitat 생태계와 맞지 않습니다. |

### 4.2 AI2-THOR

AI2-THOR를 초기 MVP simulator로 추천합니다.

선택 이유:

| 이유 | 설명 |
|---|---|
| indoor navigation 적합 | 주방, 거실 등 indoor embodied task를 빠르게 구성할 수 있습니다. |
| object metadata 접근 | Phase 1 Oracle Tokenization에서 객체 위치, visibility, object type을 활용하기 좋습니다. |
| RGB-D/segmentation 확장 | Phase 2에서 RGB-D, segmentation, detector output 기반 tokenization으로 확장할 수 있습니다. |
| 로컬 실행 현실성 | 대형 simulator보다 개인 개발자가 로컬에서 시작하기 쉽습니다. |

Habitat 대비 장점:

| 장점 | 설명 |
|---|---|
| 빠른 MVP | object metadata 기반 tokenization과 object navigation 실험을 빠르게 시작할 수 있습니다. |
| scene/object interaction | object-level metadata와 interaction 실험이 상대적으로 직관적입니다. |

한계:

| 한계 | 대응 |
|---|---|
| 대량 benchmark 표준성 | Habitat 확장으로 후속 보완합니다. |
| headless/rendering 이슈 | Docker, Xvfb, EGL, WSL2 환경을 구현 시점 공식 문서로 확인해야 합니다. |
| 실제 perception 일반화 | Phase 1 결과를 oracle-bound로 명시하고 Phase 2에서 perception-bound 평가를 진행합니다. |

### 4.3 Habitat

Habitat은 후속 확장 또는 benchmark 후보로 둡니다.

초기 MVP에서 우선순위가 낮은 이유:

| 이유 | 설명 |
|---|---|
| 초기 구현 복잡도 | RAST token schema와 baseline fairness를 먼저 검증해야 하므로 simulator 복잡도를 낮춥니다. |
| PRD의 Phase 1 목표 | AI2-THOR metadata 기반 oracle tokenization이 representation 검증에 충분합니다. |
| 개인 개발 현실성 | 환경 구축과 dataset 준비 부담을 MVP 이후로 미룹니다. |

도입 시점:

| 조건 | 설명 |
|---|---|
| AI2-THOR MVP가 안정화됨 | token schema, logger, baseline runner가 분리되어야 합니다. |
| unseen scene generalization 강화 필요 | 더 넓은 benchmark와 navigation task가 필요할 때 도입합니다. |
| perception-bound evaluation 확장 | RGB-D 기반 perception pipeline과 결합할 때 유용합니다. |

### 4.4 Pydantic or dataclasses

RAST token schema는 Pydantic 또는 dataclasses로 정의합니다. MVP에서는 Pydantic을 우선 추천하되, 실제 Pydantic v2 버전과 AI2-THOR/Python 호환성은 구현 시점에 공식 문서로 확인해야 합니다.

Pydantic 추천 이유:

| 이유 | 설명 |
|---|---|
| schema validation | EntityToken, RiskToken 등 필드 누락과 타입 오류를 빠르게 잡을 수 있습니다. |
| serialization | JSONL log와 API 응답으로 변환하기 쉽습니다. |
| versioning | `schema_version`을 명시하고 migration을 관리하기 좋습니다. |
| 문서화 | token field contract를 코드와 문서가 함께 따라가게 만들 수 있습니다. |

dataclasses가 유리한 경우:

| 경우 | 설명 |
|---|---|
| hot path 최적화 | token generation이 병목일 때 validation 비용을 줄일 수 있습니다. |
| 의존성 최소화 | 외부 dependency를 줄이고 싶을 때 적합합니다. |

권장 방식:

| 단계 | 선택 |
|---|---|
| MVP | Pydantic model로 schema validation과 JSON serialization을 우선합니다. |
| latency 최적화 | 내부 계산은 dataclasses/NumPy 구조를 쓰고 log boundary에서 Pydantic validation을 적용합니다. |

### 4.5 NetworkX

NetworkX는 scene graph baseline과 relation graph 표현에 사용합니다.

선택 이유:

| 이유 | 설명 |
|---|---|
| scene graph baseline | object node와 relation edge를 명확히 표현할 수 있습니다. |
| RAST 비교 | RelationToken 기반 구조와 일반 scene graph baseline을 같은 source에서 생성하기 좋습니다. |
| 구현 속도 | graph construction, traversal, node/edge attribute 관리가 단순합니다. |

주의점:

| 주의 | 설명 |
|---|---|
| 성능 한계 | 매우 큰 graph에서는 느릴 수 있으나 MVP scene 규모에서는 충분합니다. |
| 공정성 | Scene Graph baseline은 RAST와 동일한 object/relation source를 사용해야 합니다. |

### 4.6 NumPy / pandas / Polars

NumPy, pandas, Polars는 metric aggregation과 latency 분석에 사용합니다.

| 도구 | 역할 | 선택 기준 |
|---|---|---|
| NumPy | 거리, path margin, risk score 계산 | 모든 단계에서 P0로 사용합니다. |
| pandas | episode summary, CSV/JSONL 분석 | MVP 분석과 보고서 생성에 적합합니다. |
| Polars | 큰 로그의 빠른 aggregation | 로그가 커지면 P1/P2에서 도입합니다. |

권장:

| 단계 | 선택 |
|---|---|
| MVP | NumPy + pandas |
| 로그가 커진 뒤 | Polars 또는 DuckDB를 추가 검토 |

### 4.7 CSV / JSONL / SQLite / DuckDB / Parquet

실험 결과 저장은 append-friendly log와 query-friendly summary를 분리합니다.

| 형식 | 장점 | 단점 | 권장 단계 |
|---|---|---|---|
| CSV | 사람이 보기 쉽고 pandas로 바로 읽기 좋습니다. | nested token stream 저장이 어렵습니다. | summary metric용 P0 |
| JSONL | step별 token, latency, action log를 append하기 좋습니다. | 큰 파일에서 query가 불편합니다. | raw experiment log용 P0 |
| SQLite | 단일 파일 DB로 query와 join이 쉽습니다. | schema 설계가 필요합니다. | episode summary와 index용 P0/P1 |
| DuckDB | Parquet/CSV 분석과 aggregation이 강합니다. | MVP 초반에는 과할 수 있습니다. | 대량 분석 P1/P2 |
| Parquet | columnar storage와 대규모 분석에 적합합니다. | 사람이 직접 보기 어렵습니다. | 대량 benchmark P2 |

권장 전략:

| 단계 | 저장 방식 |
|---|---|
| MVP | JSONL step log + CSV/SQLite episode summary |
| 분석 확장 | SQLite index + DuckDB query |
| 대량 benchmark | Parquet + DuckDB |

### 4.8 FastAPI

FastAPI는 실험 결과 조회 API, token stream viewer, dashboard backend로 후속 사용합니다.

선택 이유:

| 이유 | 설명 |
|---|---|
| Python 생태계 | 기존 experiment log와 token schema model을 재사용하기 쉽습니다. |
| typed API | Pydantic schema와 잘 맞습니다. |
| dashboard 확장 | Next.js 또는 다른 frontend가 experiment log를 조회할 수 있습니다. |

MVP 판단:

| 단계 | 결정 |
|---|---|
| P0 | 필수 아님. CLI와 파일 로그로 충분합니다. |
| P1/P2 | 결과가 쌓이고 replay/dashboard가 필요해지면 도입합니다. |

### 4.9 Next.js

Next.js는 visualization dashboard, experiment viewer, token memory viewer로 후속 사용합니다.

선택 이유:

| 이유 | 설명 |
|---|---|
| interactive dashboard | token timeline, risk timeline, path replay를 웹 UI로 보여주기 좋습니다. |
| demo 확장 | 연구 결과를 지도교수/심사자에게 보여주는 데 유용합니다. |
| FastAPI 연동 | backend API와 분리된 frontend로 구성할 수 있습니다. |

MVP 판단:

| 단계 | 결정 |
|---|---|
| P0 | 만들지 않습니다. CLI/log/matplotlib 기반 분석으로 시작합니다. |
| P1 | replay viewer가 필요하면 Streamlit 또는 simple FastAPI를 먼저 검토합니다. |
| P2 | 데모 품질이 중요해지면 Next.js dashboard를 도입합니다. |

### 4.10 Docker / Docker Compose

Docker는 simulator와 Python 환경 재현성을 확보하기 위해 권장합니다.

사용 이유:

| 이유 | 설명 |
|---|---|
| 환경 재현성 | Python, simulator, system dependency 차이를 줄입니다. |
| headless 실행 | 서버나 CI에서 rendering 환경을 문서화할 수 있습니다. |
| GPU/CPU 분리 | GPU가 있는 환경과 없는 환경을 별도 compose profile로 나눌 수 있습니다. |

주의점:

| 주의 | 설명 |
|---|---|
| AI2-THOR 렌더링 | headless rendering, X server, EGL, GPU driver는 구현 시점 공식 문서 확인이 필요합니다. |
| Windows/WSL2 | GPU passthrough와 GUI rendering 이슈가 생길 수 있습니다. |
| MVP 부담 | Docker가 막히면 local venv/conda로 먼저 smoke test를 진행합니다. |

권장 환경 구분:

| 환경 | 목적 |
|---|---|
| CPU/local venv | schema, tokenizer, planner, logger unit test |
| CPU/headless Docker | metadata 기반 experiment runner |
| GPU Docker | Phase 2 perception-bound extractor 또는 detector 사용 |

### 4.11 pytest

pytest는 P0 테스트 도구입니다.

필요한 이유:

| 이유 | 설명 |
|---|---|
| schema 안정성 | token 필드 변경이 logger/planner를 깨뜨리지 않게 합니다. |
| baseline fairness | 같은 metadata snapshot에서 baseline별 representation이 생성되는지 검증합니다. |
| metric 신뢰성 | collision, near-miss, p95 latency 계산 오류를 방지합니다. |
| deterministic replay | seed 고정 scenario가 재현되는지 확인합니다. |

### 4.12 YAML config / Hydra

MVP에서는 YAML + argparse 또는 Typer를 추천합니다. Hydra는 실험 조합이 많아진 뒤 도입합니다.

MVP 추천:

| 도구 | 이유 |
|---|---|
| YAML | scenario, seed, baseline, logging path를 사람이 읽기 쉽게 관리합니다. |
| argparse/Typer | CLI runner를 단순하게 만들 수 있습니다. |

Hydra를 미루는 이유:

| 이유 | 설명 |
|---|---|
| 초기 복잡도 | config composition이 강력하지만 초반에는 구조를 복잡하게 만들 수 있습니다. |
| MVP 범위 | 먼저 config key와 log format을 안정화하는 것이 중요합니다. |

도입 시점:

| 조건 | 설명 |
|---|---|
| ablation 조합 증가 | token 제거, noise, scene split, baseline 조합이 많아질 때 도입합니다. |
| multi-run 자동화 필요 | seed sweep과 scenario sweep이 커질 때 유용합니다. |

### 4.13 MLflow / Weights & Biases / custom logger

MVP에서는 custom JSONL/CSV/SQLite logger를 추천합니다.

| 도구 | 장점 | 단점 | 권장 |
|---|---|---|---|
| custom logger | 외부 의존성 없음, information-bound log를 원하는 대로 설계 가능 | UI가 없음 | P0 |
| MLflow | local tracking 가능, metric 비교가 편함 | 초기 설정과 artifact 관리가 필요 | P1 |
| Weights & Biases | dashboard와 collaboration이 강함 | 외부 서비스 의존성이 생김 | P2 또는 협업 시 |

RAST는 latency accounting과 baseline input audit가 중요하므로, 처음에는 custom logger가 더 적합합니다.

## 5. MVP Stack

초기 4~8주 MVP에 사용할 최소 스택은 다음과 같습니다.

| 기술 | 우선순위 | 이유 |
|---|---|---|
| Python | P0 | simulator API, token schema, planner, experiment runner를 통합합니다. |
| AI2-THOR | P0 | indoor navigation과 simulator metadata 기반 oracle tokenization에 적합합니다. |
| Pydantic | P0 | EntityToken, RiskToken 등 token schema validation과 serialization에 필요합니다. |
| NumPy | P0 | 거리, path relevance, risk score 계산에 필요합니다. |
| pandas | P0 | episode summary와 latency metric aggregation에 필요합니다. |
| NetworkX | P0 | Scene Graph baseline과 relation graph 생성을 위해 필요합니다. |
| matplotlib | P1 | latency plot, path plot, risk timeline 시각화에 사용합니다. |
| JSONL | P0 | step-level token/action/latency log 저장에 적합합니다. |
| SQLite | P0/P1 | episode summary, run index, query 가능한 결과 관리에 적합합니다. |
| pytest | P0 | schema, tokenizer, planner, metric regression을 검증합니다. |
| YAML config | P0 | scenario, seed, baseline, tokenizer mode를 재현 가능하게 관리합니다. |
| argparse 또는 Typer | P0 | simple CLI experiment runner에 사용합니다. |
| Docker | P1 | 환경 재현성 확보에 권장하지만 AI2-THOR smoke test 이후 도입해도 됩니다. |

## 6. Deferred Stack

다음 기술은 MVP 이후로 미룹니다.

| 기술 | 미루는 이유 | 도입 시점 |
|---|---|---|
| Habitat | 초기 구현 복잡도를 낮추기 위해 AI2-THOR를 우선합니다. | AI2-THOR MVP 후 unseen benchmark 확장이 필요할 때 |
| FastAPI | 초기에는 파일 로그와 CLI 분석으로 충분합니다. | token stream viewer 또는 dashboard backend가 필요할 때 |
| Next.js dashboard | demo UI보다 실험 protocol 안정화가 먼저입니다. | 결과가 쌓이고 시각적 데모가 필요할 때 |
| MLflow | custom logger로 필요한 정보를 더 명확히 통제할 수 있습니다. | 실험 수가 많아져 metric tracking UI가 필요할 때 |
| ROS2 | 실제 로봇 배포가 Non-Goal입니다. | real robot bridge가 연구 범위에 들어올 때 |
| Isaac Sim | 무겁고 초기 목표보다 복잡합니다. | photorealistic/physics-heavy simulation이 필요할 때 |
| VLA model integration | representation 검증 이전에는 과합니다. | token-to-language 또는 JSON planner 실험 단계 |
| learned token extractor | Phase 1은 oracle tokenization입니다. | Phase 2 perception-bound evaluation 이후 |
| foundation-model-assisted extractor | 비용과 불확실성이 큽니다. | schema 안정화 후 extractor generalization 연구 단계 |
| GPU-accelerated perception | MVP는 GPU 의존성을 낮춥니다. | detector/segmentation 기반 Phase 2에서 필요 시 |
| real robot bridge | 실제 로봇 배포가 Non-Goal입니다. | sim-to-real 후속 연구 단계 |

## 7. Architecture Overview

기술 스택 관점의 전체 구조는 다음과 같습니다.

```text
Simulator
-> Observation Adapter
-> Oracle Metadata Adapter or Perception Adapter
-> Scene Tokenizer
-> Token Memory
-> Incremental Update Engine
-> Planner
-> Baselines
-> Evaluation Logger
-> Analysis / Dashboard
```

| 모듈 | responsibility | input | output | recommended technology | test strategy |
|---|---|---|---|---|---|
| Simulator | scene 실행, action 적용, observation 반환 | scenario config, action | observation, metadata | AI2-THOR | smoke test, deterministic reset test |
| Observation Adapter | simulator output을 공통 snapshot으로 변환 | AI2-THOR event | observation snapshot | Python, Pydantic | snapshot schema test |
| Oracle Metadata Adapter | metadata 기반 Phase 1 token source 생성 | object metadata | entity source records | Python | metadata field mapping test |
| Perception Adapter | Phase 2 perception output 변환 | RGB-D, segmentation, detector output | perception source records | Python, optional CV models | mocked detector output test |
| Scene Tokenizer | source records를 token stream으로 변환 | source records, planner path | Entity/Risk/etc tokens | Pydantic, NumPy | tokenizer unit test |
| Token Memory | previous/current token state 관리 | token stream | token state, diff | Python dict, Pydantic | state transition test |
| Incremental Update Engine | 변경된 token만 업데이트 | token diff | updated token stream, EventToken | Python, NumPy | full vs incremental equivalence test |
| Planner | token 기반 action 선택 | token stream, agent state | selected action | rule-based Python | policy test |
| Baselines | object list, scene graph, flat table, raw baseline 생성 | same snapshot | baseline representation | NetworkX, pandas | information-bound test |
| Evaluation Logger | latency, action, metric 저장 | run context, timers, metrics | JSONL/SQLite logs | custom logger | log schema test |
| Analysis / Dashboard | metric aggregation과 시각화 | logs, summaries | plots, reports, UI | pandas, matplotlib, optional FastAPI/Next.js | report smoke test |

## 8. Suggested Repository Structure

현재 작업 디렉토리는 `prd.md`, `README.md`, `LICENSE`, `.gitignore` 중심의 초기 상태입니다. 따라서 실제 디렉토리를 만들지는 않고, 다음 구조를 제안합니다.

```txt
rast/
  simulator/
    ai2thor_env.py
    observation_adapter.py

  schemas/
    tokens.py
    events.py
    metrics.py

  tokenizer/
    entity_tokenizer.py
    relation_tokenizer.py
    event_tokenizer.py
    risk_tokenizer.py
    affordance_tokenizer.py
    uncertainty_tokenizer.py
    evidence_tokenizer.py

  token_memory/
    memory.py
    incremental_update.py

  planner/
    token_planner.py
    baseline_planner.py
    policies.py

  baselines/
    object_list.py
    scene_graph.py
    flat_feature_table.py
    raw_observation.py

  experiments/
    run_experiment.py
    run_ablation.py
    scenarios/
      object_nav.yaml
      cluttered_room.yaml
      unknown_object.yaml

  evaluation/
    latency.py
    metrics.py
    reports.py

  visualization/
    plot_metrics.py
    replay_viewer.py

  configs/
    default.yaml
    ai2thor.yaml
    baselines.yaml

  tests/
    test_tokens.py
    test_tokenizer.py
    test_planner.py
    test_metrics.py

  docs/
    prd.md
    stack.md
    experiment_plan.md
```

구조 원칙:

| 원칙 | 설명 |
|---|---|
| simulator와 tokenizer 분리 | AI2-THOR 의존성이 token schema 내부로 새지 않게 합니다. |
| schemas 독립 | planner, logger, dashboard가 동일 token contract를 재사용합니다. |
| baselines 독립 | object list, scene graph, flat feature table을 같은 source에서 생성합니다. |
| evaluation 독립 | latency accounting과 information-bound audit를 실험 코드와 분리합니다. |
| docs 유지 | PRD, stack, protocol, report를 코드와 함께 버전 관리합니다. |

## 9. Data and Logging Design

RAST의 로그는 재현성, latency accounting, baseline fairness를 검증할 수 있어야 합니다.

반드시 저장할 항목:

| 항목 | 설명 |
|---|---|
| raw observation reference | image/depth 파일 경로 또는 frame id pointer |
| simulator metadata snapshot | AI2-THOR metadata의 step별 snapshot 또는 hash |
| generated tokens | RAST token stream |
| token generation latency | 전체 및 token type별 생성 시간 |
| planning latency | planner action decision 시간 |
| end-to-end latency | `T_total` |
| selected action | planner가 선택한 action |
| collision / near-miss | safety metric |
| scenario id | scenario config id |
| random seed | 재현용 seed |
| baseline type | raw/object_list/scene_graph/flat_feature_table/rast |
| ablation setting | full, without_risk, without_event 등 |
| token schema version | 예: `rast.v0.2` |

MVP 권장 로그 구성:

| 로그 | 형식 | 목적 |
|---|---|---|
| step log | JSONL | step별 observation pointer, token, action, latency 저장 |
| episode summary | CSV 또는 SQLite | success, collision count, 평균/p95 latency 저장 |
| run index | SQLite | config path, git commit, schema version, output path 추적 |

JSONL 예시:

```json
{
  "run_id": "run_2026_06_09_001",
  "episode_id": "episode_0003",
  "scenario_id": "unknown_object_nav",
  "scene_id": "FloorPlan1",
  "seed": 42,
  "step": 17,
  "baseline_type": "rast",
  "ablation_setting": "full",
  "token_schema_version": "rast.v0.2",
  "tokenizer_mode": "oracle",
  "update_mode": "incremental",
  "raw_observation_ref": "runs/run_001/frames/episode_0003_step_0017.rgb.png",
  "metadata_snapshot_ref": "runs/run_001/metadata/episode_0003_step_0017.json",
  "latency_ms": {
    "observation": 7.8,
    "perception": 1.1,
    "token_generation": 3.4,
    "planning": 2.6,
    "action": 5.0,
    "total": 19.9
  },
  "token_generation_latency_by_type_ms": {
    "EntityToken": 0.9,
    "RelationToken": 0.7,
    "RiskToken": 0.8,
    "EventToken": 0.3,
    "AffordanceToken": 0.2,
    "UncertaintyToken": 0.3,
    "EvidenceToken": 0.2
  },
  "input_units": {
    "tokens": 18,
    "objects": 9,
    "graph_nodes": 9,
    "graph_edges": 14,
    "flat_rows": 9
  },
  "selected_action": "MoveAhead",
  "collision": false,
  "near_miss": false,
  "tokens_ref": "runs/run_001/tokens/episode_0003_step_0017.json"
}
```

## 10. Latency Measurement Stack

PRD의 핵심 공격 지점은 token generation overhead입니다. 따라서 latency 측정은 P0 기능으로 구현합니다.

측정 도구:

| 도구 | 역할 |
|---|---|
| `time.perf_counter()` | Python 기본 고해상도 timer로 stage별 시간을 측정합니다. |
| context manager timing utility | `with timer.stage("token_generation"):` 형태로 반복 가능한 측정 패턴을 만듭니다. |
| custom latency logger | stage별 latency와 token type별 latency를 JSONL/SQLite로 저장합니다. |
| pandas aggregation | p50, p95, mean, std, overhead ratio를 계산합니다. |
| matplotlib | latency breakdown stacked bar, p95 comparison plot을 생성합니다. |

측정 stage:

```text
T_total = T_observation
        + T_perception
        + T_token_generation
        + T_planning
        + T_action
```

필수 분리:

| 분리 항목 | 이유 |
|---|---|
| token generation latency와 planning latency | RAST가 planning은 빠르지만 전체는 느릴 수 있는지 확인합니다. |
| full recomputation vs incremental update | Token Memory의 실질적 이점을 검증합니다. |
| token type별 latency | RiskToken, RelationToken 등이 병목인지 확인합니다. |
| average와 p95 | 평균만으로 tail latency 문제를 숨기지 않습니다. |

시각화:

| plot | 목적 |
|---|---|
| latency breakdown stacked bar | baseline별 `T_total` 구성을 비교합니다. |
| p50/p95 latency plot | planning과 end-to-end tail latency를 비교합니다. |
| token type overhead plot | token별 생성 비용을 비교합니다. |
| incremental benefit plot | changed object count별 full/incremental update 차이를 보여줍니다. |

## 11. Baseline Fairness Stack

Information-bound evaluation을 구현하기 위해 모든 baseline은 동일 simulator observation source에서 출발해야 합니다.

기술 설계:

| 항목 | 설계 |
|---|---|
| common snapshot | AI2-THOR event를 `ObservationSnapshot`으로 저장합니다. |
| shared metadata | object list, scene graph, flat table, RAST 모두 같은 metadata snapshot에서 생성합니다. |
| representation exporter | baseline별 representation을 같은 run directory에 저장합니다. |
| information leakage audit | baseline별 accessible fields와 forbidden fields를 로그로 남깁니다. |
| input unit count | object 수, graph node/edge 수, flat row 수, token 수, raw pixel 수를 기록합니다. |

Baseline별 설계:

| baseline | representation | recommended technology |
|---|---|---|
| Object List baseline | object id, category, position, confidence | Pydantic 또는 pandas DataFrame |
| Scene Graph baseline | object nodes + relation edges | NetworkX |
| Flat Feature Table baseline | RAST와 동일 scalar feature, semantic contract 없음 | pandas DataFrame |
| RAST baseline | Entity, Relation, Event, Risk, Affordance, Uncertainty, Evidence token | Pydantic token models |

audit log 예시:

```json
{
  "run_id": "run_001",
  "episode_id": "episode_0003",
  "step": 17,
  "source_snapshot_hash": "sha256:...",
  "baseline_type": "flat_feature_table",
  "accessible_fields": [
    "object_id",
    "category",
    "position",
    "confidence",
    "distance_to_planned_path",
    "classification_uncertainty"
  ],
  "forbidden_fields": [
    "token_type",
    "event_type",
    "recommended_policy",
    "evidence_pointer"
  ],
  "input_unit_count": 9
}
```

## 12. Configuration Strategy

MVP에서는 YAML + argparse/Typer를 추천합니다. Hydra는 ablation 조합과 seed sweep이 많아진 뒤 도입합니다.

필수 config 항목:

| 항목 | 예시 |
|---|---|
| simulator | `ai2thor` |
| scene | `FloorPlan1` |
| task | `object_navigation` |
| seed | `42` |
| max steps | `200` |
| baseline type | `rast`, `object_list`, `scene_graph`, `flat_feature_table`, `raw_observation` |
| token schema version | `rast.v0.2` |
| tokenizer mode | `oracle`, `perception` |
| oracle vs perception mode | `oracle_metadata` 또는 `rgbd_detector` |
| full recompute vs incremental update | `full_recompute`, `incremental` |
| noise injection | position noise, class confidence noise, depth noise |
| occlusion scenario | enabled/disabled, occluder placement |
| logging path | `runs/run_001` |

YAML 예시:

```yaml
run:
  name: unknown_object_rast_full
  seed: 42
  output_dir: runs/unknown_object_rast_full

simulator:
  name: ai2thor
  scene: FloorPlan1
  max_steps: 200

task:
  type: object_navigation
  target_object: Mug

representation:
  baseline_type: rast
  token_schema_version: rast.v0.2
  tokenizer_mode: oracle
  update_mode: incremental

scenario:
  unknown_object: true
  occlusion: true
  noise_injection:
    enabled: false

logging:
  step_log: jsonl
  summary: sqlite
  save_observation_refs: true
```

판단:

| 선택 | 이유 |
|---|---|
| YAML + argparse/Typer | MVP에 충분하고 이해하기 쉽습니다. |
| Hydra | Week 5 이후 ablation과 multi-run sweep이 커지면 검토합니다. |

## 13. Testing Strategy

연구 코드라도 schema, metric, baseline fairness는 테스트가 필요합니다.

필수 테스트:

| 테스트 | 목적 |
|---|---|
| token schema validation test | 필수 field 누락, type mismatch, schema version 오류를 잡습니다. |
| tokenizer unit test | metadata snapshot에서 기대 token이 생성되는지 확인합니다. |
| risk score calculation test | distance/path/uncertainty 변화에 따른 risk score monotonicity를 검증합니다. |
| planner policy test | RiskToken/UncertaintyToken에 따라 slow_down/replan action이 선택되는지 확인합니다. |
| metric calculation test | success, collision, near-miss, p95 latency 계산을 검증합니다. |
| baseline information-bound test | baseline별 accessible information이 동일 source에서 생성되는지 확인합니다. |
| latency logger test | stage별 timer가 누락 없이 기록되는지 확인합니다. |
| deterministic scenario regression test | 같은 seed와 scenario에서 episode summary가 재현되는지 확인합니다. |

테스트 계층:

| 계층 | 실행 환경 |
|---|---|
| pure unit test | simulator 없이 로컬/CI에서 실행 |
| simulator smoke test | AI2-THOR 설치 환경에서 최소 scene reset/step 실행 |
| integration test | 짧은 episode를 실행하고 log schema를 검증 |

## 14. Environment Setup

권장 개발 환경:

| 항목 | 권장 |
|---|---|
| OS | Ubuntu 또는 Linux 기반 우선 |
| Windows | 가능하나 WSL2 또는 Docker 사용 시 rendering/GPU 이슈를 주의합니다. |
| Python version | AI2-THOR, Pydantic, NumPy 등 공식 문서를 구현 시점에 확인해 호환 버전을 선택합니다. |
| virtual environment | `uv` 또는 virtualenv 기반을 우선 검토합니다. |
| conda | simulator/graphics dependency가 복잡하면 대안으로 사용합니다. |
| Docker | 재현성 확보를 위해 권장하되, AI2-THOR smoke test가 먼저입니다. |
| GPU | Phase 1 MVP에는 필수 아님. Phase 2 perception-bound extractor에서 필요할 수 있습니다. |
| headless rendering | Docker/Xvfb/EGL 설정은 구현 시점 AI2-THOR 공식 문서를 확인해야 합니다. |

환경별 권장:

| 환경 | 권장 사용 |
|---|---|
| native Windows | 문서 작성, pure unit test, log analysis |
| WSL2 Ubuntu | Python 개발, unit test, 일부 simulator 실행 |
| Ubuntu local | 가장 안정적인 simulator 개발 환경 후보 |
| Docker CPU | reproducible experiment runner |
| Docker GPU | Phase 2 detector/segmentation pipeline |

구체적인 라이브러리 버전과 설치 명령은 구현 시점에 AI2-THOR, Habitat, Pydantic, PyTorch 등 공식 문서를 확인해야 합니다.

## 15. Dependency Management

개인 연구 프로젝트 기준으로 `pyproject.toml` + `uv`를 우선 추천합니다.

| 선택지 | 장점 | 단점 | 판단 |
|---|---|---|---|
| requirements.txt | 단순하고 익숙합니다. | lock/reproducibility가 약합니다. | 아주 초기 smoke test에는 가능 |
| pyproject.toml + uv | 빠르고 lock 관리가 가능하며 현대적입니다. | 일부 팀원에게 낯설 수 있습니다. | MVP 권장 |
| Poetry | dependency group 관리가 좋습니다. | 상대적으로 무겁게 느껴질 수 있습니다. | 대안 |
| conda environment.yml | simulator/graphics/native dependency 관리에 유리합니다. | Python package lock이 느슨해질 수 있습니다. | AI2-THOR/Habitat 이슈 시 대안 |

권장 방식:

| 단계 | 방식 |
|---|---|
| Week 1 | `pyproject.toml` 기반 minimal dependencies |
| AI2-THOR 설치 이슈 발생 | conda environment 또는 Dockerfile을 병행 검토 |
| Phase 2 perception | PyTorch/CUDA dependency는 별도 optional group으로 분리 |

## 16. Documentation Strategy

제안 문서:

| 문서 | 역할 |
|---|---|
| `prd.md` | 연구 목표, 문제 정의, 평가 가설, 성공 기준의 source of truth |
| `stack.md` | 기술 스택과 architecture decision 기록 |
| `experiment_plan.md` | scenario, baseline, ablation, seed, run matrix 정의 |
| `token_schema.md` | token field, versioning, example, schema migration 설명 |
| `baseline_protocol.md` | information-bound evaluation과 leakage audit 규칙 |
| `latency_protocol.md` | latency stage 정의, timing utility, aggregation 방식 |
| `result_report.md` | 실험 결과, metric table, failure case, 해석 한계 정리 |
| `troubleshooting.md` | AI2-THOR, Docker, headless rendering, Windows/WSL2 문제 해결 기록 |

문서 원칙:

| 원칙 | 설명 |
|---|---|
| protocol 우선 | 실험 결과보다 측정 protocol을 먼저 고정합니다. |
| schema version 명시 | token schema 변경은 실험 결과와 함께 추적합니다. |
| 한계 명시 | Phase 1 oracle-bound 결과를 perception 성능으로 해석하지 않습니다. |

## 17. Trade-off Analysis

| 선택 | 장점 | 단점 | 권장 |
|---|---|---|---|
| AI2-THOR vs Habitat | AI2-THOR는 metadata 기반 MVP가 빠르고, Habitat은 benchmark 확장에 강합니다. | AI2-THOR는 benchmark 범위가 제한될 수 있고, Habitat은 초기 구축이 무겁습니다. | MVP는 AI2-THOR, 확장은 Habitat |
| Pydantic vs dataclasses | Pydantic은 validation/serialization이 강하고, dataclasses는 가볍습니다. | Pydantic은 hot path overhead가 있을 수 있습니다. | schema boundary는 Pydantic, 내부 최적화는 dataclasses 검토 |
| CSV/JSONL vs SQLite vs DuckDB | CSV/JSONL은 단순하고, SQLite는 query가 쉽고, DuckDB는 대량 분석에 강합니다. | CSV/JSONL은 query가 불편하고, DuckDB는 초반에 과할 수 있습니다. | MVP는 JSONL+SQLite, 대량 분석은 DuckDB |
| CLI-only vs FastAPI dashboard | CLI-only는 빠르고 단순하며, FastAPI dashboard는 공유와 시각화에 좋습니다. | dashboard는 개발 비용이 큽니다. | MVP는 CLI-only, P2에서 FastAPI |
| YAML config vs Hydra | YAML은 단순하고, Hydra는 sweep과 composition이 강합니다. | Hydra는 초반 복잡도를 올립니다. | MVP는 YAML+Typer, 조합 증가 시 Hydra |
| Docker vs local venv | Docker는 재현성이 좋고, local venv는 빠르게 시작할 수 있습니다. | Docker는 rendering/GPU 설정이 까다로울 수 있습니다. | smoke test는 local, 재현 실험은 Docker |
| rule-based tokenizer vs learned extractor | rule-based는 해석 가능하고 빠르며, learned extractor는 perception realism에 가깝습니다. | rule-based는 generalization 한계가 있고, learned는 학습/데이터 비용이 큽니다. | Phase 1은 rule/oracle, Phase 2 이후 learned 검토 |

## 18. Recommended Implementation Phases

| 주차 | 기술 스택 도입 | 산출물 |
|---|---|---|
| Week 1 | Python environment, AI2-THOR smoke test, Pydantic token schema, basic JSONL logging | 최소 scene reset/step, `rast.v0.2` token model 초안 |
| Week 2 | EntityToken/RiskToken tokenizer, object list baseline, latency logger | `T_total` breakdown log, risk score unit test |
| Week 3 | Scene graph baseline, flat feature table baseline, NetworkX integration | information-bound exporter, baseline input unit count |
| Week 4 | token planner, experiment runner, first comparison | normal/cluttered scenario 결과 |
| Week 5 | EventToken/UncertaintyToken, unknown object and occlusion scenario | ablation config, unknown/occlusion recall metric |
| Week 6 | Token Memory, incremental update, full recompute comparison | incremental update benefit report |
| Week 7 | matplotlib visualization, report generation, p50/p95 latency analysis | latency plots, risk timeline, failure case notes |
| Week 8 | dashboard 여부 판단 또는 technical report polishing | `result_report.md`, optional simple replay viewer |

## 19. Final Recommended Stack

### P0 MVP Stack

반드시 지금 쓸 것:

| 기술 | 역할 |
|---|---|
| Python | 연구 시스템 중심 언어 |
| AI2-THOR | MVP simulator |
| Pydantic | token schema validation |
| NumPy | geometry, distance, risk score 계산 |
| pandas | metric aggregation |
| NetworkX | scene graph baseline |
| JSONL | step-level experiment log |
| SQLite 또는 CSV | episode summary와 run index |
| pytest | unit/regression test |
| YAML + argparse/Typer | config 기반 experiment runner |
| matplotlib | 기본 plot과 report figure |

### P1 Research Expansion Stack

MVP 이후 실험을 강화할 때 쓸 것:

| 기술 | 역할 |
|---|---|
| Docker / Docker Compose | 재현 가능한 headless experiment 환경 |
| Polars 또는 DuckDB | 큰 로그 분석과 aggregation |
| Hydra | ablation과 seed sweep 자동화 |
| MLflow local | 실험 tracking UI가 필요할 때 |
| simple replay viewer | token/action/risk timeline 검토 |
| perception adapter mock | Phase 2 전환 전 detector output 형태를 모사 |

### P2 Future Extension Stack

후속 연구나 데모 확장 때 쓸 것:

| 기술 | 역할 |
|---|---|
| Habitat | benchmark 확장과 unseen navigation 평가 |
| FastAPI | token stream/result query API |
| Next.js | demo dashboard와 experiment viewer |
| learned token extractor | perception-bound tokenization |
| GPU-accelerated perception | detector/segmentation pipeline |
| foundation-model-assisted extractor | schema generalization 연구 |
| ROS2 | 실제 로봇 bridge 연구 |
| Isaac Sim | 고정밀 물리/렌더링 simulation 확장 |
| VLA integration | token-to-language 또는 structured JSON planner 실험 |

## 20. Open Technical Questions

| 질문 | 검토 이유 |
|---|---|
| AI2-THOR만으로 unknown object scenario를 충분히 만들 수 있는가? | label masking, confidence degradation, synthetic obstacle insertion 중 현실적인 방식을 선택해야 합니다. |
| moving obstacle을 어떻게 시뮬레이션할 것인가? | AI2-THOR 지원 범위와 scripted object movement 가능성을 확인해야 합니다. |
| EvidenceToken은 실제 image crop을 저장할 것인가, metadata pointer만 저장할 것인가? | storage cost와 explainability 수준 사이의 trade-off가 있습니다. |
| logging은 JSONL로 충분한가, SQLite가 필요한가? | step log는 JSONL이 편하지만 baseline query와 run index에는 SQLite가 유리할 수 있습니다. |
| dashboard를 언제 도입할 것인가? | 실험 protocol이 안정화되기 전 dashboard는 개발 비용을 키울 수 있습니다. |
| learned extractor는 언제부터 필요한가? | Phase 1 oracle-bound 결과가 충분히 의미 있을 때 Phase 2로 넘어가는 기준이 필요합니다. |
| Habitat으로 확장할 기준은 무엇인가? | AI2-THOR에서 schema와 baseline fairness가 안정화된 뒤 확장하는 것이 적절합니다. |
| Pydantic validation overhead는 latency 측정에 얼마나 영향을 주는가? | hot path에서는 validation boundary를 제한해야 할 수 있습니다. |
| Docker headless 환경을 P0로 둘 것인가 P1로 둘 것인가? | 개인 로컬 환경과 CI/서버 실행 요구에 따라 달라집니다. |
| Flat Feature Table planner는 RAST planner와 얼마나 같은 로직을 공유해야 하는가? | 구조화 효과와 planner 구현 차이를 분리하기 위한 핵심 설계 질문입니다. |
