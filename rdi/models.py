"""Data models for the RDI Framework.

All inter-component data uses Python dataclasses with full type hints.
Models are organized by pipeline layer:
- Layer 1 (Ingestion Gate): LicenseResult, PIIEntity, PIIScanResult, C2PAResult, LedgerEntry
- Layer 2 (Validation & Risk Scoring): QualityResult, ToxicityResult, DeduplicationResult, CMDIResult
- Pipeline output: RecordResult, RiskReport, PipelineConfig
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Layer 1: Ingestion Gate models
# ---------------------------------------------------------------------------


@dataclass
class LicenseResult:
    """Result of license classification for a text document.

    Attributes:
        category: One of CC-BY-4.0, CC-BY-SA-4.0, CC0-1.0, MIT,
            Apache-2.0, public-domain, restricted, or unknown.
        confidence: Classification confidence score in [0.0, 1.0].
        flagged_for_review: True when confidence is below the review
            threshold (default 0.7).
    """

    category: str
    confidence: float
    flagged_for_review: bool = False


@dataclass
class PIIEntity:
    """A single PII entity detected in text.

    Attributes:
        entity_type: PII category — EMAIL, PERSON, PHONE, ADDRESS, or SSN.
        start: Start character offset in the original text.
        end: End character offset in the original text.
        confidence: Detection confidence score in [0.0, 1.0].
        original_text: The original text span that was detected as PII.
    """

    entity_type: str
    start: int
    end: int
    confidence: float
    original_text: str = ""


@dataclass
class PIIScanResult:
    """Result of PII scanning and redaction for a text document.

    Attributes:
        redacted_text: The text with PII entities replaced by type-specific
            placeholder tokens (e.g. [EMAIL], [PERSON]).
        entities: List of detected PII entities with positions and types.
    """

    redacted_text: str
    entities: list[PIIEntity] = field(default_factory=list)


@dataclass
class C2PAResult:
    """Result of C2PA content credential validation.

    Stub dataclass — full implementation deferred to Phase 2.

    Attributes:
        has_credentials: Whether the file contains C2PA credentials.
        metadata: Extracted credential metadata, if any.
        error: Error message if validation could not be performed.
    """

    has_credentials: bool
    metadata: dict | None = None
    error: str | None = None


@dataclass
class LedgerEntry:
    """A single entry in the provenance ledger.

    Each entry is hash-chained to the previous entry via SHA-256,
    forming a tamper-evident append-only log.

    Attributes:
        content_hash: SHA-256 hash of the original content.
        license_result: JSON-serialized license classification result.
        pii_result: JSON-serialized PII scan result.
        timestamp: ISO 8601 timestamp of when the entry was created.
        previous_hash: entry_hash of the preceding entry, or "0" * 64
            for the genesis entry.
        entry_hash: SHA-256 hash of this entry's concatenated fields.
    """

    content_hash: str
    license_result: str
    pii_result: str
    timestamp: str
    previous_hash: str
    entry_hash: str


# ---------------------------------------------------------------------------
# Layer 2: Validation & Risk Scoring models
# ---------------------------------------------------------------------------


@dataclass
class QualityResult:
    """Result of text quality scoring.

    Stub dataclass — full implementation deferred to Phase 2.

    Attributes:
        perplexity: Raw perplexity value (non-negative).
        quality_rating: Normalized quality score in [0.0, 1.0].
    """

    perplexity: float
    quality_rating: float


@dataclass
class ToxicityResult:
    """Result of toxicity scoring across multiple categories.

    Attributes:
        scores: Mapping of category name to toxicity score in [0.0, 1.0].
            Categories: toxic, severe_toxic, obscene, threat, insult,
            identity_hate.
        is_high_risk: True if any category score exceeds 0.8.
    """

    scores: dict[str, float] = field(default_factory=dict)
    is_high_risk: bool = False


@dataclass
class DeduplicationResult:
    """Result of near-duplicate detection across a corpus.

    Attributes:
        clusters: List of clusters, where each cluster is a list of
            document IDs that are near-duplicates of each other.
        similarities: List of (doc_a, doc_b, similarity) tuples for
            detected near-duplicate pairs.
    """

    clusters: list[list[str]] = field(default_factory=list)
    similarities: list[tuple[str, str, float]] = field(default_factory=list)


@dataclass
class CMDIResult:
    """Cross-Modal Diversity Index result.

    Stub dataclass — full implementation deferred to Phase 2.

    Attributes:
        composite: Weighted composite diversity score in [0.0, 1.0].
        linguistic: Linguistic diversity sub-index in [0.0, 1.0].
        topical: Topical diversity sub-index in [0.0, 1.0].
        geographic: Geographic diversity sub-index in [0.0, 1.0].
    """

    composite: float
    linguistic: float
    topical: float
    geographic: float


# ---------------------------------------------------------------------------
# Pipeline output models
# ---------------------------------------------------------------------------


@dataclass
class RecordResult:
    """Aggregated results for a single data record.

    Attributes:
        record_id: Unique identifier for the processed record.
        license: License classification result.
        pii: PII scan and redaction result.
        quality: Text quality scoring result.
        toxicity: Toxicity scoring result.
    """

    record_id: str
    license: LicenseResult
    pii: PIIScanResult
    quality: QualityResult
    toxicity: ToxicityResult


@dataclass
class RiskReport:
    """Structured risk report for a processed dataset.

    Attributes:
        dataset_summary: High-level statistics about the dataset.
        records: Per-record validation results.
        deduplication: Corpus-level deduplication results.
        cmdi: Cross-Modal Diversity Index results.
        risk_level: Overall risk assessment — "low", "medium", or "high".
        metadata: Additional metadata (e.g. pipeline version, timestamps).
    """

    dataset_summary: dict
    records: list[RecordResult]
    deduplication: DeduplicationResult
    cmdi: CMDIResult
    risk_level: str
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Configuration for the RDI pipeline.

    Attributes:
        quality_threshold: Minimum quality rating to pass validation.
        toxicity_threshold: Score above which a record is flagged high-risk.
        dedup_threshold: Jaccard similarity threshold for deduplication.
        cmdi_weights: Weights for (linguistic, topical, geographic)
            sub-indices. Must sum to ~1.0.
        ledger_path: File path for the provenance ledger JSONL file.
        license_confidence_threshold: Confidence below which a license
            classification is flagged for manual review.
    """

    quality_threshold: float = 0.3
    toxicity_threshold: float = 0.8
    dedup_threshold: float = 0.8
    cmdi_weights: tuple[float, float, float] = (0.333, 0.333, 0.334)
    ledger_path: str = "provenance_ledger.jsonl"
    license_confidence_threshold: float = 0.7
