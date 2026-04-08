"""Provenance Ledger — tamper-evident append-only log with SHA-256 hash chaining.

Each entry is chained to the previous via SHA-256, forming an immutable audit
trail for every record processed by the RDI pipeline.  Entries are persisted as
JSON Lines (one JSON object per line).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from rdi.exceptions import LedgerIOError
from rdi.models import LedgerEntry

GENESIS_PREVIOUS_HASH = "0" * 64


def _compute_entry_hash(
    content_hash: str,
    license_result: str,
    pii_result: str,
    timestamp: str,
    previous_hash: str,
) -> str:
    """Return the SHA-256 hex digest for a ledger entry's fields."""
    payload = content_hash + license_result + pii_result + timestamp + previous_hash
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ProvenanceLedger:
    """Append-only hash-chained ledger backed by a JSON Lines file.

    Parameters:
        path: Filesystem path for the ``.jsonl`` ledger file.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._entries: list[LedgerEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(
        self,
        content_hash: str,
        license_result: str,
        pii_result: str,
    ) -> LedgerEntry:
        """Create a new ledger entry, persist it, and return it.

        The entry is hash-chained to the previous entry (or to the genesis
        sentinel ``"0" * 64`` if this is the first entry).
        """
        previous_hash = (
            self._entries[-1].entry_hash if self._entries else GENESIS_PREVIOUS_HASH
        )
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_hash = _compute_entry_hash(
            content_hash, license_result, pii_result, timestamp, previous_hash
        )
        entry = LedgerEntry(
            content_hash=content_hash,
            license_result=license_result,
            pii_result=pii_result,
            timestamp=timestamp,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        self._persist_entry(entry)
        return entry

    def verify(self) -> tuple[bool, int | None, str | None]:
        """Validate the full chain from genesis to the latest entry.

        Returns:
            A 3-tuple ``(valid, index, description)`` where *valid* is
            ``True`` when the chain is intact.  On failure, *index* is the
            0-based position of the first corrupted entry and *description*
            explains the mismatch.
        """
        if not self._entries:
            return (True, None, None)

        for i, entry in enumerate(self._entries):
            # Check previous_hash linkage
            expected_prev = (
                GENESIS_PREVIOUS_HASH if i == 0 else self._entries[i - 1].entry_hash
            )
            if entry.previous_hash != expected_prev:
                return (
                    False,
                    i,
                    f"Entry {i}: previous_hash mismatch "
                    f"(expected {expected_prev!r}, got {entry.previous_hash!r})",
                )

            # Check entry_hash integrity
            expected_hash = _compute_entry_hash(
                entry.content_hash,
                entry.license_result,
                entry.pii_result,
                entry.timestamp,
                entry.previous_hash,
            )
            if entry.entry_hash != expected_hash:
                return (
                    False,
                    i,
                    f"Entry {i}: entry_hash mismatch "
                    f"(expected {expected_hash!r}, got {entry.entry_hash!r})",
                )

        return (True, None, None)

    @property
    def entries(self) -> list[LedgerEntry]:
        """Return a shallow copy of the current entries."""
        return list(self._entries)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load existing entries from the JSONL file, if it exists."""
        if not self._path.exists():
            return
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    self._entries.append(LedgerEntry(**data))
        except (OSError, IOError) as exc:
            raise LedgerIOError(
                f"Failed to read ledger file: {exc}",
                file_path=str(self._path),
            ) from exc

    def _persist_entry(self, entry: LedgerEntry) -> None:
        """Append a single entry as one JSON line."""
        try:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(entry)) + "\n")
        except (OSError, IOError) as exc:
            raise LedgerIOError(
                f"Failed to write to ledger file: {exc}",
                file_path=str(self._path),
            ) from exc
