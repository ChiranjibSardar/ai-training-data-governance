"""Unit tests for the PIIScanner class."""

import pytest

from rdi.models import PIIEntity, PIIScanResult
from rdi.pii_scanner import PIIScanner


@pytest.fixture(scope="module")
def scanner() -> PIIScanner:
    """Module-scoped scanner so the spaCy model loads only once."""
    return PIIScanner()


class TestPIIScannerEmptyInput:
    """Empty / blank input handling."""

    def test_empty_string(self, scanner: PIIScanner) -> None:
        result = scanner.scan("")
        assert result == PIIScanResult(redacted_text="", entities=[])

    def test_none_like_empty(self, scanner: PIIScanner) -> None:
        """Whitespace-only is *not* empty — it should still go through the
        analyzer — but a truly empty string must short-circuit."""
        result = scanner.scan("")
        assert result.redacted_text == ""
        assert result.entities == []


class TestPIIScannerDetection:
    """Verify that known PII patterns are detected and redacted."""

    def test_email_redaction(self, scanner: PIIScanner) -> None:
        text = "Contact us at test@example.com for details."
        result = scanner.scan(text)
        assert "[EMAIL]" in result.redacted_text
        assert "test@example.com" not in result.redacted_text
        email_entities = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(email_entities) >= 1

    def test_person_redaction(self, scanner: PIIScanner) -> None:
        text = "Please reach out to John Smith regarding the project."
        result = scanner.scan(text)
        assert "[PERSON]" in result.redacted_text
        person_entities = [e for e in result.entities if e.entity_type == "PERSON"]
        assert len(person_entities) >= 1

    def test_phone_redaction(self, scanner: PIIScanner) -> None:
        text = "Call me at 555-123-4567 tomorrow."
        result = scanner.scan(text)
        assert "[PHONE]" in result.redacted_text
        phone_entities = [e for e in result.entities if e.entity_type == "PHONE"]
        assert len(phone_entities) >= 1

    def test_ssn_redaction(self, scanner: PIIScanner) -> None:
        text = "My SSN is 234-56-7890 and it should be private."
        result = scanner.scan(text)
        assert "[SSN]" in result.redacted_text
        assert "234-56-7890" not in result.redacted_text
        ssn_entities = [e for e in result.entities if e.entity_type == "SSN"]
        assert len(ssn_entities) >= 1

    def test_no_pii_text(self, scanner: PIIScanner) -> None:
        text = "The weather is nice today."
        result = scanner.scan(text)
        assert result.redacted_text == text
        assert result.entities == []


class TestPIIScannerEntityMetadata:
    """Verify entity metadata is populated correctly."""

    def test_entity_fields(self, scanner: PIIScanner) -> None:
        text = "Email me at alice@example.com please."
        result = scanner.scan(text)
        email_entities = [e for e in result.entities if e.entity_type == "EMAIL"]
        assert len(email_entities) >= 1
        entity = email_entities[0]
        assert entity.start >= 0
        assert entity.end > entity.start
        assert entity.end <= len(text)
        assert 0.0 <= entity.confidence <= 1.0
        assert entity.original_text == text[entity.start : entity.end]

    def test_entities_sorted_by_start(self, scanner: PIIScanner) -> None:
        text = "John Smith's email is john@example.com and SSN is 123-45-6789."
        result = scanner.scan(text)
        starts = [e.start for e in result.entities]
        assert starts == sorted(starts)
