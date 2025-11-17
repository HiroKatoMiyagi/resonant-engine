"""
Reranker Tests
"""

import pytest
from datetime import datetime, timezone

from retrieval.reranker import Reranker
from retrieval.strategy import SearchParams
from memory_store.models import MemoryResult, MemoryType


@pytest.fixture
def reranker():
    """Rerankerのフィクスチャ"""
    return Reranker()


@pytest.fixture
def sample_results():
    """サンプル検索結果"""
    now = datetime.now(timezone.utc)
    return {
        "vector": [
            MemoryResult(
                id=1,
                content="Resonant Engine philosophy",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=2,
                content="Memory Store architecture",
                memory_type=MemoryType.LONGTERM,
                similarity=0.7,
                created_at=now,
                metadata={},
            ),
        ],
        "keyword": [
            MemoryResult(
                id=1,
                content="Resonant Engine philosophy",
                memory_type=MemoryType.LONGTERM,
                similarity=0.8,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=3,
                content="Engine configuration",
                memory_type=MemoryType.LONGTERM,
                similarity=0.6,
                created_at=now,
                metadata={},
            ),
        ],
    }


class TestScoreNormalization:
    """スコア正規化のテスト"""

    def test_normalize_scores_minmax(self, reranker):
        """Min-Max正規化"""
        now = datetime.now(timezone.utc)
        search_results = {
            "vector": [
                MemoryResult(
                    id=1,
                    content="A",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.9,
                    created_at=now,
                    metadata={},
                ),
                MemoryResult(
                    id=2,
                    content="B",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.5,
                    created_at=now,
                    metadata={},
                ),
            ]
        }

        normalized = reranker._normalize_scores(search_results)

        # 最大値は1.0、最小値は0.0
        assert normalized["vector"][0].similarity == 1.0
        assert normalized["vector"][1].similarity == 0.0

    def test_normalize_same_scores(self, reranker):
        """同じスコアの正規化"""
        now = datetime.now(timezone.utc)
        search_results = {
            "vector": [
                MemoryResult(
                    id=1,
                    content="A",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.8,
                    created_at=now,
                    metadata={},
                ),
                MemoryResult(
                    id=2,
                    content="B",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.8,
                    created_at=now,
                    metadata={},
                ),
            ]
        }

        normalized = reranker._normalize_scores(search_results)

        # 同じスコアの場合は全て1.0
        assert normalized["vector"][0].similarity == 1.0
        assert normalized["vector"][1].similarity == 1.0

    def test_normalize_empty_results(self, reranker):
        """空結果の正規化"""
        search_results = {"vector": []}
        normalized = reranker._normalize_scores(search_results)
        assert normalized["vector"] == []


class TestResultMerging:
    """結果統合のテスト"""

    def test_merge_results_both_methods(self, reranker, sample_results):
        """両方の手法で見つかった場合の統合"""
        params = SearchParams(vector_weight=0.6, keyword_weight=0.4)
        normalized = reranker._normalize_scores(sample_results)
        merged = reranker._merge_results(normalized, params)

        # ID=1は両方に含まれる
        result_id1 = next((r for r in merged if r.id == 1), None)
        assert result_id1 is not None
        # ボーナス込みで高スコア
        assert result_id1.similarity > 0.9

    def test_merge_results_vector_only(self, reranker):
        """ベクトル検索のみの統合"""
        now = datetime.now(timezone.utc)
        search_results = {
            "vector": [
                MemoryResult(
                    id=1,
                    content="A",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.9,
                    created_at=now,
                    metadata={},
                )
            ],
            "keyword": [],
        }

        params = SearchParams(vector_weight=0.7, keyword_weight=0.3)
        normalized = reranker._normalize_scores(search_results)
        merged = reranker._merge_results(normalized, params)

        assert len(merged) == 1
        # vector_weight * 1.0 + keyword_weight * 0.0 = 0.7
        assert merged[0].similarity == pytest.approx(0.7, rel=0.01)

    def test_merge_results_with_temporal(self, reranker):
        """時系列検索結果の統合"""
        now = datetime.now(timezone.utc)
        search_results = {
            "temporal": [
                MemoryResult(
                    id=1,
                    content="A",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.85,
                    created_at=now,
                    metadata={},
                )
            ]
        }

        params = SearchParams(vector_weight=0.7, keyword_weight=0.3)
        normalized = reranker._normalize_scores(search_results)
        merged = reranker._merge_results(normalized, params)

        assert len(merged) == 1
        # temporal_scoreはvector_scoreとして扱われる
        assert merged[0].similarity > 0.6


class TestDeduplication:
    """重複排除のテスト"""

    def test_deduplicate_by_id(self, reranker):
        """IDベースの重複排除"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.8,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=2,
                content="B",
                memory_type=MemoryType.LONGTERM,
                similarity=0.7,
                created_at=now,
                metadata={},
            ),
        ]

        unique = reranker._deduplicate(results)

        assert len(unique) == 2
        assert unique[0].id == 1
        assert unique[1].id == 2

    def test_deduplicate_preserves_first(self, reranker):
        """重複排除時は最初の結果を保持"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.7,
                created_at=now,
                metadata={},
            ),
        ]

        unique = reranker._deduplicate(results)

        assert len(unique) == 1
        assert unique[0].similarity == 0.9


class TestReranking:
    """リランキング全体のテスト"""

    def test_rerank_full_flow(self, reranker, sample_results):
        """リランキング全体フロー"""
        params = SearchParams(vector_weight=0.6, keyword_weight=0.4, limit=10)
        results = reranker.rerank(sample_results, params)

        # 両方の手法で見つかったID=1が最高スコア
        assert results[0].id == 1
        assert len(results) == 3  # ID=1, 2, 3

    def test_rerank_respects_limit(self, reranker):
        """リランキングはlimitを尊重"""
        now = datetime.now(timezone.utc)
        search_results = {
            "vector": [
                MemoryResult(
                    id=i,
                    content=f"Memory {i}",
                    memory_type=MemoryType.LONGTERM,
                    similarity=0.9 - i * 0.1,
                    created_at=now,
                    metadata={},
                )
                for i in range(10)
            ]
        }

        params = SearchParams(limit=5)
        results = reranker.rerank(search_results, params)

        assert len(results) == 5

    def test_rerank_sorted_by_similarity(self, reranker, sample_results):
        """結果は類似度順にソート"""
        params = SearchParams()
        results = reranker.rerank(sample_results, params)

        for i in range(len(results) - 1):
            assert results[i].similarity >= results[i + 1].similarity


class TestMetricsCalculation:
    """メトリクス計算のテスト"""

    def test_calculate_mrr_hit_first(self, reranker):
        """MRR: 最初にヒット"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=2,
                content="B",
                memory_type=MemoryType.LONGTERM,
                similarity=0.8,
                created_at=now,
                metadata={},
            ),
        ]

        mrr = reranker.calculate_mrr(results, [1])
        assert mrr == 1.0

    def test_calculate_mrr_hit_second(self, reranker):
        """MRR: 2番目にヒット"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            ),
            MemoryResult(
                id=2,
                content="B",
                memory_type=MemoryType.LONGTERM,
                similarity=0.8,
                created_at=now,
                metadata={},
            ),
        ]

        mrr = reranker.calculate_mrr(results, [2])
        assert mrr == 0.5

    def test_calculate_mrr_no_hit(self, reranker):
        """MRR: ヒットなし"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=1,
                content="A",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9,
                created_at=now,
                metadata={},
            )
        ]

        mrr = reranker.calculate_mrr(results, [99])
        assert mrr == 0.0

    def test_calculate_hit_at_k_success(self, reranker):
        """Hit@K: ヒット"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=i,
                content=f"Memory {i}",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9 - i * 0.1,
                created_at=now,
                metadata={},
            )
            for i in range(10)
        ]

        hit = reranker.calculate_hit_at_k(results, [3], k=5)
        assert hit == 1.0

    def test_calculate_hit_at_k_miss(self, reranker):
        """Hit@K: ミス"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=i,
                content=f"Memory {i}",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9 - i * 0.1,
                created_at=now,
                metadata={},
            )
            for i in range(10)
        ]

        hit = reranker.calculate_hit_at_k(results, [8], k=5)
        assert hit == 0.0
