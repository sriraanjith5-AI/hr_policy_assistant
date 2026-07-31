# ADR-004: Embedding Model Selection

## Status

Proposed — **not Accepted**. The technology decision remains intentionally open.

## Date

2026-07-29

## Context

The system requires an embedding model to convert both document chunks (at ingestion time) and queries (at retrieval time) into comparable vectors (`requirements.md` FR-601–606). `domain_models.md` §5 requires every `Embedding` to carry a model/version identifier as a first-class fact — not an incidental detail — specifically because two embeddings produced by different models or versions are not comparable and must not be silently treated as if they were (`rag_design.md` Risk R-003). `interfaces.md` §5.1 already defines the Embedding Provider Interface contract a candidate must satisfy, and `requirements.md` FR-606 already requires re-embedding support when the configured model changes. `architecture.md` §17 lists embedding model selection as ADR-004, explicitly unresolved.

A decision is necessary eventually because ingestion and retrieval cannot produce real, meaningful vectors without a concrete model — but, per ADR-002's abstraction boundary, this decision is safely deferrable in the same way ADR-003's is.

## Decision

**This ADR does not select an embedding model or provider.** It defines the evaluation criteria a future decision must be judged against.

**Needs this decision must satisfy:**

- **Embedding consistency** — a single configured model/version must produce comparable vectors for both chunks (ingestion-time) and queries (retrieval-time); `interfaces.md` §5.1 already requires this at the contract level, and the selection must satisfy it in practice.
- **Version tracking** — the selected model/provider must expose a stable, retrievable model/version identifier that can be recorded on every `Embedding` (`domain_models.md` §5); an opaque or unversioned model choice would violate this requirement structurally, not merely operationally.
- **Re-embedding support** — must be feasible to re-embed the full corpus, or incrementally, when the model/version changes (`requirements.md` FR-606), without requiring an architecture change to support it.
- **Reproducibility** — embeddings for the same input should be stable and reproducible enough that Evaluation Testing (`testing.md` §10, `evaluation/benchmark_spec.md`) results remain meaningful across repeated runs, consistent with `evaluation/metrics_dictionary.md` §2's reproducibility principle.

**Candidate categories considered for future evaluation** (named for completeness of the eventual decision space, **not compared, scored, or recommended here**): open-source embedding models (self-hosted), hosted embedding APIs, and — as a dimension cutting across either category — small vs. large embedding models (a dimensionality/cost/quality trade-off, not itself a category of provider).

## Alternatives Considered

*(Framed as alternative decision-making approaches, consistent with this ADR not selecting a specific embedding model itself.)*

**1. Select an embedding model now, defaulting to whichever provider is eventually selected for the LLM (ADR-005), for operational simplicity.**
- Advantages: potentially simpler credential and vendor management if both capabilities come from the same provider.
- Disadvantages: conflates two independent decisions — embedding quality and dimensionality needs are not the same as generation quality needs, and `requirements.md` NFR-EXT-001–003 treats them as independently swappable for a reason; bundling them removes future flexibility to swap one without the other.
- Why rejected: the Provider Interface abstraction (ADR-002) already keeps these decisions architecturally independent; collapsing them for short-term convenience would work directly against that design intent.

**2. Select an open-source, self-hosted embedding model exclusively, to avoid per-call API cost entirely.**
- Advantages: potentially lower marginal cost at scale; no external API dependency for this specific capability.
- Disadvantages: shifts real operational burden (hosting, scaling, maintaining the model) onto this system's own infrastructure — a cost this ADR does not yet have enough evidence to weigh fairly against a hosted API's per-call cost; excluding hosted options before evaluation is not evidence-based.
- Why rejected: the evaluation criteria above have not yet been applied to real candidates in either category; ruling out a whole category prematurely biases the eventual decision rather than informing it.

**3. Select a hosted embedding API exclusively, for operational simplicity.**
- Advantages: lower initial operational burden; managed scaling with no infrastructure to maintain directly.
- Disadvantages: ongoing per-call cost (`requirements.md` NFR-COST-003) and a dependency on that provider's availability, mitigated but not eliminated by `interfaces.md` §7's normalized failure handling; the same premature-exclusion objection as alternative 2 applies in the opposite direction.
- Why rejected: same reasoning as alternative 2 — excluding an entire category before evaluation is not evidence-based.

## Consequences

**Positive:** implementation of the Embedding Provider Interface (`interfaces.md` §5.1) and every dependent stage — Embedding Generator and Retriever — can proceed against a stub immediately; the eventual decision will be made with real evaluation data rather than under implementation time pressure.

**Negative:** end-to-end retrieval quality and Evaluation Testing (`testing.md` §10, `evaluation/benchmark_spec.md`) cannot be validated against real embedding quality until this decision resolves.

**Trade-offs:** the same evidence-based-deferral trade-off documented in ADR-003 — earlier real-quality validation is traded for a better-evidenced final choice.

**Operational impact:** none yet.

**Testing impact:** Contract Testing (`testing.md` §6.1) can proceed against a stub regardless of this ADR's status.

**Future evolution:** once resolved, update this ADR to Accepted with the selected model/provider and the evaluation results against the criteria above.

## Impacted Specifications

`requirements.md` (FR-601–606, NFR-COST-001, NFR-COST-003, NFR-EXT-001), `architecture.md` (§4, §17 ADR-004), `interfaces.md` (§5.1), `domain_models.md` (§5, Risk R-003 reference), `rag_design.md` (Risk R-003), `testing.md` (§6.1), `tasks.md` (T-PROV-04, §9).

## Cross-Document Validation

Checked against every specification in the SDD suite. No contradiction found. Consistent with `architecture.md` §17 and `tasks.md` §9's treatment of this decision as open — no upstream document names or assumes a specific embedding model anywhere in its own text.

## Implementation Guidance

Implement the Embedding Provider Interface (`interfaces.md` §5.1) and validate every dependent stage against a stubbed implementation. Do not implement the concrete Provider Implementation until this ADR is updated to Accepted.

## Future Revisions

Revisit once the evaluation criteria above can be applied to real candidates — ideally informed by early Evaluation Testing runs (`testing.md` §10) against a provisional candidate, without treating that provisional choice as final until this ADR is formally updated. When resolved, update this ADR's Status to Accepted; do not open a new ADR number for the same decision.
