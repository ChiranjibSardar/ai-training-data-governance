"""Toxicity Filter — multi-category toxicity scoring for text.

Uses Unitary's Detoxify library (``unitary/toxic-bert``) to score text
across six toxicity categories.  The model is loaded lazily on the first
call to :meth:`score` so that importing this module is cheap.
"""

from __future__ import annotations

from rdi.exceptions import ModelLoadError
from rdi.models import ToxicityResult

# The six toxicity categories returned by the Detoxify model.
_CATEGORIES: list[str] = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
]

# Score above which a record is flagged as high-risk.
_HIGH_RISK_THRESHOLD: float = 0.8


class ToxicityFilter:
    """Scores text for toxicity across multiple categories.

    The underlying Detoxify model is created on the first invocation of
    :meth:`score` (lazy loading) so that importing this module is cheap.
    """

    def __init__(self) -> None:
        self._model = None

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _ensure_model(self) -> None:
        """Load the Detoxify model if it hasn't been loaded yet."""
        if self._model is not None:
            return

        try:
            from detoxify import Detoxify

            self._model = Detoxify("original")
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load toxicity model: {exc}",
                model_name="unitary/toxic-bert",
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, text: str) -> ToxicityResult:
        """Score *text* for toxicity across six categories.

        Parameters
        ----------
        text:
            Raw input text to score.

        Returns
        -------
        ToxicityResult
            ``scores`` maps each category name to a float in [0.0, 1.0].
            ``is_high_risk`` is ``True`` if any score exceeds 0.8.
        """
        if not text or not text.strip():
            scores = {cat: 0.0 for cat in _CATEGORIES}
            return ToxicityResult(scores=scores, is_high_risk=False)

        self._ensure_model()

        raw = self._model.predict(text)

        scores: dict[str, float] = {}
        for cat in _CATEGORIES:
            scores[cat] = float(raw.get(cat, 0.0))

        is_high_risk = any(s > _HIGH_RISK_THRESHOLD for s in scores.values())

        return ToxicityResult(scores=scores, is_high_risk=is_high_risk)
