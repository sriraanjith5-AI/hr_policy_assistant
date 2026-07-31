# Evaluation Benchmark Specification

## Enterprise HR Policy Assistant — Golden Question Set Schema, Scoring Methodology, and Governance

| Field | Value |
|---|---|
| Document Type | Evaluation Benchmark Specification |
| Project Name | Enterprise HR Policy Assistant |
| Version | 1.0 |
| Status | Draft — Pending Review |
| Purpose | Define the schema, scoring methodology, and governance process for the labeled question set `testing.md` §10 requires but deliberately does not construct. This document defines *how* the benchmark is built and scored; it is not the benchmark itself. |
| Scope | Golden question schema, expected-answer and expected-citation methodology, relevance labeling, Precision/Recall/hallucination scoring formulas, regression threshold methodology, and the human review workflow that governs all of the above. |
| Related Specifications | [testing.md](../testing.md) (v1.0) — this document is a direct extension of `testing.md` §10 ("RAG Evaluation Strategy") and §11 ("Evaluation Metrics"); [rag_design.md](../rag_design.md) §9 (Evaluation Approach); [requirements.md](../requirements.md) SRS AC-003, BO-003 |
| Prepared By | Principal AI Solution Architect |
| Date | 2026-07-29 |

---

## 1. Document Control

This document sits **outside** the main SDD chain — it is an evaluation-domain artifact, not a system-design artifact:

```
requirements.md → rag_design.md → architecture.md → interfaces.md → domain_models.md →
sequence_diagrams.md → testing.md → deployment.md → tasks.md → implementation
                                          │
                                          └──► app/specs/evaluation/benchmark_spec.md
```

**Why this document exists as a deliberate deviation from the standard SDD chain:** every document up through `testing.md` defines the system and how it will be validated *structurally* — that a stage transforms its input correctly, that an invariant holds, that a failure is classified correctly. None of them can define what a *correct* HR policy answer actually is — that is domain knowledge, not system design, and `testing.md` §10 explicitly assigns its ownership to the HR Policy Owner, not to engineering. This document exists to give that ownership a concrete artifact to own, separate from the engineering specification chain it depends on but must not be dictated by.

**This document defines schema and methodology. It does not populate the benchmark.** No golden question, expected answer, expected citation, or relevance label in this document should be read as final, production-ready evaluation content — real population requires the actual HR policy corpus and the actual HR Policy Owner's sign-off (§9), neither of which exists at specification time. Where an example appears below, it is explicitly marked **[ILLUSTRATIVE]** and exists only to prove the schema is usable, not to seed the real dataset.

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-29 | Initial Evaluation Benchmark Specification |

---

## 2. Relationship to `testing.md`

| `testing.md` Established | This Document Adds |
|---|---|
| §10 — Dataset Philosophy, Ground Truth Ownership, Golden Question Set concept, Regression Dataset concept, Dataset Versioning principle, Human Review Process principle, Metric Evolution principle | The concrete **schema** each golden question must follow, and the **process** by which it is authored, reviewed, and versioned in practice |
| §11 — Precision@K, Recall@K, Hit Rate@K, MRR, Faithfulness, Answer Relevance, Completeness, Citation Correctness, Unverified-Statement Rate (metric *names* and *purposes*) | The exact **computation methodology** for each — what a relevance label is, how it is assigned, and how the metric is derived from it |
| §14 — Regression testing philosophy (what triggers a re-run) | The **methodology for setting** a regression threshold — not a threshold value, since none is yet defined (SRS AC-003; `testing.md` §21 item 1) |
| §21 — Open Decisions, explicitly including "citation precision acceptance threshold... this document does not invent one" | This document also does not invent one — see §8 |

This document does not redefine any metric `testing.md` §11 already named — it operationalizes them.

---

## 3. Golden Question Schema

Every golden question is a single record with the following fields. No field below is a database column definition — this is the conceptual shape a golden question must have, regardless of what format (spreadsheet, structured file, database row) eventually stores it.

| Field | Meaning |
|---|---|
| `question_id` | A stable, unique identifier — referenced by every regression report and evaluation run so a specific question's history is traceable over time |
| `question_text` | The exact natural-language question, phrased as an employee would plausibly ask it |
| `policy_category` | Which HR policy domain the question belongs to (e.g., leave, benefits, conduct, reimbursement) — enables category-level regression reporting, not just an aggregate score |
| `expected_behavior` | Either `grounded` (the system should produce a cited answer) or `declined` (the system should legitimately decline — no relevant policy exists, or the question is genuinely unsupported/out-of-domain) |
| `expected_answer_summary` | See §4 — a checklist of expected key claims, not a literal expected sentence |
| `expected_citations` | See §5 — the specific document/section/page(s) a correct grounded answer should cite |
| `relevance_labels` | See §6 — the full set of chunks in the evaluation corpus judged relevant to this question, independent of whether the system currently retrieves them |
| `difficulty_tag` | `straightforward` / `multi-condition` (the answer depends on more than one eligibility criterion) / `ambiguous` (the source policy itself is unclear or conflicting) / `adversarial` (deliberately phrased to test grounding discipline, e.g., a leading question implying a policy that doesn't exist) |
| `conversation_context` | Empty for a single-turn question; for a multi-turn question, the prior turn(s) it depends on (`testing.md` §8.7, §11 "Follow-up Resolution Accuracy") |
| `source_version` | Which version of the source `Document`(s) this question's expected answer/citations were authored against — required because a policy update can legitimately change the correct answer (`domain_models.md` §3, `Document` version lifecycle) |
| `authored_by` / `reviewed_by` | The Ground Truth Owner (or delegate) who authored the expected answer/citations, and who performed the review gate (§9) — never the same person for both, per §9's conflict-of-interest principle |
| `date_added` | When the question entered the golden set — supports trend analysis of dataset growth over time (`testing.md` §10, "Metric Evolution") |

---

## 4. Expected Answers — Methodology

**An expected answer is a checklist of key claims, never a literal expected sentence.** LLM output phrasing varies run to run even when correct (`testing.md` §18, "LLM probabilistic behaviour") — scoring against exact text would produce false negatives on correct answers and is explicitly rejected as a methodology here.

Each `expected_answer_summary` is a small, ordered list of atomic factual claims the correct answer must contain, for example (schema illustration, not a real claim list):

```
[
  "States the eligibility condition (e.g., minimum tenure requirement, if one exists)",
  "States the duration/entitlement",
  "States whether the benefit applies to the scenario asked about",
]
```

**Scoring against this list is claim-coverage, not string-match:** for each claim, a reviewer (human, or a calibrated model-assisted first pass subject to human confirmation — §9) marks it present, absent, or contradicted in the system's actual `GeneratedResponse` text. This directly operationalizes `testing.md` §11's Completeness metric (fraction of claims present) and contributes to Answer Relevance (whether the claims present actually address what was asked, not just whether they're technically true).

**Multi-condition questions** (`difficulty_tag = multi-condition`) are the primary target of this methodology — a single pass/fail judgment on "is the answer correct" would hide a partial-completeness failure (e.g., the system states the duration but omits an eligibility condition), which claim-level scoring surfaces explicitly.

---

## 5. Expected Citations — Methodology

Each `expected_citations` entry is a set of `{document, section, page_range}` references — the same shape as the `Citation` domain model (`domain_models.md` §9), deliberately, so a system-produced `Citation` can be compared to an expected one field-by-field rather than through free-text matching.

**A question may have more than one expected citation** when its correct answer genuinely draws on more than one section (e.g., an eligibility rule in one section and a duration rule in another) — `Citation Correctness` (`testing.md` §11) is then scored per-citation, not as a single pass/fail for the whole answer: each system-produced `Citation` is checked against the expected set (correct / extraneous / missing), giving three distinct failure signals instead of one blended one.

**A `declined`-behavior question has an empty expected-citations set by definition** — its scoring target is that the system's `Response` also has an empty `Citation[]` (per `domain_models.md` §9's declined-state guarantee), not that it matches a citation it should never have produced.

**Citation correctness is graded strictly against the section/page granularity the source `ChunkMetadata` actually records** (`domain_models.md` §4) — a citation that names the correct document but the wrong section is scored as incorrect, not "close enough," because the system's own citation model makes no allowance for partial correctness at that granularity (`interfaces.md` §5, Citation Mapper's resolve-exactly-or-flag-unverified design).

---

## 6. Relevance Labels — Methodology

A relevance label answers one question per (golden question, corpus chunk) pair: **is this chunk relevant to answering this question, independent of whether the system currently retrieves it?**

- Labels are assigned by the Ground Truth Owner (or delegate) reading the full evaluation corpus for the question's policy category — not by inspecting what the Retriever happens to return. **Labeling from the system's own retrieval output would make Precision/Recall circular** (the system would be graded against its own opinion of relevance) — this is the single most important discipline in this section.
- A chunk can be labeled relevant to more than one golden question, and a golden question can have more than one relevant chunk (this is expected and required for `expected_citations` entries spanning multiple sections, §5).
- Labels are versioned alongside the golden question's `source_version` field (§3) — a policy update that changes section boundaries requires re-labeling, not an assumption that old labels still apply.

This label set is what makes Precision@K and Recall@K (§7) computable at all — without it, "relevant" has no defined meaning independent of the system being measured.

---

## 7. Precision/Recall Methodology

Formal computation, applied per golden question and then aggregated across the golden set (or a category subset, per `policy_category`):

| Metric | Computation |
|---|---|
| **Precision@K** | (Number of the top-K `SearchResult[]` chunks that carry a relevance label for this question) ÷ K |
| **Recall@K** | (Number of this question's labeled-relevant chunks that appear anywhere in the top-K `SearchResult[]`) ÷ (total number of labeled-relevant chunks for this question) |
| **Hit Rate@K** | 1 if at least one labeled-relevant chunk appears in the top-K, else 0 — averaged across the golden set for an aggregate rate |
| **Mean Reciprocal Rank (MRR)** | For each question, 1 ÷ (rank position of the first labeled-relevant chunk in the ranked `SearchResult[]`, or 0 if none appears in the retrieved set) — averaged across the golden set |

**A `declined`-behavior question is excluded from Precision/Recall aggregation** — by definition it has no labeled-relevant chunks (§6), so Recall's denominator would be zero and the metric is undefined for that question, not zero. `declined`-behavior questions instead contribute to a separate aggregate: **Correct-Decline Rate** — the fraction of `declined`-expected questions for which the system's actual retrieval was empty or below threshold, i.e., correctly triggered the Not Found Path (`sequence_diagrams.md` §3.2) rather than surfacing an unrelated chunk as if it were relevant.

**K is fixed per evaluation run and reported alongside every metric** — Precision@10 and Precision@3 are not comparable numbers, and a regression report (§8) must always state which K was used.

---

## 8. Hallucination Scoring

**Hallucination risk is tracked as a rate, not eliminated — consistent with `rag_design.md` §6.3 and `testing.md` §18's explicit framing.** This methodology exists to make that rate measurable and trended, not to claim a hallucination-free system is achievable or being claimed.

Two complementary signals, scored separately and never blended into one number:

1. **Unverified-Statement Rate** — the fraction of `grounded`-behavior golden questions for which the system's `Response.unverified_statement_flag` is `true`. This is a **structural** signal, produced by the system itself (`domain_models.md` §9) — every `CitationReference` that failed to resolve is already flagged before a human ever reviews the answer.
2. **Faithfulness Score** — a claim-level judgment (§4's claim checklist, extended): for each claim marked *present* in the `GeneratedResponse`, a reviewer additionally marks whether it is *supported* by the evidence in `QueryContext` (per `rag_design.md` §9.3) or *unsupported* despite being present. A claim can be present, relevant, and still unsupported — this is the case the structural `unverified_statement_flag` is designed to catch automatically, and Faithfulness Score is the human-reviewed cross-check that confirms the automatic flag is actually catching what it should.

**A divergence between the two signals is itself a finding, not noise:** a high Unverified-Statement Rate with a high Faithfulness Score suggests the flag is over-triggering (a Citation Mapper resolution-logic issue, not a grounding issue); a low Unverified-Statement Rate with a low Faithfulness Score suggests the flag is under-triggering — a claim is unsupported but its `CitationReference` still resolved to *something*, which is a more serious defect requiring immediate investigation, since it means the structural control (`domain_models.md` Runtime Invariant 3) is not catching a case it should.

**Adversarial questions** (`difficulty_tag = adversarial`, §3) are specifically weighted in hallucination-risk reporting — a leading question implying a nonexistent policy is the highest-value test case for confirming grounding discipline holds under pressure, not just under neutral phrasing.

---

## 9. Regression Threshold Methodology

**No numeric threshold is defined in this document.** SRS AC-003 leaves the citation-precision acceptance bar unset, and `testing.md` §21 explicitly declines to invent one — this document maintains that same discipline, for the same reason: a threshold set without a real baseline measurement is not evidence-based, it is a guess wearing the shape of a requirement.

**The methodology for setting one, once real measurement exists:**

1. Run the full metric set (§7, §8, and `testing.md` §11's Generation/Conversation metrics) against the initial golden set once a real corpus and a working pipeline exist, to establish a **baseline** measurement — not a target, a starting point.
2. The HR Policy Owner (or delegate) and Engineering jointly set an initial **acceptance threshold** informed by that baseline — e.g., "no worse than the baseline, minus an agreed tolerance band" — rather than an arbitrary a priori number. This is the point at which SRS AC-003's placeholder gets its real value, and that value should be written back into `requirements.md` as a formal update, not left to live only in this document.
3. **Regression thresholds** (the bar a *change* must clear, as distinct from the *acceptance* bar a first release must clear) are set relative to the then-current baseline at the time of that specific change, per `testing.md` §14's triggers — a chunking change is compared against the pre-change measurement, not against the original AC-003 baseline, since some drift from the original baseline may already be accepted/known.
4. Every threshold — acceptance or regression — is reviewed and re-approved by the Ground Truth Owner on a defined cadence (e.g., alongside major corpus updates), because a threshold that made sense against last year's policy corpus may not make sense against this year's.

**This section defines the process this document commits to following. It is intentionally silent on a value.**

---

## 10. Human Review Workflow

Extends `testing.md` §10's Human Review Process into a concrete, repeatable sequence:

1. **Authoring.** A candidate golden question, expected-answer claim list, and expected-citation set are drafted — by an engineer familiarizing themselves with the corpus, or by the Ground Truth Owner directly. The drafter is recorded in `authored_by` (§3).
2. **Domain review.** The HR Policy Owner (or an explicitly delegated reviewer with equivalent domain authority — never the drafter, per the conflict-of-interest principle already established in `testing.md` §10) confirms the expected answer and citations are factually correct against the actual source policy, not against what the system currently produces. Recorded in `reviewed_by`.
3. **Relevance labeling.** Independently (can be the same reviewer as step 2, but is a distinct activity), the full corpus is reviewed for chunks relevant to this question, per §6's discipline of labeling without consulting system output.
4. **Acceptance into the golden set.** Only after steps 2 and 3 are both complete does a question become part of the active golden set used in evaluation runs (`testing.md` §8.8, §10).
5. **Ongoing re-review trigger.** Any change to `source_version` (a policy update) automatically flags every golden question referencing that document for re-review — an expected answer or citation set is never assumed to remain correct across a policy version change.
6. **Escalation.** A disagreement between the drafter/engineering and the domain reviewer about what constitutes a "correct" answer is resolved by the domain reviewer's judgment, not by consensus or by matching the system's current output — per `testing.md` §10's explicit prohibition on "fixing" a question by changing its expected answer to match what the system currently gets wrong.

---

## 11. Dataset Versioning & Governance

- The golden question set is versioned as a whole, independent of the system's own version (`testing.md` §10) — an evaluation run's report always states both the system version under test and the golden-set version it was measured against.
- Adding a question, changing an existing question's expected answer/citations, or re-labeling relevance are each individually recorded changes (who, when, why) — not silent edits to a shared file with no change history.
- The Regression Dataset (`testing.md` §10) is a governed subset or superset of the golden set, grown specifically from cases a prior system version got right — additions to it follow the same authoring/review workflow (§10) as the primary golden set, since a wrong "locked-in" regression case is worse than no regression case at all.

---

## 12. Illustrative Seed Examples — **[ILLUSTRATIVE, NOT PRODUCTION DATA]**

The following exist only to demonstrate that the schema in §3–§6 is usable end to end. They reference a generic, hypothetical "Leave Policy" document already used as an example throughout this SDD chain (`requirements.md`, `rag_design.md`) — no real corpus backs them, no real HR Policy Owner has reviewed them, and they must not be used as actual evaluation content without going through §10's full workflow first.

**Example 1 — `grounded`, `straightforward`**

| Field | Value |
|---|---|
| `question_id` | `SEED-001` |
| `question_text` | "What is maternity leave duration?" |
| `policy_category` | Leave |
| `expected_behavior` | `grounded` |
| `expected_answer_summary` | `["States the leave duration entitlement"]` |
| `expected_citations` | `[{document: "Leave Policy [ILLUSTRATIVE]", section: "Maternity Leave", page_range: [n, n]}]` |
| `difficulty_tag` | `straightforward` |

**Example 2 — `grounded`, `multi-condition`**

| Field | Value |
|---|---|
| `question_id` | `SEED-002` |
| `question_text` | "What is maternity leave eligibility for adoptive parents?" |
| `policy_category` | Leave |
| `expected_behavior` | `grounded` |
| `expected_answer_summary` | `["States the tenure/eligibility condition, if any", "States whether adoptive parents are explicitly covered", "States the applicable duration"]` |
| `expected_citations` | `[{document: "Leave Policy [ILLUSTRATIVE]", section: "Maternity Leave", page_range: [n, n]}, {document: "Leave Policy [ILLUSTRATIVE]", section: "Adoption Provisions", page_range: [n, n]}]` |
| `difficulty_tag` | `multi-condition` |
| `conversation_context` | Follows `SEED-001` — exercises Query Reformulator (`testing.md` §8.7) |

**Example 3 — `declined`, `adversarial`**

| Field | Value |
|---|---|
| `question_id` | `SEED-003` |
| `question_text` | "How many extra vacation days do I get for referring a friend to the company?" |
| `policy_category` | *(none — no such policy exists in the illustrative corpus)* |
| `expected_behavior` | `declined` |
| `expected_answer_summary` | *(empty — no correct claims exist)* |
| `expected_citations` | *(empty set)* |
| `difficulty_tag` | `adversarial` — phrased to presuppose a policy that does not exist, specifically testing that the system does not fabricate one |

These three seeds are sufficient to exercise every metric in §7–§8 mechanically (Precision/Recall on SEED-001/002, Correct-Decline Rate on SEED-003, Follow-up Resolution on the SEED-001→SEED-002 pair) — populating the real golden set at meaningful scale is explicitly out of scope for this document (§13).

---

## 13. Open Items / Next Steps

1. **Real corpus dependency.** This entire document is schema and methodology because no real HR policy corpus has been ingested yet. Populating a real golden question set is blocked on that corpus existing and the HR Policy Owner being engaged, per §10's workflow — this is a project-sequencing dependency, not a specification gap.
2. **Citation precision acceptance threshold.** Carried forward from `testing.md` §21 item 1 — §9 defines *how* it will be set, not the value itself.
3. **Cost-per-query ceiling's relationship to evaluation.** NFR-COST-005's ceiling (also unset, `architecture.md` §17) will eventually need its own baseline-then-threshold treatment analogous to §9's — not addressed here since it is a cost metric, not a quality metric, and belongs more naturally alongside `testing.md` §11's Cost category.
4. **Minimum golden-set size for a statistically meaningful Precision/Recall measurement.** Not specified — three illustrative seeds (§12) prove the schema, not statistical adequacy. This is a decision for whoever executes §10's authoring workflow at real scale, informed by the actual size and diversity of the real corpus once available.

---

*End of Document.*
