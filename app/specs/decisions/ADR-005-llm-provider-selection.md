# ADR-005: LLM Provider Selection

## Status

Proposed — **not Accepted**. The technology decision remains intentionally open.

## Date

2026-07-29

## Context

The system requires an LLM to generate grounded answers from an assembled prompt (`requirements.md` FR-1101–1106). `interfaces.md` §5.3 already defines the LLM Provider Interface contract a candidate must satisfy, including configurable generation parameters and normalized failure handling. `domain_models.md` §8 establishes that `GeneratedResponse` represents a completed response regardless of transport, with streaming explicitly left as a future capability (Open Decision 5, carried through `testing.md` §21 and `sequence_diagrams.md` §15) — a decision distinct from, though related to, provider selection. `architecture.md` §17 lists LLM provider selection as ADR-005, explicitly unresolved.

A decision is necessary eventually because generation cannot be validated against a real model without one — but, per ADR-002's abstraction boundary, this decision is deferrable in the same way ADR-003's and ADR-004's are.

## Decision

**This ADR does not select an LLM provider.** It defines the evaluation criteria a future decision must be judged against.

**Needs this decision must satisfy:**

- **Provider independence** — the selection must be fully substitutable behind the LLM Provider Interface (`interfaces.md` §5.3) without any Pipeline Stage or Orchestrator change, per `requirements.md` NFR-EXT-003.
- **Streaming readiness** — the MVP reference path is blocking generation (`domain_models.md` §8), but the selected provider's API should not structurally preclude adding streaming support later; `interfaces.md` §5.3 already supports both modes at the contract level, and the eventual candidate should be checked against that, not merely assumed compatible.
- **Prompt portability** — the versioned prompt template (`interfaces.md` 4.13) must be renderable in a form the selected provider accepts without provider-specific prompt syntax leaking into the Prompt Assembler stage itself — the same "no framework/vendor leakage" discipline `domain_models.md` §16 states generally, applied here specifically to provider-specific prompt conventions.
- **Token accounting** — the provider must expose token usage on every completion, required for `GeneratedResponse`'s recorded usage (`domain_models.md` §8) and every Cost metric this suite defines (`evaluation/metrics_dictionary.md` §11).
- **Error normalization** — the provider's failure modes (rate-limiting, timeout, refusal, transient error) must be mappable to the shared failure taxonomy (`interfaces.md` §7) without an impedance mismatch that would let a vendor-specific error type leak past the Provider Implementation boundary established in ADR-002.
- **Provider abstraction fit for the grounding-decline signal** — the provider's API must expose a distinguishable finish reason (or equivalent signal) so a completion that declines due to insufficient context can be recognized as a Business Outcome, not a Technical Failure, per `sequence_diagrams.md` §3.3 and §10's explicit classification requirement.

**Candidate categories considered for future evaluation** (named for completeness of the eventual decision space, **not compared, scored, or recommended here**): hosted commercial APIs, local/self-hosted models, and enterprise-contracted providers (dedicated capacity or private deployment arrangements).

## Alternatives Considered

*(Framed as alternative decision-making approaches, consistent with this ADR not selecting a specific LLM provider itself.)*

**1. Select a hosted commercial API now, for the fastest path to a working end-to-end MVP.**
- Advantages: fastest route to a functioning system; minimal operational setup required.
- Disadvantages: per-call cost and rate limits apply from day one; a choice made under time pressure risks not holding up once the full evaluation criteria above — particularly error normalization and grounding-decline signal fidelity — are checked against it.
- Why rejected: `interfaces.md` §5.3's contract is already fully implementable against a stub — there is no architectural blocker forcing an early real-provider choice, so the same evidence-based-deferral logic as ADR-003 and ADR-004 applies here too.

**2. Select a self-hosted/local model now, to avoid any external LLM dependency entirely.**
- Advantages: no per-call API cost; full control over model version and availability.
- Disadvantages: shifts significant infrastructure and operational burden (compute provisioning, model serving, scaling) onto this system directly — a real cost this ADR does not yet have sufficient evidence to weigh fairly against a hosted option; excluding hosted options prematurely is not evidence-based.
- Why rejected: the same premature-category-exclusion objection raised in ADR-004 applies equally here.

**3. Commit to an enterprise-contracted provider immediately, assuming procurement or compliance requirements will favor it regardless of technical evaluation.**
- Advantages: may pre-resolve procurement or compliance concerns earlier in the project.
- Disadvantages: procurement and compliance considerations are legitimate inputs to the eventual choice, but are not, on their own, sufficient justification to skip the technical evaluation criteria above — particularly error normalization and grounding-decline signal fidelity, which are architecture-level concerns a procurement decision cannot resolve on its own.
- Why rejected: this ADR is a technical architecture decision; non-technical inputs inform but do not substitute for the evaluation criteria this document defines.

## Consequences

**Positive:** implementation of the LLM Provider Interface (`interfaces.md` §5.3) and every dependent stage — Response Generator, Citation Mapper, and Query Analyzer if its eventual mechanism is LLM-assisted — can proceed against a stub immediately.

**Negative:** end-to-end generation quality, grounding-decline behavior, and Evaluation Testing (`testing.md` §10–§11, `evaluation/benchmark_spec.md`) cannot be validated against a real provider until this decision resolves.

**Trade-offs:** the same evidence-based-deferral trade-off documented in ADR-003 and ADR-004.

**Operational impact:** none yet.

**Testing impact:** Contract Testing (`testing.md` §6.3) can proceed against a stub regardless of this ADR's status; once a candidate is evaluated, its specific grounding-decline finish-reason mapping should be validated as part of Contract Testing, since this is the one criterion above most likely to vary meaningfully between providers.

**Future evolution:** once resolved, update this ADR to Accepted with the selected provider, the evaluation results, and specifically how its API's finish-reason/grounding-decline signal was validated against `sequence_diagrams.md` §3.3's requirement.

## Impacted Specifications

`requirements.md` (FR-1101–1106, NFR-EXT-003, NFR-COST-001), `architecture.md` (§4, §17 ADR-005), `interfaces.md` (§5.3), `domain_models.md` (§8, Open Decision 5), `sequence_diagrams.md` (§3.1, §3.3, §15 item 5), `testing.md` (§6.3, §21 item 5), `tasks.md` (T-PROV-06, §9).

## Cross-Document Validation

Checked against every specification in the SDD suite. No contradiction found. Consistent with `architecture.md` §17, `testing.md` §21, and `tasks.md` §9's treatment of this decision as open. **One related-but-distinct point worth stating explicitly rather than conflating:** streaming support (`domain_models.md` Open Decision 5) is a separate open decision from provider selection — resolving this ADR does not resolve that one, and this ADR does not attempt to.

## Implementation Guidance

Implement the LLM Provider Interface (`interfaces.md` §5.3) and validate every dependent stage against a stubbed implementation, including both the grounded-completion path and the insufficient-context-finish-reason path (`sequence_diagrams.md` §3.1, §3.3). Do not implement the concrete Provider Implementation until this ADR is updated to Accepted.

## Future Revisions

Revisit once the evaluation criteria above can be applied to real candidates. This ADR's eventual resolution should also inform — but does not by itself resolve — the separate streaming-semantics open decision (`domain_models.md` Open Decision 5). When resolved, update this ADR's Status to Accepted; do not open a new ADR number for the same decision.
