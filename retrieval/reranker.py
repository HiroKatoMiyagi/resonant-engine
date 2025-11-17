"""
Reranker - リランキング

複数検索結果を統合し、最終順位を決定します。
「ノイズを抑え、最も澄んだ共鳴を前面に出す整音」
"""

from typing import Dict, List, Set

from memory_store.models import MemoryResult

from .strategy import SearchParams


class Reranker:
    """
    検索結果のリランキング

    複数の検索手法から得られた結果を統合し、
    重複を排除して最終的な順位を決定します。
    """

    def rerank(
        self, search_results: Dict[str, List[MemoryResult]], params: SearchParams
    ) -> List[MemoryResult]:
        """
        複数検索結果を統合しリランキング

        Args:
            search_results: {検索手法: 結果リスト}
            params: 検索パラメータ

        Returns:
            List[MemoryResult]: リランキング後の結果
        """
        # 1. スコア正規化
        normalized = self._normalize_scores(search_results)

        # 2. IDベースで統合
        merged = self._merge_results(normalized, params)

        # 3. 重複排除
        unique = self._deduplicate(merged)

        # 4. 最終ソート
        unique.sort(key=lambda r: r.similarity, reverse=True)

        return unique[: params.limit]

    def _normalize_scores(
        self, search_results: Dict[str, List[MemoryResult]]
    ) -> Dict[str, List[MemoryResult]]:
        """
        スコアをMin-Max正規化

        各検索手法の結果を0-1の範囲に正規化します。
        """
        normalized: Dict[str, List[MemoryResult]] = {}

        for method, results in search_results.items():
            if not results:
                normalized[method] = []
                continue

            scores = [r.similarity for r in results]
            min_score = min(scores)
            max_score = max(scores)

            if max_score - min_score < 1e-6:
                # 全て同じスコアの場合
                for r in results:
                    r.similarity = 1.0
            else:
                for r in results:
                    r.similarity = (r.similarity - min_score) / (max_score - min_score)

            normalized[method] = results

        return normalized

    def _merge_results(
        self, search_results: Dict[str, List[MemoryResult]], params: SearchParams
    ) -> List[MemoryResult]:
        """
        IDベースで結果を統合し、加重平均スコアを計算

        複数の検索手法で同じ記憶が見つかった場合、
        両方のスコアを重み付けして統合します。
        """
        merged: Dict[int, Dict] = {}

        # ベクトル検索結果
        for r in search_results.get("vector", []):
            merged[r.id] = {
                "result": r,
                "vector_score": r.similarity,
                "keyword_score": 0.0,
                "temporal_score": 0.0,
            }

        # キーワード検索結果
        for r in search_results.get("keyword", []):
            if r.id in merged:
                merged[r.id]["keyword_score"] = r.similarity
            else:
                merged[r.id] = {
                    "result": r,
                    "vector_score": 0.0,
                    "keyword_score": r.similarity,
                    "temporal_score": 0.0,
                }

        # 時系列検索結果（ベクトルスコアとして扱う）
        for r in search_results.get("temporal", []):
            if r.id in merged:
                # 既存のスコアと時系列スコアを統合
                merged[r.id]["temporal_score"] = r.similarity
            else:
                merged[r.id] = {
                    "result": r,
                    "vector_score": r.similarity,
                    "keyword_score": 0.0,
                    "temporal_score": r.similarity,
                }

        # 加重平均スコア計算
        final_results: List[MemoryResult] = []
        for item in merged.values():
            # 基本スコア計算
            vector_score = item["vector_score"]
            keyword_score = item["keyword_score"]
            temporal_score = item["temporal_score"]

            # 時系列スコアがある場合は、ベクトルスコアとして扱う
            if temporal_score > 0:
                vector_score = max(vector_score, temporal_score)

            final_score = params.vector_weight * vector_score + params.keyword_weight * keyword_score

            # 複数の検索手法でヒットした場合のボーナス
            hit_count = sum(
                [
                    1 if item["vector_score"] > 0 else 0,
                    1 if item["keyword_score"] > 0 else 0,
                    1 if item["temporal_score"] > 0 else 0,
                ]
            )
            if hit_count > 1:
                # 複数手法でヒットした場合は5%ボーナス
                final_score = min(1.0, final_score * 1.05)

            item["result"].similarity = final_score
            final_results.append(item["result"])

        return final_results

    def _deduplicate(
        self, results: List[MemoryResult], threshold: float = 0.95
    ) -> List[MemoryResult]:
        """
        重複排除

        同一IDの記憶を排除します。
        将来的にはEmbedding類似度での重複判定も実装予定。

        Args:
            results: 検索結果リスト
            threshold: 類似度閾値（将来用）

        Returns:
            重複排除後の結果
        """
        seen: Set[int] = set()
        unique: List[MemoryResult] = []

        for r in results:
            if r.id not in seen:
                unique.append(r)
                seen.add(r.id)

        return unique

    def calculate_mrr(
        self, results: List[MemoryResult], relevant_ids: List[int]
    ) -> float:
        """
        Mean Reciprocal Rank (MRR) を計算

        Args:
            results: 検索結果リスト
            relevant_ids: 関連する記憶IDリスト

        Returns:
            MRRスコア (0.0 - 1.0)
        """
        if not relevant_ids:
            return 0.0

        for i, result in enumerate(results):
            if result.id in relevant_ids:
                return 1.0 / (i + 1)

        return 0.0

    def calculate_hit_at_k(
        self, results: List[MemoryResult], relevant_ids: List[int], k: int = 5
    ) -> float:
        """
        Hit@K を計算

        Args:
            results: 検索結果リスト
            relevant_ids: 関連する記憶IDリスト
            k: 上位K件

        Returns:
            Hit@Kスコア (0.0 or 1.0)
        """
        if not relevant_ids:
            return 0.0

        top_k_ids = {r.id for r in results[:k]}
        if any(rid in top_k_ids for rid in relevant_ids):
            return 1.0

        return 0.0
