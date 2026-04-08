# Implementation Plan: RDI Framework POC

## Overview

This plan implements a proof-of-concept of the RDI Framework covering 5 pipeline components (PII Scanner, Provenance Ledger, Toxicity Filter, Deduplicator, Risk Report), a minimal Pipeline orchestrator, and a CLI (`rdi run`). Deferred components (License Classifier, Quality Scorer, CMDI Calculator, C2PA Validator) are stubbed with pass-through defaults so the pipeline runs end-to-end.

## Tasks

- [x] 1. Project scaffolding and package structure
  - [x] 1.1 Create package layout and pyproject.toml
    - Create `rdi/` package directory with `__init__.py`
    - Create `pyproject.toml` with project metadata and POC dependencies: `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `detoxify`, `datasketch`, `click`, `tqdm`, `hypothesis`, `pytest`
    - Create `tests/` directory with `conftest.py`
    - _Requirements: 11.1, 11.4, 11.5_
  - [x] 1.2 Define data models and exception hierarchy
    - Create `rdi/models.py` with all dataclasses: `PIIEntity`, `PIIScanResult`, `LedgerEntry`, `ToxicityResult`, `DeduplicationResult`, `RecordResult`, `RiskReport`, `PipelineConfig`
    - Include stub dataclasses for deferred components: `LicenseResult`, `QualityResult`, `CMDIResult`, `C2PAResult`
    - Create `rdi/exceptions.py` with `RDIError`, `ModelLoadError`, `LedgerIOError`, `LedgerIntegrityError`, `ValidationError`
    - _Requirements: 11.4, 11.5_
  - [x] 1.3 Create stub modules for deferred components
    - Create `rdi/license_classifier.py` — returns `LicenseResult(category="unknown", confidence=0.0, flagged_for_review=True)` for any input
    - Create `rdi/quality_scorer.py` — returns `QualityResult(perplexity=0.0, quality_rating=0.0)` for any input
    - Create `rdi/cmdi_calculator.py` — returns `CMDIResult(composite=0.0, linguistic=0.0, topical=0.0, geographic=0.0)` for any input
    - Create `rdi/c2pa_validator.py` — returns `C2PAResult(has_credentials=False, error="C2PA validation deferred to Phase 2")` for any input
    - _Requirements: 11.1, 11.2_

- [x] 2. Checkpoint — Verify scaffolding
  - Ensure package imports work and all stub modules are importable. Ask the user if questions arise.

- [x] 3. PII Scanner implementation
  - [x] 3.1 Implement PIIScanner class
    - Create `rdi/pii_scanner.py` with `PIIScanner` class
    - Use `presidio-analyzer` with `en_core_web_lg` spaCy model for NER, plus regex recognizers for emails, phones, SSNs
    - Implement `scan(text: str) -> PIIScanResult` method
    - Redact detected entities with type-specific placeholders: `[EMAIL]`, `[PERSON]`, `[PHONE]`, `[ADDRESS]`, `[SSN]`
    - Handle empty input by returning `PIIScanResult(redacted_text="", entities=[])`
    - _Requirements: 2.1, 2.2, 2.3, 2.5_
  - [ ]* 3.2 Write property test for PIIScanner output invariant
    - **Property 3: PIIScanner output invariant**
    - Test that for any text with injected PII patterns, `scan()` returns valid `PIIScanResult` with correct placeholder tokens and entity positions within text bounds
    - **Validates: Requirements 2.2, 2.3**

- [x] 4. Provenance Ledger implementation
  - [x] 4.1 Implement ProvenanceLedger class
    - Create `rdi/provenance_ledger.py` with `ProvenanceLedger` class
    - Implement `append(content_hash, license_result, pii_result) -> LedgerEntry` with SHA-256 hash chaining
    - Genesis entry uses `"0" * 64` as `previous_hash`
    - Each `entry_hash` = SHA-256 of `(content_hash + license_result + pii_result + timestamp + previous_hash)`
    - Implement `verify() -> tuple[bool, int | None, str | None]` to validate chain integrity
    - Persist entries as JSON Lines (one JSON object per line)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  - [ ]* 4.2 Write property test for ledger entry structure
    - **Property 4: Ledger entry structure and persistence**
    - Test that appended entries contain all required fields and JSONL line count matches entry count
    - **Validates: Requirements 3.1, 3.5**
  - [ ]* 4.3 Write property test for ledger chain integrity
    - **Property 5: Ledger chain integrity**
    - Test that `entry[i].previous_hash == entry[i-1].entry_hash` for all entries, and genesis has `previous_hash == "0" * 64`
    - **Validates: Requirements 3.2**
  - [ ]* 4.4 Write property test for ledger verification correctness
    - **Property 6: Ledger verification correctness**
    - Test that `verify()` succeeds on untampered ledgers and detects the first corrupted entry on tampered ledgers
    - **Validates: Requirements 3.3, 3.4**
  - [ ]* 4.5 Write property test for ledger round-trip
    - **Property 7: Ledger round-trip**
    - Test that writing a `LedgerEntry` and reading it back produces identical field values
    - **Validates: Requirements 3.6**

- [x] 5. Checkpoint — Verify PII Scanner and Provenance Ledger
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Toxicity Filter implementation
  - [x] 6.1 Implement ToxicityFilter class
    - Create `rdi/toxicity_filter.py` with `ToxicityFilter` class
    - Use `detoxify` library for multi-category toxicity scoring
    - Implement `score(text: str) -> ToxicityResult` returning scores for: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, `identity_hate`
    - Set `is_high_risk = True` if any score > 0.8
    - Return all 0.0 scores for empty input
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [ ]* 6.2 Write property test for ToxicityFilter output invariant
    - **Property 9: ToxicityFilter output invariant**
    - Test that `score()` returns all six category scores, each in `[0.0, 1.0]`
    - **Validates: Requirements 6.1, 6.2**
  - [ ]* 6.3 Write property test for ToxicityFilter high-risk flagging
    - **Property 10: ToxicityFilter high-risk flagging**
    - Test that `is_high_risk == any(s > 0.8 for s in scores.values())`
    - **Validates: Requirements 6.3**

- [x] 7. Deduplicator implementation
  - [x] 7.1 Implement Deduplicator class
    - Create `rdi/deduplicator.py` with `Deduplicator` class
    - Use `datasketch` MinHash with LSH for near-duplicate detection
    - Implement `deduplicate(documents: list[tuple[str, str]]) -> DeduplicationResult` accepting `(doc_id, text)` tuples
    - Accept configurable `threshold` (default 0.8) and `num_perm` (default 128)
    - Return clusters (every doc ID in exactly one cluster) and similarity pairs
    - Return empty results for empty corpus
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_
  - [ ]* 7.2 Write property test for Deduplicator output structure
    - **Property 11: Deduplicator output structure**
    - Test that every input doc ID appears in exactly one cluster and all similarity scores are in `[0.0, 1.0]`
    - **Validates: Requirements 7.1, 7.3**
  - [ ]* 7.3 Write property test for identical document clustering
    - **Property 12: Deduplicator identical document clustering**
    - Test that two documents with identical content are placed in the same cluster
    - **Validates: Requirements 7.5**

- [x] 8. Checkpoint — Verify Toxicity Filter and Deduplicator
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Risk Report generation
  - [x] 9.1 Implement RiskReport generation logic
    - Create `rdi/risk_report.py` with functions to build, serialize, and deserialize `RiskReport`
    - Implement `generate_report(records, deduplication, cmdi, config) -> RiskReport` that computes `risk_level` from aggregate scores
    - Implement `to_json(report) -> str` and `from_json(json_str) -> RiskReport` for serialization
    - Risk level thresholds: "high" if any record is high-risk toxic or >50% flagged for review; "medium" if >20% duplicates or any quality below threshold; "low" otherwise
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  - [ ]* 9.2 Write property test for RiskReport structure invariant
    - **Property 16: RiskReport structure invariant**
    - Test that generated reports serialize as valid JSON, contain all required sections, and `risk_level` is in `{"low", "medium", "high"}`
    - **Validates: Requirements 9.2, 9.3, 9.4**
  - [ ]* 9.3 Write property test for RiskReport round-trip
    - **Property 17: RiskReport round-trip**
    - Test that serializing to JSON and deserializing back produces an equivalent `RiskReport`
    - **Validates: Requirements 9.5**

- [x] 10. Pipeline orchestrator and CLI
  - [x] 10.1 Implement Pipeline class
    - Create `rdi/pipeline.py` with `Pipeline` class
    - Orchestrate POC components: PIIScanner → ProvenanceLedger → ToxicityFilter → Deduplicator → RiskReport
    - Use stubs for deferred components (LicenseClassifier, QualityScorer, CMDICalculator, C2PAValidator)
    - Implement `run(input_path: Path, output_path: Path) -> RiskReport`
    - Accept `PipelineConfig` for thresholds
    - Show progress via `tqdm`
    - _Requirements: 11.2, 11.3_
  - [x] 10.2 Implement CLI with click
    - Create `rdi/cli.py` with `click` commands
    - Implement `rdi run --input <path> --output <path> [--threshold-toxicity 0.8]`
    - Implement `rdi validate-ledger --ledger <path>`
    - Handle errors: non-existent input path (exit code 1), no text files found (exit code 1), output not writable (exit code 1)
    - Wire CLI entry point in `pyproject.toml`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 11. Sample data and demo script
  - [x] 11.1 Create sample data and demo
    - Create `samples/` directory with 3-5 small `.txt` files containing varied content (clean text, text with PII patterns, mildly toxic text, duplicate text)
    - Create `demo.sh` script that runs `rdi run --input samples/ --output output/` and `rdi validate-ledger --ledger output/provenance_ledger.jsonl`
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Deferred components (License Classifier, Quality Scorer, CMDI Calculator, C2PA Validator) are stubbed so the pipeline runs end-to-end
- Property tests validate correctness properties from the design document using `hypothesis`
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
