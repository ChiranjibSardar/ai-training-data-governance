"""License classification component for the RDI Framework.

This module provides the ``LicenseClassifier`` class, which classifies text
documents by their associated open-source license type.

.. note::
    This is a **Phase 2 stub**.  The full implementation (fine-tuned
    ``distilbert-base-uncased`` or zero-shot ``facebook/bart-large-mnli``)
    is deferred to Phase 2.  The stub returns a safe default for every input
    so the pipeline can run end-to-end.
"""

from rdi.models import LicenseResult


class LicenseClassifier:
    """Classifies text documents by open-source license type.

    Phase 2 stub — always returns ``LicenseResult(category="unknown",
    confidence=0.0, flagged_for_review=True)`` regardless of input.

    Args:
        confidence_threshold: Confidence below which a classification is
            flagged for manual review.  Defaults to ``0.7``.
    """

    def __init__(self, confidence_threshold: float = 0.7) -> None:
        self.confidence_threshold = confidence_threshold

    def classify(self, text: str) -> LicenseResult:
        """Classify the license type of *text*.

        Phase 2 stub — returns a default ``"unknown"`` result for any input.

        Args:
            text: The raw text document to classify.

        Returns:
            A ``LicenseResult`` with ``category="unknown"``,
            ``confidence=0.0``, and ``flagged_for_review=True``.
        """
        return LicenseResult(
            category="unknown",
            confidence=0.0,
            flagged_for_review=True,
        )
