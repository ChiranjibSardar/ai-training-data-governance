"""Unit tests for rdi.risk_report module."""

import json

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
from rdi.risk_report import from_json, generate_report, to_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record(
    record_id: str = "rec-1",
    license_category: str = "MIT",
    license_confidence: float = 0.95,
    flagged: bool = False,
    quality_rating: float = 0.8,
    is_high_risk: bool = False,
    tox_scores: dict[str, float] | None = None,
) -> RecordResult:
    """Build a RecordResult with sensible defaults."""
    if tox_scores is None:
        tox_scores = {
            "toxic": 0.1,
            "severe_toxic": 0.0,
            "obscene": 0.05,
            "threat": 0.0,
            "insult": 0.1,
            "identity_hate": 0.0,
        }
    return RecordResult(
        record_id=record_id,
        license=LicenseResult(
            category=license_category,
            confidence=license_confidence,
            flagged_for_review=flagged,
        ),
        pii=PIIScanResult(redacted_text="clean text", entities=[]),
        quality=QualityResult(perplexity=25.0, quality_rating=quality_rating),
        toxicity=ToxicityResult(scores=tox_scores, is_high_risk=is_high_risk),
    )


_DEFAULT_DEDUP = DeduplicationResult(clusters=[["rec-1"]], similarities=[])
_DEFAULT_CMDI = CMDIResult(composite=0.5, linguistic=0.5, topical=0.5, geographic=0.5)
_DEFAULT_CONFIG = PipelineConfig()


# ---------------------------------------------------------------------------
# generate_report tests
# ---------------------------------------------------------------------------

class TestGenerateReport:
    """Tests for generate_report function."""

    def test_produces_valid_risk_report(self):
        records = [_make_record()]
        report = generate_report(records, _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)

        assert isinstance(report, RiskReport)
        assert report.risk_level in {"low", "medium", "high"}
        assert report.dataset_summary["total_records"] == 1
        assert len(report.records) == 1
        assert report.deduplication is _DEFAULT_DEDUP
        assert report.cmdi is _DEFAULT_CMDI
        assert "generated_at" in report.metadata

    def test_risk_level_high_when_toxic(self):
        toxic_record = _make_record(
            is_high_risk=True,
            tox_scores={"toxic": 0.95, "severe_toxic": 0.0, "obscene": 0.0,
                        "threat": 0.0, "insult": 0.0, "identity_hate": 0.0},
        )
        report = generate_report([toxic_record], _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "high"

    def test_risk_level_high_when_majority_flagged(self):
        # >50% flagged for review → high
        records = [
            _make_record(record_id="r1", flagged=True),
            _make_record(record_id="r2", flagged=True),
            _make_record(record_id="r3", flagged=False),
        ]
        report = generate_report(records, _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "high"

    def test_risk_level_low_for_clean_data(self):
        records = [_make_record(record_id=f"r{i}") for i in range(5)]
        dedup = DeduplicationResult(
            clusters=[[f"r{i}"] for i in range(5)],
            similarities=[],
        )
        report = generate_report(records, dedup, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "low"

    def test_risk_level_medium_when_quality_below_threshold(self):
        records = [_make_record(quality_rating=0.1)]
        report = generate_report(records, _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "medium"

    def test_risk_level_medium_when_high_duplicate_ratio(self):
        # >20% duplicates → medium
        records = [_make_record(record_id=f"r{i}") for i in range(5)]
        dedup = DeduplicationResult(
            clusters=[["r0", "r1", "r2"], ["r3"], ["r4"]],
            similarities=[("r0", "r1", 0.9), ("r0", "r2", 0.85)],
        )
        report = generate_report(records, dedup, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "medium"

    def test_empty_records_list(self):
        report = generate_report([], _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.risk_level == "low"
        assert report.dataset_summary["total_records"] == 0
        assert report.dataset_summary["high_risk_count"] == 0
        assert report.records == []

    def test_dataset_summary_counts(self):
        records = [
            _make_record(record_id="r1", is_high_risk=True,
                         tox_scores={"toxic": 0.9, "severe_toxic": 0.0,
                                     "obscene": 0.0, "threat": 0.0,
                                     "insult": 0.0, "identity_hate": 0.0}),
            _make_record(record_id="r2", flagged=True),
            _make_record(record_id="r3"),
        ]
        dedup = DeduplicationResult(
            clusters=[["r1", "r2"], ["r3"]],
            similarities=[("r1", "r2", 0.85)],
        )
        report = generate_report(records, dedup, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        assert report.dataset_summary["total_records"] == 3
        assert report.dataset_summary["high_risk_count"] == 1
        assert report.dataset_summary["flagged_for_review_count"] == 1
        assert report.dataset_summary["duplicate_cluster_count"] == 1


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

class TestSerialization:
    """Tests for to_json and from_json."""

    def test_to_json_produces_valid_json(self):
        records = [_make_record()]
        report = generate_report(records, _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        json_str = to_json(report)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["risk_level"] in {"low", "medium", "high"}
        assert "dataset_summary" in parsed
        assert "records" in parsed

    def test_round_trip_produces_equivalent_report(self):
        pii_entities = [
            PIIEntity(entity_type="EMAIL", start=0, end=15, confidence=0.99,
                      original_text="test@example.com"),
        ]
        records = [
            RecordResult(
                record_id="rt-1",
                license=LicenseResult(category="CC-BY-4.0", confidence=0.88,
                                      flagged_for_review=False),
                pii=PIIScanResult(redacted_text="[EMAIL] said hello",
                                  entities=pii_entities),
                quality=QualityResult(perplexity=30.0, quality_rating=0.75),
                toxicity=ToxicityResult(
                    scores={"toxic": 0.1, "severe_toxic": 0.0, "obscene": 0.0,
                            "threat": 0.0, "insult": 0.05, "identity_hate": 0.0},
                    is_high_risk=False,
                ),
            ),
        ]
        dedup = DeduplicationResult(
            clusters=[["rt-1"]],
            similarities=[],
        )
        cmdi = CMDIResult(composite=0.6, linguistic=0.7, topical=0.5, geographic=0.6)
        report = generate_report(records, dedup, cmdi, _DEFAULT_CONFIG)

        json_str = to_json(report)
        restored = from_json(json_str)

        assert restored.risk_level == report.risk_level
        assert restored.dataset_summary == report.dataset_summary
        assert len(restored.records) == len(report.records)

        orig_rec = report.records[0]
        rest_rec = restored.records[0]
        assert rest_rec.record_id == orig_rec.record_id
        assert rest_rec.license.category == orig_rec.license.category
        assert rest_rec.license.confidence == orig_rec.license.confidence
        assert rest_rec.license.flagged_for_review == orig_rec.license.flagged_for_review
        assert rest_rec.pii.redacted_text == orig_rec.pii.redacted_text
        assert len(rest_rec.pii.entities) == len(orig_rec.pii.entities)
        assert rest_rec.pii.entities[0].entity_type == "EMAIL"
        assert rest_rec.quality.perplexity == orig_rec.quality.perplexity
        assert rest_rec.quality.quality_rating == orig_rec.quality.quality_rating
        assert rest_rec.toxicity.scores == orig_rec.toxicity.scores
        assert rest_rec.toxicity.is_high_risk == orig_rec.toxicity.is_high_risk

        assert restored.deduplication.clusters == report.deduplication.clusters
        assert restored.cmdi.composite == report.cmdi.composite
        assert restored.cmdi.linguistic == report.cmdi.linguistic

    def test_round_trip_with_similarities(self):
        records = [_make_record(record_id="a"), _make_record(record_id="b")]
        dedup = DeduplicationResult(
            clusters=[["a", "b"]],
            similarities=[("a", "b", 0.92)],
        )
        report = generate_report(records, dedup, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        json_str = to_json(report)
        restored = from_json(json_str)

        assert len(restored.deduplication.similarities) == 1
        sim = restored.deduplication.similarities[0]
        assert sim[0] == "a"
        assert sim[1] == "b"
        assert abs(sim[2] - 0.92) < 1e-9

    def test_round_trip_empty_records(self):
        report = generate_report([], _DEFAULT_DEDUP, _DEFAULT_CMDI, _DEFAULT_CONFIG)
        json_str = to_json(report)
        restored = from_json(json_str)
        assert restored.records == []
        assert restored.risk_level == "low"
        assert restored.dataset_summary["total_records"] == 0
