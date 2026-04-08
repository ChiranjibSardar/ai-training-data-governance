"""PII Scanner — detects and redacts personally identifiable information.

Uses Microsoft Presidio with a spaCy NER backend (`en_core_web_lg`) plus
regex-based recognizers for emails, phone numbers, and SSNs.  The spaCy
model and Presidio engine are loaded lazily on first call to `scan()`.
"""

from __future__ import annotations

from rdi.exceptions import ModelLoadError
from rdi.models import PIIEntity, PIIScanResult

# Mapping from Presidio entity types to our redaction placeholders.
_ENTITY_TYPE_MAP: dict[str, str] = {
    "EMAIL_ADDRESS": "EMAIL",
    "PERSON": "PERSON",
    "PHONE_NUMBER": "PHONE",
    "LOCATION": "ADDRESS",
    "US_SSN": "SSN",
}

# Only these Presidio entity types are recognised by the scanner.
_SUPPORTED_ENTITIES = list(_ENTITY_TYPE_MAP.keys())


class PIIScanner:
    """Scans text for PII and returns a redacted copy with entity metadata.

    The underlying spaCy model and Presidio ``AnalyzerEngine`` are created
    on the first invocation of :meth:`scan` (lazy loading) so that importing
    this module is cheap.
    """

    def __init__(self) -> None:
        self._analyzer = None

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _ensure_analyzer(self) -> None:
        """Create the Presidio AnalyzerEngine if it hasn't been created yet."""
        if self._analyzer is not None:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [
                        {"lang_code": "en", "model_name": "en_core_web_lg"},
                    ],
                }
            )
            nlp_engine = provider.create_engine()
            self._analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=["en"],
            )
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load PII scanner model: {exc}",
                model_name="en_core_web_lg",
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, text: str) -> PIIScanResult:
        """Scan *text* for PII, returning redacted text and entity metadata.

        Parameters
        ----------
        text:
            Raw input text to scan.

        Returns
        -------
        PIIScanResult
            ``redacted_text`` has each detected entity replaced by a
            type-specific placeholder such as ``[EMAIL]`` or ``[PERSON]``.
            ``entities`` lists every detected :class:`PIIEntity`.
        """
        if not text:
            return PIIScanResult(redacted_text="", entities=[])

        self._ensure_analyzer()

        results = self._analyzer.analyze(
            text=text,
            language="en",
            entities=_SUPPORTED_ENTITIES,
        )

        # Sort by start position descending so we can replace from the end
        # of the string without invalidating earlier offsets.
        results = sorted(results, key=lambda r: r.start, reverse=True)

        entities: list[PIIEntity] = []
        redacted = text

        for result in results:
            mapped_type = _ENTITY_TYPE_MAP.get(result.entity_type)
            if mapped_type is None:
                continue  # skip unsupported entity types

            placeholder = f"[{mapped_type}]"
            original_text = text[result.start : result.end]

            entities.append(
                PIIEntity(
                    entity_type=mapped_type,
                    start=result.start,
                    end=result.end,
                    confidence=result.score,
                    original_text=original_text,
                )
            )

            redacted = redacted[: result.start] + placeholder + redacted[result.end :]

        # Return entities in document order (ascending start).
        entities.sort(key=lambda e: e.start)

        return PIIScanResult(redacted_text=redacted, entities=entities)
