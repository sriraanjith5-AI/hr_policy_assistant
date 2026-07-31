# Architecture Implementation Guidelines

## Enterprise HR Policy Assistant — Consolidated Import, Dependency, and Layer Rules

## 1. Document Control

| Field | Value |
|---|---|
| Document Type | Architecture Implementation Guidelines |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| References | [architecture.md](./architecture.md) (SAD v1.2), [interfaces.md](./interfaces.md) (v1.1), [domain_models.md](./domain_models.md) (v1.3), [deployment.md](./deployment.md) (v1.0), [decisions/ADR-001-custom-orchestration.md](./decisions/ADR-001-custom-orchestration.md), [decisions/ADR-002-provider-abstraction-boundary.md](./decisions/ADR-002-provider-abstraction-boundary.md) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-31 |

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-31 | Initial Architecture Implementation Guidelines |

## 2. Purpose

This document formalizes **no new architecture**. Every rule below already exists, approved, in `architecture.md`, `interfaces.md`, `domain_models.md`, `deployment.md`, ADR-001, or ADR-002 — it was simply scattered across those six documents rather than checkable in one place before writing a line of code. That gap was identified explicitly during the Sprint 1.5 governance review: the *business* rules (what each layer does) were thoroughly explicit; the *import/dependency mechanism* rules (what each layer may literally `import`) were correct in substance but never consolidated. This document closes that specific gap and no other.

## 3. Scope

**In scope**: layer responsibilities, dependency direction, import allow/forbid rules per layer, provider/orchestrator/pipeline-stage/domain-model rules, configuration/logging/error-handling rules, and runtime invariant protection — all at the level of "what may depend on what," not "how a class is written."

**Out of scope**: Python naming/style conventions (`CODING_STANDARDS.md`), business/functional requirements (`requirements.md`), runtime call sequences (`sequence_diagrams.md`), and test strategy (`testing.md`). Where this document needs to reference any of those, it cites them rather than restating them.

## 4. Relationship to Existing Specifications

This document is **subordinate to** every document it consolidates. Where anything here appears to disagree with `architecture.md`, `interfaces.md`, `domain_models.md`, `deployment.md`, ADR-001, or ADR-002, the upstream document governs and this document has a defect to correct — not the other way around. This document adds no authority of its own; it only removes the friction of assembling already-approved rules from six places into one.

## 5. Repository Architecture Overview

The Sprint 1 folder structure (frozen — see Section 24) maps directly to `architecture.md` §3.0's layered model:

```
app/
├── core/            → Cross-Cutting Infrastructure (config, logging, exceptions)
├── domain/          → Domain Model Layer
├── providers/
│   ├── interfaces/       → Provider Interface Layer
│   └── implementations/  → Provider Implementation Layer
├── orchestrators/   → Orchestration Layer
├── pipeline/
│   ├── ingestion/   → Pipeline Stage Layer (ingestion stages)
│   └── query/       → Pipeline Stage Layer (query stages)
└── utils/           → Utility Layer
```

The Application Layer (future FastAPI, `architecture.md` §3) has no folder yet — correctly, since the MVP has none (`architecture.md` §8).

## 6. Layer Definitions

| Layer | Definition | Source |
|---|---|---|
| Application Layer | Thin transport adapter; no business logic. Not yet present. | `architecture.md` §3, §8 |
| Orchestration Layer | Sequencing and outcome-routing for the Query and Ingestion workflows. | `architecture.md` §3; `interfaces.md` §3 |
| Pipeline Stage Layer | Independently testable transformation steps, one responsibility each. | `architecture.md` §3; `interfaces.md` §4 |
| Domain Model Layer | The shared, provider-independent business vocabulary every other layer is expressed in terms of. | `architecture.md` §3; `domain_models.md` |
| Provider Interface Layer | Narrow, domain-model-typed contracts for the three permitted external capabilities. | `architecture.md` §4; `interfaces.md` §5 |
| Provider Implementation Layer | Concrete adapters; the only place a vendor SDK may be imported. | `architecture.md` §3.0; ADR-002 |
| External Infrastructure | Vendor services themselves (Embedding Service, Vector Database, LLM Service). Never imported directly by anything above Provider Implementations. | `architecture.md` §3.0 |
| Cross-Cutting Infrastructure | Configuration, logging, exceptions — shared by every layer above it, depends on nothing app-specific. | `architecture.md` §10 |
| Utility Layer | Small, stateless, domain-independent helpers. | Sprint 1 structural review |

## 7. Dependency Direction Rules

The one-way chain, restated verbatim from `architecture.md` §3.0:

```
Application Layer
        ↓
Orchestration Layer
        ↓
Pipeline Stage Layer
        ↓
Domain Model Layer
        ↓
Provider Interfaces
        ↓
Provider Implementations
        ↓
External Infrastructure
```

**Why this direction, not another**: Dependency Inversion (`architecture.md` §3.0, §11) — high-level policy (Orchestrators, Pipeline Stages) must not depend on low-level detail (which vendor is behind a Provider Interface). Both the high-level and low-level code depend on the same abstraction — the Provider Interface — and the abstraction depends on neither. A dependency arrow ever pointing the other way (e.g., a Provider Interface importing a Pipeline Stage) is not a style violation — it is a Dependency Inversion violation and must be treated as a defect, not a preference.

## 8. Allowed Imports by Layer

| Layer | May Import | Reason |
|---|---|---|
| Orchestrators | Pipeline Stage contracts (their declared input/output, not internals); Domain Models; `core/` | Orchestrators sequence stages and route on reported outcomes only (`interfaces.md` §3) |
| Pipeline Stages | Domain Models; Provider Interfaces; `core/`; `utils/` | A stage's contract is expressed entirely in domain-model terms (`interfaces.md` §4) and its only external capability access is through an interface (ADR-002) |
| Domain Models | Nothing app-specific | `domain_models.md` §2: domain models must remain reproducible, provider-independent, and framework-independent — a dependency of any kind above them would compromise that |
| Provider Interfaces | Domain Models only | A contract is expressed in domain-model terms and nothing else (`interfaces.md` §5) |
| Provider Implementations | The Provider Interface it satisfies; Domain Models (to construct return values); the corresponding External SDK; `core/` | ADR-002: this is the one layer permitted to import a vendor SDK, and it exists specifically to translate vendor-native shapes into domain models |
| `core/` (config, logging, exceptions) | Standard library only | Foundational — everything else depends on `core/`; `core/` must depend on nothing app-specific to avoid a circular dependency (Section 23 of `CODING_STANDARDS.md`) |
| `utils/` | Standard library / generic, non-vendor libraries only | Stateless, domain-independent helpers; must never gain a dependency on Domain Models, Providers, or Orchestrators, or it stops being generic |
| Application Layer (future) | Orchestrators only | `architecture.md` §3: a thin adapter, no business logic, calls into the core, never the reverse |

## 9. Forbidden Imports by Layer

| Layer | Must Never Import | Reason |
|---|---|---|
| Pipeline Stages | A Provider Implementation directly; any vendor SDK directly (OpenAI-shaped objects, Chroma/Pinecone-shaped objects, an embedding library's native vector type, a PDF parser library's native document/page object) | `architecture.md` §2.1 names these exact examples; `domain_models.md` §16 ("Provider Leakage") |
| Orchestrators | A vendor SDK of any kind; a Provider Implementation directly; anything that would require inspecting a domain model's *content* (an embedding's vector values, a chunk's text) to make a routing decision | `interfaces.md` §3's Orchestrator Responsibility Boundary — orchestrators route on already-reported outcomes, never inspect content themselves |
| Domain Models | Anything — no framework object (`domain_models.md` §16, "Framework Leakage" — no LangChain/LlamaIndex-shaped object), no vendor SDK object, no Provider, no Pipeline Stage, no Orchestrator | Domain models must remain the one stable, dependency-free layer everything else can rely on |
| Provider Interfaces | A vendor SDK of any kind; a specific Provider Implementation | An interface that imports its own implementation, or a vendor type, is not an abstraction (ADR-002) |
| Provider Implementations | A Pipeline Stage; an Orchestrator; another Provider Implementation | Prevents an inverted dependency — implementations must never need to know about the business logic that calls them |
| `core/` | Domain Models; Providers; Pipeline Stages; Orchestrators | `core/` must remain the one layer with zero app-specific dependencies, or every other layer's stability depends transitively on layers that were supposed to depend on `core/`, not the reverse |
| `utils/` | Domain Models; Providers; Pipeline Stages; Orchestrators | The moment `utils/` depends on any of these, it has stopped being generic and should have its content moved to whichever layer it actually serves |

## 10. Provider Boundary Rules

Per ADR-002, restated as implementation rules:

1. A Provider Implementation's only responsibilities are **translation** (vendor-native response → domain model) and **failure normalization** (vendor-specific error → the shared taxonomy, `interfaces.md` §7).
2. **Business logic never belongs inside a Provider Implementation.** A Provider Implementation that ranks, filters, selects, or interprets retrieved content has taken on a Pipeline Stage's responsibility and is a defect to correct, not a convenience to keep.
3. Every Provider Implementation must satisfy its Provider Interface's contract exactly, including every documented failure scenario (`interfaces.md` §4/§5 tables) — not only the success path.
4. PDF parsing is the one library `requirements.md` C-003 permits without a corresponding Provider Interface — it is consumed directly by the PDF Parser stage (`architecture.md` §4's own explicit carve-out), because interchangeability was never required for it the way it was for Embedding, Vector Store, and LLM access. This is the single, deliberate exception to "every vendor SDK sits behind an interface" — not a precedent for adding others.

## 11. Orchestrator Rules

Per ADR-001 and `interfaces.md` §3, restated as an allowed/forbidden pair (identical to the table already validated in `testing.md` §7):

**Allowed**: invoke stages in sequence; propagate a stage's reported outcome unchanged; decide retry-*eligibility* by failure category (never re-attempt the call itself — that belongs to the Provider Implementation); stop execution on a non-recoverable failure or a short-circuit condition; route to a terminal outcome based on a value already reported to it.

**Forbidden**: transform a domain model's content; inspect an embedding's vector values; perform or duplicate retrieval ranking logic; construct or interpret a prompt; derive or validate a citation. An orchestrator observed doing any of these has taken on a Pipeline Stage's responsibility.

## 12. Pipeline Stage Rules

1. One stage, one responsibility — matches exactly one `interfaces.md` §4 subsection. A stage handling more than one subsection's responsibility should be split.
2. A stage's declared dependency is always a Provider Interface or another stage's declared output — never a concrete Provider Implementation, and never another stage's internal logic (`architecture.md` §11, Single Responsibility).
3. A stage never reaches into another stage's internals to get something it needs — if two stages need to share something, that something belongs in `domain/` or `core/`, not passed by back-channel.
4. A stage's failure scenarios must be classified correctly as Business Outcome or Technical Failure before any error-handling code is written (Section 16 below) — this classification is itself part of the stage's contract, not an implementation afterthought.

## 13. Domain Model Rules

1. Every domain model has **exactly one owner** — a single Pipeline Stage (or, for `Response`'s declined state, the Not Found Path) — per `domain_models.md` §14's Ownership Matrix. No model is ever constructed or mutated by two different components.
2. A domain model never contains a vendor SDK object, a framework-native object, or a processing artifact with no independent business meaning (`domain_models.md` §16).
3. A domain model's meaning is defined once, in `domain_models.md` — no other document, and no code comment, redefines what a domain model represents.
4. Domain models are immutable once constructed unless `domain_models.md` explicitly states otherwise for that model (e.g., `ConversationSession`'s state transitions, §10).

## 14. Configuration Rules

1. Exactly one component (`core/config/`) resolves configuration; no Pipeline Stage, Orchestrator, or Provider reads an environment variable or configuration file directly (`architecture.md` §10.3).
2. Configuration is validated at startup, before any traffic is accepted — a missing or invalid required value is a startup failure, never a runtime surprise (SRS FR-1603).
3. Every component receives already-resolved configuration values, not raw configuration sources — see `CODING_STANDARDS.md` §15 for the code-level mechanism.
4. Secrets are never logged, never embedded in an error message, and never present in a configuration diagnostic without redaction (SRS FR-1604, FR-1605).

## 15. Logging Rules

1. Every stage, orchestrator, and provider call emits a structured log entry carrying: Correlation ID, Request ID, Execution timestamp, Component name, Processing duration, and (on failure) Error information — exactly the fields `interfaces.md` §8 requires, no more, no fewer as a baseline.
2. One correlation ID threads through every stage, provider, and retry attempt within a single request or ingestion run — this must hold even once the system scales to multiple instances (`deployment.md` §10).
3. Full document text and full generated answer text are not logged at routine verbosity — only identifiers and outcomes (SRS FR-1505).
4. Logging is obtained from one shared point (`core/logging/`), never an independently instantiated logger scattered per file.

## 16. Error Handling Rules

1. Every error is classified into the shared taxonomy — Validation, Parsing, Embedding, Retrieval, LLM, Citation validation, Configuration (`interfaces.md` §7) — never a bare, uncategorized exception.
2. Every error carries a recoverable/non-recoverable classification (SRS FR-1403); an Orchestrator retries a recoverable failure and fails the unit of work (without crashing the surrounding batch or session) on a non-recoverable one.
3. **The following are never errors, under any circumstance** — they are first-class, successful outcomes and must never populate the error taxonomy or an `ErrorContext`:
   - An empty `SearchResult[]` (no relevant evidence found).
   - An LLM decline due to insufficient grounding.
   - A truncated `QueryContext` (evidence exceeding the token budget).
   - An unresolved `CitationReference` (sets `unverified_statement_flag`, does not fail the request).

   (`interfaces.md` §7, "Not Error Conditions"; `domain_models.md` §11.) Code that maps any of these four into the error taxonomy is a contract violation, not a defensible implementation choice.

## 17. Runtime Invariant Protection

Every one of `domain_models.md` §19's six Runtime Invariants, plus the `ExecutionMetadata` ownership boundary (§11), must hold in the implemented system exactly as they hold in the specification. Stated here with the concrete way each could be violated in code, so it is checkable during review:

| Invariant | Could Be Violated By |
|---|---|
| 1. Grounded `Response` requires `QueryContext` + `GeneratedResponse`; declined `Response` varies by trigger | Citation Mapper being invoked, or attempting to invoke it, without both objects present |
| 2. `QueryContext` never exists without evidence or an explicit no-context outcome | Context Builder constructing a `QueryContext` with zero `RetrievedChunk[]` instead of short-circuiting |
| 3. `Citation` never exists without `CitationReference` resolution | Any code path constructing a `Citation` directly from a claim, bypassing resolution |
| 4. Provider failures never produce a partial `GeneratedResponse` | A Response Generator implementation returning a partially-filled object on a caught exception instead of propagating the failure |
| 5. Orchestrators never modify domain model meaning | An Orchestrator containing any conditional logic that inspects domain model *content* rather than a value already reported to it |
| 6. Domain models never contain provider-specific objects | A Provider Implementation returning its vendor SDK's native object instead of translating it first |
| `ExecutionMetadata` never becomes a business model | `ExecutionMetadata`/`ErrorContext` fields appearing as attributes on `Response`, `GeneratedResponse`, or `QueryContext` themselves |

## 18. External SDK Usage Rules

A vendor SDK import may appear in **exactly two kinds of files**: a Provider Implementation module under `app/providers/implementations/`, or the PDF Parser stage's own module (the one Section 10.4 carve-out). It must never appear anywhere else — not in a Pipeline Stage, not in an Orchestrator, not in `core/`, not in `utils/`, not in `domain/`. This is the single most consequential, most mechanically checkable rule in this document.

## 19. Adding New Components

1. The component must first have a contract in `interfaces.md` (or, for a domain model, a definition in `domain_models.md`) before implementation code is written — specification precedes implementation, per this project's Specification-Driven Development discipline.
2. A new component that owns a new domain model must be added to `domain_models.md` §14's Ownership Matrix at the same time.
3. A component that does not map to exactly one of the layers in Section 6 must not be added without first revising `architecture.md` — this document does not have the authority to introduce a new layer.

## 20. Modifying Existing Components

1. A change to a component's contract (input, output, failure scenarios) requires updating `interfaces.md` first, then the implementation — never the reverse.
2. A change to a domain model's meaning requires updating `domain_models.md` and checking every consumer listed in its Ownership Matrix row before the change is accepted.
3. A change that would violate a Runtime Invariant (Section 17) or a Frozen Architecture Decision (Section 24) is out of scope for implementation-level modification entirely — it requires a specification and/or ADR revision first.

## 21. Architecture Review Checklist

Before approving a change:

- [ ] Does every import in the changed files appear in Section 8's allowed list for that layer?
- [ ] Does any import appear in Section 9's forbidden list?
- [ ] Does a vendor SDK import appear anywhere outside a Provider Implementation or the PDF Parser stage (Section 18)?
- [ ] Does an Orchestrator contain any logic beyond Section 11's allowed list?
- [ ] Does every domain model constructed or mutated have exactly one owner, per Section 13?
- [ ] Are any of the four "Not Error Conditions" (Section 16) at risk of being classified as an error?
- [ ] Does the change touch anything in Section 24 (Frozen Architecture Decisions) without an accompanying ADR update?

## 22. Correct Dependency Examples

Illustrative import shapes only — not runnable application code:

```python
# ✓ Pipeline Stage -> Provider Interface
from app.providers.interfaces.embedding_provider import EmbeddingProviderInterface

# ✓ Provider Implementation -> Provider Interface (implements it)
from app.providers.interfaces.embedding_provider import EmbeddingProviderInterface

# ✓ Orchestrator -> Pipeline Stage (its declared contract)
from app.pipeline.query.retriever import Retriever

# ✓ Domain Model -> nothing above it
# app/domain/embedding.py has no imports from app.pipeline, app.orchestrators, or app.providers
```

## 23. Incorrect Dependency Examples

```python
# ✗ Pipeline Stage -> Provider Implementation (skips the interface)
from app.providers.implementations.some_vector_store_provider import SomeVectorStoreProvider

# ✗ Provider Implementation -> Pipeline Stage (inverted dependency)
from app.pipeline.query.retriever import Retriever

# ✗ Orchestrator -> Vendor SDK (skips every layer beneath it)
import some_vendor_sdk

# ✗ Domain Model -> Provider Interface (domain models depend on nothing)
from app.providers.interfaces.embedding_provider import EmbeddingProviderInterface
```

## 24. Architectural Decisions That Must Not Change

Every item below is already approved by `architecture.md`, ADR-001, ADR-002, or `domain_models.md`'s Runtime Invariants. None is introduced here — this section only collects them into one place. None may change without a corresponding ADR update (or, for Runtime Invariants, a `domain_models.md` revision carrying the same rigor).

- The seven-stage dependency chain in Section 7 (`architecture.md` §3.0).
- Custom orchestration, no orchestration framework (ADR-001).
- The three-interface Provider boundary — Embedding, Vector Store, LLM, no more, no fewer (ADR-002).
- The Orchestrator Responsibility Boundary (Section 11).
- Every Pipeline Stage's contract shape as defined in `interfaces.md` §4.
- The "exactly one owner" rule for every domain model (`domain_models.md` §14).
- All six Runtime Invariants and the `ExecutionMetadata` containment rule (`domain_models.md` §19, §11).
- The citation single-source-of-truth mechanism — resolved once at ingestion, never re-derived at query time (`domain_models.md` §9).
- The shared error taxonomy's category list (`interfaces.md` §7) and the four Not Error Conditions (Section 16).

## 25. Open Recommendations

Items this document does **not** mandate, because doing so would introduce a new decision beyond what any upstream document has approved:

- **Which specific static-analysis/lint tooling enforces Sections 8–9's import rules.** The rule is mandatory; the enforcement mechanism is not yet chosen.
- **Where the dependency-injection composition point lives** (see `CODING_STANDARDS.md` §14) — affects how Orchestrators and Pipeline Stages actually receive their Provider Interface instances, not yet decided.
- **`typing.Protocol` vs. `abc.ABC` for expressing Provider Interfaces in Python** — a real trade-off with no spec-level mandate either way; see `CODING_STANDARDS.md` §20 for the full discussion.

## 26. Cross-Document Validation

Every rule in this document was checked against its cited source before inclusion; nothing here contradicts `architecture.md`, `interfaces.md`, `domain_models.md`, `deployment.md`, ADR-001, or ADR-002. Two pre-existing, already-self-documented terminology inconsistencies live elsewhere in the specification suite (an environment-naming variance between `deployment.md` §18 and `testing.md` §4; a metric-naming variance flagged in `metrics_dictionary.md` §17) — neither is an architectural rule this document governs, and neither is resolved here, consistent with prior review findings that these remain open documentation items, not code-structure or import-boundary conflicts.

---

*End of Document.*
