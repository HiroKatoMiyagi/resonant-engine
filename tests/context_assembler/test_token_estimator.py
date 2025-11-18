from context_assembler.token_estimator import TokenEstimator


def test_estimate_japanese_text():
    """日本語テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [{"role": "user", "content": "こんにちは"}]  # 5文字

    tokens = estimator.estimate(messages)
    # 5文字 * 2 + オーバーヘッド10 = 20
    assert 15 <= tokens <= 25


def test_estimate_english_text():
    """英語テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [{"role": "user", "content": "Hello World"}]  # 11文字

    tokens = estimator.estimate(messages)
    # 11文字 * 0.5 + オーバーヘッド10 = 15.5
    assert 10 <= tokens <= 20


def test_estimate_mixed_text():
    """日英混在テキストのトークン推定"""
    estimator = TokenEstimator()

    messages = [{"role": "user", "content": "Resonant Engineは呼吸のリズムです"}]

    tokens = estimator.estimate(messages)
    assert tokens > 20  # それなりの量


def test_estimate_multiple_messages():
    """複数メッセージのトークン推定"""
    estimator = TokenEstimator()

    messages = [
        {"role": "system", "content": "You are Kana"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]

    tokens = estimator.estimate(messages)
    assert tokens > 30  # 各メッセージ + オーバーヘッド


def test_estimate_string():
    """文字列トークン推定"""
    estimator = TokenEstimator()

    tokens = estimator.estimate_string("こんにちは")
    assert 8 <= tokens <= 12  # 5文字 * 2 = 10


def test_estimate_empty_messages():
    """空のメッセージリストのトークン推定"""
    estimator = TokenEstimator()

    messages = []
    tokens = estimator.estimate(messages)
    assert tokens == 0


def test_estimate_empty_content():
    """空のコンテンツのトークン推定"""
    estimator = TokenEstimator()

    messages = [{"role": "user", "content": ""}]
    tokens = estimator.estimate(messages)
    assert tokens == 10  # オーバーヘッドのみ
