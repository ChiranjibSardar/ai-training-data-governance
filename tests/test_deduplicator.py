"""Unit tests for the Deduplicator component."""

import pytest

from rdi.deduplicator import Deduplicator
from rdi.models import DeduplicationResult


class TestDeduplicatorEmptyCorpus:
    """Empty corpus returns empty results."""

    def test_empty_list_returns_empty_result(self):
        dedup = Deduplicator()
        result = dedup.deduplicate([])
        assert result.clusters == []
        assert result.similarities == []


class TestDeduplicatorIdenticalDocuments:
    """Identical documents are placed in the same cluster."""

    def test_identical_docs_same_cluster(self):
        dedup = Deduplicator()
        text = "the quick brown fox jumps over the lazy dog"
        docs = [("doc1", text), ("doc2", text)]
        result = dedup.deduplicate(docs)

        # Both doc IDs must appear in the same cluster.
        for cluster in result.clusters:
            if "doc1" in cluster:
                assert "doc2" in cluster
                break
        else:
            pytest.fail("doc1 not found in any cluster")

    def test_identical_docs_have_similarity_pair(self):
        dedup = Deduplicator()
        text = "the quick brown fox jumps over the lazy dog"
        docs = [("doc1", text), ("doc2", text)]
        result = dedup.deduplicate(docs)

        assert len(result.similarities) >= 1
        pair_ids = {(a, b) for a, b, _ in result.similarities}
        assert ("doc1", "doc2") in pair_ids or ("doc2", "doc1") in pair_ids


class TestDeduplicatorUnrelatedDocuments:
    """Unrelated documents end up in separate clusters."""

    def test_unrelated_docs_separate_clusters(self):
        dedup = Deduplicator()
        docs = [
            ("doc1", "the quick brown fox jumps over the lazy dog"),
            ("doc2", "quantum mechanics describes subatomic particle behaviour"),
        ]
        result = dedup.deduplicate(docs)

        # Each doc should be in its own cluster.
        for cluster in result.clusters:
            assert not ("doc1" in cluster and "doc2" in cluster), (
                "Unrelated documents should not share a cluster"
            )


class TestDeduplicatorPartitioning:
    """Every doc ID appears in exactly one cluster."""

    def test_all_doc_ids_in_exactly_one_cluster(self):
        dedup = Deduplicator()
        docs = [
            ("a", "hello world this is a test document"),
            ("b", "hello world this is a test document"),
            ("c", "completely different content about space exploration"),
            ("d", "another unique document about cooking recipes"),
        ]
        result = dedup.deduplicate(docs)

        all_ids = [doc_id for doc_id, _ in docs]
        clustered_ids = [doc_id for cluster in result.clusters for doc_id in cluster]

        # Every input ID appears exactly once across all clusters.
        assert sorted(clustered_ids) == sorted(all_ids)


class TestDeduplicatorSimilarityScores:
    """Similarity scores are in [0.0, 1.0]."""

    def test_similarity_scores_in_valid_range(self):
        dedup = Deduplicator()
        text = "the quick brown fox jumps over the lazy dog"
        docs = [("doc1", text), ("doc2", text)]
        result = dedup.deduplicate(docs)

        for _, _, sim in result.similarities:
            assert 0.0 <= sim <= 1.0


class TestDeduplicatorConfigurableThreshold:
    """Configurable threshold affects clustering behaviour."""

    def test_low_threshold_clusters_more(self):
        # Two somewhat similar docs.
        docs = [
            ("doc1", "the quick brown fox jumps over the lazy dog today"),
            ("doc2", "the quick brown fox leaps over the lazy cat today"),
        ]

        strict = Deduplicator(threshold=0.95)
        lenient = Deduplicator(threshold=0.3)

        strict_result = strict.deduplicate(docs)
        lenient_result = lenient.deduplicate(docs)

        # With a lenient threshold we expect fewer clusters (more merging).
        assert len(lenient_result.clusters) <= len(strict_result.clusters)

    def test_custom_num_perm(self):
        dedup = Deduplicator(num_perm=64)
        text = "the quick brown fox jumps over the lazy dog"
        docs = [("doc1", text), ("doc2", text)]
        result = dedup.deduplicate(docs)

        # Should still detect identical docs regardless of num_perm.
        for cluster in result.clusters:
            if "doc1" in cluster:
                assert "doc2" in cluster
                break


class TestDeduplicatorReturnType:
    """Return type is DeduplicationResult."""

    def test_returns_deduplication_result(self):
        dedup = Deduplicator()
        result = dedup.deduplicate([("x", "some text here")])
        assert isinstance(result, DeduplicationResult)
