"""Near-duplicate detection using MinHash with Locality-Sensitive Hashing.

Uses the ``datasketch`` library to build MinHash signatures for each document
and LSH to efficiently find candidate near-duplicate pairs above a configurable
Jaccard similarity threshold.
"""

from __future__ import annotations

from datasketch import MinHash, MinHashLSH

from rdi.models import DeduplicationResult


class Deduplicator:
    """Detect near-duplicate documents in a text corpus.

    Args:
        threshold: Jaccard similarity threshold for considering two
            documents as near-duplicates. Defaults to 0.8.
        num_perm: Number of permutation functions for MinHash.
            Defaults to 128.
    """

    def __init__(self, threshold: float = 0.8, num_perm: int = 128) -> None:
        self.threshold = threshold
        self.num_perm = num_perm

    def _build_minhash(self, text: str) -> MinHash:
        """Create a MinHash signature from word-level shingles."""
        m = MinHash(num_perm=self.num_perm)
        for word in text.lower().split():
            m.update(word.encode("utf-8"))
        return m

    def deduplicate(
        self, documents: list[tuple[str, str]]
    ) -> DeduplicationResult:
        """Identify near-duplicate clusters in a corpus.

        Args:
            documents: List of ``(doc_id, text)`` tuples.

        Returns:
            A :class:`DeduplicationResult` with cluster assignments and
            similarity scores for detected duplicate pairs.
        """
        if not documents:
            return DeduplicationResult(clusters=[], similarities=[])

        # Build MinHash signatures for every document.
        signatures: dict[str, MinHash] = {}
        for doc_id, text in documents:
            signatures[doc_id] = self._build_minhash(text)

        # Insert into LSH index to find candidate pairs.
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        for doc_id, mh in signatures.items():
            lsh.insert(doc_id, mh)

        # Query each document to discover its neighbours.
        similarities: list[tuple[str, str, float]] = []
        seen_pairs: set[tuple[str, str]] = set()

        for doc_id, mh in signatures.items():
            candidates = lsh.query(mh)
            for cand_id in candidates:
                if cand_id == doc_id:
                    continue
                pair = tuple(sorted((doc_id, cand_id)))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                sim = signatures[pair[0]].jaccard(signatures[pair[1]])
                similarities.append((pair[0], pair[1], sim))

        # Build clusters via union-find.
        parent: dict[str, str] = {doc_id: doc_id for doc_id, _ in documents}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for a, b, _ in similarities:
            union(a, b)

        # Group doc IDs by their root.
        cluster_map: dict[str, list[str]] = {}
        for doc_id, _ in documents:
            root = find(doc_id)
            cluster_map.setdefault(root, []).append(doc_id)

        clusters = list(cluster_map.values())

        return DeduplicationResult(clusters=clusters, similarities=similarities)
