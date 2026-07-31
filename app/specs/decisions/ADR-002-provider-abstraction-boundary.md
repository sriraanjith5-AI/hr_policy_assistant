# ADR-002: Provider Abstraction Boundary

## Status

Accepted

## Date

2026-07-29

## Context

The system depends on exactly three external capabilities — embedding generation, vector storage/search, and LLM generation — each of which is, in practice, satisfied by a specific vendor's SDK or API. `requirements.md` Constraint C-003 restricts third-party library use to four integration points (PDF parsing, embedding generation, vector database access, LLM API access); NFR-EXT-001–003 require that a provider be replaceable without touching pipeline logic; C-007 requires cloud portability. `architecture.md` §3.0 and §4 formalize the resulting Provider Interface / Provider Implementation split and the Dependency Inversion Principle it depends on. `interfaces.md` §5 defines the three Provider Interfaces (Embedding, Vector Store, LLM) as concrete contracts.

A decision is necessary here because "where exactly does vendor-specific code end and this system's own code begin" is not self-evident without an explicit boundary — and getting it wrong (even partially) reintroduces the vendor-coupling risk the rest of this architecture's provider-independence claims depend on.

## Decision

Only a Provider Implementation may import or interact with a vendor SDK — the Embedding Service's client library, the Vector Database's client library, or the LLM Service's client library. Every Pipeline Stage and every Orchestrator depends exclusively on a Provider Interface (`interfaces.md` §5), expressed entirely in domain-model terms (`domain_models.md`) — never on a Provider Implementation, and never on a vendor SDK type, directly.

**Architectural boundary, stated precisely:** `Provider Interface (contract, domain-model-shaped)` → `Provider Implementation (the only place a vendor SDK is imported)` → `External Infrastructure (the vendor service itself)`. A Pipeline Stage calls a Provider Interface method with domain-model inputs and receives domain-model outputs; it has no visibility into, and no dependency on, which vendor or SDK sits behind that interface.

**Intentionally not included:** a Provider Implementation contains no business logic. It does not rank, filter, or select retrieval candidates (that is the Retriever's responsibility); it does not construct or interpret a prompt; it does not resolve or validate a citation. Its sole responsibilities are (a) translating a vendor-native response into the domain model the interface promises, and (b) normalizing a vendor-specific failure into the shared failure taxonomy (`interfaces.md` §7). Nothing beyond translation and normalization belongs inside this boundary.

## Alternatives Considered

**1. Direct vendor SDK usage inside Pipeline Stages, with no abstraction layer.**
- Advantages: less code overall — no separate interface and implementation to define and maintain; faster initial development.
- Disadvantages: a vendor SDK's response object would leak directly into domain-model-typed pipeline code, violating `domain_models.md` §16 ("Provider Leakage"); swapping a provider (the resolution of ADR-003/004/005, once made) would require changing every Pipeline Stage that touches it, not one isolated Implementation; unit-testing a stage would require either a live vendor connection or ad hoc, per-stage mocking of that vendor's own SDK surface, with no shared, reusable contract to test against.
- Why rejected: directly contradicts `requirements.md` NFR-EXT-001–003 (provider swap without touching pipeline logic) and `domain_models.md`'s Provider Independence principle; this is not a close call.

**2. A single, informally-combined "provider adapter" per vendor category, without a formally separated Interface and Implementation.**
- Advantages: fewer conceptual layers to introduce and document than a fully separated Interface/Implementation split.
- Disadvantages: without an explicit, named interface contract, nothing structurally prevents a future change from silently adding a vendor-specific parameter or return shape that leaks past the intended boundary; Contract Testing (`testing.md` §6) becomes harder to define crisply, since there is no single, stable, implementation-independent contract to validate a candidate against.
- Why rejected: `architecture.md` §3.0 documents this exact simplification as a defect found and corrected in an earlier draft of the architecture — collapsing the interface/implementation distinction was found, on review, to obscure the Dependency Inversion Principle the whole boundary depends on for its guarantees to actually hold.

**3. A generic third-party dependency-injection or plugin-management framework to handle provider substitution.**
- Advantages: some off-the-shelf tooling exists for registering and swapping implementations at runtime.
- Disadvantages: introduces a new external dependency to solve a problem this system's own narrow, three-interface surface does not require generic tooling to solve; adds an abstraction layer on top of an abstraction layer, requiring a reader to learn the plugin framework's own concepts in addition to the Provider Interface concept already defined here.
- Why rejected: `architecture.md` §14's Abstraction vs. Simplicity trade-off explicitly favors abstracting only at genuine external boundaries and avoiding indirection introduced for its own sake; three well-defined swap points do not warrant a general-purpose plugin architecture.

## Consequences

**Positive:** provider replacement (once ADR-003/004/005 resolve) requires changing exactly one Provider Implementation, never a Pipeline Stage or Orchestrator; Contract Testing (`testing.md` §6) can validate any candidate implementation against one fixed, stable contract; cloud portability (`requirements.md` C-007) is achieved structurally, not merely by policy statement.

**Negative:** requires writing and maintaining an explicit interface definition in addition to each implementation — more upfront structure than calling a vendor SDK directly from within a stage.

**Trade-offs:** a small, deliberate amount of translation-layer code (vendor-native response → domain model) is concentrated at the Provider Implementation boundary, in exchange for eliminating vendor coupling everywhere else in the system.

**Operational impact:** a provider outage or vendor API change is contained to one Provider Implementation's failure-handling logic (`interfaces.md` §7; `sequence_diagrams.md` §5.1) — its blast radius never extends into Pipeline Stage or Orchestrator behavior.

**Testing impact:** enables Contract Testing (`testing.md` §6) as its own reusable, first-class test category, and lets every Pipeline Stage's Unit tests (`testing.md` §5) run against a stubbed Provider Interface with zero live dependency, per `domain_models.md` §2's Testability principle.

**Future evolution:** this boundary is expected to remain stable indefinitely — the interface count (three) is fixed by `architecture.md` §4's current scope, and no upstream document anticipates adding a fourth provider category without a prior architecture revision.

## Impacted Specifications

`requirements.md` (C-003, NFR-EXT-001–003, C-007), `architecture.md` (§3.0, §4, §11), `interfaces.md` (§2.1, §5), `domain_models.md` (§2, §16), `sequence_diagrams.md` (§2.2, §8.1), `testing.md` (§6), `tasks.md` (T-PROV-01–06).

## Cross-Document Validation

Checked against every specification in the SDD suite. No contradiction found. One point of historical note, not a current inconsistency: `architecture.md` v1.0's original layered diagram depicted Provider Abstraction as a single, undifferentiated layer; this was corrected to the explicit Provider Interface/Provider Implementation split documented here in `architecture.md` v1.2 §3.0. This ADR reflects, and is fully consistent with, the corrected current version — every downstream document (`interfaces.md`, `domain_models.md`, `sequence_diagrams.md`, `testing.md`, `deployment.md`) already assumes the corrected split, not the earlier simplified version.

## Implementation Guidance

Define each Provider Interface (Embedding, Vector Store, LLM) purely in terms of domain models and plain scalars (`interfaces.md` §5) — never a vendor-specific type. Implement each Provider Implementation as the sole location permitted to import that provider's vendor SDK, responsible only for translation and failure normalization, never business logic. Verify via Contract Testing (`testing.md` §6) that no implementation's output ever contains a vendor-native object, and that every simulated vendor failure normalizes to the shared taxonomy (`interfaces.md` §7).

## Future Revisions

Revisit only if a fourth external dependency category is introduced that does not fit within the existing three-interface model (a genuinely new kind of capability, not merely a new vendor within an existing category, which ADR-003/004/005 already handle without requiring a change here). Such an addition would itself require an `architecture.md` revision before a corresponding ADR here would be meaningful.
