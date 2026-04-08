"""Pipeline orchestrator for the RDI Framework.

Coordinates all pipeline components in a two-layer architecture:

- **Layer 1 (Ingestion Gate):** Per-record processing — license classification,
  PII scanning, provenance logging, quality scoring, and toxicity filtering.
- **Layer 2 (Corpus-level):** Deduplication and diversity analysis across the
  full corpus.

The final output is a :class:`~rdi.models.RiskReport` written as JSON to the
configured output directory.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from tqdm import tqdm

from rdi.cmdi_calculator import CMDICalculator
from rdi.deduplicator import Deduplicator
from rdi.license_classifier import LicenseClassifier
from rdi.models import PipelineConfig, RecordResult, RiskReport
from rdi.pii_scanner import PIIScanner
from rdi.provenance_ledger import ProvenanceLedger
from rdi.quality_scorer import QualityScorer
from rdi.risk_report import generate_report, to_json
from rdi.toxicity_filter import ToxicityFilter


class Pipeline:
    """End-to-end RDI pipeline orchestrator.

    Args:
        config: Pipeline configuration with thresholds and paths.
            Defaults to :class:`~rdi.models.PipelineConfig` defaults.
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig()

        # Layer 1 components
        self.license_classifier = LicenseClassifier(
            confidence_threshold=self.config.license_confidence_threshold,
        )
        self.pii_scanner = PIIScanner()
        self.quality_scorer = QualityScorer(
            quality_threshold=self.config.quality_threshold,
        )
        self.toxicity_filter = ToxicityFilter()

        # Layer 2 components
        self.deduplicator = Deduplicator(threshold=self.config.dedup_threshold)
        self.cmdi_calculator = CMDICalculator(weights=self.config.cmdi_weights)

    def run(self, input_path: Path, output_path: Path) -> RiskReport:
        """Execute the full pipeline on text files at *input_path*.

        Args:
            input_path: Directory containing ``.txt`` files, or a single
                ``.txt`` file path.
            output_path: Directory where ``risk_report.json`` and
                ``provenance_ledger.jsonl`` will be written.  Created
                automatically if it does not exist.

        Returns:
            The generated :class:`~rdi.models.RiskReport`.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Resolve input files
        files = self._collect_files(input_path)

        # Initialise provenance ledger in the output directory
        ledger_path = output_path / self.config.ledger_path
        ledger = ProvenanceLedger(path=ledger_path)

        # ------------------------------------------------------------------
        # Layer 1 — Per-record ingestion gate
        # ------------------------------------------------------------------
        records: list[RecordResult] = []
        documents: list[tuple[str, str]] = []  # (doc_id, text) for dedup
        texts: list[str] = []  # raw texts for CMDI

        for file_path in tqdm(files, desc="Processing records"):
            text = file_path.read_text(encoding="utf-8")
            doc_id = file_path.name

            # License classification (stub)
            license_result = self.license_classifier.classify(text)

            # PII scanning
            pii_result = self.pii_scanner.scan(text)

            # Compute content hash
            content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

            # Append to provenance ledger
            ledger.append(
                content_hash=content_hash,
                license_result=json.dumps(asdict(license_result)),
                pii_result=json.dumps(asdict(pii_result)),
            )

            # Quality scoring (stub)
            quality_result = self.quality_scorer.score(text)

            # Toxicity filtering
            toxicity_result = self.toxicity_filter.score(text)

            records.append(
                RecordResult(
                    record_id=doc_id,
                    license=license_result,
                    pii=pii_result,
                    quality=quality_result,
                    toxicity=toxicity_result,
                )
            )

            documents.append((doc_id, text))
            texts.append(text)

        # ------------------------------------------------------------------
        # Layer 2 — Corpus-level analysis
        # ------------------------------------------------------------------
        deduplication = self.deduplicator.deduplicate(documents)
        cmdi = self.cmdi_calculator.compute(texts)

        # ------------------------------------------------------------------
        # Generate and persist report
        # ------------------------------------------------------------------
        report = generate_report(records, deduplication, cmdi, self.config)

        report_path = output_path / "risk_report.json"
        report_path.write_text(to_json(report), encoding="utf-8")

        return report

    @staticmethod
    def _collect_files(input_path: Path) -> list[Path]:
        """Return a sorted list of ``.txt`` files from *input_path*.

        If *input_path* is a single file it is returned as a one-element
        list.  If it is a directory, all ``.txt`` files within it (non-
        recursive) are returned sorted by name.
        """
        if input_path.is_file():
            return [input_path]
        return sorted(input_path.glob("*.txt"))
