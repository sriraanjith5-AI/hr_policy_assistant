# ADR-003: Vector Database Selection

## Status

Proposed — **not Accepted**. The technology decision remains intentionally open.

## Date

2026-07-29

## Context

The system requires a vector database to store chunk text, metadata, and embeddings, and to serve similarity search (`requirements.md` FR-701–705, FR-801–806). `requirements.md` NFR-EXT-002 requires that this provider be replaceable without touching pipeline logic, and C-007 requires cloud portability. `architecture.md` §4 and `interfaces.md` §5.2 already define the Vector Store Provider Interface a candidate technology must satisfy, independent of which vendor or technology is eventually chosen. `architecture.md` §17 lists vector database selection as ADR-003, explicitly unresolved as of that document's approval.

A decision is necessary eventually because the system cannot serve real retrieval traffic without a concrete vector database behind the interface — but per ADR-002, the interface abstraction already makes this decision safely deferrable: every other component can be built, tested, and validated against a stubbed implementation while this selection remains open (`tasks.md` §9).

## Decision

**This ADR does not select a vector database.** It defines the evaluation criteria a future decision must be judged against, and confirms that implementation of every other component may proceed against the Vector Store Provider Interface (`interfaces.md` §5.2) while this selection remains open.

**Evaluation criteria** (stated without weighting or scoring any candidate against them here):

- **Persistence** — durability and backup/recovery characteristics. Relevant to `deployment.md` §13's Document Store/Vector Index derivation principle: because the Vector Index is a derived, re-indexable artifact, a candidate with comparatively weaker native persistence guarantees is more tolerable than it would be for a true source of truth — this is a factor to weigh, not a decision this document makes.
- **Metadata filtering** — must support metadata-predicate filtering as an optional parameter on the same similarity-search call, not a separate code path, per `rag_design.md` §6.2 and `interfaces.md` §5.2.
- **Scalability** — must support the knowledge-base size and concurrent-query targets in `requirements.md` NFR-SCALE-001–003, and fit the independent-scaling deployment story in `deployment.md` §11.
- **Embedding dimensions** — must support whatever vector dimensionality the eventual embedding model (ADR-004) produces, without an artificial ceiling forcing a mismatch.
- **Operational complexity** — self-hosted vs. managed-service operational burden, relevant to `deployment.md` §9 (Operational Readiness) and §13 (Backup and Recovery).
- **Cost** — both storage cost and query-volume cost structure, relevant to `requirements.md` NFR-COST-001–005.
- **Testing** — must be feasible to sandbox or credibly stub, so Contract Testing (`testing.md` §6.2) does not require a live instance for every test tier.
- **Future portability** — must not create a dependency that would violate `requirements.md` C-007's cloud-portability constraint.

**Candidate categories considered for future evaluation** (named for completeness of the eventual decision space, **not compared, scored, or recommended here**): Chroma, FAISS, Qdrant, Pinecone, Weaviate, Milvus.

## Alternatives Considered

*(Framed as alternative decision-making approaches, consistent with this ADR not selecting a specific vector database itself.)*

**1. Select a vector database now, based on the team's current familiarity.**
- Advantages: removes this open decision immediately; avoids any appearance of indecision in the specification suite.
- Disadvantages: a decision made on familiarity rather than the evaluation criteria above risks being re-litigated once real scale, cost, and persistence requirements are better understood; the architecture does not structurally require this decision early, since `interfaces.md` §5.2 already fully specifies the contract independent of it.
- Why rejected: the Provider Interface abstraction (ADR-002) exists specifically to make this decision safely deferrable — deferring it is the architecturally consistent choice here, not a gap to be closed prematurely.

**2. Select two candidates now and build a dual implementation to compare them empirically before finalizing.**
- Advantages: produces real, empirical comparison data ahead of commitment.
- Disadvantages: doubles the Provider Implementation effort for a decision that can be made with a single implementation once criteria-based evaluation is complete; Contract Testing (`testing.md` §6) already provides a mechanism to swap and compare implementations later without needing two production-grade builds in parallel now.
- Why rejected: disproportionate effort for a decision the existing interface boundary already de-risks.

**3. Adopt a database-agnostic query abstraction library that itself supports multiple vector database backends, deferring the underlying choice to that library.**
- Advantages: superficially appears to defer the decision further, with less apparent commitment to any one technology.
- Disadvantages: introduces a new external dependency — the abstraction library itself — that this system's own Vector Store Provider Interface (`interfaces.md` §5.2) already renders unnecessary; it would be an abstraction layer stacked on top of an abstraction layer, contradicting `architecture.md` §14's Abstraction vs. Simplicity principle.
- Why rejected: redundant with an abstraction boundary the architecture already provides at no additional dependency cost.

## Consequences

**Positive:** implementation of every Pipeline Stage, both Orchestrators, and every other Provider Interface can proceed immediately and completely independent of this decision (`tasks.md` §4, §9); the eventual decision will be evidence-based against the criteria above, not made under implementation time pressure.

**Negative:** retrieval cannot be validated end-to-end against a real vector database until this decision resolves; Contract Testing (`testing.md` §6.2) can validate the interface contract against a stub, but not final real-world persistence or scale characteristics, until a candidate is selected.

**Trade-offs:** deferring this decision trades earlier end-to-end validation for a better-evidenced final choice.

**Operational impact:** none yet — no operational commitment has been made in any environment.

**Testing impact:** `testing.md` §6.2's Contract Testing should and can proceed against a stub/sandboxed implementation regardless of when this ADR resolves.

**Future evolution:** once resolved, this ADR will be updated to Accepted status with the selected candidate, the evaluation results against the criteria above, and the specific trade-offs accepted — not superseded by a new ADR number.

## Impacted Specifications

`requirements.md` (NFR-EXT-002, NFR-SCALE-001–003, NFR-COST-001–005, C-007), `architecture.md` (§4, §17 ADR-003), `interfaces.md` (§5.2), `domain_models.md` (§7 `SearchResult`, §16 Provider Leakage), `deployment.md` (§9, §11, §13, §17), `tasks.md` (T-PROV-05, T-APP-06, T-APP-07, §9).

## Cross-Document Validation

Checked against every specification in the SDD suite. No contradiction found. Every upstream document that references this decision (`architecture.md` §17, `deployment.md` §19, `tasks.md` §9) consistently treats it as open, and none of them prematurely assumes a specific vector database anywhere in their own text — including in example diagrams, which uniformly use the generic label "Vector Database" rather than naming a product.

## Implementation Guidance

Implement the Vector Store Provider Interface (`interfaces.md` §5.2) and validate every dependent Pipeline Stage against a stubbed or sandboxed implementation. Do not implement the concrete Provider Implementation until this ADR is updated to Accepted.

## Future Revisions

Revisit as soon as the evaluation criteria above can be applied to real candidates with real data — reasonably, once Phase 1 (`rag_design.md` §10) is far enough along to exercise realistic scale and query patterns. When resolved, update this ADR's Status to Accepted and add the selected candidate, evaluation results, and accepted trade-offs; do not open a new ADR number for the same decision.
