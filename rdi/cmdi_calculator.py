"""Cross-Modal Diversity Index (CMDI) calculator for the RDI Framework.

This module provides the ``CMDICalculator`` class, which computes linguistic,
topical, and geographic diversity sub-indices for a text corpus and combines
them into a weighted composite score.

.. note::
    This is a **Phase 2 stub**.  The full implementation (language detection
    via ``langdetect``, LDA via ``gensim``, geographic NER via ``spacy``)
    is deferred to Phase 2.  The stub returns all-zero scores for every
    input so the pipeline can run end-to-end.
"""

from rdi.models import CMDIResult


class CMDICalculator:
    """Computes the Cross-Modal Diversity Index for a text corpus.

    Phase 2 stub — always returns ``CMDIResult(composite=0.0,
    linguistic=0.0, topical=0.0, geographic=0.0)`` regardless of input.

    Args:
        weights: A triple ``(linguistic, topical, geographic)`` of weights
            that should sum to approximately 1.0.  Defaults to
            ``(0.333, 0.333, 0.334)``.
    """

    def __init__(
        self,
        weights: tuple[float, float, float] = (0.333, 0.333, 0.334),
    ) -> None:
        self.weights = weights

    def compute(self, texts: list[str]) -> CMDIResult:
        """Compute diversity sub-indices and composite score for *texts*.

        Phase 2 stub — returns all-zero scores for any input.

        Args:
            texts: A list of text documents comprising the corpus.

        Returns:
            A ``CMDIResult`` with ``composite=0.0``, ``linguistic=0.0``,
            ``topical=0.0``, and ``geographic=0.0``.
        """
        return CMDIResult(
            composite=0.0,
            linguistic=0.0,
            topical=0.0,
            geographic=0.0,
        )
