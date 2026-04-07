# Requirements Document

## Introduction

This document specifies the requirements for implementing Layers 1 and 2 of the Responsible Data Infrastructure (RDI) Framework as a working Python codebase. The implementation transforms the existing conceptual framework into production-quality open-source software demonstrating AI training data governance capabilities. The scope covers the Ingestion Gate (Layer 1) and Validation & Risk Scoring (Layer 2) pipeline components, with a text-only Cross-Modal Diversity Index (CMDI) prototype.

All components use exclusively open-source models, tools, and public datasets. No proprietary data or internal tooling is used.

## Glossary

- **RDI_Pipeline**: The end-to-end Python pipeline that processes text data through ingestion and validation layers
- **Ingestion_Gate**: Layer 1 module responsible for C2PA validation, license classification, PII scanning, and provenance logging before data enters the validation stage
- **License_Classifier**: ML-based component that classifies text documents by their associated open-source license type (e.g., CC-BY, CC-BY-SA, public domain, restricted)
- **PII_Scanner**: Component that detects and redacts personally identifiable information (names, emails, phone numbers, addresses, SSNs) from text data
- **Provenance_Ledger**: Append-only, hash-chained audit log that records every ingestion decision with cryptographic integrity verification
- **C2PA_Validator**: Thin wrapper around the c2patool CLI that checks C2PA content credentials on supported media files
- **Validation_Engine**: Layer 2 module responsible for quality scoring, toxicity filtering, deduplication, and diversity measurement
- **Quality_Scorer**: Component that assigns a text quality score based on perplexity measurement using a small open-source language model
- **Toxicity_Filter**: Component that scores text for toxic, obscene, threatening, or identity-attack content using open-source classifiers
- **Deduplicator**: Component that detects near-duplicate text documents using MinHash/LSH algorithms
- **CMDI_Calculator**: Component that computes the text-only Cross-Modal Diversity Index measuring linguistic, topical, and geographic diversity of a text corpus
- **Risk_Report**: Structured JSON output summarizing all validation scores and risk flags for a processed dataset
- **Data_Record**: A single unit of text data passing through the pipeline, with associated metadata

## Requirements

### Requirement 1: License Classification

**User Story:** As a data governance engineer, I want to automatically classify the license type of incoming text data, so that I can enforce rights compliance before data enters the training pipeline.

#### Acceptance Criteria

1. WHEN a text document is submitted to the Ingestion_Gate, THE License_Classifier SHALL classify the document into one of the following license categories: CC-BY-4.0, CC-BY-SA-4.0, CC0-1.0, MIT, Apache-2.0, public-domain, restricted, or unknown.
2. WHEN the License_Classifier produces a classification, THE License_Classifier SHALL return a confidence score between 0.0 and 1.0 alongside the predicted license category.
3. WHEN the License_Classifier confidence score is below 0.7, THE Ingestion_Gate SHALL flag the Data_Record for manual review.
4. THE License_Classifier SHALL achieve a minimum F1 score of 0.80 on a held-out test set of open-source license texts.
5. IF the License_Classifier receives an empty or malformed input, THEN THE License_Classifier SHALL return the category "unknown" with a confidence score of 0.0.

### Requirement 2: PII Scanning and Redaction

**User Story:** As a data governance engineer, I want to detect and redact personally identifiable information from text data, so that privacy-sensitive content does not enter the training pipeline.

#### Acceptance Criteria

1. WHEN a text document is submitted to the Ingestion_Gate, THE PII_Scanner SHALL scan the document for the following PII entity types: person names, email addresses, phone numbers, physical addresses, and social security numbers.
2. WHEN the PII_Scanner detects a PII entity, THE PII_Scanner SHALL replace the entity with a type-specific placeholder token (e.g., `[EMAIL]`, `[PERSON]`, `[PHONE]`, `[ADDRESS]`, `[SSN]`).
3. WHEN the PII_Scanner completes scanning, THE PII_Scanner SHALL return a redacted version of the text and a list of detected entities with their types, positions, and confidence scores.
4. THE PII_Scanner SHALL detect email addresses and phone numbers with a minimum precision of 0.95.
5. IF the PII_Scanner receives an empty input, THEN THE PII_Scanner SHALL return an empty string and an empty entity list.

### Requirement 3: Provenance Ledger

**User Story:** As a data governance auditor, I want an immutable, hash-chained audit log of all ingestion decisions, so that I can verify the integrity and traceability of the data pipeline.

#### Acceptance Criteria

1. WHEN a Data_Record passes through the Ingestion_Gate, THE Provenance_Ledger SHALL create a ledger entry containing: a SHA-256 hash of the Data_Record content, the license classification result, the PII scan result, a timestamp in ISO 8601 format, and the hash of the previous ledger entry.
2. THE Provenance_Ledger SHALL chain each entry to the previous entry using SHA-256 hashing, forming a tamper-evident append-only log.
3. WHEN a verification request is made, THE Provenance_Ledger SHALL validate the integrity of the entire chain by recomputing and comparing hashes from the genesis entry to the latest entry.
4. IF the Provenance_Ledger detects a broken hash chain during verification, THEN THE Provenance_Ledger SHALL return the index of the first corrupted entry and a description of the mismatch.
5. THE Provenance_Ledger SHALL persist ledger entries to a JSON Lines file, with one entry per line.
6. FOR ALL valid ledger entries, writing an entry and then reading the ledger SHALL produce a ledger containing that entry with identical field values (round-trip property).

### Requirement 4: C2PA Content Credential Validation

**User Story:** As a data governance engineer, I want to validate C2PA content credentials on media files, so that I can verify provenance claims before ingesting data.

#### Acceptance Criteria

1. WHEN a media file with C2PA content credentials is submitted, THE C2PA_Validator SHALL extract and return the credential metadata including the claim generator, assertions, and signature status.
2. WHEN a media file without C2PA credentials is submitted, THE C2PA_Validator SHALL return a result indicating no credentials were found.
3. IF the c2patool CLI is not installed on the system, THEN THE C2PA_Validator SHALL raise a descriptive error indicating that c2patool is required and provide installation instructions.
4. IF the C2PA_Validator receives an unsupported file format, THEN THE C2PA_Validator SHALL return an error specifying the supported formats.

### Requirement 5: Text Quality Scoring

**User Story:** As a data governance engineer, I want to score the quality of text data using perplexity measurement, so that I can filter out low-quality or incoherent text before it enters training.

#### Acceptance Criteria

1. WHEN a text document is submitted to the Validation_Engine, THE Quality_Scorer SHALL compute a perplexity score using a small open-source language model (GPT-2 or equivalent).
2. WHEN the Quality_Scorer computes a perplexity score, THE Quality_Scorer SHALL normalize the score to a quality rating between 0.0 (lowest quality) and 1.0 (highest quality).
3. THE Quality_Scorer SHALL process text documents of up to 10,000 tokens without truncation errors.
4. IF the Quality_Scorer receives an empty or whitespace-only input, THEN THE Quality_Scorer SHALL return a quality rating of 0.0.
5. WHEN two text documents are submitted, THE Quality_Scorer SHALL assign a higher quality rating to a well-formed English paragraph than to a string of random characters.

### Requirement 6: Toxicity Filtering

**User Story:** As a data governance engineer, I want to score text data for toxic content, so that I can prevent harmful material from entering the training pipeline.

#### Acceptance Criteria

1. WHEN a text document is submitted to the Validation_Engine, THE Toxicity_Filter SHALL return toxicity scores across the following categories: toxic, severe-toxic, obscene, threat, insult, and identity-hate.
2. THE Toxicity_Filter SHALL return each category score as a float between 0.0 and 1.0.
3. WHEN any single toxicity category score exceeds 0.8, THE Toxicity_Filter SHALL flag the Data_Record as high-risk.
4. THE Toxicity_Filter SHALL use an open-source toxicity classification model (Detoxify or equivalent HuggingFace model).
5. IF the Toxicity_Filter receives an empty input, THEN THE Toxicity_Filter SHALL return scores of 0.0 for all categories.

### Requirement 7: Near-Duplicate Detection

**User Story:** As a data governance engineer, I want to detect near-duplicate documents in a text corpus, so that I can remove redundant data and prevent training bias from overrepresented content.

#### Acceptance Criteria

1. WHEN a corpus of text documents is submitted to the Deduplicator, THE Deduplicator SHALL identify clusters of near-duplicate documents using MinHash with Locality-Sensitive Hashing (LSH).
2. THE Deduplicator SHALL accept a configurable Jaccard similarity threshold parameter, with a default value of 0.8.
3. WHEN near-duplicate clusters are identified, THE Deduplicator SHALL return the cluster assignments and the estimated Jaccard similarity between duplicate pairs.
4. THE Deduplicator SHALL process a corpus of 10,000 documents within 60 seconds on a machine with 16 GB RAM.
5. WHEN two identical documents are submitted, THE Deduplicator SHALL place the two documents in the same duplicate cluster.
6. WHEN two completely unrelated documents are submitted, THE Deduplicator SHALL place the two documents in separate clusters.

### Requirement 8: Cross-Modal Diversity Index (CMDI) — Text

**User Story:** As a data governance researcher, I want to measure the linguistic, topical, and geographic diversity of a text corpus, so that I can quantify representational fairness and identify gaps in training data.

#### Acceptance Criteria

1. THE CMDI_Calculator SHALL compute a composite diversity score between 0.0 (no diversity) and 1.0 (maximum diversity) for a given text corpus.
2. THE CMDI_Calculator SHALL compute three sub-index scores: linguistic diversity (language distribution), topical diversity (topic distribution via LDA or equivalent), and geographic diversity (geographic entity distribution via NER).
3. WHEN computing the composite CMDI score, THE CMDI_Calculator SHALL combine the three sub-index scores using configurable weights that sum to 1.0, with default equal weights of 0.333 each.
4. THE CMDI_Calculator SHALL compute linguistic diversity using the Shannon entropy of the language distribution in the corpus, normalized to the range 0.0 to 1.0.
5. THE CMDI_Calculator SHALL compute topical diversity using the Shannon entropy of the topic distribution produced by an LDA model, normalized to the range 0.0 to 1.0.
6. THE CMDI_Calculator SHALL compute geographic diversity using the Shannon entropy of geographic named entities extracted from the corpus, normalized to the range 0.0 to 1.0.
7. WHEN a corpus contains documents in only one language on one topic from one geographic region, THE CMDI_Calculator SHALL return a composite score below 0.15.
8. IF the CMDI_Calculator receives an empty corpus, THEN THE CMDI_Calculator SHALL return a composite score of 0.0 and sub-index scores of 0.0.
9. FOR ALL valid corpora, computing CMDI on the same corpus twice SHALL produce identical composite and sub-index scores (determinism property).

### Requirement 9: Risk Report Generation

**User Story:** As a data governance engineer, I want a structured report summarizing all validation results for a processed dataset, so that I can make informed curation decisions and maintain audit records.

#### Acceptance Criteria

1. WHEN a dataset has been processed through the Ingestion_Gate and Validation_Engine, THE RDI_Pipeline SHALL generate a Risk_Report in JSON format.
2. THE Risk_Report SHALL include: dataset-level summary statistics, per-record license classifications, per-record PII scan results, per-record quality scores, per-record toxicity scores, deduplication results, and the CMDI score with sub-indices.
3. THE Risk_Report SHALL include a top-level risk assessment of "low", "medium", or "high" based on configurable threshold rules applied to the aggregate scores.
4. THE Risk_Report SHALL be parseable as valid JSON by any standard JSON parser.
5. FOR ALL valid Risk_Reports, serializing the report to JSON and deserializing it back SHALL produce an equivalent Risk_Report object (round-trip property).

### Requirement 10: Pipeline CLI Interface

**User Story:** As a developer or reviewer, I want to run the RDI pipeline from the command line, so that I can process datasets and generate reports without writing custom code.

#### Acceptance Criteria

1. THE RDI_Pipeline SHALL provide a CLI command `rdi run` that accepts an input directory or file path and an output directory path.
2. WHEN `rdi run` is executed, THE RDI_Pipeline SHALL process all text files in the input path through Layer 1 (Ingestion_Gate) and Layer 2 (Validation_Engine) sequentially.
3. WHEN processing completes, THE RDI_Pipeline SHALL write the Risk_Report to the specified output directory.
4. THE RDI_Pipeline SHALL provide a CLI command `rdi validate-ledger` that verifies the integrity of the Provenance_Ledger.
5. THE RDI_Pipeline SHALL display a progress indicator during processing showing the number of records processed out of the total.
6. IF the input path does not exist or contains no processable files, THEN THE RDI_Pipeline SHALL exit with a non-zero exit code and a descriptive error message.

### Requirement 11: Pipeline Python Library Interface

**User Story:** As a developer, I want to use the RDI pipeline components as a Python library, so that I can integrate individual components into custom workflows.

#### Acceptance Criteria

1. THE RDI_Pipeline SHALL expose each component (License_Classifier, PII_Scanner, Provenance_Ledger, C2PA_Validator, Quality_Scorer, Toxicity_Filter, Deduplicator, CMDI_Calculator) as an importable Python class with a documented public API.
2. WHEN a component is instantiated, THE component SHALL accept configuration parameters through the constructor.
3. THE RDI_Pipeline SHALL provide a top-level `Pipeline` class that orchestrates all components in sequence and returns a Risk_Report.
4. THE RDI_Pipeline SHALL use Python type hints on all public methods and classes.
5. THE RDI_Pipeline SHALL include docstrings on all public methods and classes following Google-style docstring conventions.
