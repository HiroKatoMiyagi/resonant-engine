import pytest
from app.services.term_drift.detector import TermDriftDetector
from app.services.term_drift.models import DriftType

def test_extract_japanese_definition():
    """日本語定義文からの用語抽出テスト"""
    detector = TermDriftDetector(None)  # poolはモック
    
    text = """
    「Intent」はユーザーの意図を表すデータモデルです。
    「Memory」は過去の会話記録を保持する仕組みである。
    「Bridge」は異なるシステム間を接続するコンポーネントとする。
    """
    
    # extract_terms_from_text is async, but doesn't use self.pool in current implementation
    # Wait, it IS async def, so we need to run it in loop or mock
    # Actually, the logic is purely synchronous regex currently, but defined as async.
    # We should run it with pytest-asyncio
    pass

@pytest.mark.asyncio
async def test_extract_japanese_definition_async():
    detector = TermDriftDetector(None)
    text = """
    「Intent」はユーザーの意図を表すデータモデルです。
    「Memory」は過去の会話記録を保持する仕組みである。
    「Bridge」は異なるシステム間を接続するコンポーネントとする。
    """
    terms = await detector.extract_terms_from_text(text, "test.md")
    
    assert len(terms) >= 3
    term_names = [t["term_name"] for t in terms]
    assert "Intent" in term_names
    assert "Memory" in term_names
    assert "Bridge" in term_names
    
    intent_term = next(t for t in terms if t["term_name"] == "Intent")
    assert "ユーザーの意図" in intent_term["definition_text"]

@pytest.mark.asyncio
async def test_extract_english_definition():
    """英語定義文からの用語抽出テスト"""
    detector = TermDriftDetector(None)
    
    text = """
    Intent is a data model representing user's request.
    Memory refers to the storage of past conversations.
    Bridge means a component connecting different systems.
    """
    
    terms = await detector.extract_terms_from_text(text, "test.md")
    
    assert len(terms) >= 3
    term_names = [t["term_name"] for t in terms]
    assert "Intent" in term_names
    assert "Memory" in term_names
    assert "Bridge" in term_names

@pytest.mark.asyncio
async def test_extract_markdown_heading():
    """Markdown見出しからの用語抽出テスト"""
    detector = TermDriftDetector(None)
    
    text = """
    # Intent
    
    ユーザーの要望を表現するオブジェクト。content, user_idを持つ。
    
    # Memory
    
    過去の会話を保持するシステム。検索・取得機能を提供。
    """
    
    terms = await detector.extract_terms_from_text(text, "README.md")
    
    assert len(terms) >= 2
    intent_term = next((t for t in terms if t["term_name"] == "Intent"), None)
    assert intent_term is not None
    assert "ユーザーの要望" in intent_term["definition_text"]

def test_categorize_term():
    """用語カテゴリ判定テスト"""
    detector = TermDriftDetector(None)
    
    assert detector._categorize_term("Intent") == "domain_object"
    assert detector._categorize_term("Memory") == "domain_object"
    assert detector._categorize_term("Yuno") == "domain_object"
    
    assert detector._categorize_term("API") == "technical"
    assert detector._categorize_term("Authentication") == "technical"
    
    assert detector._categorize_term("Sprint") == "process"
    assert detector._categorize_term("Deploy") == "process"
    
    assert detector._categorize_term("MyCustomTerm") == "custom"

def test_calculate_similarity():
    """Jaccard類似度計算テスト"""
    detector = TermDriftDetector(None)
    
    sim1 = detector._calculate_similarity(
        "ユーザーの要望を表すデータ",
        "ユーザーの要望を表すデータ"
    )
    assert sim1 == 1.0
    
    sim2 = detector._calculate_similarity(
        "ユーザーの要望を表すデータ",
        "ユーザーの意図を表すオブジェクト"
    )
    assert 0.0 < sim2 < 1.0
    
    sim3 = detector._calculate_similarity(
        "認証システム",
        "データベース接続"
    )
    assert sim3 < 0.3
    
    sim4 = detector._calculate_similarity("", "")
    assert sim4 == 0.0

def test_determine_drift_type():
    """ドリフトタイプ判定テスト"""
    detector = TermDriftDetector(None)
    
    drift1 = detector._determine_drift_type(
        "content, user_id",
        "content, user_id, ai_response, status, metadata"
    )
    assert drift1 == DriftType.EXPANSION
    
    drift2 = detector._determine_drift_type(
        "content, user_id, ai_response, status",
        "content, user_id"
    )
    assert drift2 == DriftType.CONTRACTION
    
    drift3 = detector._determine_drift_type(
        "Basic認証でログイン",
        "JWT Token認証でログイン"
    )
    assert drift3 == DriftType.SEMANTIC_SHIFT
