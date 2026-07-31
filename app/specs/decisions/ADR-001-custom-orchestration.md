# ADR-001: Custom Orchestration Over an Orchestration Framework

## Status

Accepted

## Date

2026-07-29

## Context

The system requires control-flow logic that sequences pipeline stages — deciding what runs next, how a stage's output feeds the next stage's input, and how a short-circuit (an empty retrieval, an LLM decline) is routed to a terminal response rather than continuing the sequence. This is a distinct architectural concern from the stages themselves.

`requirements.md` Constraints C-001 and C-002 already mandate that this sequencing logic be custom-built and that no RAG/LLM orchestration framework be used anywhere in the system. `architecture.md` §1 (Principle 1) and §14 ("Architecture Trade-offs — Custom Orchestration") record this as a deliberate architectural decision, not an omission, with reasons already stated: understanding RAG internals directly, maintaining execution control over the system's grounding and citation guarantees, and interview/audit explainability. `rag_design.md` §1 states the same principle as the foundation the entire pipeline design builds on. `interfaces.md` §3 formalizes the resulting Orchestrator Responsibility Boundary (sequencing only, never business logic) as a contract, and `sequence_diagrams.md` §8.2 demonstrates that boundary holds across every runtime flow.

A decision is necessary here because "how should stages be sequenced" is answerable in more than one architecturally valid way — a framework-provided chain abstraction is a common, real alternative in the RAG space — and this document exists to record why that alternative was not taken, with enough detail that the decision is defensible on its own terms, not merely inherited by citation.

## Decision

The system uses custom-built orchestration logic — a Query Orchestrator and an Ingestion Orchestrator (`interfaces.md` §3.1–3.2) — to sequence pipeline stages. No RAG/LLM orchestration framework (LangChain, LlamaIndex, or functional equivalent) is used anywhere in the system, for orchestration or for any other purpose.

**Architectural boundary:** an Orchestrator's responsibility is limited to invoking stages in the sequence `sequence_diagrams.md` already specifies, propagating each stage's reported outcome to the next, coordinating retry-eligibility decisions (never retry execution itself — that belongs to the Provider Implementation, see ADR-002), and routing to a terminal outcome (a cited `Response`, a declined `Response`, or a normalized failure) based on values already reported to it. This exact allowed/forbidden boundary is enumerated in `testing.md` §7.

**Intentionally not included:** no framework-managed "chain" object, no framework-native domain objects (a framework's own document, message, or memory abstraction), no framework-specific prompt-templating syntax, and no framework-mediated retrieval or memory abstraction. Every domain concept the orchestrators pass between stages is defined once, in `domain_models.md`, independent of any framework's naming or shape.

## Alternatives Considered

**1. LangChain (or an equivalent general-purpose RAG orchestration framework).**
- Advantages: faster initial development via pre-built chain abstractions; a large ecosystem of pre-built integrations; less orchestration code to write for common patterns.
- Disadvantages: control flow is partially hidden inside framework internals, reducing transparency and audit/interview explainability; framework version upgrades can silently change chain behavior underneath the application; framework-native objects risk leaking framework-specific concepts into what this system requires to be provider-independent domain models; enforcing this system's specific Runtime Invariants (`domain_models.md` §19) is harder when generation is mediated by an abstraction not designed around them.
- Why rejected: `requirements.md` C-001 explicitly excludes it as an architectural constraint, and `architecture.md` §14 documents the trade-off as deliberate — transparency and control were prioritized over development velocity for this specific layer.

**2. LlamaIndex (or a similar retrieval/indexing-focused framework).**
- Advantages: purpose-built retrieval and indexing abstractions; potentially less orchestration code than a general-purpose chain framework.
- Disadvantages: the same core objection as LangChain applies — indexing and retrieval logic is partially hidden inside framework internals; framework-native chunk/node objects would still require translation into this system's own domain models to satisfy `domain_models.md`'s provider-independence discipline, reducing the framework's claimed benefit; this system's citation-traceability guarantees (`domain_models.md` §9) would need independent re-verification against a framework not designed around them.
- Why rejected: `requirements.md` C-001/C-002's custom-orchestration mandate is framework-agnostic — it excludes any RAG orchestration framework, not LangChain specifically.

**3. A minimal internal workflow/state-machine library (a generic, non-RAG-specific orchestration helper).**
- Advantages: could reduce boilerplate for sequencing and retry-coordination logic without introducing RAG-specific abstractions or framework-native domain objects.
- Disadvantages: still introduces an external dependency whose abstractions and upgrade cadence sit outside this system's control; the actual sequencing surface this system needs (`interfaces.md` §3's Orchestrator Responsibility Boundary) is narrow enough that a generic library would add indirection without meaningfully reducing implementation effort.
- Why rejected: `architecture.md` §14's Abstraction vs. Simplicity trade-off explicitly favors abstracting only at genuine external boundaries (the three Provider Interfaces, see ADR-002) — a generic orchestration library is not one of those boundaries, and the orchestrators required are already deliberately thin.

No strawman alternative is included above — each of the three was evaluated on its actual merits and rejected for a specific, cited architectural reason, not dismissed by construction.

## Consequences

**Positive:** full transparency and control over sequencing logic (`architecture.md` §14); no hidden framework behavior to audit or explain; every Runtime Invariant (`domain_models.md` §19) is directly enforceable and testable (`testing.md` §7, §9) without working around framework internals; strong interview/explainability value, since every pipeline step can be described in this system's own vocabulary end to end.

**Negative:** more orchestration-layer code to write and maintain than a framework would otherwise supply; the team bears full responsibility for the correctness of retry-coordination and error-propagation logic (`interfaces.md` §7) rather than inheriting it from a framework's tested implementation.

**Trade-offs:** orchestration-layer development velocity is traded for architectural transparency, testability against this system's own invariants, and independence from a framework's release cycle and internal behavior changes.

**Operational impact:** no framework-version upgrade risk affects orchestration behavior; orchestration logic changes only when this system's own specification changes (`tasks.md` T-ING-08, T-QRY-10), never as a side effect of an unrelated dependency update.

**Testing impact:** enables Component Testing (`testing.md` §7) as a distinct category that directly asserts Orchestrator behavior against a fixed allowed/forbidden action list — this would be substantially harder to test with the same rigor if sequencing were mediated by a framework's internal chain semantics.

**Future evolution:** if a future capability (Phase 4 Agentic Extension, `rag_design.md` §10) requires materially more complex orchestration — dynamic planning or multi-step autonomous decision-making, as distinct from fixed sequencing and routing — this ADR should be revisited rather than silently extended to cover a fundamentally different problem.

## Impacted Specifications

`requirements.md` (C-001, C-002), `rag_design.md` (§1), `architecture.md` (§1, §3, §14), `interfaces.md` (§3), `domain_models.md` (§19, Runtime Invariant 5), `sequence_diagrams.md` (§8.2), `testing.md` (§7), `tasks.md` (T-ING-08, T-QRY-10).

## Cross-Document Validation

Checked against every specification in the SDD suite. No contradiction found. Every upstream document, from `requirements.md`'s original constraint through `tasks.md`'s implementation tasks, consistently treats custom orchestration as an already-settled decision — none of them present it as open or propose an alternative anywhere in their own text. This ADR formalizes an existing, internally consistent decision; it does not introduce a new one.

**Note on scope:** this decision governs orchestration *of the pipeline*. It does not govern, and should not be read as prohibiting, the use of libraries at the three permitted Provider Interface boundaries (embedding, vector storage, LLM access) — see ADR-002 for that separate, narrower boundary.

## Implementation Guidance

Implement the Query Orchestrator and Ingestion Orchestrator as the only components responsible for stage sequencing (`interfaces.md` §3.1–3.2). Limit each orchestrator's logic strictly to the allowed actions `testing.md` §7 enumerates (invoke, propagate outcomes, coordinate retry-eligibility, stop execution, route success/failure) and verify the absence of every forbidden action (transform domain data, interpret embeddings, perform retrieval, construct prompts, derive citations) via the Component Testing approach already specified there. No RAG orchestration framework, chain abstraction, or framework-native domain object should appear anywhere in orchestrator or pipeline-stage code.

## Future Revisions

Revisit this ADR if either condition arises: (a) Phase 4 Agentic Extension (`rag_design.md` §10) is formally scoped and requires control flow materially beyond fixed sequencing and outcome-based routing, or (b) the custom orchestration logic's ongoing maintenance burden is found, in practice and with evidence, to outweigh the transparency and control benefits recorded above. Neither condition currently holds.
