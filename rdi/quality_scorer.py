"""Text quality scoring component for the RDI Framework.

This module provides the ``QualityScorer`` class, which assigns a quality
rating to text documents based on perplexity measurement.

.. note::
    This is a **Phase 2 stub**.  The full implementation (GPT-2 perplexity
    scoring with sliding-window tokenisation) is deferred to Phase 2.
    The stub returns a zero-score default for every input so the pipeline
    can run end-to-end.
"""

from rdi.models import QualityResult


class QualityScorer:
    """Scores text quality using perplexity measurement.

    Phase 2 stub — always returns ``QualityResult(perplexity=0.0,
    quality_rating=0.0)`` regardless of input.

    Args:
        quality_threshold: Minimum quality rating to pass validation.
            Defaults to ``0.3``.
    """

    def __init__(self, quality_threshold: float = 0.3) -> None:
        self.quality_threshold = quality_threshold

    def score(self, text: str) -> QualityResult:
        """Compute a quality score for *text*.

        Phase 2 stub — returns a default zero-score result for any input.

        Args:
            text: The raw text document to score.

        Returns:
            A ``QualityResult`` with ``perplexity=0.0`` and
            ``quality_rating=0.0``.
        """
        return QualityResult(perplexity=0.0, quality_rating=0.0)
