# Enterprise AI Hiring Platform Roadmap

This document captures the current state of Oasis and a practical roadmap for evolving it into an enterprise-grade AI hiring assessment platform.

## Product Thesis

Oasis should be positioned as an AI hiring assessment operating system, not only a coding-test platform. The strongest product wedge is evidence-based assessment of real AI engineering work:

- realistic production-style AI incidents
- isolated hands-on candidate environments
- rubric-backed deterministic and AI-assisted evaluation
- replayable engineering evidence for recruiters and hiring managers
- compliance-ready audit trails for regulated hiring workflows

The platform should make clear that AI assists evaluation and humans make hiring decisions.

## Current Repository State

The repository currently contains:

- `platform/api`: FastAPI control plane for authentication, challenge discovery, session creation, evaluation, invites, telemetry, and admin results.
- `platform/ui`: static candidate, recruiter, profile, registration, and login pages.
- `challenges`: domain-specific assessment packs with `manifest.yaml`, candidate workspaces, mock services, and grader scripts.
- `platform/infra`: early AWS CDK scaffolding for a sandbox VPC and ECS cluster.
- `docker-compose.yml`: local orchestrator, Ollama, adversary service, and code-server setup.

Current core flow:

1. Admin creates invite.
2. Candidate registers and selects a challenge.
3. API provisions a code-server workspace.
4. Candidate runs tests or submits.
5. Grader runs in a disposable Python container.
6. Admin reviews verdict, feedback, code, and trace logs.

## Key Gaps To Enterprise Grade

### Security

- The orchestrator mounts `/var/run/docker.sock`, giving the API broad host control.
- Sandboxes use default passwords in local compose.
- WebSocket interview sessions are not authenticated per connection.
- Challenge workspaces are mounted from shared folders.
- Secret management is environment-string based.
- There is no audit trail for admin actions, session access, or evaluation changes.

### Evaluation Quality

- Grader verdicts are parsed from unstructured text.
- A current bug maps `FAIL` or `ERROR` output to `PASS`; that should become a rejection or review state.
- LLM-as-judge output lacks structured evidence, confidence, rubric linkage, and repeatability controls.
- There is no reviewer calibration, appeal path, or human override workflow.

### Data Model

- SQLite is fine for local MVP, but enterprise needs Postgres and migrations.
- There is no organization, tenant, job, role, candidate profile, assessment assignment, or rubric schema.
- Candidate artifacts are stored directly on evaluation records instead of an artifact store.
- Invites do not have expiry, scoped challenge/job assignment, resend tracking, or revocation.

### Compliance

AI-assisted hiring systems may trigger employment selection, automated decision tool, and high-risk AI obligations depending on jurisdiction and usage. The platform should support:

- candidate notices and consent
- job-related validation evidence
- disparate impact and bias monitoring
- audit exports
- model and rubric versioning
- data retention controls
- human-in-the-loop decision records

Relevant public references:

- NYC Local Law 144 AEDT requirements: https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page
- EEOC employment selection procedures guidance: https://www.eeoc.gov/laws/guidance/employment-tests-and-selection-procedures
- EU AI Act Annex III high-risk employment systems: https://artificialintelligenceact.eu/annex/3/

## Target Product Modules

### 1. Assessment Studio

Build, version, and validate role-specific assessment simulations.

Capabilities:

- challenge authoring with manifests, templates, services, seed data, and expected artifacts
- rubric builder with weighted dimensions
- deterministic test cases and hidden test cases
- LLM judge prompt/version management
- challenge preview and dry-run validation
- benchmark candidates and calibration submissions

### 2. Candidate Sandbox

Provide a reliable, isolated, accessible candidate environment.

Capabilities:

- per-session cloned workspace
- code-server or browser IDE
- terminal and test runner
- resumable sessions
- accessibility accommodations
- resource and time limits
- immutable base challenge templates
- session artifact snapshotting on submit

### 3. Evaluation Engine

Generate defensible, structured assessment evidence.

Capabilities:

- deterministic checks first
- trace analysis
- LLM judge as a secondary evaluator
- structured JSON result schema
- rubric-dimension scores
- confidence and evidence fields
- reviewer override
- evaluator regression tests
- reproducible grading runs

### 4. Recruiter Console

Help hiring teams review signals without turning AI output into an automatic hiring decision.

Capabilities:

- candidate scorecards
- side-by-side comparisons
- role and job pipelines
- replayable session timelines
- source code and trace inspection
- structured interviewer notes
- reviewer assignments
- final human decision records

### 5. Compliance Center

Make the system usable by enterprise legal, HR, and security teams.

Capabilities:

- candidate notice configuration
- audit logs
- rubric and model version history
- adverse impact reporting
- data retention policies
- evidence exports
- access reviews
- legal hold support

### 6. Integrations

Meet enterprise buyers where their hiring workflow already lives.

Capabilities:

- SSO/SAML/OIDC
- SCIM user provisioning
- ATS integrations: Greenhouse, Lever, Ashby, Workday
- webhook delivery
- Slack/email notifications
- calendar scheduling
- HRIS exports

## Target Architecture

Recommended production architecture:

- `api-gateway`: request routing, rate limiting, auth enforcement
- `identity-service`: orgs, users, roles, SSO, SCIM
- `control-plane`: jobs, invites, sessions, challenges, evaluations
- `sandbox-orchestrator`: provisions isolated candidate environments
- `evaluation-runner`: async queue workers for grading
- `artifact-service`: stores code snapshots, logs, traces, generated reports
- `analytics-service`: funnel, quality, and fairness metrics
- `compliance-service`: audit exports, notices, retention, access logs
- `frontend`: recruiter app, candidate app, admin console
- `event-bus`: session, evaluation, invite, and integration events

Recommended infrastructure:

- Postgres for transactional data
- Redis, SQS, or Celery-compatible queue for async jobs
- S3-compatible object storage for artifacts
- OpenTelemetry for traces
- managed secrets store
- ECS/Fargate, Kubernetes, or Firecracker-based isolation for sandboxes
- WAF, TLS, centralized logging, and SIEM export

## Data Model Direction

Introduce first-class entities:

- `Organization`
- `User`
- `Role`
- `Team`
- `Job`
- `Candidate`
- `Invite`
- `Assessment`
- `Challenge`
- `ChallengeVersion`
- `Rubric`
- `RubricDimension`
- `Session`
- `Artifact`
- `Evaluation`
- `EvaluationRun`
- `ReviewerDecision`
- `AuditLog`
- `ConsentRecord`
- `IntegrationConnection`

Important modeling principles:

- Never mutate historical challenge, rubric, or evaluator versions.
- Every candidate result should point to exact versions of challenge, grader, rubric, model, and prompt.
- Artifacts should be immutable after submission.
- Human decision records should be distinct from AI/evaluator recommendations.

## Evaluation Result Schema

Move graders to structured JSON output:

```json
{
  "schema_version": "1.0",
  "verdict": "review",
  "score": 74,
  "max_score": 100,
  "dimensions": [
    {
      "id": "security",
      "label": "Security",
      "score": 18,
      "max_score": 25,
      "evidence": ["PII redaction test passed", "Prompt injection case failed"],
      "confidence": 0.82
    }
  ],
  "checks": [
    {
      "id": "unit_tests",
      "status": "passed",
      "summary": "14 of 16 tests passed"
    }
  ],
  "llm_judgments": [
    {
      "model": "local-judge",
      "prompt_version": "2026-04-25",
      "finding": "Candidate mitigated recursive loop but missed adversarial payload handling",
      "confidence": 0.7
    }
  ],
  "recommendation": "human_review_required"
}
```

Recommended verdict states:

- `strong_hire`
- `hire`
- `review`
- `no_hire`
- `invalid`
- `error`

Avoid `PASS` because it is ambiguous: it can mean passed the assessment or passed on the candidate.

## Roadmap

### Phase 1: Harden The MVP

Target: 2-4 weeks

Goals:

- Fix verdict parsing bug.
- Replace unstructured grader output with JSON.
- Add per-session cloned workspaces.
- Add invite expiry, revocation, and challenge/job scoping.
- Remove default admin password from code.
- Add API tests for auth, invites, sessions, and evaluation parsing.
- Add evaluator tests for each challenge.
- Add basic audit log table.

Deliverables:

- reliable local demo
- safer session lifecycle
- structured evaluation records
- basic regression test suite

### Phase 2: Enterprise Control Plane

Target: 4-8 weeks

Goals:

- Migrate from SQLite to Postgres.
- Add Alembic migrations.
- Add organizations, jobs, candidates, teams, and roles.
- Add scoped RBAC.
- Add artifact storage abstraction.
- Move evaluations from FastAPI `BackgroundTasks` to a queue worker.
- Add admin activity logs.
- Add session state machine.

Deliverables:

- multi-tenant data model
- durable evaluation processing
- production-grade persistence foundation
- auditable admin workflows

### Phase 3: Secure Sandbox Orchestration

Target: 6-10 weeks

Goals:

- Remove direct Docker socket dependency from the orchestrator.
- Provision sandboxes through ECS/Fargate, Kubernetes Jobs, or a dedicated worker.
- Apply CPU, memory, disk, network, and runtime limits.
- Add egress controls.
- Add per-session secrets and short-lived credentials.
- Add automatic teardown and orphan cleanup.
- Snapshot candidate artifacts on submit.

Deliverables:

- isolated candidate execution
- hardened sandbox provisioning API
- reproducible artifacts
- lower host compromise risk

### Phase 4: Hiring-Grade Evaluation

Target: 8-12 weeks

Goals:

- Add rubric schema and rubric builder UI.
- Support deterministic, trace-based, and LLM-assisted grading.
- Add evaluator versioning.
- Add reviewer calibration workflows.
- Add human override with reason codes.
- Add score explanations and evidence cards.
- Add challenge benchmark suite.
- Add evaluator drift monitoring.

Deliverables:

- defensible scorecards
- reviewer-ready evidence
- repeatable challenge evaluation
- reduced LLM-judge risk

### Phase 5: Compliance And Integrations

Target: 8-16 weeks

Goals:

- Add candidate notices and consent records.
- Add data retention policies.
- Add adverse impact analytics.
- Add audit packet exports.
- Add SSO/SAML/OIDC.
- Add SCIM.
- Add Greenhouse, Lever, Ashby, or Workday integration.
- Add webhooks and notification templates.

Deliverables:

- enterprise security and HR readiness
- compliance reporting foundation
- ATS-integrated hiring workflow
- buyer-facing trust package

## Near-Term Engineering Backlog

High priority:

- Fix `FAIL` and `ERROR` verdict handling.
- Add `EvaluationResult` Pydantic schema.
- Make every grader emit JSON.
- Clone challenge workspace per session.
- Persist artifacts outside the challenge template directory.
- Require non-default `SECRET_KEY`.
- Remove or disable demo login outside local development.
- Add WebSocket auth.

Medium priority:

- Add rate limiting on auth endpoints.
- Add invite expiration.
- Add challenge manifest validation.
- Add health checks.
- Add structured logging.
- Add OpenTelemetry trace IDs to sessions and evaluations.
- Add cleanup job for abandoned sandboxes.

Lower priority:

- Replace alerts in the UI with proper notification components.
- Convert static UI into a frontend app when workflows outgrow simple pages.
- Improve challenge authoring ergonomics.
- Add visual replay of session events.

## Success Metrics

Platform reliability:

- sandbox provisioning success rate
- median sandbox startup time
- evaluation completion rate
- orphaned sandbox count
- evaluator error rate

Hiring signal quality:

- reviewer agreement rate
- candidate score distribution by challenge
- challenge completion rate
- false positive and false negative review findings
- rubric calibration consistency

Enterprise readiness:

- audit export completeness
- SSO adoption
- ATS sync success rate
- data retention policy coverage
- security review pass rate

Fairness and compliance:

- adverse impact ratios where demographic data is legally collected
- notice delivery rate
- consent record completeness
- human override rate by job and reviewer
- evaluation drift over time

## Product Principles

- Do not make fully automated hiring decisions.
- Prefer work-sample evidence over abstract quizzes.
- Prefer deterministic tests over LLM judgment when deterministic tests can answer the question.
- Make every AI-generated recommendation explainable, reviewable, and overridable.
- Preserve historical versions of rubrics, prompts, graders, and challenge templates.
- Treat candidate data as sensitive employment data.
- Build auditability from the beginning, not as an afterthought.

