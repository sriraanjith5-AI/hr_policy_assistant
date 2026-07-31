# Testing Strategy Specification

## Enterprise HR Policy Assistant — Engineering Testing Strategy

| Field | Value |
|---|---|
| Document Type | Testing Strategy Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| Purpose | Define the authoritative engineering testing strategy that demonstrates how the implementation will be validated against every upstream specification — not a QA checklist, but the mechanism by which "the system does what the spec says" becomes a checkable, ongoing claim. |
| Scope | Every Functional Requirement, Non-Functional Requirement, Runtime Invariant, Interface Contract, Domain Model, and Sequence Diagram already approved in this SDD chain. This document defines *how* each is validated; it does not redefine *what* any of them require. |
| Intended Audience | AI/ML Engineers and Backend Engineers implementing the system; QA Engineers deriving concrete test suites; Engineering Managers assessing readiness; Solution Architects auditing specification-to-implementation traceability. |
| Related Specifications | [requirements.md](./requirements.md) (SRS v1.0), [rag_design.md](./rag_design.md) (v1.1), [architecture.md](./architecture.md) (SAD v1.2), [interfaces.md](./interfaces.md) (v1.1), [domain_models.md](./domain_models.md) (v1.3), [sequence_diagrams.md](./sequence_diagrams.md) (v1.1) |
| Downstream Documents (not yet created) | `deployment.md`, `tasks.md`, `app/specs/evaluation/benchmark_spec.md` |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## 1. Document Control

`testing.md` is the seventh document in the Specification-Driven Development (SDD) chain:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
```

**This is not merely a QA document.** Every prior document in this chain made a claim about the system — a requirement, a contract, an invariant, a sequence. This document is where each of those claims becomes something that can actually be checked. A specification chain that stops at `sequence_diagrams.md` describes an intended system; this document is what turns "intended" into "verifiable."

**Core rule governing every section below: no test category exists without a specification reference, and no significant requirement exists without at least one planned validation.** Where a gap is found in either direction during this document's own construction, it is documented as an open decision (§21) rather than silently left implicit.

**Technology independence is a hard constraint, not a style preference.** This document names no testing framework, no assertion library, no CI product, and contains no code. The reasoning is architectural, not stylistic: `architecture.md` §11 and `interfaces.md` §2 both establish Provider Independence and Dependency Inversion as first-class design principles specifically so the *system* survives a provider or framework swap without a rewrite. A testing strategy that hard-codes a specific test framework's syntax would reintroduce exactly the coupling the rest of this SDD chain worked to avoid. Every test category defined here is described by *what it verifies and why*, not *which tool runs it* — see §19 for how this pays off when a provider or framework actually changes.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Testing Strategy Specification |

---

## 2. Testing Philosophy

**This system is unusually testable, and that testability was designed in, not added after the fact.** Every property below is a direct, load-bearing consequence of a decision already made in `architecture.md` or `interfaces.md` — this section explains *why* each one lowers the cost and raises the confidence of testing.

**Custom orchestration** (`architecture.md` §1, §14; `interfaces.md` §3) means the sequencing logic that decides "what happens next" is a small, inspectable, hand-written control flow — not a framework's internal chain semantics. A test can assert exact call order and exact short-circuit behavior (`sequence_diagrams.md` §3.2, §3.3) because the orchestration *is* the thing being tested, not a black box wrapping it.

**Stage isolation** (`interfaces.md` §4; `architecture.md` §11, "Single Responsibility") means every one of the fifteen numbered pipeline stages has exactly one responsibility and a contract expressed entirely in domain models. A stage can be unit-tested with hand-constructed inputs and no live dependency, because its contract never requires one (`interfaces.md` §9).

**Provider abstraction** (`interfaces.md` §5; `architecture.md` §4) means the only three points where a vendor SDK is ever touched are behind narrow interfaces. This is what makes Contract Testing (§6) possible as a distinct, reusable test category: a Provider Implementation is tested once against its interface's contract, and every stage that depends on that interface inherits the guarantee without needing its own provider-specific test.

**Dependency inversion** (`architecture.md` §3.0, §11) means every dependency in the system points at an interface, never a concrete implementation. This is the single property that makes substitution-based testing possible at every level: a stage's dependency can be satisfied by a test double with zero code changes to the stage itself.

**Deterministic domain models** (`domain_models.md` §2, "Testability") means every object exchanged between components — `TextChunk`, `SearchResult`, `QueryContext`, `Response` — is a plain value/entity with no hidden dependency on a live provider, a clock, or a database connection. A test can construct one by hand and know exactly what it represents, because `domain_models.md` already defines its meaning independent of any implementation.

**Runtime invariants** (`domain_models.md` §19; `sequence_diagrams.md` §13) turn "the system should behave correctly" into six specific, falsifiable claims. A testing strategy without them would have to rediscover what "correct" means at test-design time; this strategy inherits that definition already made.

**Why each stage can be validated independently:** because `interfaces.md` §2 (Dependency Inversion, Single Responsibility) and `architecture.md` §3 (the layered dependency direction) together guarantee that a stage's behavior is fully determined by its declared input and its declared dependencies — nothing else. If a stage's test needs anything not listed in its `interfaces.md` contract, that is itself a specification defect to raise, not a reason to write a broader test.

---

## 3. Testing Strategy

The complete testing pyramid for this system, layered from narrowest/cheapest to broadest/most expensive. Each level has a distinct objective; none substitutes for another.

| Level | Objective | Detailed In |
|---|---|---|
| **Unit Testing** | Validate one pipeline stage's transformation logic in isolation, against hand-constructed domain-model inputs. | §5 |
| **Contract Testing** | Validate that a Provider Implementation satisfies its Provider Interface's contract — input/output shape, failure normalization, model/version preservation — independent of which vendor sits behind it. | §6 |
| **Component Testing** | Validate that an Orchestrator correctly sequences its stages and correctly classifies/propagates outcomes, using stage test doubles rather than real stages. | §7 |
| **Integration Testing** | Validate a complete runtime flow, end to end, matching a specific `sequence_diagrams.md` diagram exactly. | §8 |
| **Evaluation Testing** | Validate RAG *quality* — retrieval relevance, answer faithfulness, citation correctness — against a labeled question set, not just structural correctness. | §10–§11 |
| **Resilience Testing** | Validate failure handling — provider outages, malformed input, retry behavior, batch isolation — under deliberately injected failure conditions. | §12 |
| **Performance Testing** | Validate latency, throughput, and scalability against the SRS's numeric NFR targets. | §13 |
| **Regression Testing** | Detect quality or behavioral degradation introduced by a configuration, prompt, chunking, embedding, or provider change. | §14 |
| **Acceptance Testing** | Validate that the delivered system satisfies the SRS's Functional and Non-Functional Requirements and the domain model's Runtime Invariants, as a formal sign-off gate. | §15 |

**Relationship between levels:** Unit and Contract tests are the foundation — fast, provider-independent, run on every change. Component tests sit just above them, validating orchestration logic against stage doubles. Integration tests compose real (or realistically stubbed) stages into the flows `sequence_diagrams.md` already specified. Evaluation, Resilience, and Performance tests are specialized integration-level concerns with their own cadence and infrastructure needs (§4). Regression testing is not a separate pyramid level so much as a *policy* for when the levels above are re-run (§14). Acceptance testing is the aggregation point — it does not introduce new test logic, it certifies that the levels below already cover every requirement (§15).

---

## 4. Test Environment Strategy

| Environment | Purpose | Provider Behavior |
|---|---|---|
| **Development** | Fast local iteration on a single stage or a small integration slice. | Stubbed Provider Interfaces by default (`interfaces.md` §9) — no live provider calls required to develop or unit-test a stage. |
| **CI** | Automated validation on every change, gating merge. | Unit, Contract (against stubbed or sandboxed providers), Component, and the fast subset of Integration tests run here. Evaluation, full Performance, and long-running Resilience tests are typically excluded from the fastest CI gate and run on a separate cadence (e.g., pre-merge-to-main or nightly) — this document does not mandate a specific pipeline topology, only that the split exists. |
| **Pre-production** | Realistic end-to-end validation against real (or realistic sandboxed) providers, at a scale close to production. | Real Provider Implementations, real (or a dedicated non-production instance of) External Infrastructure. This is where Evaluation Testing (§10–§11) and full Performance Testing (§13) run at meaningful scale. |
| **Production validation** | Confirm the deployed system continues to satisfy its contracts and quality bars post-deployment, without re-running the full suite against live traffic. | Synthetic canary queries against the golden question set (§10), observability validation (§17), and regression-triggered re-evaluation (§14) — not exploratory testing against real employee data. |

No cloud vendor, hosting platform, or specific CI product is named — that is a `deployment.md` concern, out of scope here.

**Isolated datasets:** every environment above except Production draws from the Test Data Strategy in §16, never from real HR policy content or real employee queries, to keep test outcomes reproducible and free of any real-data privacy concern.

**Deterministic fixtures:** wherever a test's expected outcome depends on retrieval or generation quality, the input is a fixed, versioned fixture (a specific `Document`, a specific labeled `Query`) — never a live, uncontrolled source — so a test failure is attributable to a code or configuration change, not to fixture drift.

**Repeatable execution:** Contract, Component, and Unit tests are fully deterministic by construction (`domain_models.md` §2, "Testability" — no live provider, no clock dependency). Integration and Evaluation tests that do call a real LLM inherit some non-determinism from the LLM itself (§18) — this is mitigated, not eliminated, by fixing every other variable (retrieval set, prompt template version, generation parameters) and evaluating against tolerance bands rather than exact-match assertions where LLM output is involved.

**Controlled provider behavior:** every Provider Interface's test double (§6, §9) can be configured to return a specific normalized failure category on demand (`interfaces.md` §7) — this is what makes Resilience Testing (§12) possible without depending on an actual provider outage occurring during a test run.

---

## 5. Unit Testing Strategy

One subsection per pipeline stage, per `interfaces.md` §4, plus the Not Found Path (a stage-equivalent responsibility, `rag_design.md` §5.10). Each table is read top-to-bottom as Purpose, Inputs, Outputs, Normal behaviour, Boundary cases, Failure cases, Expected domain models, Expected interface usage.

### 5.1 Document Loader

| | |
|---|---|
| Purpose | Validate a source PDF and assign document identity and provenance |
| Inputs | Document location/source (raw file or reference) |
| Outputs | `Document` (validated, ID + provenance) |
| Normal behaviour | Well-formed PDF within configured size limits, not encrypted → `Document` created with stable identity and provenance (FR-101, FR-103, FR-104, FR-109) |
| Boundary cases | File exactly at the configured size limit; minimum single-page PDF; re-ingestion of an already-known source (must resolve to the *same* `Document` identity, new version — FR-104, FR-105) |
| Failure cases | Malformed file (FR-107); file exceeds size limit (FR-108); encrypted/unreadable file (FR-206) — each a non-recoverable, per-document failure |
| Expected domain models | `Document` |
| Expected interface usage | `interfaces.md` 4.1 — no Provider Interface dependency |

### 5.2 PDF Parser

| | |
|---|---|
| Purpose | Extract page-ordered text, structural markers, and table content |
| Inputs | `Document` (validated) |
| Outputs | Extracted document content — per-page text, structure, fidelity indicator |
| Normal behaviour | Fully extractable document → full-fidelity text per page (FR-201–204) |
| Boundary cases | A document with one scanned (image) page among otherwise-extractable pages; a document with complex multi-column or table layout |
| Failure cases | A page that cannot be extracted at all → flagged reduced-fidelity/unparseable, **not** a hard failure (FR-205); the whole document unopenable → a true parse failure |
| Expected domain models | `ExtractedDocument` (raw facet) |
| Expected interface usage | `interfaces.md` 4.2 — PDF parsing library at the External Infrastructure boundary; stage's own contract is domain-shaped only |

### 5.3 Text Preprocessor

| | |
|---|---|
| Purpose | Normalize extracted text while preserving raw text and structural cues |
| Inputs | Extracted document content |
| Outputs | `ExtractedDocument` (normalized facet — same object as raw, per `domain_models.md` §3 merge) |
| Normal behaviour | Artifacts stripped, boilerplate deduplicated, encoding standardized (FR-301–304) |
| Boundary cases | A document consisting almost entirely of repeated boilerplate (e.g., a legal disclaimer on every page); non-standard character encoding |
| Failure cases | None expected to be non-recoverable at this stage — an unnormalizable encoding is a data-quality warning attached to the affected page, not a hard failure |
| Expected domain models | `ExtractedDocument` (finalized, both facets) |
| Expected interface usage | `interfaces.md` 4.3 — no Provider Interface dependency |

### 5.4 Semantic Chunker

| | |
|---|---|
| Purpose | Split normalized text into semantically bounded chunks |
| Inputs | `ExtractedDocument` + chunking configuration |
| Outputs | `TextChunk[]` (unenriched) |
| Normal behaviour | Chunks at or below the configured target size, respecting sentence boundaries, with configured overlap (FR-401–404) |
| Boundary cases | A semantic unit that exceeds the configured maximum size (must fall back to a hard split, `rag_design.md` §4.4); a document short enough to produce exactly one chunk |
| Failure cases | Malformed or empty input from the prior stage — no failure mode intrinsic to chunking itself given valid input |
| Expected domain models | `TextChunk[]` |
| Expected interface usage | `interfaces.md` 4.4 — no Provider Interface dependency; deterministic, fully unit-testable with no live call (`domain_models.md` §2) |

### 5.5 Metadata Extractor

| | |
|---|---|
| Purpose | Attach structural and policy-domain metadata to each chunk |
| Inputs | `TextChunk[]` + document-level provenance + extraction fidelity flags |
| Outputs | `TextChunk[]` + `ChunkMetadata` |
| Normal behaviour | Page, section, and policy-domain fields populated where extractable (FR-501–503) |
| Boundary cases | A chunk spanning a section boundary; a document with no discernible policy category |
| Failure cases | None that block the pipeline — an unextractable field is represented as an explicit null (FR-503), never a stage failure |
| Expected domain models | `ChunkMetadata` (referencing, not duplicating, `DocumentMetadata`) |
| Expected interface usage | `interfaces.md` 4.5 — no Provider Interface dependency |

### 5.6 Embedding Generator

| | |
|---|---|
| Purpose | Produce a vector embedding for each chunk, recording model/version |
| Inputs | `TextChunk[]` + `ChunkMetadata` |
| Outputs | `Embedding` per chunk, attached |
| Normal behaviour | Batch embedding succeeds; model/version recorded on every `Embedding` (FR-601, FR-604, FR-603) |
| Boundary cases | A single-chunk batch; a maximum-size batch per configured batching limits |
| Failure cases | Embedding Provider failure (rate-limited, timeout, transient) — retried per policy; an unrecoverable per-chunk failure is reported without aborting the batch (FR-605) |
| Expected domain models | `Embedding` |
| Expected interface usage | `interfaces.md` 4.6 → Embedding Provider Interface (§6.1) |

### 5.7 Vector Indexer

| | |
|---|---|
| Purpose | Persist embedded chunks to the vector index; replace-on-re-ingestion |
| Inputs | `TextChunk[]` + `Embedding` |
| Outputs | Ingestion result summary |
| Normal behaviour | Successful upsert of a new document's chunks (FR-701, FR-702) |
| Boundary cases | Re-ingestion of an already-indexed `Document` — the prior version's chunks are atomically replaced, not duplicated (SRS FR-105/FR-702; `sequence_diagrams.md` §4.1's re-ingestion note) |
| Failure cases | Vector Store Provider unavailable or rejects an upsert — retried per policy; unrecoverable failure reported as this document's outcome without corrupting previously indexed documents (NFR-REL-005) |
| Expected domain models | `TextChunk`, `Embedding` (consumed); no new model produced |
| Expected interface usage | `interfaces.md` 4.7 → Vector Store Provider Interface (§6.2) |

### 5.8 Session Manager

| | |
|---|---|
| Purpose | Resolve session identity and load bounded conversation history |
| Inputs | Session identifier + current query text |
| Outputs | `ConversationSession` |
| Normal behaviour | New session created on first turn; existing session resolved with bounded history on subsequent turns (FR-1301–1303) |
| Boundary cases | History exactly at the configured bound (oldest message must be evicted, not silently retained); explicit reset (`domain_models.md` §10, `sequence_diagrams.md` §6.1) |
| Failure cases | Session store unreachable — recoverable failure subject to retry; on exhaustion, proceeds with empty history rather than blocking the request, degradation logged |
| Expected domain models | `ConversationSession`, `ConversationMessage[]` (contained) |
| Expected interface usage | `interfaces.md` 4.8 — backing store is an implementation swap point (ADR-007), not a contract change |

### 5.9 Query Analyzer *(provisional — `architecture.md` §16)*

| | |
|---|---|
| Purpose | Classify a query before retrieval; route conversational/unsupported queries away from the grounded path |
| Inputs | `ConversationSession` |
| Outputs | Query category (`policy_query` / `conversational` / `unsupported`) |
| Normal behaviour | A clearly HR-policy-shaped question classifies `policy_query`; a greeting classifies `conversational`; an out-of-domain question classifies `unsupported` |
| Boundary cases | An ambiguous query that could plausibly be either conversational or policy-related — the specific classification mechanism (rule-based, classifier, or LLM-assisted) is an open decision (`architecture.md` ADR-008), so boundary-case *expected outcomes* are only testable once that mechanism is chosen; the *contract shape* (category value returned) is testable now |
| Failure cases | Classification mechanism failure — falls back to a configured default category rather than blocking the request |
| Expected domain models | `Query` (provisional category field, not yet committed — `domain_models.md` §6) |
| Expected interface usage | `interfaces.md` 4.9 — testing this stage's existence at all is contingent on `architecture.md` §16 formally accepting the extension; see §21 |

### 5.10 Query Reformulator

| | |
|---|---|
| Purpose | Resolve ambiguous follow-up queries into a self-contained retrieval query |
| Inputs | Current query + `ConversationSession` |
| Outputs | `Query` (resolved form — same object, not a new one, per `domain_models.md` §6 merge) |
| Normal behaviour | A pronoun-dependent follow-up ("What about for adoptive parents?") resolves into a self-contained query using prior turn content (`sequence_diagrams.md` §6.1) |
| Boundary cases | The very first turn in a session (nothing to reformulate against — original and resolved form should be identical); a follow-up referencing a turn beyond the bounded history window |
| Failure cases | Reformulation mechanism failure — falls back to the original query unmodified, a deliberate degrade-gracefully behavior, not a hard failure |
| Expected domain models | `Query` |
| Expected interface usage | `interfaces.md` 4.10 — mechanism open (`architecture.md` ADR-008-adjacent); see §21 |

### 5.11 Retriever

| | |
|---|---|
| Purpose | Embed the query, search, filter, deduplicate, optionally re-rank |
| Inputs | `Query` (via its transient `Embedding`) + retrieval configuration |
| Outputs | `SearchResult[]` (possibly empty) |
| Normal behaviour | Relevant chunks returned above threshold, ranked, deduplicated (FR-801–806) |
| Boundary cases | Exactly `top_K_candidates` results returned; a query where the top result sits exactly at the configured similarity threshold; near-duplicate chunks from overlapping windows (must collapse to one, FR-806) |
| Failure cases | Vector Store or Embedding Provider unavailable/erroring — a true failure, distinct from a legitimately empty result (`sequence_diagrams.md` §3.2) |
| Expected domain models | `SearchResult[]` |
| Expected interface usage | `interfaces.md` 4.11 → Embedding Provider Interface + Vector Store Provider Interface (§6.1, §6.2) |

### 5.12 Context Builder

| | |
|---|---|
| Purpose | Assemble selected evidence into a token-budgeted, ordered context |
| Inputs | `SearchResult[]` + `ConversationSession` + context token budget |
| Outputs | `RetrievedChunk[]` + `QueryContext` (or the explicit no-context signal — `domain_models.md` §19.2) |
| Normal behaviour | Evidence fits within budget, assembled in deterministic order (FR-901–903) |
| Boundary cases | Evidence exactly at the token budget boundary (no truncation) vs. one token over (truncation flag set, FR-904); an empty `SearchResult[]` (must **not** produce a `QueryContext` at all — this is the single most important boundary case for this stage, directly validating Runtime Invariant 2) |
| Failure cases | None that block the pipeline under normal operation — token-budget overflow is expected, handled behavior |
| Expected domain models | `RetrievedChunk[]`, `QueryContext` |
| Expected interface usage | `interfaces.md` 4.12 — no Provider Interface dependency |

### 5.13 Prompt Assembler

| | |
|---|---|
| Purpose | Render the versioned prompt template with context and instructions |
| Inputs | `QueryContext` + query |
| Outputs | Rendered prompt (processing artifact, not a domain model — `domain_models.md` §16) |
| Normal behaviour | Template renders with all required sections populated (FR-1001–1004) |
| Boundary cases | Maximum context size within the prompt's own token budget; few-shot examples present vs. absent (FR-1005) |
| Failure cases | Configured prompt template missing or malformed — a configuration error, ideally caught at startup validation (FR-1603) rather than per-request |
| Expected domain models | `QueryContext` (consumed); no domain model produced (the output is explicitly excluded from the domain model, §5.13's own row is the test that confirms this exclusion holds) |
| Expected interface usage | `interfaces.md` 4.13 — no Provider Interface dependency |

### 5.14 Response Generator

| | |
|---|---|
| Purpose | Submit the assembled prompt to the LLM Provider Interface; return the generated response |
| Inputs | Rendered prompt + generation configuration |
| Outputs | `GeneratedResponse` — completed only, never partial (`domain_models.md` §8, Runtime Invariant 4) |
| Normal behaviour | A completed call with citable content, finish reason indicating success (FR-1101–1103) |
| Boundary cases | A completed call with a grounding-driven decline finish reason (`sequence_diagrams.md` §3.3) — this is a **successful** call, not a failure case, and must be tested as such |
| Failure cases | Rate-limited, timeout, refused, transient, unknown provider failure — normalized (`interfaces.md` §5.3); none of these ever produces a `GeneratedResponse` |
| Expected domain models | `GeneratedResponse` |
| Expected interface usage | `interfaces.md` 4.14 → LLM Provider Interface (§6.3); MVP reference path is blocking — see §7 for the streaming-independence note carried from `sequence_diagrams.md` §3.1 |

### 5.15 Citation Mapper

| | |
|---|---|
| Purpose | Resolve generated references to source citations; flag unresolvable claims |
| Inputs | `GeneratedResponse` + `QueryContext` (citation metadata) — only reached on the grounded path |
| Outputs | `Citation[]` + `Response` (grounded state) |
| Normal behaviour | Every `CitationReference` resolves to a `Citation` pointing at the correct `TextChunk` (FR-1201–1204) |
| Boundary cases | A claim with no matching `CitationReference` at all vs. a `CitationReference` present but unresolvable — both distinct paths to `unverified_statement_flag = true`; a response with the maximum number of distinct citations |
| Failure cases | None that block the pipeline — an unresolvable reference sets the flag, never fails the request; a true failure would only occur if the citation metadata map itself is corrupted (a Context Builder contract defect, not a normal Citation Mapper case) |
| Expected domain models | `CitationReference` (internal), `Citation`, `Response` |
| Expected interface usage | `interfaces.md` 4.15 — no Provider Interface dependency; **never** calls back to the Vector Store Provider Interface (this negative assertion is itself a required test — see §9) |

### 5.16 Not Found Path *(stage-equivalent responsibility, `rag_design.md` §5.10)*

| | |
|---|---|
| Purpose | Assemble the declined `Response` shape for any of three trigger cases |
| Inputs | None, or a discarded `GeneratedResponse` (trigger case 3 — `domain_models.md` §9) |
| Outputs | `Response` (declined state — empty `Citation[]`, `unverified_statement_flag = false`, by construction) |
| Normal behaviour | Identical, fixed output shape regardless of which of the three triggers fired |
| Boundary cases | Trigger case 3 specifically — a `GeneratedResponse` *does* exist and must be verifiably discarded, not partially incorporated into the declined `Response` |
| Failure cases | None — this is itself the terminal handler for three other paths' non-error outcomes; it has no failure mode of its own |
| Expected domain models | `Response` (declined state) |
| Expected interface usage | Invoked by the Query Orchestrator (§7.2), never invokes Citation Mapper — this non-invocation is a required negative assertion |

---

## 6. Contract Testing Strategy

Every Provider Interface is tested against its contract independent of which vendor implementation satisfies it — this is what lets a provider swap (`architecture.md` ADR-003/004/005) happen without re-testing every Pipeline Stage that depends on it.

**Every Provider Interface's contract test verifies the same four properties:**

1. **Provider replacement never changes pipeline behaviour.** The same contract test suite is run against every candidate implementation of a given interface; a Pipeline Stage's unit tests (§5) never need to change when the implementation behind its declared Provider Interface changes.
2. **Vendor SDK objects never escape provider implementations.** Every output the interface returns is asserted to be a domain model (`Embedding`, `SearchResult[]`, `GeneratedResponse`) — never a vendor-shaped object, and never an object with a vendor-specific field bolted on (`domain_models.md` §16, "Provider Leakage").
3. **Errors are normalized.** Every simulated failure mode (timeout, rate-limit, authentication failure, malformed response) is asserted to surface as one of the shared failure categories (`interfaces.md` §7) — never a vendor-specific exception type reaching the caller.
4. **Model/version metadata is preserved.** Every `Embedding` the interface returns carries a non-empty model/version identifier, and a query embedded with one model/version is detectable as incompatible with an index built from a different one (Risk R-003).

### 6.1 Embedding Provider Interface

| Contract Behavior | Verification Approach |
|---|---|
| Generate document embeddings (batch) | Submit a batch of chunk texts; assert one `Embedding` per input, in order, each with model/version populated |
| Generate query embeddings (single) | Submit one query text; assert a single `Embedding` returned |
| Expose model metadata | Assert every `Embedding` carries an opaque model identifier — never a provider-specific model-selection type |
| Failure normalization | Simulate timeout, rate-limit, and transient failures; assert each normalizes to its documented category (`interfaces.md` §5.1) |

### 6.2 Vector Store Provider Interface

| Contract Behavior | Verification Approach |
|---|---|
| Store vectors | Upsert a batch of chunks; assert success/failure reported per chunk, never as one opaque batch result |
| Search vectors | Query with a known `Embedding`; assert `SearchResult[]` is ranked, domain-shaped, and carries the expected `ChunkMetadata` reference |
| Metadata filtering | Assert a metadata predicate narrows results correctly, using the same search call as an unfiltered query — never a separate code path (`rag_design.md` §6.2) |
| Replace-on-re-ingestion | Upsert a document's chunks twice with different content; assert the second upsert's results are the *only* ones returned by a subsequent search — no duplication |
| Model/version mismatch detection | Search using an `Embedding` tagged with a model/version different from what the index was built with; assert this is detected and reported, not silently compared (Risk R-003) |
| Failure normalization | Simulate unavailability; assert normalization per `interfaces.md` §5.2 |

### 6.3 LLM Provider Interface

| Contract Behavior | Verification Approach |
|---|---|
| Generate responses (blocking) | Submit a prompt; assert a `GeneratedResponse` with text, token usage, and finish reason |
| Configurable model parameters | Assert temperature/max-tokens/timeout configuration is honored without requiring a code change to the calling stage |
| Failure normalization | Simulate rate-limit, timeout, refusal, and transient failures; assert each normalizes to its documented category (`interfaces.md` §5.3), and assert none of them ever produces a `GeneratedResponse` |
| Grounding-decline is not a failure | Simulate a completion with an insufficient-context finish reason; assert this returns a normal `GeneratedResponse`, not a normalized failure |

---

## 7. Orchestrator Testing

Orchestrator tests are deliberately separate from stage tests, because an orchestrator's correctness is about *sequencing and routing*, never about *computing*. This mirrors `sequence_diagrams.md` §8.2's structural audit, turned into a test design.

**Confirmed allowed, with a validation approach for each:**

| Allowed | Validation Approach |
|---|---|
| Coordinate | Every stage in a flow is invoked exactly once, in the order `sequence_diagrams.md` specifies, using stage test doubles that record invocation order |
| Sequence | Assert a later stage's test-double input matches exactly the prior stage's test-double output — no transformation in between |
| Propagate outcomes | Assert a stage's reported failure/success reaches the orchestrator's own output unchanged |
| Retry | Assert a recoverable-category failure triggers exactly one retry call to the same Provider Interface test double before either succeeding or exhausting (`sequence_diagrams.md` §5.1) |
| Cancel | Assert a non-recoverable failure or a Not Found short-circuit stops the remaining sequence — later stages' test doubles record zero invocations |

**Confirmed forbidden, with a validation approach proving absence:**

| Forbidden | Validation Approach |
|---|---|
| Transform business data | Substitute a stage's test double with one that returns a deliberately unusual (but contract-valid) value; assert the orchestrator's output reflects that value unchanged — if the orchestrator "normalizes" or "cleans" it, that is a defect |
| Interpret embeddings | Assert the orchestrator's own code path never inspects an `Embedding`'s vector content — only ever passes it opaquely between the Retriever's test double and its declared consumer |
| Perform retrieval | Substitute the Retriever's test double with one whose ranking logic is intentionally reversed from realistic; assert the orchestrator's behavior is identical regardless — this proves the orchestrator does not depend on, or duplicate, ranking logic |
| Construct prompts | Substitute the Prompt Assembler's test double with one returning an obviously malformed rendered prompt; assert the orchestrator passes it through to the Response Generator's test double unexamined |
| Derive citations | Substitute the Citation Mapper's test double with one returning a deliberately empty `Citation[]` regardless of input; assert the orchestrator's final output reflects that empty list — it never adds, infers, or second-guesses a citation itself |

**Query Orchestrator** and **Ingestion Orchestrator** (`interfaces.md` §3.1, §3.2) are each tested against this same table — the objectives are identical, only the specific stage sequence differs (`sequence_diagrams.md` §3, §4).

---

## 8. Integration Testing

Derived directly from `sequence_diagrams.md` — one subsection per runtime sequence, each field below matching that diagram's own structure exactly.

### 8.1 Grounded Answer (`sequence_diagrams.md` §3.1)

| | |
|---|---|
| Purpose | Confirm the complete happy path produces a correctly grounded, cited answer |
| Preconditions | A populated index containing at least one chunk relevant to the test query |
| Expected runtime path | Session Manager → Query Analyzer → Query Reformulator → Retriever → Context Builder → Prompt Assembler → Response Generator → Citation Mapper, in that order, no short-circuit |
| Expected domain models | `ConversationSession`, `Query`, `SearchResult[]`, `RetrievedChunk[]`, `QueryContext`, `GeneratedResponse`, `Citation[]`, `Response` (grounded) |
| Expected response | Non-empty answer text, at least one `Citation`, `unverified_statement_flag = false` for a fully-supported answer |
| Expected observability | One correlation ID spanning every stage call; per-stage `ExecutionMetadata` present for all eight stages |
| Expected runtime invariants | 1 (grounded requires `QueryContext` + `GeneratedResponse`), 3 (`Citation` from `CitationReference`), 6 (no provider-specific object crosses into a stage) |
| Expected requirements covered | FR-801–1205, NFR-MOD-001/002, NFR-EXT-001–003 |

### 8.2 Empty Retrieval (`sequence_diagrams.md` §3.2)

| | |
|---|---|
| Purpose | Confirm hallucination prevention when no relevant evidence exists |
| Preconditions | A query with no matching content in the index (or an index deliberately empty for this test) |
| Expected runtime path | ...→ Retriever returns `SearchResult[] = []` → Not Found Path, **skipping** Context Builder, Prompt Assembler, Response Generator, Citation Mapper entirely |
| Expected domain models | `SearchResult[] = []`; explicitly **no** `QueryContext`, **no** `GeneratedResponse` |
| Expected response | `Response` (declined) — empty answer content, empty `Citation[]`, `unverified_statement_flag = false` |
| Expected observability | No `ErrorContext` created — this is logged as a successful, declined outcome, not a failure |
| Expected runtime invariants | 1 (declined path may exist without `QueryContext`), 2 (`QueryContext` never exists without evidence) |
| Expected requirements covered | FR-805, FR-1106 |

### 8.3 LLM Decline (`sequence_diagrams.md` §3.3)

| | |
|---|---|
| Purpose | Confirm the LLM's own grounding refusal is honored without fabrication |
| Preconditions | A query where retrieval succeeds, but the retrieved evidence is engineered (via the LLM Provider Interface test double) to trigger an insufficient-context finish reason |
| Expected runtime path | ...→ Context Builder → Prompt Assembler → Response Generator → LLM declines → Not Found Path, **skipping** Citation Mapper |
| Expected domain models | `QueryContext` **does** exist; `GeneratedResponse` **does** exist; **no** `Citation` is ever created from it |
| Expected response | `Response` (declined) — identical shape to §8.2's, despite different upstream lineage |
| Expected observability | `GeneratedResponse`'s finish reason logged; no `ErrorContext` (this is a successful call, not a failure) |
| Expected runtime invariants | 1 (all three declined trigger cases, specifically case 3), 5 (Not Found Path, not the Orchestrator, assembles the declined `Response`) |
| Expected requirements covered | FR-1106, `domain_models.md` §9 "Response State Clarification" |

### 8.4 Document Ingestion (`sequence_diagrams.md` §4.1)

| | |
|---|---|
| Purpose | Confirm a source PDF becomes fully indexed, retrievable content |
| Preconditions | A well-formed representative HR policy PDF fixture |
| Expected runtime path | Document Loader → PDF Parser → Text Preprocessor → Semantic Chunker → Metadata Extractor → Embedding Generator → Vector Indexer, in order |
| Expected domain models | `Document` → `ExtractedDocument` → `TextChunk[]` → `ChunkMetadata` → `Embedding` — the full canonical chain (`domain_models.md` §12) |
| Expected response | Ingestion result summary reporting success, chunk count, no reduced-fidelity flags for a well-formed fixture |
| Expected observability | One correlation ID for the ingestion run; per-stage `ExecutionMetadata` |
| Expected runtime invariants | 6 (no vendor-specific object crosses a Pipeline Stage boundary) |
| Expected requirements covered | FR-101–705 |

### 8.5 Failure Isolation (`sequence_diagrams.md` §4.2)

| | |
|---|---|
| Purpose | Confirm one document's ingestion failure does not abort a batch |
| Preconditions | A batch of two documents, one well-formed, one deliberately malformed/unparseable |
| Expected runtime path | Document A completes the full §8.4 path; Document B fails at PDF Parser; the Ingestion Orchestrator continues to (or has already completed) Document A regardless of order |
| Expected domain models | Document A's full chain exists; Document B produces no `TextChunk`/`Embedding` at all |
| Expected response | Two independent ingestion results — one success, one failure — never a single aborted batch result |
| Expected observability | `ExecutionMetadata` + `ErrorContext` for Document B only, correlated to its own run, distinct from Document A's |
| Expected runtime invariants | 5 (Orchestrator only isolates and routes, never "fixes" or retries the malformed document itself) |
| Expected requirements covered | FR-1404, NFR-REL-005 |

### 8.6 Provider Failure (`sequence_diagrams.md` §5.1)

| | |
|---|---|
| Purpose | Confirm vendor-specific failures are normalized and retried/failed correctly, for each of the three Provider Interfaces |
| Preconditions | A Provider Implementation test double configured to fail on Attempt 1 |
| Expected runtime path | Attempt 1 fails → normalized failure propagated to the Orchestrator → retry-eligibility decided by category → Attempt 2 → success or exhaustion |
| Expected domain models | None produced on a fully-exhausted failure; the normal domain model produced on an Attempt-2 success |
| Expected response | On exhaustion: the calling stage's own documented failure behavior (e.g., Embedding Generator reports a per-chunk failure without aborting the batch) |
| Expected observability | `ExecutionMetadata` + `ErrorContext` per attempt, sharing one correlation ID |
| Expected runtime invariants | 4 (no partial `GeneratedResponse` on an LLM Provider failure specifically), 6 |
| Expected requirements covered | `interfaces.md` §7, NFR-EXT-001–003, NFR-REL-002/003 |

### 8.7 Conversation Management (`sequence_diagrams.md` §6.1)

| | |
|---|---|
| Purpose | Confirm multi-turn continuity, session isolation, and reset behavior |
| Preconditions | A fresh session; a second query that depends on the first turn's content to resolve correctly |
| Expected runtime path | Turn 1 (full grounded path) → persist → Turn 2 (reformulation uses Turn 1's `ConversationMessage`) → persist → explicit reset |
| Expected domain models | `ConversationSession` (Created → Active → Reset), `ConversationMessage[]` (bounded, ordered) |
| Expected response | Turn 2's answer correctly reflects the resolved (not literal) query text |
| Expected observability | Distinct correlation IDs per turn, shared session identifier across turns |
| Expected runtime invariants | None of the six numbered invariants directly govern session mechanics, but this test confirms `ConversationSession`'s own lifecycle rules (`domain_models.md` §10) hold |
| Expected requirements covered | FR-1301–1306 |

### 8.8 Offline Evaluation (`sequence_diagrams.md` §7.1)

| | |
|---|---|
| Purpose | Confirm the Evaluation Harness observes, rather than forks, production logic |
| Preconditions | A small labeled question set (§10) and a populated index matching it |
| Expected runtime path | Evaluation Harness calls the same Query Orchestrator entry point as any other caller, once per labeled question |
| Expected domain models | The full grounded-or-declined chain per question, observed not altered |
| Expected response | Computed metrics (§11), not a stored `EvaluationResult` domain model (`domain_models.md` §17) |
| Expected observability | Aggregate metrics correlate back to individual question correlation IDs for debugging a regression |
| Expected runtime invariants | All six, transitively, since this test exercises the same paths as §8.1–8.3 across many questions |
| Expected requirements covered | `rag_design.md` §9, NFR-TEST-002/003 |

---

## 9. Runtime Invariant Validation

Every invariant `domain_models.md` §19 states, plus the `ExecutionMetadata` ownership boundary check `sequence_diagrams.md` §13 added, gets at least one explicit validation approach here — beyond simply "covered by an integration test," each invariant also gets a targeted, minimal test designed to fail *specifically* if that invariant is violated, independent of whether the broader integration test happens to catch it too.

| Invariant | Validation Approach(es) |
|---|---|
| 1. Grounded `Response` requires `QueryContext` + `GeneratedResponse`; declined `Response` varies by trigger | (a) §8.1/§8.2/§8.3 integration coverage; (b) a targeted assertion on the Citation Mapper's test double: it is never invoked unless both a `QueryContext` and a `GeneratedResponse` exist in that request's trace |
| 2. `QueryContext` cannot exist without evidence or an explicit no-context outcome | A targeted Context Builder unit test (§5.12) asserting that an empty `SearchResult[]` input produces the no-context signal, never a `QueryContext` instance with zero `RetrievedChunk[]` |
| 3. `Citation` cannot be created without `CitationReference` resolution | A targeted Citation Mapper unit test (§5.15) asserting no code path constructs a `Citation` except via resolving a `CitationReference`; a claim with no `CitationReference` must set the unverified flag, never a fabricated `Citation` |
| 4. Provider failures cannot create a partial `GeneratedResponse` | A targeted Response Generator unit test (§5.14): every simulated LLM Provider failure category is asserted to produce zero `GeneratedResponse` instances, only an `ErrorContext` |
| 5. Orchestrators cannot modify domain model meaning | §7's full orchestrator test table — in particular, the "substitute an unusual-but-valid stage output and assert it passes through unchanged" pattern is the direct falsification test for this invariant |
| 6. Domain models cannot contain provider-specific objects | Contract tests (§6) assert every Provider Interface's output is domain-shaped; a static/structural review (not a runtime test, but a required check) confirms no Pipeline Stage's declared dependencies include a vendor SDK type |
| Additional: `ExecutionMetadata` never becomes a business model | A targeted assertion, run across every integration test in §8: `Response`, `GeneratedResponse`, and `QueryContext` are checked to never carry an `ExecutionMetadata` or `ErrorContext` field — those only ever appear in the separate observability record for the same correlation ID |

---

## 10. RAG Evaluation Strategy

RAG systems fail in ways structural correctness tests cannot see — a pipeline can pass every unit, contract, component, and integration test in §5–§9 and still retrieve the wrong policy section, or generate a fluent but unfaithful answer. This section exists because of that gap, and it is intentionally more detailed than a typical RAG evaluation write-up, because the SRS's own acceptance criteria (AC-003) explicitly leaves the precision bar unset — this strategy is what will eventually let that bar be set with evidence rather than guessed.

**Dataset Philosophy.** The evaluation dataset is not a byproduct of testing — it is a first-class artifact with its own ownership, versioning, and review process, because it is the only mechanism this system has for turning "the answer sounds right" into "the answer is verifiably right." A dataset built casually produces evaluation results no one should trust; this strategy treats dataset construction with the same rigor as the pipeline it evaluates.

**Ground Truth Ownership.** Per SRS AS-008, the HR Policy Owner is accountable for the correctness of source policy content — by direct extension, the HR Policy Owner (or a delegate with equivalent domain authority) owns what counts as a *correct* answer and a *correct* citation for any given golden question. Engineering owns the mechanics of measurement; it does not own the definition of correctness. This separation is deliberate: an engineer grading their own system's retrieval quality is a conflict of interest the process must not depend on.

**Golden Question Set.** A curated, versioned set of representative employee questions spanning the HR policy domain (leave, benefits, conduct, reimbursement, etc. — per `requirements.md`'s example policy categories), each with:
- **Expected Citations** — the specific document, section, and page a correct answer should cite, established by Ground Truth Owner review, not inferred from a first system run.
- **Expected Behaviour** — whether the question should produce a grounded answer, or should legitimately decline (e.g., a question about a policy that does not exist in the corpus, deliberately included to validate the declined path against real-shaped input, not just synthetic empty-index tests).

**Regression Dataset.** A superset or sibling of the Golden Question Set specifically curated to catch *degradation* — questions chosen because a prior version of the system got them right, so a future change that breaks them is caught immediately (§14). This dataset grows over time as production or evaluation runs surface new cases worth locking in.

**Dataset Versioning.** The dataset is versioned independently of the pipeline's own version — a pipeline version is evaluated *against* a specific, named dataset version, and a regression report (§14) always states which dataset version it used, so a metric change can be attributed to a pipeline change, a dataset change, or both, never left ambiguous.

**Human Review Process.** No golden question's expected citation or expected behaviour is accepted into the dataset without a human review step from someone with HR policy domain authority (not merely engineering judgment) — this is the same principle as Ground Truth Ownership, applied as a gate rather than a general statement. A question that the system currently gets wrong is not "fixed" by changing its expected answer to match the system's output — that would defeat the dataset's purpose.

**Metric Evolution.** The specific metrics in §11 are not expected to be final. As the system encounters real failure modes not anticipated here (e.g., a specific ambiguous-policy phrasing that reliably confuses retrieval), the evaluation strategy is expected to grow new targeted checks — this document defines the *methodology* for that growth (§19), not a closed metric list.

**No actual dataset is defined in this document.** Every golden question, expected citation, and expected answer referenced above is a placeholder for content that does not yet exist — constructing it is the explicit purpose of `app/specs/evaluation/benchmark_spec.md` (§22).

---

## 11. Evaluation Metrics

### Retrieval

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Precision@K | How much of what's retrieved is actually relevant | Fraction of top-K `SearchResult[]` matching the golden question's expected evidence | Low precision → noisy context, wasted tokens, possible faithfulness degradation | `rag_design.md` §9.2 |
| Recall@K | How much of the relevant evidence was found at all | Fraction of expected evidence chunks present within top-K | Low recall → the answer cannot possibly be fully correct, regardless of generation quality | `rag_design.md` §9.2 |
| Hit Rate@K | Binary retrieval success per question | Whether at least one expected chunk appears in top-K | A coarse but interview-explainable retrieval health signal | `rag_design.md` §9.2 |
| Mean Reciprocal Rank (MRR) | How highly the correct evidence ranks, not just whether it's present | Average of 1 ÷ (rank of first correct chunk), across the golden set | Low MRR with high Recall suggests a re-ranking gap, not a retrieval-coverage gap | `rag_design.md` §9.2 |

### Generation

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Faithfulness | Whether every claim is supported by retrieved evidence | Compare `GeneratedResponse` content against `QueryContext`'s evidence | Low faithfulness correlates with a high `unverified_statement_flag` rate — the two should be checked together, not independently | `rag_design.md` §9.3 |
| Answer Relevance | Whether the answer addresses the question asked | Human or model-assisted comparison of `GeneratedResponse` against the golden question's intent | Distinct from faithfulness — an answer can be fully faithful to irrelevant evidence | `rag_design.md` §9.3 |
| Completeness | Whether all relevant aspects present in the evidence are covered | Compare `GeneratedResponse` against the full scope of `QueryContext`'s evidence, not just the first matching fact | Low completeness on a multi-condition policy (e.g., eligibility with several criteria) is a specific, checkable failure mode | `rag_design.md` §9.3 |

### Citation

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Citation Correctness | Whether attached citations point to the actual source of each claim | Compare each `Citation` against the golden question's Expected Citations | The precision bar for this metric is the SRS's own open item (AC-003) — see §21 | `rag_design.md` §9.3, SRS AC-003 |
| Unverified-Statement Rate | Aggregate rate of claims that could not be traced to evidence | Fraction of `Response`s across the golden set with `unverified_statement_flag = true` | A direct, quantified proxy for residual hallucination risk (`rag_design.md` §6.3) — tracked, not eliminated | `domain_models.md` §9 |

### Conversation

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Follow-up Resolution Accuracy | Whether Query Reformulator correctly resolves a context-dependent follow-up | Compare the resolved `Query` text against the golden multi-turn question's expected self-contained form | Low accuracy directly explains a downstream retrieval/generation failure on turn 2+ that would otherwise look like a retrieval bug | FR-1304 |
| Session Isolation Integrity | Whether one session's history ever leaks into another's | Structural check across concurrent-session integration runs — no shared `ConversationMessage` between distinct `session_id`s | A correctness bar, not a quality gradient — any leak is a defect, not a "low score" | FR-1302 |

### Performance

See §13 for the full performance testing strategy; the metrics themselves are the NFR-PERF targets already defined in `requirements.md` (p95 end-to-end latency, time-to-first-token, retrieval latency, ingestion throughput) — not redefined here to avoid two sources of truth for the same numbers.

### Reliability

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Availability | Whether the query-serving path meets its uptime target | Measured over a rolling monthly window, excluding scheduled maintenance | Target already fixed at 99.5% monthly | NFR-REL-001 |
| Failure Isolation Effectiveness | Whether one document's or one request's failure ever corrupts unrelated state | Structural check across §8.5/§8.6 runs — a failed unit of work never affects a concurrent successful one | A correctness bar, not a quality gradient | NFR-REL-005 |

### Cost

| Metric | Purpose | Measurement | Interpretation | Reference |
|---|---|---|---|---|
| Token Usage per Query | Direct cost driver | `GeneratedResponse`'s recorded token usage, aggregated across the golden set | Tracked as a trend, flagged if it exceeds the configured cost-per-query ceiling | NFR-COST-001, NFR-COST-005 |
| Embedding Call Volume | Ingestion + retrieval-time cost driver | Count of Embedding Provider Interface calls, distinguishing new-chunk embedding from redundant re-embedding | A rising redundant-embedding rate indicates a caching or idempotency regression | NFR-COST-003 |

**No arbitrary numeric thresholds are introduced in this table.** Where `requirements.md` already fixes a number (availability, latency percentiles), it is cited, not restated with a new value. Where `requirements.md` leaves a number open (citation precision, AC-003; cost-per-query ceiling, NFR-COST-005), this document does not invent one — see §21.

---

## 12. Failure Injection Strategy

Every failure mode below is deliberately simulated, never waited-for as a real outage, so Resilience Testing (§3) is repeatable and does not depend on an actual provider incident occurring during a test run. Each is classified as a **Business Outcome** (never an `ErrorContext`) or a **Technical Failure** (always an `ErrorContext`), per `sequence_diagrams.md` §10 — this classification is the thing under test as much as the failure-handling behavior itself, because misclassifying one as the other is its own defect class.

| Simulated Failure | Classification | Injection Point | Expected Handling |
|---|---|---|---|
| Embedding timeout | Technical Failure | Embedding Provider Implementation test double | Normalized to `timeout`, retried per policy (§6.1, §9 Invariant 4) |
| Embedding model/version mismatch | Technical Failure | Vector Store Provider Interface test double (query embedding tagged with a different model/version than the index) | Detected and reported, never silently compared (Risk R-003, §6.2) |
| Vector database unavailable | Technical Failure | Vector Store Provider Implementation test double | Normalized to `transient` or `unknown`, retried per policy |
| LLM timeout | Technical Failure | LLM Provider Implementation test double | Normalized to `timeout`; never produces a partial `GeneratedResponse` (Invariant 4) |
| LLM refusal (grounding-driven decline) | **Business Outcome** | LLM Provider Implementation test double (finish reason = insufficient context) | Routed to Not Found Path; `GeneratedResponse` **does** exist but is discarded, not treated as a failure (§8.3) |
| Malformed PDF | Technical Failure | Document Loader / PDF Parser input fixture | Non-recoverable, isolated per-document failure, batch continues (§8.5) |
| Corrupted metadata | Technical Failure | Metadata Extractor input fixture (malformed upstream provenance) | Reported as a stage failure, not silently defaulted — distinct from an *unextractable* field, which is a normal null (FR-503), not a failure |
| Conversation storage unavailable | Technical Failure | Session Manager backing-store test double | Recoverable, retried; on exhaustion, proceeds with empty history (§5.8), degradation logged |
| Configuration validation failure | Technical Failure | Startup-time configuration loader (out of this document's per-request scope — see §21) | Fail-fast before any traffic is accepted (SRS FR-1603); out of scope for the request-time diagrams this strategy otherwise traces to |
| Retry exhaustion | Technical Failure | Any Provider Implementation test double, configured to fail every attempt | Classified non-recoverable once the retry budget (owned by configuration, not this document) is exhausted; fails the unit of work only, never crashes the surrounding batch/session |

**Unsupported question category** (Query Analyzer classifying `unsupported`) and **no relevant policy found** (empty `SearchResult[]`) are the remaining two Business Outcomes already covered structurally in §8.2 and are not repeated here as injection targets, since they are the *absence* of a failure rather than a simulated one.

---

## 13. Performance Testing Strategy

Every performance test traces directly to a numeric NFR target already fixed in `requirements.md` — this document introduces no new numbers.

| Dimension | What Is Measured | Reference |
|---|---|---|
| Retrieval latency | Time from query embedding through ranked `SearchResult[]` return, at a target knowledge-base size | NFR-PERF-003 (p95 ≤ 500ms @ 100K chunks) |
| Generation latency | Time-to-first-token in streaming mode (once implemented — currently MVP blocking, §7) | NFR-PERF-002 |
| End-to-end latency | Full grounded-answer path, Employee question to `Response` returned | NFR-PERF-001 (p95 ≤ 8s) |
| Concurrent sessions | System behavior under the target concurrent-session load | NFR-SCALE-001 (≥ 50 concurrent sessions) |
| Batch ingestion | Time to fully ingest a representative multi-document batch | NFR-PERF-004 (50-page PDF ≤ 2 min) |
| Memory behaviour | Whether request-handling components hold bounded, not unbounded, in-process state as concurrency scales | NFR-SCALE-001 (statelessness precondition — `architecture.md` §13) |
| Token consumption | Aggregate and per-query token usage under realistic query mix | NFR-COST-001 |
| Context size | Distribution of `QueryContext` sizes and truncation-flag frequency under realistic retrieval volume | FR-901–904 |
| Provider throughput | Whether a single Provider Implementation becomes a bottleneck independent of pipeline logic — validated by substituting a faster/slower test double and confirming only that provider's latency contribution changes, nothing else in the pipeline | NFR-EXT-001–003 (provider-swap-without-pipeline-rewrite, extended to performance isolation) |

**No load-testing tool, harness, or platform is named here** — this section defines *what* is measured and *why it matters against a specific NFR*, leaving *how* (which tool generates the load) to `deployment.md` or an implementation-time decision, consistent with this document's technology-independence constraint.

---

## 14. Regression Testing Strategy

**Regression testing philosophy:** any change that could plausibly move a metric in §11 is treated as regression-relevant until proven otherwise — the default assumption is "this might have changed quality," not "this is surely safe." This is deliberately conservative, because RAG systems are exactly the kind of system where a change with an obviously-safe *description* (e.g., "just adjusted the chunk overlap") can have a non-obvious *effect* on retrieval quality.

**Coverage:**

| Area | What Regression Testing Confirms |
|---|---|
| Retrieval quality | Precision@K, Recall@K, Hit Rate@K, MRR (§11) have not degraded against the Regression Dataset (§10) |
| Citation quality | Citation Correctness and Unverified-Statement Rate have not degraded |
| Grounding | The declined-path rate on genuinely unanswerable golden questions has not dropped (i.e., the system has not started fabricating answers where it previously, correctly, declined) |
| Runtime invariants | §9's targeted validations still pass — a regression here is a structural defect, not a quality drift, and should block release harder than a quality-metric regression |
| Performance | §13's latency/throughput targets have not regressed beyond their NFR bounds |
| Provider replacement | Swapping a Provider Implementation produces contract-test-identical behavior (§6) and evaluation-metric-equivalent quality — a provider swap that changes quality silently is exactly the risk `architecture.md`'s abstraction boundary exists to make visible, not to hide |
| Prompt changes | Any change to the versioned prompt template (`interfaces.md` 4.13) re-runs the full Evaluation Testing suite (§10–§11) before promotion |
| Chunking changes | Any change to chunk size, overlap, or splitting strategy re-runs Retrieval quality metrics specifically, since this is the most direct lever on retrieval behavior (`rag_design.md` §6.4) |
| Embedding changes | A new embedding model or version re-runs the full retrieval-and-downstream chain, since a changed embedding space can shift which chunks even become candidates |
| Configuration changes | Any change to top-K, similarity threshold, or context token budget re-runs Retrieval and Performance metrics, since these are explicit cost/quality trade-off levers (`rag_design.md` §6.4, NFR-COST-002) |

**What triggers regression execution:** any pull request or change set touching a prompt template, chunking configuration, embedding model/version, retrieval configuration, or Provider Implementation is treated as regression-relevant by default. A change confined to a single Pipeline Stage's internal logic with no change to its declared contract (`interfaces.md`) or its effect on retrieval/generation output is covered by that stage's own unit tests (§5) and does not require a full regression run — this is the practical payoff of stage isolation (§2): most changes are provably scoped to one stage and do not need the expensive full-corpus re-evaluation.

---

## 15. Acceptance Testing

A summary-level traceability matrix, grouped by requirement area rather than enumerated FR-by-FR — the SRS's ~90 FRs and ~43 NFRs are individually traceable through §5–§14 above, but reproducing every single ID as its own row here would make this table unmaintainable as a living document rather than more useful; the granular mapping is expected to live in `tasks.md`, later in the SDD chain, as an actively maintained artifact rather than a static table frozen at this document's approval date.

| Requirement Area | Test Category | Validation Method | Expected Evidence | Status |
|---|---|---|---|---|
| FR-101–109 (Document Ingestion) | Unit, Integration | §5.1–5.2, §8.4 | Passing ingestion-success and ingestion-failure-isolation runs | Planned |
| FR-201–206 (PDF Parsing) | Unit | §5.2 | Fidelity-flag behavior confirmed on a scanned-page fixture | Planned |
| FR-301–305 (Text Preprocessing) | Unit | §5.3 | Raw + normalized text both retrievable post-processing | Planned |
| FR-401–407 (Semantic Chunking) | Unit, Regression | §5.4, §14 | Deterministic chunk boundaries; regression suite on chunking-config change | Planned |
| FR-501–505 (Metadata Extraction) | Unit | §5.5 | Explicit-null behavior confirmed for unextractable fields | Planned |
| FR-601–606 (Embedding Generation) | Unit, Contract | §5.6, §6.1 | Model/version recorded on every `Embedding` | Planned |
| FR-701–705 (Vector Storage) | Unit, Contract | §5.7, §6.2 | Replace-on-re-ingestion confirmed, no duplication | Planned |
| FR-801–806 (Semantic Retrieval) | Unit, Integration, Evaluation | §5.11, §8.1, §11 | Precision@K/Recall@K measured against golden set | Planned |
| FR-901–905 (Context Construction) | Unit, Integration | §5.12, §8.1, §8.2 | `QueryContext` never constructed with zero evidence | Planned |
| FR-1001–1005 (Prompt Generation) | Unit | §5.13 | Rendered prompt confirmed to never be treated as a domain model | Planned |
| FR-1101–1106 (LLM Response Generation) | Unit, Contract, Integration | §5.14, §6.3, §8.1, §8.3 | Grounding-decline confirmed as a successful, non-error outcome | Planned |
| FR-1201–1205 (Citation Generation) | Unit, Integration, Evaluation | §5.15, §8.1, §11 | Citation Correctness and Unverified-Statement Rate measured | Planned |
| FR-1301–1306 (Conversation Support) | Unit, Integration, Evaluation | §5.8, §5.10, §8.7, §11 | Follow-up resolution and session isolation confirmed | Planned |
| FR-1401–1405 (Error Handling) | Component, Resilience | §7, §12 | Business-outcome/technical-failure classification confirmed for every injected case | Planned |
| FR-1501–1505 (Logging) | Observability | §17 | Correlation ID continuity confirmed across every integration scenario | Planned |
| FR-1601–1605 (Configuration Management) | Resilience | §12 (configuration validation failure) | Fail-fast-at-startup confirmed | Planned |
| NFR-PERF-001–004 | Performance | §13 | Latency targets measured against fixed NFR values | Planned |
| NFR-SCALE-001–003 | Performance | §13 | Concurrent-session and batch-ingestion behavior measured | Planned |
| NFR-REL-001–005 | Resilience, Performance | §12, §13 | Availability and failure-isolation targets measured | Planned |
| NFR-EXT-001–005 | Contract, Regression | §6, §14 | Provider-swap-without-pipeline-change confirmed | Planned |
| NFR-TEST-001–004 | (This entire document is the response to this NFR category) | §3–§9 | The pyramid itself | Satisfied by design |
| NFR-SEC-001–007 | Observability, Contract | §17, §6 | Secret-redaction and untrusted-input handling confirmed | Planned |
| NFR-COST-001–005 | Evaluation, Performance | §11 (Cost), §13 | Token usage and cost-per-query tracked | Planned |
| Runtime Invariants 1–6 + ExecutionMetadata boundary | Unit, Component, Integration | §9 | Targeted falsification test per invariant | Planned |

**Status column values used throughout this document's lifetime:** *Planned* (this document defines the approach, no test yet exists), *In Progress*, *Passing*, *Failing*, *Waived* (with a documented, approved reason). Every row above is currently *Planned* because this is a specification document, not a test execution report.

---

## 16. Test Data Strategy

| Data Category | Why It Exists |
|---|---|
| Synthetic HR documents | The default fixture type — avoids any dependency on real, potentially sensitive HR content while still exercising the full ingestion pipeline realistically |
| Representative policies | Cover the breadth of policy categories the golden question set (§10) will query against — leave, benefits, conduct, reimbursement — so retrieval and generation are validated across the actual domain, not one narrow slice of it |
| Conversation history fixtures | Deterministic multi-turn sequences for §8.7 and the Follow-up Resolution Accuracy metric (§11) — without a fixed history, a reformulation test's expected output cannot be pinned down |
| Malformed documents | Exercise §5.1/§5.2's failure paths and §8.5's isolation behavior deliberately, rather than waiting for a real malformed upload to surface a gap |
| Duplicate documents | Exercise re-ingestion's replace-semantics (§5.7, §8.4's note) — confirms identity stability and non-duplication under a controlled, repeatable condition |
| Large documents | Exercise chunking boundary cases (§5.4) and ingestion performance targets (§13, NFR-PERF-004) at a realistic upper bound |
| Boundary-case documents | Single-page documents, documents producing exactly one chunk, documents at the configured size limit — each targets a specific boundary row in §5's tables |
| Versioned policies | Exercise `Document`'s version lifecycle (`domain_models.md` §3) — confirms a policy update correctly supersedes, rather than duplicates or corrupts, the prior version's indexed content |
| Conflicting policies | Deliberately constructed to test how retrieval and generation behave when two chunks present ambiguous or contradictory guidance — this is a known, currently-unresolved modeling gap (`requirements_review_summary.md` Missing Requirement #10) and this fixture category exists specifically to make that gap observable in testing rather than only in production |
| Evaluation corpus | The indexed backing content the Golden Question Set (§10) is evaluated against — distinct from the general ingestion fixtures above because its content is deliberately matched to the golden questions' expected citations, not just structurally representative |

No actual document content, question text, or conversation transcript is defined in this document — every row above names a *category* of fixture this strategy requires, not the fixture itself.

---

## 17. Observability Validation

Observability is not assumed to work because it was specified (`architecture.md` §10; `interfaces.md` §8) — it is itself validated, because a monitoring gap discovered only after a production incident defeats the purpose of having specified it at all.

| Observability Concern | Validation Approach |
|---|---|
| Logging | Every integration scenario in §8 asserts a structured log entry exists for every stage transition it exercises, per `interfaces.md` §8's required fields |
| Metrics | Per-stage latency percentiles and error rates are asserted to be derivable from the same structured log events integration tests already produce — never a separately instrumented path that could silently drift from what's actually logged (`architecture.md` §10.2) |
| Tracing | Every integration scenario asserts a single correlation ID threads through every stage, provider, and (where applicable) retry attempt it involves — this is the most load-bearing observability assertion, since without it, every other signal is unattributable to a specific request |
| Correlation IDs | §8.5 and §8.6 specifically assert that two concurrently-processed units of work (two documents in a batch; two retry attempts) never share, and never lose, their distinct correlation ID |
| Error propagation | §9's `ErrorContext` containment check (never a peer of `ExecutionMetadata`, never leaking into a business model) is itself an observability validation, not only a domain-model one |
| Latency measurements | §11 and §13's metrics are asserted to be computable directly from `ExecutionMetadata.processing_duration` values already required by every stage call — no parallel, redundant timing mechanism |
| Cost metrics | Token usage figures on `GeneratedResponse` (§11, Cost category) are asserted to be present and non-zero on every successful LLM Provider Interface call |
| Security logging | Secret redaction (SRS FR-1604, NFR-SEC-002) is validated by asserting no configuration diagnostic output or error log ever contains a raw credential value, across every failure-injection scenario in §12 |

---

## 18. Risks and Testing Limitations

**What testing in this document cannot guarantee, stated plainly rather than implied:**

- **LLM probabilistic behavior.** The same prompt and context can legitimately produce different phrasing on different runs. This strategy mitigates this by evaluating against tolerance bands and semantic/faithfulness criteria (§11) rather than exact-text assertions, but it cannot guarantee bit-for-bit reproducibility of generated text, and does not attempt to.
- **Provider outages.** Contract and Resilience testing (§6, §12) validate that the system *handles* a provider failure correctly — they cannot prevent a real provider outage from occurring, and pre-production testing against a sandboxed or mocked provider cannot fully replicate every real-world failure mode a live vendor service might exhibit.
- **Future model drift.** A model swap or silent vendor-side model update can change quality in ways the Regression Testing strategy (§14) is designed to catch — but only for changes the team controls or is aware of. A vendor silently updating a model version behind a stable API name is a real, imperfectly-mitigated risk; the Regression Dataset's ongoing re-evaluation (§10, §14) is the best available detection mechanism, not a guarantee.
- **Policy ambiguity.** Where a real HR policy is itself ambiguous or contradictory (the "Conflicting policies" fixture category, §16), testing can confirm the system behaves consistently and declines rather than fabricates — it cannot resolve the underlying policy ambiguity, which is a business, not an engineering, problem.
- **Human judgement.** Answer Relevance, Completeness, and Citation Correctness (§11) ultimately depend on human (or human-delegated) review at some point in the loop (§10, Human Review Process) — this strategy reduces how much human review is needed per change (via the Regression Dataset), but does not eliminate the need for it entirely, nor should it.
- **Prompt interpretation.** The LLM's interpretation of the prompt template's instructions is not fully deterministic or fully inspectable — grounding instructions (`rag_design.md` §6.3) reduce, but do not guarantee, faithful adherence, which is precisely why `unverified_statement_flag` and Faithfulness measurement (§11) exist as ongoing signals rather than one-time checks.

**How testing reduces — without eliminating — these risks:** every category in §3's pyramid narrows the space in which an undetected failure can hide. Unit and Contract testing eliminate entire classes of structural defect deterministically. Evaluation testing converts "probably fine" into a measured, trended number. Regression testing catches drift before it reaches production. None of this adds up to a formal guarantee of correctness for a system whose core component (an LLM) is fundamentally probabilistic — and this document does not claim otherwise, consistent with `rag_design.md` §6.3's own framing of the architecture's hallucination-risk posture.

---

## 19. Testing Evolution

| Change | What Changes in the Test Suite | What Remains Unchanged (and Why) |
|---|---|---|
| New embedding model | Contract tests (§6.1) re-run against the new implementation; a full Retrieval-quality regression run (§14) is required since the embedding space itself shifted | Every Pipeline Stage's unit tests (§5) — none of them depend on which embedding model is configured, only on the `Embedding` domain model's shape |
| New vector database | Contract tests (§6.2) re-run; Retrieval-quality regression confirms behavioral equivalence | Retriever, Context Builder, and every downstream stage's unit tests — they consume `SearchResult[]`, never a vector-database-specific object |
| New LLM | Contract tests (§6.3) re-run; a full Generation- and Citation-quality regression run is required | Response Generator's and Citation Mapper's unit tests, which are expressed entirely in terms of `GeneratedResponse`'s finish-reason vocabulary, not any vendor's completion schema |
| New PDF parser | Unit tests for PDF Parser (§5.2) are re-run against the new library, specifically the fidelity-flag boundary cases | Every stage downstream of Text Preprocessor — they never see the PDF parsing library's own types, only `ExtractedDocument` |
| New provider (any of the three) | Same as the specific row above, generalized: Contract Testing (§6) exists specifically so this is a bounded, predictable cost, not a system-wide re-test | The Orchestrator test suite (§7) and every stage unit test outside the directly affected one |
| New orchestration feature | Component tests (§7) extend to cover the new sequencing/routing behavior; the affected Integration scenario(s) in §8 are updated or a new one is added if a genuinely new runtime path is introduced (§21 mirrors `sequence_diagrams.md` §12's own "do not add unnecessary diagrams" discipline for this case) | Every stage's own unit tests, and every other Integration scenario not touching the new feature |
| New language support | A new Evaluation corpus and golden question set localized to the new language (§10, §16); Text Preprocessor and Semantic Chunker unit tests extended for language-specific normalization/boundary behavior | The Provider Interfaces, Orchestrators, and every domain model definition — none of them are language-specific by design (`requirements.md` FE-003 anticipates this as a future enhancement, not a current-scope concern) |

**The general pattern:** because Provider Independence and Dependency Inversion (§2) mean every external or vendor-specific concern is isolated behind exactly three interfaces, the *cost* of any provider-level change is bounded to Contract Testing plus a quality regression run — never a rewrite of the Unit or Component test suites. This is the same architectural property `architecture.md` §14 cites as the reason for the custom-orchestration decision, now shown to pay off specifically in testing cost, not just implementation flexibility.

---

## 20. Related and Forthcoming Documents

- [requirements.md](./requirements.md) — the source of truth for every FR/NFR this strategy validates.
- [rag_design.md](./rag_design.md) — the source of truth for the evaluation metrics referenced in §11.
- [architecture.md](./architecture.md) — the source of truth for the layering and ownership boundaries §7–§9 validate.
- [interfaces.md](./interfaces.md) — the source of truth for every contract §5–§6 test against.
- [domain_models.md](./domain_models.md) — the source of truth for every object and invariant §9 validates.
- [sequence_diagrams.md](./sequence_diagrams.md) — the direct source for every §8 integration scenario.
- `app/specs/evaluation/benchmark_spec.md` (not yet created) — will supply the actual golden question set, expected citations, and scoring methodology this document deliberately left undefined (§10, §21).
- `deployment.md`, `tasks.md` (not yet created) — later in the SDD chain; `deployment.md` in particular will own the configuration-validation-failure startup sequence flagged as out of this document's per-request scope (§12), and the specific CI/environment tooling deliberately left unnamed here (§4).

Where this document and an upstream document disagree, the upstream document governs, per the SDD chain order above.

---

## 21. Open Testing Decisions

Carried forward or newly surfaced by this document, none resolved here:

1. **Citation precision acceptance threshold.** SRS AC-003 explicitly leaves this numeric bar unset. §11's Citation Correctness metric is measurable today; the pass/fail threshold it should be judged against is not yet defined, and this document does not invent one, per its own "avoid arbitrary numeric thresholds" constraint.
2. **Query Analyzer and Query Reformulator test scope.** Both remain contingent on upstream open decisions (`domain_models.md` §20 items 1–2) — §5.9/§5.10's *contract shape* is testable now; their *behavioral correctness* against specific inputs cannot be fully specified until the classification/reformulation mechanism is chosen.
3. **CI/environment tooling and pipeline topology.** §4 deliberately describes environment *purpose*, not a specific tool or pipeline product — that remains a `deployment.md` decision.
4. **Cost-per-query ceiling.** NFR-COST-005 requires one to exist and be monitorable but does not fix a starting value (`architecture.md` §17 note) — §11's Cost metrics are measurable without it, but the "flagged as over budget" behavior cannot be tested until a value is set.
5. **Streaming test coverage.** Per `domain_models.md` Open Decision 5 and `sequence_diagrams.md` §15 item 5, no test in this document exercises a streaming LLM call — the MVP reference path is blocking throughout. Streaming-specific test design is deferred until the streaming failure-semantics question itself is resolved.

---

*End of Document.*
