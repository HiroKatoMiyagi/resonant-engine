import asyncpg
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
import re

from .models import (
    TermDefinition, TermDrift, DriftType, DriftStatus,
    TermCategory
)

logger = logging.getLogger(__name__)

class TermDriftDetector:
    """用語ドリフト検出サービス"""
    
    # 類似度閾値
    SIMILARITY_THRESHOLD = 0.7
    
    # ドメインオブジェクトキーワード
    DOMAIN_OBJECTS = [
        "Intent", "Memory", "Bridge", "Yuno", "Kana", "Tsumu",
        "Contradiction", "Choice", "Session", "Profile"
    ]
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def extract_terms_from_text(
        self,
        text: str,
        source: str
    ) -> List[Dict[str, Any]]:
        """
        テキストから用語定義を抽出
        
        Args:
            text: 分析対象テキスト
            source: ソース識別子（ファイル名等）
            
        Returns:
            List[Dict]: 抽出された用語定義リスト
        """
        extracted_terms = []
        
        # パターン1: "XはYである" / "X is Y"
        definition_patterns = [
            r'「([^」]+)」は[、]?(.+?)(?:です|である|とする)',
            r'(\w+)\s*(?:is|means|refers to)\s*(.+?)(?:\.|$)',
            r'(?:^|\n)#\s*(\w+)\s*\n+(.+?)(?=\n#|\Z)',  # Markdown見出し
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                term_name, definition = match
                extracted_terms.append({
                    "term_name": term_name.strip(),
                    "definition_text": definition.strip()[:500],
                    "definition_source": source,
                    "term_category": self._categorize_term(term_name)
                })
        
        # パターン2: ドメインオブジェクト検出
        for domain_obj in self.DOMAIN_OBJECTS:
            if domain_obj in text:
                # コンテキストを抽出
                context = self._extract_context(text, domain_obj)
                if context and len(context) > 20:
                    extracted_terms.append({
                        "term_name": domain_obj,
                        "definition_text": context,
                        "definition_source": source,
                        "term_category": TermCategory.DOMAIN_OBJECT.value
                    })
        
        return extracted_terms
    
    def _categorize_term(self, term_name: str) -> str:
        """用語のカテゴリを判定"""
        if term_name in self.DOMAIN_OBJECTS:
            return TermCategory.DOMAIN_OBJECT.value
        
        technical_keywords = ["API", "Auth", "Database", "Token", "Cache"]
        if any(kw.lower() in term_name.lower() for kw in technical_keywords):
            return TermCategory.TECHNICAL.value
        
        process_keywords = ["Sprint", "Deploy", "Test", "Build", "Release"]
        if any(kw.lower() in term_name.lower() for kw in process_keywords):
            return TermCategory.PROCESS.value
        
        return TermCategory.CUSTOM.value
    
    def _extract_context(self, text: str, term: str) -> Optional[str]:
        """用語の周辺コンテキストを抽出"""
        sentences = re.split(r'[。.!?]', text)
        relevant_sentences = [s for s in sentences if term in s]
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:3])[:500]
        return None
    
    async def register_term_definition(
        self,
        user_id: str,
        term: Dict[str, Any]
    ) -> Tuple[UUID, bool]:
        """
        用語定義を登録（既存との比較・ドリフト検出含む）
        
        Args:
            user_id: ユーザーID
            term: 用語定義
            
        Returns:
            Tuple[UUID, bool]: (定義ID, ドリフト検出フラグ)
        """
        async with self.pool.acquire() as conn:
            # 既存定義を取得
            existing = await conn.fetchrow("""
                SELECT id, definition_text, version, defined_at
                FROM term_definitions
                WHERE user_id = $1 AND term_name = $2 AND is_current = TRUE
            """, user_id, term["term_name"])
            
            drift_detected = False
            
            if existing:
                # 類似度計算
                similarity = self._calculate_similarity(
                    existing['definition_text'],
                    term['definition_text']
                )
                
                if similarity < self.SIMILARITY_THRESHOLD:
                    # ドリフト検出！
                    drift_detected = True
                    
                    # 既存定義を非現行に
                    await conn.execute("""
                        UPDATE term_definitions
                        SET is_current = FALSE
                        WHERE id = $1
                    """, existing['id'])
                    
                    # 新定義を登録
                    new_id = await conn.fetchval("""
                        INSERT INTO term_definitions
                            (user_id, term_name, term_category, definition_text,
                             definition_source, version, is_current)
                        VALUES ($1, $2, $3, $4, $5, $6, TRUE)
                        RETURNING id
                    """, user_id, term["term_name"], term.get("term_category"),
                        term["definition_text"], term.get("definition_source"),
                        existing['version'] + 1)
                    
                    # ドリフトを記録
                    drift_type = self._determine_drift_type(
                        existing['definition_text'],
                        term['definition_text']
                    )
                    
                    await conn.execute("""
                        INSERT INTO term_drifts
                            (user_id, term_name, original_definition_id,
                             new_definition_id, drift_type, confidence_score,
                             change_summary)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, user_id, term["term_name"], existing['id'], new_id,
                        drift_type.value, 1.0 - similarity,
                        f"定義が変化: 類似度 {similarity:.2f}")
                    
                    logger.warning(
                        f"Term drift detected: {term['term_name']} "
                        f"(similarity: {similarity:.2f})"
                    )
                    
                    return new_id, True
                else:
                    # 変化なし、既存IDを返す
                    return existing['id'], False
            else:
                # 新規登録
                new_id = await conn.fetchval("""
                    INSERT INTO term_definitions
                        (user_id, term_name, term_category, definition_text,
                         definition_source, version, is_current)
                    VALUES ($1, $2, $3, $4, $5, 1, TRUE)
                    RETURNING id
                """, user_id, term["term_name"], term.get("term_category"),
                    term["definition_text"], term.get("definition_source"))
                
                return new_id, False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Jaccard類似度計算"""
        words1_list = text1.lower().split()
        words2_list = text2.lower().split()
        
        # 分割結果が少ない（日本語など）場合は文字単位で処理
        if len(words1_list) <= 1 and len(words2_list) <= 1:
            words1 = set(text1.lower())
            words2 = set(text2.lower())
            # 空文字除去
            words1.discard('')
            words2.discard(' ')
            words2.discard('')
            words1.discard(' ')
        else:
            words1 = set(words1_list)
            words2 = set(words2_list)
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _determine_drift_type(self, old_def: str, new_def: str) -> DriftType:
        """ドリフトタイプを判定"""
        old_words = set(old_def.lower().split())
        new_words = set(new_def.lower().split())
        
        added = new_words - old_words
        removed = old_words - new_words
        
        if len(added) > len(removed) * 2:
            return DriftType.EXPANSION
        elif len(removed) > len(added) * 2:
            return DriftType.CONTRACTION
        elif len(added) > 0 and len(removed) > 0:
            return DriftType.SEMANTIC_SHIFT
        else:
            return DriftType.CONTEXT_CHANGE
    
    async def get_pending_drifts(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[TermDrift]:
        """未解決のドリフト一覧を取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM term_drifts
                WHERE user_id = $1 AND status = 'pending'
                ORDER BY detected_at DESC
                LIMIT $2
            """, user_id, limit)
            
            return [TermDrift(**dict(row)) for row in rows]
    
    async def resolve_drift(
        self,
        drift_id: UUID,
        resolution_action: str,
        resolution_note: str,
        resolved_by: str
    ) -> bool:
        """ドリフトを解決"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE term_drifts
                SET status = 'resolved',
                    resolution_action = $1,
                    resolution_note = $2,
                    resolved_by = $3,
                    resolved_at = NOW()
                WHERE id = $4 AND status = 'pending'
            """, resolution_action, resolution_note, resolved_by, drift_id)
            
            return result == "UPDATE 1"
