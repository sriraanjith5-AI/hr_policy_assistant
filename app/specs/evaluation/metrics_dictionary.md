# Metrics Dictionary

## Enterprise HR Policy Assistant — Authoritative Metric Definitions

| Field | Value |
|---|---|
| Document Type | Metrics Dictionary |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| Purpose | Provide the single authoritative definition, ownership, formula, collection point, and reporting usage for every metric named anywhere in this specification suite — so `testing.md`, `deployment.md`, `benchmark_spec.md`, and any future dashboard or alerting system all mean the same thing when they say "Precision@K" or "Citation Accuracy." This document defines metrics. It does not define datasets, thresholds, or target values. |
| Scope | Every metric referenced by `testing.md`, `deployment.md`, `evaluation/benchmark_spec.md`, `rag_design.md` §9, and `requirements.md`'s NFR categories. No new metric is introduced here that isn't already implied by an upstream document's stated need to measure something. |
| References | [requirements.md](../requirements.md) (SRS v1.0), [rag_design.md](../rag_design.md) (v1.1), [architecture.md](../architecture.md) (SAD v1.2), [interfaces.md](../interfaces.md) (v1.1), [domain_models.md](../domain_models.md) (v1.3), [sequence_diagrams.md](../sequence_diagrams.md) (v1.1), [testing.md](../testing.md) (v1.0), [deployment.md](../deployment.md) (v1.0), [evaluation/benchmark_spec.md](./benchmark_spec.md) (v1.0) |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## 1. Document Control

`metrics_dictionary.md` sits alongside `benchmark_spec.md`, outside the primary SDD chain, as a second evaluation-domain artifact serving a distinct purpose:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
                                          │
                                          ├──► evaluation/benchmark_spec.md
                                          └──► evaluation/metrics_dictionary.md
```

**The division of labor between the two evaluation documents is deliberate and non-overlapping:** `benchmark_spec.md` defines *how the system is evaluated* — the golden question schema, the scoring methodology, the regression-threshold-setting process, the human review workflow. This document defines *what every metric means* — its formula, its unit, its owner, its collection point — independent of any specific evaluation run. `benchmark_spec.md` computes metrics this document defines; it does not redefine them, and if the two ever appear to disagree, that is a defect in one of the two documents, not a legitimate difference of opinion — §17 exists to catch exactly that.

**Why this document exists as a distinct artifact, not folded into `testing.md` or `benchmark_spec.md`:** a metric used in Evaluation Testing, restated slightly differently in a deployment dashboard, restated slightly differently again in a regression report, is a silent source of confusion that compounds over the system's lifetime — two numbers that are supposed to mean the same thing but don't, discovered only when someone notices they disagree. This document exists to make that impossible by construction: every document in this suite that names a metric is expected to cite this one, never redefine it.

**This document defines metrics. It does not:**
- define benchmark datasets (that is `benchmark_spec.md`),
- define acceptance thresholds (that is SRS AC-003 and future ADR-governed decisions, per `testing.md` §21 and `benchmark_spec.md` §9), or
- invent target values, SLA percentages, or production goals of any kind.

Every metric below has a **formula**, not a **target** — the difference between "how is this measured" and "what value counts as good" is maintained strictly throughout.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Metrics Dictionary |

---

## 2. Metric Design Principles

| Principle | What It Means Here |
|---|---|
| **Every metric has exactly one definition.** | A metric name (e.g., "Citation Accuracy") appears in exactly one place in this document with exactly one formula. Every other document in this suite references that definition rather than restating it — §17 audits this. |
| **Metrics measure observable behaviour.** | Every metric below is computed from something the system actually produces or logs (a `Response`, a `SearchResult[]`, an `ExecutionMetadata` record) — never from an assumption about internal state that isn't externally observable. |
| **Metrics are technology independent.** | No formula below references a specific vector database's scoring function, a specific LLM vendor's token-counting convention, or a specific monitoring product's data model — consistent with `architecture.md` §4 and `interfaces.md` §2.1's provider-independence discipline, applied here to measurement. |
| **Metrics are implementation independent.** | A metric's definition does not change when a Provider Implementation is swapped (`architecture.md` ADR-003–005) — it is defined in terms of domain models (`domain_models.md`), which are themselves provider-independent by construction. |
| **Metrics are reproducible.** | Given the same system version, the same input, and the same configuration, a metric's value is computable again and arrives at the same (or, for LLM-involving metrics, a tolerance-band-consistent) result — this mirrors `testing.md` §4's "deterministic fixtures" and §18's honest treatment of LLM non-determinism. |
| **Metrics never encode business policy.** | A metric reports a fact (a rate, a count, a duration); it does not itself decide whether that fact is acceptable. "Citation Accuracy is 0.87" is a metric; "Citation Accuracy must be ≥ 0.90 to release" is a policy decision this document deliberately does not make (`testing.md` §21; `benchmark_spec.md` §9). |
| **Metrics are versionable.** | This document's own version history (§1) is the versioning mechanism for every metric it defines — a formula change is a version change here, never a silent edit (§16). |
| **Metrics should remain comparable across releases.** | A metric's formula is stable across system versions unless a version change explicitly deprecates and replaces it (§16) — this is what makes a trend line (§9, §10, §11) meaningful at all. |

---

## 3. Metric Classification

| Category | Purpose | Catalog |
|---|---|---|
| **Retrieval** | Measures how well the Retriever surfaces relevant evidence, independent of what the LLM later does with it | §5 |
| **Generation** | Measures the LLM's output — its content, size, outcome (grounded vs. declined), and failure behavior | §6 |
| **Citation** | Measures whether generated claims are correctly and completely traced back to evidence | §7 |
| **Evaluation** | Measures quality against the labeled golden set — the human-grounded, `benchmark_spec.md`-governed layer above the structural metrics in §5–§7 | §8 |
| **Performance** | Measures latency and throughput across every stage — the one category that owns *all* timing metrics, regardless of which stage they're measured on (§9's own note explains why) | §9 |
| **Reliability** | Measures failure, retry, and degradation behavior at the Provider Interface and Orchestrator boundary | §10 |
| **Cost** | Measures token usage and the cost it implies, at ingestion time and query time | §11 |
| **Deployment & Operational** | Measures the health, configuration integrity, and observability completeness of a running deployment | §12 |
| **Observability** *(cross-cutting, no dedicated catalog section)* | Not a separate metric catalog — every category above already produces its metrics *via* the observability mechanism `interfaces.md` §8 defines (correlation IDs, structured `ExecutionMetadata`). The metrics that measure the observability mechanism *itself* (e.g., correlation-ID coverage) are cataloged in §12, alongside Deployment metrics, since both concern the operational health of the running system rather than the quality of any one answer. |

---

## 4. Metric Definition Template

Every metric in §5–§12 is defined against this template. To keep the per-metric catalog tables scannable, **`Owner` is stated individually for every metric** (per this document's own quality requirement that every metric have exactly one architectural owner); **`Consumers`, `Reporting Frequency`, and `Notes` follow their category's stated default** (given once, in each catalog section's introduction) **unless a specific metric's row states an exception inline.**

| Field | Meaning |
|---|---|
| **Name** | The single canonical name for this metric, used identically in every other document in this suite. |
| **Purpose** | Why this metric exists — what question it answers. |
| **Definition** | A precise, conceptual description of what is being measured. |
| **Formula (conceptual only)** | How the metric's value is derived from observable inputs — never tied to a specific database query language or computation engine. |
| **Unit** | The measurement unit (percentage, ratio, count, tokens, milliseconds, etc.) — never a currency amount or an absolute target. |
| **Collection Point** | The specific runtime component and moment at which the underlying observation is captured (cross-referenced to `interfaces.md` §4–§5 and `sequence_diagrams.md`). |
| **Owner** | The single architectural component accountable for this metric being correct and available — always a Pipeline Stage, Orchestrator, Provider Interface, or the Evaluation Harness (`architecture.md` §2's ownership discipline) — **never** an external provider. |
| **Consumers** | Who reads this metric and for what purpose (category default, stated once per §5–§12 section). |
| **Related FR** | The Functional Requirement(s) this metric provides evidence for, where applicable. |
| **Related NFR** | The Non-Functional Requirement(s) this metric provides evidence for, where applicable. |
| **Related Benchmark Section** | The `benchmark_spec.md` section that operationalizes this metric's scoring methodology, where applicable. |
| **Related Runtime Component** | Folded into `Collection Point` above, to avoid a redundant column — the component and the moment are stated together. |
| **Reporting Frequency** | How often this metric is meaningfully recomputed (category default, stated once per §5–§12 section). |
| **Notes** | Anything that doesn't fit the above — most often, a cross-reference to a related metric this one should be interpreted alongside. |

---

## 5. Retrieval Metrics

**Owner (category default unless stated otherwise): Retriever.** **Consumers (category default): Evaluation Harness, regression reporting (`testing.md` §14).** **Reporting Frequency (category default): per evaluation run; not computed from unlabeled production traffic (§15).**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR/Benchmark |
|---|---|---|---|---|---|---|
| **Precision@K** | How much of what's retrieved is actually relevant | (Count of top-K `SearchResult[]` carrying a relevance label) ÷ K | Ratio | Retriever, upon `SearchResult[]` return | Retriever | FR-801–806; `benchmark_spec.md` §7 |
| **Recall@K** | How much of the relevant evidence was found at all | (Count of labeled-relevant chunks appearing in top-K) ÷ (total labeled-relevant chunks for the question) | Ratio | Retriever | Retriever | FR-802–806; `benchmark_spec.md` §7 |
| **Hit Rate@K** | Binary retrieval success per question | 1 if any labeled-relevant chunk appears in top-K, else 0; averaged across a question set | Ratio (averaged) | Retriever | Retriever | FR-801–806; `benchmark_spec.md` §7 |
| **Mean Reciprocal Rank (MRR)** | How highly the correct evidence ranks, not just whether it's present | Mean of 1 ÷ (rank of first labeled-relevant chunk), across a question set | Ratio | Retriever | Retriever | FR-801–806; `benchmark_spec.md` §7 |
| **NDCG (future-ready)** | A graded-relevance ranking quality measure, for use once relevance labels carry more than a binary relevant/not-relevant judgment | Standard normalized discounted cumulative gain over graded relevance labels | Ratio | Retriever | Retriever | Not currently used — `rag_design.md` §6.5's future relevance-grading stage would be the trigger for adopting graded labels this metric requires |
| **Average Similarity Score** | The mean relevance signal strength across a result set, independent of any relevance label | Mean of the similarity scores carried on `SearchResult[]` | Score (provider-relative, unitless) | Retriever | Retriever | FR-801–802 |
| **Retrieved Candidate Count** | How many candidates the Vector Store Provider Interface actually returned, before selection | Count of `SearchResult[]` items | Count | Retriever | Retriever | FR-801, FR-803 |
| **Selected Chunk Count** | How many candidates survived selection into evidence | Count of `RetrievedChunk[]` items in the `QueryContext` | Count | Context Builder | Context Builder | FR-901–903 |
| **Retrieved Token Count** | The evidence volume actually assembled for generation | Sum of token counts across a `QueryContext`'s `RetrievedChunk[]` | Tokens | Context Builder | Context Builder | FR-901, FR-904 |
| **Context Utilization** | How much of the configured context budget was actually used | Retrieved Token Count ÷ configured context token budget | Ratio | Context Builder | Context Builder | FR-904; NFR-COST-002 |
| **Duplicate Chunk Rate** | How much of the raw candidate set was near-duplicate overlap | (Candidates removed by deduplication) ÷ (Retrieved Candidate Count, pre-dedup) | Ratio | Retriever | Retriever | FR-806 |
| **Metadata Filter Effectiveness** | Whether a metadata predicate meaningfully narrows the candidate set, when applied | Change in Precision@K (or candidate count) between a filtered and unfiltered search for the same query | Ratio (delta) | Retriever | Retriever | FR-803 |

**No target value is stated for any row above** — a Precision@K of 0.6 is not "bad" or "good" in this document; it is a fact, interpretable only against a threshold this document deliberately does not set (§9 of `benchmark_spec.md`).

---

## 6. Generation Metrics

**Owner (category default): Response Generator.** **Consumers (category default): Evaluation Harness, Cost reporting (§11), regression reporting.** **Reporting Frequency (category default): per evaluation run for quality-shaped metrics; continuously for outcome-rate and failure metrics once in Production (§15).**

**Scope note:** this category owns content and outcome measures of generation — it deliberately does **not** include timing (Generation Latency lives in §9, per that section's stated "Performance owns all timing metrics" convention, applied consistently to avoid the exact duplication risk §2's "exactly one definition" principle exists to prevent).

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR/Benchmark |
|---|---|---|---|---|---|---|
| **Grounded Response Rate** | How often the system produces a cited answer rather than declining | (Count of `Response`s in grounded state) ÷ (total `Response`s) | Ratio | Query Orchestrator, upon `Response` return | Query Orchestrator | FR-1101–1106; `domain_models.md` §9 |
| **Declined Response Rate** | How often the system correctly declines | (Count of `Response`s in declined state) ÷ (total `Response`s) — the complement of Grounded Response Rate | Ratio | Query Orchestrator | Query Orchestrator | FR-805, FR-1106 |
| **Response Completeness** | Whether all relevant aspects present in the evidence are covered by the answer | Fraction of a golden question's expected claims (`benchmark_spec.md` §4) present in the `GeneratedResponse` | Ratio | Evaluation Harness (post-hoc, against `benchmark_spec.md` claim checklists) | Evaluation Harness | FR-1102–1103; `rag_design.md` §9.3; `benchmark_spec.md` §4 |
| **Prompt Size** | The input volume sent to the LLM | Token count of the rendered prompt (`domain_models.md` §8) | Tokens | Prompt Assembler | Prompt Assembler | FR-1001–1005; NFR-COST-001 |
| **Completion Size** | A lightweight, protocol-agnostic proxy for answer length, usable even when a full token count is unavailable (e.g., for a declined `Response`, which has no `GeneratedResponse` token usage in two of its three trigger cases — `domain_models.md` §9) | Character or word count of `Response.answer_text` | Characters or words | Query Orchestrator | Query Orchestrator | FR-1101 |
| **Generated Token Count** | The authoritative, billing-relevant output size — see §11 for its cost derivation | Token count recorded on `GeneratedResponse` (`interfaces.md` §5.3) | Tokens | Response Generator | Response Generator | FR-1101; NFR-COST-001 |
| **Streaming Time To First Token (future)** | Latency to the first delivered token, once streaming mode is adopted | Time from generation call start to first delta received | Milliseconds | Response Generator / LLM Provider Interface | Response Generator | Not currently applicable — MVP reference path is blocking (`domain_models.md` §8); NFR-PERF-002 |
| **Generation Failure Rate** | How often a generation call results in a genuine Technical Failure — **never** to be confused with Declined Response Rate, which counts a Business Outcome | (Count of Response Generator calls resulting in a normalized provider failure) ÷ (total Response Generator calls) | Ratio | Response Generator | Response Generator | FR-1104; `interfaces.md` §7; `sequence_diagrams.md` §10 |

---

## 7. Citation Metrics

**Owner (category default): Citation Mapper.** **Consumers (category default): Evaluation Harness, regression reporting.** **Reporting Frequency (category default): per evaluation run (structural sub-metrics may additionally be visible per-request in Production — see §15).**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR/Benchmark |
|---|---|---|---|---|---|---|
| **Citation Accuracy** | Whether attached citations point to the actual correct source — **the same metric `testing.md` §11 and `benchmark_spec.md` §5/§7 name "Citation Correctness"; see §17 for the naming-drift finding this document does not silently resolve** | Fraction of a `Response`'s `Citation[]` matching the golden question's expected citations, per `benchmark_spec.md` §5's per-citation (correct / extraneous / missing) scoring | Ratio | Evaluation Harness | Citation Mapper | FR-1201–1205; SRS AC-003; `benchmark_spec.md` §5, §7 |
| **Citation Coverage** | Whether claims are cited at all, independent of whether the citation is correct | Fraction of a `Response`'s claims carrying at least one `Citation` | Ratio | Citation Mapper | Citation Mapper | FR-1201–1204 |
| **Average Citations per Response** | The typical citation density of a grounded answer | Mean count of `Citation[]` entries across grounded `Response`s | Count (averaged) | Citation Mapper | Citation Mapper | FR-1201 |
| **Unsupported Claim Rate** | How often a present, cited-or-uncited claim is not actually backed by the evidence, per human/Faithfulness review | Fraction of claims judged unsupported in `benchmark_spec.md` §8's Faithfulness scoring | Ratio | Evaluation Harness | Evaluation Harness | `rag_design.md` §9.3; `benchmark_spec.md` §8 |
| **Unverified Statement Rate** | The system's own structural hallucination-risk signal — the same metric `domain_models.md` §9 and `rag_design.md` §7.3 already define; not redefined here | Fraction of grounded `Response`s with `unverified_statement_flag = true` | Ratio | Citation Mapper | Citation Mapper | FR-1203; `domain_models.md` §9; `benchmark_spec.md` §8 |
| **Citation Resolution Success** | The near-complement of Unverified Statement Rate, framed as a success rate rather than a risk rate — the two should always be read together (§13) | (Count of `CitationReference`s resolving to a `Citation`) ÷ (total `CitationReference`s parsed from a `GeneratedResponse`) | Ratio | Citation Mapper | Citation Mapper | FR-1203–1204; `domain_models.md` §19 (Runtime Invariant 3) |
| **Broken Citation Rate** | How often a previously-valid `Citation` now points to a `TextChunk`/`Document` reference that no longer exists (e.g., after deletion or re-ingestion) | Fraction of audited `Citation`s whose referenced `TextChunk`/`Document` is no longer resolvable at audit time | Ratio | Evaluation Harness (periodic audit, not per-request) | Evaluation Harness | SRS FR-106, FR-105/FR-702; `domain_models.md` §3 |

---

## 8. Evaluation Metrics

Reference: [benchmark_spec.md](./benchmark_spec.md). **Owner (category default): Evaluation Harness.** **Consumers (category default): HR Policy Owner (Ground Truth review, `testing.md` §10), Engineering (regression gating, `testing.md` §14).** **Reporting Frequency (category default): per evaluation run.**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR/Benchmark |
|---|---|---|---|---|---|---|
| **Answer Correctness** | Aggregate, per-question correctness against the golden set | Fraction of a question's `expected_answer_summary` claims (`benchmark_spec.md` §4) judged present and supported | Ratio | Evaluation Harness | Evaluation Harness | SRS BO-003; `benchmark_spec.md` §4 |
| **Claim Correctness** | The atomic unit Answer Correctness aggregates — per-claim, not per-question | Present / Absent / Contradicted judgment per claim (`benchmark_spec.md` §4) | Categorical | Evaluation Harness | Evaluation Harness | `benchmark_spec.md` §4 |
| **Human Review Score** | The human-reviewed cross-check against automated Faithfulness/Correctness scoring — not the golden-question-authoring review itself (`benchmark_spec.md` §10, step 2), but the ongoing periodic re-review of sampled system answers | Fraction of sampled answers a human reviewer judges correct, over a review batch | Ratio | Evaluation Harness (human-in-the-loop) | HR Policy Owner (or delegate) — the one metric in this document whose *owner* is a human role, not a system component, because the judgment itself is inherently human, per `testing.md` §10's Ground Truth Ownership principle | `testing.md` §10; `benchmark_spec.md` §10 |
| **Faithfulness** | Whether every claim is supported by retrieved evidence — the same metric `rag_design.md` §9.3 and `testing.md` §11 already name; not redefined here | Fraction of claims judged supported by `QueryContext`'s evidence, per `benchmark_spec.md` §8's claim-level scoring | Ratio | Evaluation Harness | Evaluation Harness | `rag_design.md` §9.3; `benchmark_spec.md` §8 |
| **Answer Relevance** | Whether the answer addresses the question asked, independent of factual correctness | Human or model-assisted judgment comparing `GeneratedResponse` against question intent | Ratio or categorical | Evaluation Harness | Evaluation Harness | `rag_design.md` §9.3 |
| **Evaluation Coverage** | Whether the golden set actually spans the policy domain, not just its size | Fraction of known `policy_category` values (or a diversity measure across `difficulty_tag`, `benchmark_spec.md` §3) represented in the active golden set | Ratio | Evaluation Harness | Evaluation Harness | `benchmark_spec.md` §3, §13 (item 4) |
| **Regression Stability** | Whether repeated evaluation runs against the *same* system version and *same* golden set produce consistent results — measures evaluation reproducibility itself, distinct from regression *detection* | Variance (or range) of a given metric's value across repeated runs under identical conditions | Statistical spread | Evaluation Harness | Evaluation Harness | `testing.md` §18 (LLM probabilistic behaviour) |
| **Evaluation Dataset Growth** | Trend of golden-set size and diversity over time | Count of active golden questions, and count of policy categories represented, at successive points in time | Count (trended) | Evaluation Harness | Evaluation Harness | `benchmark_spec.md` §11 |

---

## 9. Performance Metrics

**This section owns every timing/throughput metric in this document, regardless of which stage it measures — a deliberate structural decision so that, e.g., "Generation Latency" has exactly one home rather than a competing definition in §6.**

**Owner (per-row, since ownership genuinely varies by which stage is being timed).** **Consumers (category default): Deployment Monitoring (`deployment.md` §10).** **Reporting Frequency (category default): continuous in Production; per-run in Staging/Testing.**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR |
|---|---|---|---|---|---|---|
| **End-to-End Latency** | Full grounded-or-declined query path, Employee question to `Response` returned | Time from Query Orchestrator invocation to `Response` return | Milliseconds | Query Orchestrator | Query Orchestrator | NFR-PERF-001 |
| **Retrieval Latency** | Time for the Retriever's full embed-and-search sequence | Time from Retriever invocation to `SearchResult[]` return | Milliseconds | Retriever | Retriever | NFR-PERF-003 |
| **Embedding Latency** | The embedding-call-specific portion of retrieval time | Time from Embedding Provider Interface call to `Embedding` return | Milliseconds | Embedding Provider Interface | Embedding Provider Interface | NFR-PERF-003 (contributing factor) |
| **Generation Latency** | Time for the LLM call to complete | Time from Response Generator invocation to `GeneratedResponse` return | Milliseconds | Response Generator | Response Generator | NFR-PERF-001 (contributing factor) |
| **Citation Resolution Latency** | Time for Citation Mapper's resolution step | Time from Citation Mapper invocation to `Response` (grounded) return | Milliseconds | Citation Mapper | Citation Mapper | NFR-PERF-001 (contributing factor) |
| **Index Build Time** | Time to fully index one document's chunks into the Vector Database | Time from Vector Indexer invocation to ingestion result return | Milliseconds/seconds | Vector Indexer | Vector Indexer | NFR-PERF-004 (contributing factor) |
| **Document Ingestion Time** | Full ingestion path, one document | Time from Ingestion Orchestrator invocation (per document) to that document's ingestion result | Seconds | Ingestion Orchestrator | Ingestion Orchestrator | NFR-PERF-004 |
| **Throughput** | How many requests or ingestions complete per unit time | Count of completed `Response`s (or completed document ingestions) ÷ time window | Requests (or documents) per second/minute | Query Orchestrator / Ingestion Orchestrator | Query Orchestrator / Ingestion Orchestrator | NFR-SCALE-001–003 |
| **Concurrent Sessions** | How many `ConversationSession`s are simultaneously active | Count of `ConversationSession`s in the Active state at a point in time | Count | Session Manager | Session Manager | NFR-SCALE-001 |
| **Resource Utilization (conceptual only)** | Whether request-handling components hold bounded, not unbounded, state as load scales — a structural property, not a specific memory/CPU number | Qualitative/structural check that no component's per-request state grows without bound as concurrency increases (`architecture.md` §13) | Not applicable — structural, not numeric | Query Orchestrator (statelessness check) | Query Orchestrator | NFR-SCALE-001 |

---

## 10. Reliability Metrics

**Owner (category default): the Provider Implementation for provider-originated failures; the relevant Orchestrator for routing/isolation behavior.** **Consumers (category default): Deployment Monitoring.** **Reporting Frequency (category default): continuous in Production; per-injection-scenario in Testing (`testing.md` §12).**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR |
|---|---|---|---|---|---|---|
| **Retry Rate** | How often a Provider Interface call needed at least one retry | (Calls requiring ≥ 1 retry) ÷ (total calls), per provider | Ratio | Provider Implementation | Provider Implementation | NFR-REL-003 |
| **Failure Rate** | How often a call ends in a non-recoverable `ErrorContext` | (Calls ending non-recoverable) ÷ (total calls), per provider | Ratio | Provider Implementation | Provider Implementation | FR-1401–1403 |
| **Recovery Success** | How effective retrying actually is, distinct from how often it's attempted | (Retried calls that eventually succeeded) ÷ (total retried calls) | Ratio | Provider Implementation | Provider Implementation | NFR-REL-003 |
| **Provider Availability** | The success rate of a given provider's calls, tracked per provider (Embedding, Vector Store, LLM) | (Successful calls) ÷ (total calls), per provider, over a time window | Ratio | Provider Implementation | Provider Implementation | NFR-REL-001 |
| **Timeout Rate** | How often a call fails specifically due to timeout, as distinct from other failure categories | (Calls normalized to the `timeout` category) ÷ (total calls) | Ratio | Provider Implementation | Provider Implementation | NFR-REL-002 |
| **Graceful Degradation Rate** | How often the system degrades a capability rather than failing the whole request | (Requests degrading, e.g., proceeding with empty history) ÷ (total requests affected by that dependency's unavailability) | Ratio | Session Manager (for session degradation) or the relevant stage | Session Manager | `interfaces.md` §4.8; NFR-REL-002 |
| **Session Recovery Success** | How often a degraded session resumes normal operation once its dependency is reachable again | (Sessions returning to normal operation after degradation) ÷ (total degraded sessions) | Ratio | Session Manager | Session Manager | `deployment.md` §12, §16 |

---

## 11. Cost Metrics

**Owner (category default): Embedding Provider Interface / LLM Provider Interface (as the source of token-usage data), aggregated by the Query and Ingestion Orchestrators.** **Consumers (category default): Deployment Monitoring, Engineering cost review.** **Reporting Frequency (category default): continuous in Production, aggregated daily.**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR |
|---|---|---|---|---|---|---|
| **Prompt Tokens** | Input-side token cost driver | Token count of the rendered prompt sent to the LLM Provider Interface | Tokens | LLM Provider Interface | LLM Provider Interface | NFR-COST-001 |
| **Completion Tokens** | Output-side token cost driver | Token count of `GeneratedResponse` text (same underlying value as §6's Generated Token Count) | Tokens | LLM Provider Interface | LLM Provider Interface | NFR-COST-001 |
| **Embedding Tokens** | Ingestion- and retrieval-time embedding cost driver | Token count processed per Embedding Provider Interface call | Tokens | Embedding Provider Interface | Embedding Provider Interface | NFR-COST-001, NFR-COST-003 |
| **Token Cost** | The monetary cost implied by token usage — **the unit price itself is a provider/contract detail never stated in this document** | (Prompt + Completion + Embedding Tokens) × provider-specific unit price (external to this document) | Currency (unspecified) | Computed from Prompt/Completion/Embedding Tokens | Query Orchestrator / Ingestion Orchestrator (aggregation only — the provider owns the raw token counts) | NFR-COST-001 |
| **Cost Per Query** | Per-request cost attribution | Token Cost attributable to one grounded or declined `Response` | Currency (unspecified) | Query Orchestrator | Query Orchestrator | NFR-COST-005 |
| **Cost Per Document** | Per-ingestion cost attribution | Token Cost attributable to ingesting one `Document` (embedding cost only, in the current architecture) | Currency (unspecified) | Ingestion Orchestrator | Ingestion Orchestrator | NFR-COST-001 |
| **Average Daily Cost** | Trended aggregate spend, for the ceiling-monitoring intent NFR-COST-005 requires (without this document stating the ceiling itself) | Sum of Cost Per Query and Cost Per Document over a rolling day | Currency (unspecified) | Aggregated from Query/Ingestion Orchestrator records | Query Orchestrator / Ingestion Orchestrator | NFR-COST-005 |
| **Cache Savings** | Cost avoided by not re-embedding an unchanged chunk on re-ingestion | (Embedding Tokens a naive full re-embed would have cost) − (Embedding Tokens actually incurred) | Tokens (or the Token Cost equivalent) | Embedding Generator | Embedding Generator | NFR-COST-003 |
| **Re-Embedding Cost** | The cost specifically attributable to an intentional re-embedding after an embedding model change — distinct from Cache Savings, which is about *avoiding* unnecessary re-embedding | Embedding Tokens incurred specifically by a model-version-change-triggered re-embedding run | Tokens (or the Token Cost equivalent) | Embedding Generator | Embedding Generator | SRS FR-606; `domain_models.md` §5 |

---

## 12. Deployment & Operational Metrics

**Includes the Observability sub-catalog per §3's cross-cutting note.** **Owner (category default): the Core Engine's configuration/logging components, or deployment orchestration for deployment-lifecycle metrics.** **Consumers (category default): System Administrator, Deployment Monitoring (`deployment.md` §10).** **Reporting Frequency (category default): continuous in Production; per-deployment-attempt for lifecycle metrics.**

| Metric | Purpose | Formula (conceptual) | Unit | Collection Point | Owner | Related FR/NFR |
|---|---|---|---|---|---|---|
| **Deployment Success Rate** | How often a deployment attempt reaches Verification successfully | (Deployment attempts passing Verification) ÷ (total deployment attempts) | Ratio | Deployment orchestration (`deployment.md` §14) | Deployment orchestration | `deployment.md` §14 |
| **Configuration Validation Failures** | How often startup configuration validation fails | Count of startup validation failures per deployment attempt or time window | Count | Core Engine's configuration-loading component | Core Engine (configuration component) | FR-1603; `deployment.md` §6, §9 |
| **Health Check Status** | The current liveness/readiness state of a running instance — a status/gauge, not a rate | `live` / `not-live`; `ready` / `not-ready`, at a point in time | Categorical (status) | Core Engine | Core Engine | NFR-OBS-001; `deployment.md` §9 |
| **Readiness Success Rate** | The trended version of Health Check Status — how often readiness checks return "ready" over a window | (Readiness checks returning "ready") ÷ (total readiness checks) | Ratio | Core Engine | Core Engine | NFR-OBS-001 |
| **Startup Time** | How long an instance takes to become ready | Duration from process start to first "ready" readiness result | Seconds | Core Engine | Core Engine | `deployment.md` §9 |
| **Shutdown Time** | How long graceful shutdown takes | Duration from shutdown signal to completion of in-flight work | Seconds | Core Engine | Core Engine | `deployment.md` §9 |
| **Configuration Drift Detection** | Whether a running instance's effective configuration still matches its intended, versioned configuration | Count of detected discrepancies between effective and intended configuration, per audit | Count | Core Engine's configuration-loading component (diagnostic capability, SRS FR-1605) | Core Engine (configuration component) | FR-1605; `deployment.md` §6, §16 |
| **Index Synchronization Status** | Whether the Vector Database's indexed content is consistent with the Document Store's current documents | Structural comparison of `Document`/`TextChunk` lineage between the two stores, at audit time | Categorical (in-sync / drifted) | Vector Indexer (audit-time, not per-request) | Vector Indexer | `deployment.md` §13 |
| **Correlation ID Coverage** | Whether every logged event actually carries a valid correlation ID — the foundational observability-completeness check | (Logged events with a non-null, valid correlation ID) ÷ (total logged events) | Ratio | Every stage/orchestrator/provider interface (aggregated) | Core Engine's logging component | `interfaces.md` §8; NFR-OBS-003 |
| **Log Completeness Rate** | Whether every call produced its required `ExecutionMetadata` record | (Calls with a corresponding `ExecutionMetadata` record) ÷ (total calls) | Ratio | Every stage/orchestrator/provider interface (aggregated) | Core Engine's logging component | `interfaces.md` §8; FR-1501–1505 |

---

## 13. Metric Relationships

Conceptual relationships only — no formulas or proofs. Each of these exists to help a future reader interpret a metric *in context*, since no metric in this document should be read in isolation from the ones it trades off against.

- **Higher Recall may reduce Precision.** Casting a wider retrieval net (a larger candidate set, a lower similarity threshold) tends to catch more of the relevant evidence but also more irrelevant noise alongside it — the two metrics (§5) are in tension, not independently maximizable.
- **Larger Context may increase Cost and Latency.** A higher Context Utilization (§5) means more `RetrievedChunk[]` tokens flow into the prompt, which increases Prompt Tokens and Token Cost (§11) and typically increases Generation Latency (§9), since the LLM has more input to process.
- **Higher top-K affects Latency, Cost, and potentially Precision.** Increasing the configured top-K (`rag_design.md` §6.4) tends to increase Retrieval Latency (more candidates to score/re-rank), increase downstream Cost (more candidates available to include in context), and can decrease Precision@K (a larger K makes it statistically easier for irrelevant chunks to occupy some of the top-K positions).
- **Citation Accuracy depends on Retrieval Quality.** No amount of citation-resolution logic (§7) can produce a correct citation if the underlying retrieval (§5) never surfaced the correct chunk in the first place — a Citation Accuracy regression should always prompt checking Precision@K/Recall@K before assuming the defect is in Citation Mapper.
- **Grounded Response Rate depends on Context Quality.** A low Average Similarity Score or low Context Utilization (§5) increases the likelihood of the empty-retrieval or LLM-decline short-circuits (`sequence_diagrams.md` §3.2/§3.3), which lowers Grounded Response Rate (§6) — this is by design (grounding discipline over fabrication), not a defect, but the relationship is real and should inform interpretation.
- **Retry Rate increases End-to-End Latency.** Every retry (§10) adds its own attempt's latency to the overall request — a rising Retry Rate should be expected to correlate with a rising End-to-End Latency (§9), and the two should be reviewed together when either regresses.
- **Unverified Statement Rate and Citation Resolution Success move inversely.** They are near-complements of the same underlying resolution process (§7) — a change in one without a corresponding inverse change in the other is itself worth investigating, not just tracking each in isolation.
- **Provider Availability and Failure Rate move inversely.** Definitionally related (§10) — tracked separately because Failure Rate distinguishes *why* a call failed (recoverable vs. not) in a way a single Availability number does not.
- **Evaluation Coverage affects how much Regression Stability can be trusted.** A narrow or low-diversity golden set (§8) can show artificially high Regression Stability simply because it doesn't exercise enough variation to reveal instability that a broader set would surface — a high Regression Stability reading should always be read alongside Evaluation Coverage, not celebrated on its own.

---

## 14. Metric Ownership

| Metric Category | Primary Owner | Collected By | Consumed By | Referenced In |
|---|---|---|---|---|
| Retrieval | Retriever | Retriever, Context Builder | Evaluation Harness, regression reporting | `rag_design.md` §9, `testing.md` §11, `benchmark_spec.md` §7 |
| Generation | Response Generator | Response Generator, Query Orchestrator | Evaluation Harness, Cost reporting | `rag_design.md` §9, `testing.md` §11 |
| Citation | Citation Mapper | Citation Mapper | Evaluation Harness | `rag_design.md` §9, `testing.md` §11, `benchmark_spec.md` §5, §7–§8 |
| Evaluation | Evaluation Harness | Evaluation Harness (with HR Policy Owner for Human Review Score) | HR Policy Owner, Engineering | `benchmark_spec.md`, `testing.md` §10–§11 |
| Performance | Distributed — each stage/orchestrator owns its own latency measurement (§9's per-row Owner column) | Every stage, orchestrator, and provider interface | Deployment Monitoring | `requirements.md` NFR-PERF, `sequence_diagrams.md` §11, `deployment.md` §10 |
| Reliability | Provider Implementations (failure/retry) and Orchestrators (routing, isolation) | Provider Implementations, Orchestrators | Deployment Monitoring | `interfaces.md` §7, `sequence_diagrams.md` §5.1/§9, `deployment.md` §12 |
| Cost | Embedding/LLM Provider Interfaces (raw token counts), aggregated by the Orchestrators | Provider Interfaces, Orchestrators | Deployment Monitoring, Engineering | `requirements.md` NFR-COST, `testing.md` §11 |
| Deployment & Operational (incl. Observability) | Core Engine's configuration/logging components; deployment orchestration for lifecycle metrics | Core Engine, deployment orchestration | System Administrator, Deployment Monitoring | `deployment.md` §6–§10, §12–§14 |

**No row above assigns ownership to an external provider** (the Embedding Service, the Vector Database, or the LLM Service) — every owner is a component this system's own architecture defines (`architecture.md` §2), consistent with `domain_models.md` §2's Business Ownership principle applied to measurement rather than to domain meaning.

---

## 15. Metric Lifecycle

| Stage | What's Meaningful Here |
|---|---|
| **Development** | No aggregate metric is meaningful yet — only individual Unit test pass/fail (`testing.md` §5), which this document does not treat as a metric in its own right. |
| **Testing (CI)** | Reliability metrics (§10) are exercised via deliberate failure injection (`testing.md` §12), producing *simulated* rather than *observed* rates — useful for confirming handling logic, not yet a trend. |
| **Evaluation** | Retrieval, Generation (quality-shaped rows), Citation, and Evaluation category metrics (§5, §6's quality rows, §7, §8) are computed against `benchmark_spec.md`'s golden set. **These are offline-only** — they require ground truth (expected answers, expected citations, relevance labels) that does not exist for live, unlabeled production traffic. |
| **Production** | Performance (§9), Reliability (§10), Cost (§11), and Deployment & Operational (§12) metrics are **runtime-only**, continuously collected from real traffic — none of them require ground truth. Generation's outcome-rate metrics (Grounded/Declined Response Rate, Generation Failure Rate — §6) are also runtime-observable, since they require no labeled comparison, only the `Response`'s own recorded state. |
| **Historical Analysis** | Any metric can be trended over time once repeatedly collected — Average Daily Cost (§11), Evaluation Dataset Growth (§8), and Regression Stability (§8) are specifically *designed* as trend metrics, not point-in-time ones. |
| **Regression** | Retrieval, Generation (quality rows), Citation, and Evaluation metrics are re-computed against the Regression Dataset (`benchmark_spec.md` §11) whenever `testing.md` §14's triggers fire — this is the Evaluation-stage computation, run on a change-triggered cadence rather than a fixed schedule. |
| **Monitoring** | Performance, Reliability, Cost, and Deployment & Operational metrics are the ones a Production monitoring capability continuously observes — this document does not name that capability's specific technology (§18). |

**A metric belonging to §5–§8 (Retrieval, quality-shaped Generation rows, Citation, Evaluation) that has no ground-truth-free path to computation is Evaluation-only, not runtime-only.** A metric belonging to §9–§12 is runtime-only by nature, since it requires no labeled comparison at all. This distinction is the single most important fact this section establishes, and future dashboards or alerting should be built respecting it — attempting to compute Precision@K from unlabeled live traffic without a relevance label source would silently produce a meaningless number, not a real metric.

---

## 16. Metric Evolution

| Rule | Statement |
|---|---|
| **Backward compatibility** | Adding a new metric to this document never changes an existing metric's name, formula, or unit. |
| **Versioning** | A metric's formula is versioned via this document's own version history (§1) — a formula change is recorded as a dated change entry, never a silent in-place edit. |
| **Deprecation** | A metric no longer collected is marked *deprecated* in this document (with the version and reason), not deleted — historical dashboards or reports referencing it by name remain interpretable. |
| **Replacement** | A deprecated metric's replacement, if one exists, is explicitly cross-referenced (old name → new name, with the reason for the change) — a silent rename is never acceptable under this document's "exactly one definition" principle (§2). |
| **Historical comparability** | A formula change to an existing (non-deprecated) metric is itself treated as a discontinuity — any trend line or regression comparison spanning the change point must flag it, not silently plot pre- and post-change values as if they were the same measurement. |

---

## 17. Cross-Document Validation

Every metric name used in this document was checked against every prior specification that names a metric, to confirm this document is consolidating existing definitions, not silently introducing competing ones.

| Check | Result |
|---|---|
| Precision@K, Recall@K, Hit Rate@K, MRR (`rag_design.md` §9.2, `testing.md` §11, `benchmark_spec.md` §7) | **Consistent.** Identical formulas across all four documents; this document adds Unit/Collection Point/Owner detail, not a redefinition. |
| Faithfulness, Answer Relevance (`rag_design.md` §9.3, `testing.md` §11, `benchmark_spec.md` §8) | **Consistent.** |
| Unverified Statement Rate / `unverified_statement_flag` rate (`domain_models.md` §9, `rag_design.md` §7.3, `testing.md` §11, `benchmark_spec.md` §8) | **Consistent.** |
| Completeness (`testing.md` §11, `rag_design.md` §9.3) vs. **Response Completeness** (this document's requested outline, §6) | **Minor naming variation found, not silently resolved.** This document uses "Response Completeness" per its own requested structure; `testing.md` and `rag_design.md` use "Completeness." Same metric, same formula — the name should be unified in a future revision of one document or the other. |
| Citation Correctness (`testing.md` §11, `benchmark_spec.md` §5, §7) vs. **Citation Accuracy** (this document's requested outline, §7) | **Naming inconsistency found, not silently resolved.** This is the more significant of the two naming drifts found in this review: two different names for the identical formula and identical scoring methodology (`benchmark_spec.md` §5). This document's own §2 principle ("every metric has exactly one definition") is *substantively* satisfied — the formula truly is defined once, here — but the *name* is not yet unified across the three documents that discuss it. Flagged for reconciliation, not resolved here, per this document's own instruction not to silently redefine or silently rename. |
| Cost-per-query, token usage metrics (`requirements.md` NFR-COST-001–005, `testing.md` §11) | **Consistent.** No competing formula found; this document is the first to state the Token Cost formula explicitly (prior documents named the metric without formalizing its derivation). |
| Correlation ID / `ExecutionMetadata` fields (`interfaces.md` §8, `deployment.md` §10) | **Consistent.** This document's Correlation ID Coverage and Log Completeness Rate (§12) are new *aggregate* metrics computed *from* those existing fields — they do not redefine the fields themselves. |

---

## 18. Open Metric Decisions

Carried forward only — no threshold, acceptance percentage, production target, or SLA value is introduced here; those remain out of this document's scope by design (§1).

1. **Citation Accuracy / Citation Correctness naming reconciliation** (§17) — a documentation-consistency item, newly surfaced by this document, not yet resolved in either direction.
2. **Response Completeness / Completeness naming reconciliation** (§17) — the same kind of finding, lower severity.
3. **Citation precision acceptance threshold** (SRS AC-003; `testing.md` §21; `benchmark_spec.md` §9) — this document defines the Citation Accuracy metric precisely; the value that would count as acceptable remains unset, by design, upstream of this document.
4. **Cost-per-query ceiling** (NFR-COST-005; `architecture.md` §17) — this document defines Cost Per Query and Average Daily Cost precisely; the ceiling value itself remains unset.
5. **Minimum golden-set size / diversity for a statistically meaningful Evaluation Coverage reading** (`benchmark_spec.md` §13, item 4) — affects how Evaluation Coverage and Regression Stability (§8, §13) should be interpreted once real data exists, not resolved here.
6. **Monitoring/alerting technology** (`deployment.md` §19, item 7 — "CI/environment tooling") — this document defines every metric a future monitoring capability would need to compute; it deliberately does not name that capability's technology, per its own technology-neutrality constraint.
7. **Whether periodic human-reviewed production sampling (feeding Human Review Score, §8, §15) is adopted as an ongoing operational practice** — newly surfaced by this document's Metric Lifecycle analysis (§15); no upstream document commits to this practice, only to the golden-question-authoring review `benchmark_spec.md` §10 already requires.

---

## 19. Related Documents

Every specification document that consumes a metric this document defines:

- [requirements.md](../requirements.md) — every NFR (Performance, Reliability, Cost, Observability, Security) this document's metrics provide evidence for.
- [rag_design.md](../rag_design.md) §9 — the original source of the Retrieval/Generation/Citation quality metric *names*, now given their single authoritative formula here.
- [architecture.md](../architecture.md) — the ownership discipline (§2's "never an external provider") this document's §14 applies to metrics specifically.
- [interfaces.md](../interfaces.md) §8 — the `ExecutionMetadata` fields every Performance, Reliability, and Deployment & Operational metric in this document is ultimately derived from.
- [domain_models.md](../domain_models.md) — the domain models (`Response`, `GeneratedResponse`, `Citation`, `CitationReference`) this document's formulas are expressed in terms of.
- [sequence_diagrams.md](../sequence_diagrams.md) §11 — the performance observation points this document's §9 formalizes into named metrics.
- [testing.md](../testing.md) §11 — the metric categories and consumers this document's §5–§12 give a single authoritative formula to.
- [deployment.md](../deployment.md) §10, §12, §16 — the operational metrics this document's §12 formalizes, and the consumer (Deployment Monitoring) this document's §14 cites throughout.
- [evaluation/benchmark_spec.md](./benchmark_spec.md) — the scoring *methodology* for every Evaluation- and Citation-category metric this document defines the *formula* for; the two documents are companions, not competitors, per §1's stated division of labor.

Where this document and an upstream document disagree on a metric's *formula*, that is a defect to correct in this document (since this is the authoritative source, per §1) — where they disagree only on a metric's *name* (§17), that is a documentation-consistency item, carried forward in §18, not resolved by unilaterally renaming anything here.

---

*End of Document.*
