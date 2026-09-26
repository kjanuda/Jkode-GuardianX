# Guardian X

> **Evidence-First AI Telecom Intelligence Platform**

Guardian X is a geo-aware, evidence-first telecom intelligence platform designed to detect network degradation, correlate affected devices and cells, identify and verify likely root causes, explain incidents using grounded AI, and generate guarded remediation recommendations.

Guardian X combines deterministic root-cause analysis, population correlation, cross-layer intelligence, geographic and terrain context, machine learning, local LLM reasoning, alert lifecycle management, guarded action planning, simulation, verification, feedback, and an operational dashboard.

> **Guardian X V1 operates in ADVISORY mode only.**
> Real OSS, BSS, NMS, RAN, or production-network execution is not enabled.

---

## 1. Why Guardian X?

Modern telecom networks continuously generate:

- Device telemetry
- Cell KPIs
- Signal quality measurements
- Network alarms
- Topology information
- Geographic information
- Environmental context
- Historical performance data

When network degradation occurs, engineers often need to manually correlate information from multiple systems before identifying the actual root cause.

Guardian X provides an evidence-first intelligence pipeline that brings those layers together.

It can:

- Detect network degradation
- Identify whether degradation affects a single device or a wider population
- Correlate device, cell, RF, topology, and historical evidence
- Add terrain, elevation, vegetation, and environmental context
- Build canonical evidence packets
- Perform evidence fusion
- Produce deterministic structured RCA
- Verify the RCA before treating it as authoritative
- Use ML and local LLM reasoning as supporting intelligence
- Generate alerts
- Produce guarded remediation recommendations
- Simulate proposed actions
- Verify simulated outcomes
- Preserve rollback readiness
- Present findings through a dashboard and AI Agent

---

## 2. End-to-End Guardian X Process

```text
Network Telemetry
        │
        ▼
Validation & Normalization
        │
        ▼
PostgreSQL / PostGIS
        │
        ├────────────────────┐
        ▼                    ▼
Device Health       Population Correlation
        │                    │
        └──────────┬─────────┘
                    ▼
          Cross-Layer Intelligence
                    │
                    ▼
      Geo / Terrain / Environment
                    │
                    ▼
          Canonical Evidence Layer
                    │
                    ▼
             Evidence Fusion
                    │
                    ▼
               RCA Hierarchy
                    │
                    ▼
       Structured Deterministic RCA
                    │
                    ▼
        Deterministic Verification
                    │
          ┌─────────┴─────────┐
          │                   │
       VERIFIED       NEEDS MORE EVIDENCE
          │
          ▼
     Authoritative RCA
          │
          ├──────────────┐
          │              │
          ▼              ▼
     ML Support     Local LLM / RAG
          │              │
          └───────┬──────┘
                   ▼
          Consensus Analysis
                   │
                   ▼
            Alert Lifecycle
                   │
                   ▼
        Guarded Action Planner
                   │
                   ▼
             Safety Gate
                   │
                   ▼
             Human Review
                   │
                   ▼
          Dry-Run Simulation
                   │
                   ▼
      Deterministic Verification
                   │
                   ▼
       Rollback Decision / Feedback
                   │
                   ▼
      Dashboard + Guardian AI Agent
```

---

## 3. High-Level Architecture

For the detailed architecture, see [`docs/architecture.md`](docs/architecture.md).

---

## 4. Evidence-First RCA Architecture

Guardian X separates authoritative diagnosis from supporting AI intelligence.

```text
Canonical Evidence
        │
        ▼
Structured RCA
        │
        ▼
Deterministic Verifier
        │
        ├── VERIFIED
        │      │
        │      ▼
        │  Authoritative RCA
        │
        └── REJECTED / INSUFFICIENT
               │
               ▼
         More Evidence Required
```

Supporting systems include:

- Evidence fusion
- RCA hierarchy
- Machine learning
- Local LLM reasoning
- RAG evidence grounding
- Consensus analysis

These systems may support diagnosis and explanation, but they cannot override a verified deterministic RCA.

---

## 5. Safety Architecture

Guardian X V1 intentionally separates intelligence from execution.

```text
Verified RCA
    │
    ▼
Action Plan
    │
    ▼
Safety Gate
    │
    ▼
Human Review
    │
    ▼
Simulation Approval
    │
    ▼
Dry-Run Simulation
    │
    ▼
Deterministic Verification
    │
    ▼
Rollback Decision
    │
    ▼
Feedback
```

Guardian X V1 safety state:

```text
execution_mode                  = ADVISORY
requires_human_approval         = true
auto_eligible                   = false

execution_allowed               = false
auto_execution_allowed          = false
physical_change_allowed         = false

deterministic_rca_authoritative = true
llm_can_override_rca            = false
llm_can_execute_actions         = false
```

Guardian X V1 exposes no production network execution control.

---

## 6. Core Capabilities

### Network Intelligence

- Device-level health analysis
- Cell-level degradation analysis
- Population correlation
- Cross-layer evidence correlation
- Historical evidence analysis
- Coverage and propagation signatures
- Congestion signatures
- Interference signatures
- Outage signatures

### Geo Intelligence

Guardian X combines network intelligence with geographic context.

Capabilities include:

- Tower mapping
- Cell mapping
- Device mapping
- Sector context
- Serving-cell context
- Elevation context
- Terrain-aware analysis
- Vegetation context
- Environmental context
- Interactive Leaflet network map
- Alert overlays
- RCA overlays
- Action-plan context

### Root Cause Analysis

Guardian X includes:

- Canonical evidence generation
- Evidence quality controls
- Evidence fusion
- RCA hierarchy
- Structured deterministic RCA
- Deterministic verification
- ML RCA prediction
- Local LLM proposal analysis
- Proposal verification
- Consensus analysis
- Evidence audit history

---

## 7. Alert Lifecycle

Guardian X supports the following alert lifecycle:

```text
OPEN
  │
  ▼
ACKNOWLEDGED
  │
  ▼
MITIGATING
  │
  ▼
RESOLVED
```

A resolved alert may later become `REOPENED`.

Alerts may contain:

- Device
- Severity
- Risk score
- Root cause
- Alert title
- Occurrence count
- First seen time
- Last seen time
- Resolution state

---

## 8. Guarded Remediation

Verified RCA findings may be translated into guarded action plans.

```text
Verified RCA
     │
     ▼
Action Planning
     │
     ▼
Safety Gate
     │
     ▼
Human Review
     │
     ▼
Simulation Approval
     │
     ▼
Dry Run
     │
     ▼
Verification
     │
     ▼
Rollback Readiness
     │
     ▼
Feedback
```

Guardian X V1 does not execute physical network changes.

---

## 9. Guardian AI Agent

Guardian X includes a local evidence-grounded AI assistant.

**Local AI Stack**
- Ollama
- qwen3.5:4b

The Agent can explain:

- RCA cases
- Root causes
- Evidence
- Alerts
- Devices
- Cells
- Action plans
- Verification states
- Safety states

Example question:

```text
Why is RCA-13 diagnosed as terrain propagation,
and what action is Guardian X recommending?
```

Agent flow:

```text
User Question
     │
     ▼
Entity Resolution
     │
     ▼
Guardian X Evidence Builder
     │
     ▼
Compact Evidence Packet
     │
     ▼
Local Ollama Model
     │
     ▼
Evidence-Grounded Explanation
```

The Agent is read-only.

```text
read_only_agent                   = true
deterministic_rca_authoritative   = true
llm_can_override_rca              = false
llm_can_execute_actions           = false
real_network_execution_enabled    = false
auto_execution_enabled            = false
```

The LLM is an explanation and reasoning layer, not the final operational authority.

---

## 10. Technology Stack

**Backend**
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- PostGIS
- Uvicorn
- uv

**AI / ML**
- Structured deterministic RCA
- Evidence fusion
- ML RCA prediction
- RAG-style evidence grounding
- Consensus analysis
- Ollama
- qwen3.5:4b

**Frontend**
- Next.js 16
- React
- TypeScript
- Tailwind CSS
- Leaflet
- React Leaflet
- Lucide React
- Framer Motion

---

## 11. Repository Structure

```text
GuardianX/
│
├── apps/
│   │
│   ├── api/
│   │   └── app/
│   │       ├── actions/
│   │       ├── agent/
│   │       ├── api/
│   │       ├── core/
│   │       ├── correlation/
│   │       ├── db/
│   │       ├── explanation/
│   │       ├── features/
│   │       ├── feedback/
│   │       ├── geo/
│   │       ├── ingestion/
│   │       ├── ml/
│   │       ├── models/
│   │       ├── rca/
│   │       ├── risk/
│   │       ├── schemas/
│   │       └── services/
│   │
│   └── web/
│       └── src/
│           ├── app/
│           ├── components/
│           ├── lib/
│           └── types/
│
├── data/
│   ├── cache/
│   └── ml/
│
├── docs/
│   └── architecture.md
│
├── scripts/
│
└── README.md
```

---

## 12. Dashboard Modules

### Overview — `/`

Provides high-level Guardian X operational intelligence.

### Alerts — `/alerts`

Displays:

- Active alerts
- Historical alerts
- Severity
- Root cause
- Risk
- Occurrences

### RCA Intelligence — `/rca`, `/rca/{caseId}`

Displays:

- RCA cases
- Structured diagnosis
- Confidence
- Verifier state
- Evidence
- Prediction history
- LLM proposal audit
- Consensus
- Action linkage

### Action Plans — `/actions`, `/actions/{planId}`

Displays:

- Recommended action
- RCA linkage
- Safety gate
- Human review
- Simulation state
- Verification state
- Rollback readiness

### Geo Intelligence — `/map`

Displays:

- Towers
- Cells
- Devices
- Active alert devices
- RCA context
- Action context
- Network topology

### Guardian AI Agent — `/agent`

Provides natural-language access to Guardian X evidence and verified intelligence.

---

## 13. Resilience

The frontend includes:

- Backend health monitoring
- ONLINE / OFFLINE state
- Route-level error boundaries
- Independent API failure handling
- Retry controls
- Empty states
- Agent timeout handling
- Safe action states

Same-origin Next.js proxy routes include:

```text
/api/backend-health
/api/agent/query
```

---

## 14. Backend Setup

Navigate to the API directory:

```powershell
cd E:\GuardianX\apps\api
```

Start FastAPI:

```powershell
uv run fastapi dev app/main.py --port 8001
```

Backend: `http://127.0.0.1:8001`

Swagger: `http://127.0.0.1:8001/docs`

Health endpoint: `GET /health`

Expected response:

```json
{
  "status": "healthy"
}
```

---

## 15. Ollama Setup

Verify installed models:

```powershell
ollama list
```

Guardian X V1 model:

```text
qwen3.5:4b
```

Install if required:

```powershell
ollama pull qwen3.5:4b
```

Start Ollama if required:

```powershell
ollama serve
```

Default Ollama endpoint: `http://localhost:11434`

Local AI performance depends on available CPU, RAM, and GPU resources.

---

## 16. Frontend Setup

Navigate to:

```powershell
cd E:\GuardianX\apps\web
```

Install dependencies:

```powershell
npm install
```

Verify `.env.local`:

```env
NEXT_PUBLIC_GUARDIAN_API_URL=http://127.0.0.1:8001
```

Start:

```powershell
npm run dev
```

Frontend: `http://localhost:3000`

Production validation:

```powershell
npm run lint
npm run build
```

---

## 17. Main API Surface

### Dashboard

```text
GET /api/v1/dashboard/summary
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/incidents
GET /api/v1/dashboard/map
GET /api/v1/dashboard/device/{device_external_id}
```

### Alerts

```text
GET /api/v1/alerts/active
GET /api/v1/alerts/history
GET /api/v1/alerts/device/{device_external_id}
```

### RCA

```text
GET /api/v1/rca/cases/{case_id}
GET /api/v1/rca/cases/{case_id}/evidence-packet

GET /api/v1/rca/device/{device_external_id}/cases
GET /api/v1/rca/cell/{cell_external_id}/cases
```

Guardian X also includes RCA processing APIs for: evidence fusion, RCA hierarchy, structured RCA, ML prediction, local LLM proposals, proposal verification, and consensus.

### Actions

```text
GET  /api/v1/actions/{plan_id}

POST /api/v1/actions/plan/{case_id}
POST /api/v1/actions/{plan_id}/policy-review
POST /api/v1/actions/{plan_id}/approve-simulation
POST /api/v1/actions/{plan_id}/reject
POST /api/v1/actions/{plan_id}/simulate

POST /api/v1/actions/simulations/{simulation_id}/verify
POST /api/v1/actions/{plan_id}/sync-lifecycle
```

These endpoints implement guarded planning and simulation. They do not expose production telecom execution.

### Guardian AI Agent

```text
POST /api/v1/agent/query
```

Example:

```json
{
  "question": "Why is RCA-13 diagnosed as terrain propagation, and what action is Guardian X recommending?",
  "case_id": 13
}
```

---

## 18. Example Guardian X RCA

A validated development scenario demonstrates the Guardian X reasoning chain.

```text
RCA Case          RCA-13
Scope             GX-CELL-001
Structured RCA    STRUCTURED_RCA_V1
Primary Cause     TERRAIN_PROPAGATION_LIKELY
Confidence        0.6904
Verifier          VERIFIED
Supporting        VEGETATION_PROPAGATION_POSSIBLE
```

Guardian X generated:

```text
Plan             PLAN-2
Action           REVIEW_TERRAIN_AWARE_COVERAGE
Target           GX-CELL-001
Mode             ADVISORY
Human Approval   REQUIRED
Auto Eligible    NO
Real Execution   DISABLED
```

The plan was evaluated through dry-run simulation and deterministic verification without enabling physical network changes.

---

## 19. Final Validation

Guardian X V1 passed its final end-to-end regression.

Validated backend APIs:

```text
/api/v1/dashboard/summary
/api/v1/dashboard/overview
/api/v1/dashboard/incidents
/api/v1/dashboard/map
/api/v1/alerts/active
/api/v1/alerts/history
/api/v1/rca/cases/13
/api/v1/actions/2
/api/v1/agent/query
```

Validated frontend routes:

```text
/
/alerts
/rca
/rca/13
/actions
/actions/2
/map
/agent
/api/backend-health
```

Final result:

```text
========================================
GUARDIAN X FINAL REGRESSION: PASS
========================================
```

Verified safety invariants:

| Invariant | Status |
|---|---|
| Deterministic RCA authoritative | PASS |
| Guardian Agent read-only | PASS |
| LLM cannot override RCA | PASS |
| LLM cannot execute actions | PASS |
| Human approval required | PASS |
| Auto execution disabled | PASS |
| Physical network changes disabled | PASS |
| Read-path DB counts unchanged | PASS |

---

## 20. Known V1 Limitations

Guardian X V1 is currently a research and prototype platform.

Current limitations include:

- No live production OSS/BSS/NMS integration
- No real RAN configuration execution
- No autonomous network modification
- Local LLM latency depends on host hardware
- Some development geo/environment evidence may be synthetic
- Enterprise authentication and RBAC are not implemented
- Production observability requires further work
- Production security hardening requires further work
- Real-world telecom validation requires controlled integration

---

## 21. Future Development

Potential Guardian X V2 areas include:

- Real OSS/BSS/NMS connectors
- Enterprise authentication
- Role-based access control
- Streaming telemetry
- Event-driven RCA pipelines
- GPU-accelerated local AI
- Real DEM data pipelines
- Advanced environmental datasets
- Multi-cell topology reasoning
- Network digital twin integration
- Production approval workflows
- Advanced feedback learning
- Incident timeline reconstruction
- Operational audit dashboards
- Controlled higher-level automation

Autonomous remediation should only be considered after extensive production-grade safety validation.

---

## 22. Design Principle

Guardian X follows one core principle:

> **AI may explain and recommend, but verified evidence controls the decision.**

Deterministic verification remains the authority for diagnosis and remediation eligibility.

---

## 23. Guardian X V1 Status

| Component | Status |
|---|---|
| Telemetry / Data Foundation | COMPLETE |
| Population Correlation | COMPLETE |
| Cross-Layer Intelligence | COMPLETE |
| Geo Intelligence | COMPLETE |
| Canonical Evidence | COMPLETE |
| Evidence Fusion | COMPLETE |
| RCA Hierarchy | COMPLETE |
| Structured RCA | COMPLETE |
| Deterministic Verification | COMPLETE |
| ML RCA Integration | COMPLETE |
| Local LLM / RAG | COMPLETE |
| Consensus | COMPLETE |
| Alert Lifecycle | COMPLETE |
| Guarded Actions | COMPLETE |
| Simulation / Verification | COMPLETE |
| Feedback Foundation | COMPLETE |
| Dashboard Backend | COMPLETE |
| Dashboard Frontend | COMPLETE |
| Alerts UI | COMPLETE |
| RCA UI | COMPLETE |
| Action UI | COMPLETE |
| Interactive Geo Map | COMPLETE |
| Guardian AI Agent | COMPLETE |
| Health / Resilience | COMPLETE |
| Final E2E Regression | PASS |

### Guardian X V1 Complete

Guardian X demonstrates an evidence-first approach to AI-assisted telecom operations in which machine intelligence supports engineering decisions without bypassing deterministic verification or operational safety controls.