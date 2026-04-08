"""Risk report generation, serialization, and deserialization.

Provides functions to build a RiskReport from pipeline results,
serialize it to JSON, and reconstruct it from JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from rdi.models import (
    CMDIResult,
    DeduplicationResult,
    LicenseResult,
    PIIEntity,
    PIIScanResult,
    PipelineConfig,
    QualityResult,
    RecordResult,
    RiskReport,
    ToxicityResult,
)


def _compute_risk_level(
    records: list[RecordResult],
    deduplication: DeduplicationResult,
    config: PipelineConfig,
) -> str:
    """Determine the overall risk level from aggregate scores.

    Thresholds:
        - "high": any record has high-risk toxicity OR >50% of records
          are flagged for review.
        - "medium": >20% of documents are in duplicate clusters (clusters
          with more than one member) OR any record quality is below the
          configured quality threshold.
        - "low": otherwise.

    Args:
        records: Per-record validation results.
        deduplication: Corpus-level deduplication results.
        config: Pipeline configuration with thresholds.

    Returns:
        One of ``"low"``, ``"medium"``, or ``"high"``.
    """
    total = len(records)

    # --- HIGH checks ---
    if total > 0:
        high_risk_toxic = any(r.toxicity.is_high_risk for r in records)
        flagged_count = sum(
            1 for r in records if r.license.flagged_for_review
        )
        flagged_ratio = flagged_count / total
        if high_risk_toxic or flagged_ratio > 0.5:
            return "high"

    # --- MEDIUM checks ---
    if total > 0:
        # Duplicate ratio: documents that belong to a cluster of size > 1
        duplicate_doc_count = sum(
            len(c) for c in deduplication.clusters if len(c) > 1
        )
        duplicate_ratio = duplicate_doc_count / total if total > 0 else 0.0
        if duplicate_ratio > 0.2:
            return "medium"

        quality_below = any(
            r.quality.quality_rating < config.quality_threshold for r in records
        )
        if quality_below:
            return "medium"

    return "low"


def generate_report(
    records: list[RecordResult],
    deduplication: DeduplicationResult,
    cmdi: CMDIResult,
    config: PipelineConfig,
) -> RiskReport:
    """Build a RiskReport from pipeline results.

    Args:
        records: Per-record validation results.
        deduplication: Corpus-level deduplication results.
        cmdi: Cross-Modal Diversity Index results.
        config: Pipeline configuration with thresholds.

    Returns:
        A fully populated ``RiskReport``.
    """
    total = len(records)
    high_risk_count = sum(1 for r in records if r.toxicity.is_high_risk)
    flagged_for_review_count = sum(
        1 for r in records if r.license.flagged_for_review
    )
    duplicate_cluster_count = sum(
        1 for c in deduplication.clusters if len(c) > 1
    )

    dataset_summary = {
        "total_records": total,
        "high_risk_count": high_risk_count,
        "flagged_for_review_count": flagged_for_review_count,
        "duplicate_cluster_count": duplicate_cluster_count,
    }

    risk_level = _compute_risk_level(records, deduplication, config)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "0.1.0",
    }

    return RiskReport(
        dataset_summary=dataset_summary,
        records=records,
        deduplication=deduplication,
        cmdi=cmdi,
        risk_level=risk_level,
        metadata=metadata,
    )


def to_json(report: RiskReport) -> str:
    """Serialize a RiskReport to a JSON string.

    Uses ``dataclasses.asdict()`` for conversion and ``json.dumps``
    with ``indent=2`` for human-readable output.

    Args:
        report: The risk report to serialize.

    Returns:
        A JSON-formatted string.
    """
    data = asdict(report)
    # Convert tuple-based similarities to lists for JSON compatibility
    return json.dumps(data, indent=2, default=str)


def from_json(json_str: str) -> RiskReport:
    """Deserialize a JSON string into a RiskReport.

    Reconstructs all nested dataclasses from the parsed JSON dict.

    Args:
        json_str: A JSON string previously produced by ``to_json``.

    Returns:
        A reconstructed ``RiskReport`` instance.
    """
    data = json.loads(json_str)

    records = [_record_from_dict(r) for r in data["records"]]

    dedup_data = data["deduplication"]
    deduplication = DeduplicationResult(
        clusters=dedup_data["clusters"],
        similarities=[
            tuple(s) for s in dedup_data["similarities"]
        ],
    )

    cmdi_data = data["cmdi"]
    cmdi = CMDIResult(
        composite=cmdi_data["composite"],
        linguistic=cmdi_data["linguistic"],
        topical=cmdi_data["topical"],
        geographic=cmdi_data["geographic"],
    )

    return RiskReport(
        dataset_summary=data["dataset_summary"],
        records=records,
        deduplication=deduplication,
        cmdi=cmdi,
        risk_level=data["risk_level"],
        metadata=data.get("metadata", {}),
    )


def _record_from_dict(d: dict) -> RecordResult:
    """Reconstruct a RecordResult from a plain dict."""
    lic = d["license"]
    license_result = LicenseResult(
        category=lic["category"],
        confidence=lic["confidence"],
        flagged_for_review=lic.get("flagged_for_review", False),
    )

    pii_data = d["pii"]
    entities = [
        PIIEntity(
            entity_type=e["entity_type"],
            start=e["start"],
            end=e["end"],
            confidence=e["confidence"],
            original_text=e.get("original_text", ""),
        )
        for e in pii_data.get("entities", [])
    ]
    pii_result = PIIScanResult(
        redacted_text=pii_data["redacted_text"],
        entities=entities,
    )

    qual = d["quality"]
    quality_result = QualityResult(
        perplexity=qual["perplexity"],
        quality_rating=qual["quality_rating"],
    )

    tox = d["toxicity"]
    toxicity_result = ToxicityResult(
        scores=tox["scores"],
        is_high_risk=tox.get("is_high_risk", False),
    )

    return RecordResult(
        record_id=d["record_id"],
        license=license_result,
        pii=pii_result,
        quality=quality_result,
        toxicity=toxicity_result,
    )
