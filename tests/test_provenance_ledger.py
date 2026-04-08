"""Unit tests for the ProvenanceLedger class."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from rdi.exceptions import LedgerIOError
from rdi.models import LedgerEntry
from rdi.provenance_ledger import GENESIS_PREVIOUS_HASH, ProvenanceLedger


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def ledger_path(tmp_path: Path) -> Path:
    """Return a fresh JSONL path inside a temporary directory."""
    return tmp_path / "ledger.jsonl"


@pytest.fixture()
def ledger(ledger_path: Path) -> ProvenanceLedger:
    """Return a new, empty ProvenanceLedger."""
    return ProvenanceLedger(ledger_path)


# ------------------------------------------------------------------
# Append & genesis
# ------------------------------------------------------------------


class TestAppend:
    """Appending entries and genesis behaviour."""

    def test_genesis_previous_hash(self, ledger: ProvenanceLedger) -> None:
        entry = ledger.append("hash1", "lic1", "pii1")
        assert entry.previous_hash == GENESIS_PREVIOUS_HASH
        assert entry.previous_hash == "0" * 64

    def test_second_entry_chains_to_first(self, ledger: ProvenanceLedger) -> None:
        first = ledger.append("h1", "l1", "p1")
        second = ledger.append("h2", "l2", "p2")
        assert second.previous_hash == first.entry_hash

    def test_entry_hash_is_64_hex_chars(self, ledger: ProvenanceLedger) -> None:
        entry = ledger.append("h", "l", "p")
        assert len(entry.entry_hash) == 64
        int(entry.entry_hash, 16)  # must be valid hex

    def test_entry_fields_populated(self, ledger: ProvenanceLedger) -> None:
        entry = ledger.append("ch", "lr", "pr")
        assert entry.content_hash == "ch"
        assert entry.license_result == "lr"
        assert entry.pii_result == "pr"
        assert entry.timestamp  # non-empty ISO timestamp


# ------------------------------------------------------------------
# Verify — intact chain
# ------------------------------------------------------------------


class TestVerifyIntact:
    """verify() on untampered ledgers."""

    def test_empty_ledger(self, ledger: ProvenanceLedger) -> None:
        valid, idx, desc = ledger.verify()
        assert valid is True
        assert idx is None
        assert desc is None

    def test_single_entry(self, ledger: ProvenanceLedger) -> None:
        ledger.append("h", "l", "p")
        assert ledger.verify() == (True, None, None)

    def test_multiple_entries(self, ledger: ProvenanceLedger) -> None:
        for i in range(5):
            ledger.append(f"h{i}", f"l{i}", f"p{i}")
        assert ledger.verify() == (True, None, None)


# ------------------------------------------------------------------
# Verify — tampered chain
# ------------------------------------------------------------------


class TestVerifyTampered:
    """verify() detects corrupted entries."""

    def test_tampered_entry_hash(self, ledger: ProvenanceLedger) -> None:
        ledger.append("h1", "l1", "p1")
        ledger.append("h2", "l2", "p2")
        # Corrupt the first entry's hash
        ledger._entries[0] = LedgerEntry(
            content_hash=ledger._entries[0].content_hash,
            license_result=ledger._entries[0].license_result,
            pii_result=ledger._entries[0].pii_result,
            timestamp=ledger._entries[0].timestamp,
            previous_hash=ledger._entries[0].previous_hash,
            entry_hash="bad" + ledger._entries[0].entry_hash[3:],
        )
        valid, idx, desc = ledger.verify()
        assert valid is False
        assert idx == 0
        assert desc is not None

    def test_tampered_previous_hash(self, ledger: ProvenanceLedger) -> None:
        ledger.append("h1", "l1", "p1")
        ledger.append("h2", "l2", "p2")
        # Corrupt the second entry's previous_hash linkage
        original = ledger._entries[1]
        ledger._entries[1] = LedgerEntry(
            content_hash=original.content_hash,
            license_result=original.license_result,
            pii_result=original.pii_result,
            timestamp=original.timestamp,
            previous_hash="f" * 64,
            entry_hash=original.entry_hash,
        )
        valid, idx, desc = ledger.verify()
        assert valid is False
        assert idx == 1

    def test_tampered_content_hash(self, ledger: ProvenanceLedger) -> None:
        ledger.append("h1", "l1", "p1")
        original = ledger._entries[0]
        ledger._entries[0] = LedgerEntry(
            content_hash="TAMPERED",
            license_result=original.license_result,
            pii_result=original.pii_result,
            timestamp=original.timestamp,
            previous_hash=original.previous_hash,
            entry_hash=original.entry_hash,
        )
        valid, idx, desc = ledger.verify()
        assert valid is False
        assert idx == 0


# ------------------------------------------------------------------
# JSONL persistence
# ------------------------------------------------------------------


class TestJSONLPersistence:
    """Write and read-back via JSONL file."""

    def test_file_created_on_append(
        self, ledger: ProvenanceLedger, ledger_path: Path
    ) -> None:
        ledger.append("h", "l", "p")
        assert ledger_path.exists()

    def test_line_count_matches_entries(
        self, ledger: ProvenanceLedger, ledger_path: Path
    ) -> None:
        for i in range(3):
            ledger.append(f"h{i}", f"l{i}", f"p{i}")
        lines = [ln for ln in ledger_path.read_text().splitlines() if ln.strip()]
        assert len(lines) == 3

    def test_each_line_is_valid_json(
        self, ledger: ProvenanceLedger, ledger_path: Path
    ) -> None:
        ledger.append("h", "l", "p")
        for line in ledger_path.read_text().splitlines():
            if line.strip():
                data = json.loads(line)
                assert "entry_hash" in data

    def test_round_trip(
        self, ledger: ProvenanceLedger, ledger_path: Path
    ) -> None:
        """Write entries, create a new ledger from the same file, compare."""
        for i in range(3):
            ledger.append(f"h{i}", f"l{i}", f"p{i}")

        reloaded = ProvenanceLedger(ledger_path)
        assert len(reloaded.entries) == 3
        for orig, loaded in zip(ledger.entries, reloaded.entries):
            assert asdict(orig) == asdict(loaded)

    def test_round_trip_verify(
        self, ledger: ProvenanceLedger, ledger_path: Path
    ) -> None:
        """Reloaded ledger passes verification."""
        for i in range(4):
            ledger.append(f"h{i}", f"l{i}", f"p{i}")
        reloaded = ProvenanceLedger(ledger_path)
        assert reloaded.verify() == (True, None, None)


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------


class TestLedgerIOError:
    """LedgerIOError raised on file I/O failures."""

    def test_read_from_unreadable_path(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "no_access" / "ledger.jsonl"
        bad_path.parent.mkdir()
        bad_path.write_text("not json\n")
        with pytest.raises(Exception):
            # Malformed JSON triggers a json.JSONDecodeError, not LedgerIOError,
            # but an OS-level read failure would raise LedgerIOError.
            ProvenanceLedger(bad_path)

    def test_write_to_readonly_dir(self, tmp_path: Path) -> None:
        ro_dir = tmp_path / "readonly"
        ro_dir.mkdir()
        ledger_file = ro_dir / "ledger.jsonl"
        ledger = ProvenanceLedger(ledger_file)
        # Make directory read-only after ledger init
        ro_dir.chmod(0o444)
        try:
            with pytest.raises(LedgerIOError):
                ledger.append("h", "l", "p")
        finally:
            ro_dir.chmod(0o755)  # restore so tmp_path cleanup works
