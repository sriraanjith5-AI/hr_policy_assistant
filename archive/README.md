# Archive

Code preserved for historical reference only. Nothing here should be imported by, or used as a basis for, the real implementation.

## `pre_sdd_prototypes/`

Five files written before the Specification-Driven Development (SDD) chain (`app/specs/`) existed: `app/chunking/text_chunker.py`, `app/embeddings/embedder.py`, `app/loaders/pdf_loader.py`, `main.py`, and `main_test.py`. They were exploratory spikes for understanding chunking, embedding, and PDF parsing conceptually, and predate every approved architectural decision in this repository.

They are archived, not deleted or reused, because each one conflicts with an already-approved decision:

- `embedder.py` imports `sentence_transformers` directly and hardcodes the model `all-MiniLM-L6-v2`. This bypasses the Provider Interface boundary entirely (`interfaces.md` Section 5.1, ADR-002) and pre-empts a technology decision that is still open (`app/specs/decisions/ADR-004-embedding-model-selection.md` — Proposed, not Accepted).
- `pdf_loader.py` imports `pypdf` directly with no Provider Interface boundary, and conflates what the specification splits into two distinct stages — Document Loader (`interfaces.md` 4.1) and PDF Parser (4.2) — into one class returning a raw string, not a `Document`/`ExtractedDocument` domain object (`domain_models.md` Section 3).
- `text_chunker.py` implements naive fixed-size character-window splitting, which does not respect sentence boundaries (`requirements.md` FR-401–404) and does not produce `TextChunk` domain objects (`domain_models.md` Section 4) — its behavior does not match the Semantic Chunker's actual contract (`interfaces.md` 4.4).
- `main.py` and `main_test.py` are scratch scripts wiring the three files above together outside any Orchestrator, with no domain model, no Provider Interface, and (in `main_test.py`) an interactive `input()` call — not an automated test in the sense `testing.md` defines.

They remain useful as a record of early exploration and are kept, not discarded, for that reason. They must not be un-archived into `app/` without being rewritten against the approved contracts in `interfaces.md` and the domain models in `domain_models.md`.
