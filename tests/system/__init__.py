"""
Resonant Engine システムテスト

このパッケージには、システム全体の統合テストが含まれています。
モックを使用せず、実際のPostgreSQLとClaude APIを使用してテストします。

テストカテゴリ:
- ST-DB: データベース接続テスト
- ST-API: REST APIテスト
- ST-BRIDGE: BridgeSetパイプラインテスト
- ST-AI: Claude API (Kana) テスト
- ST-MEM: メモリシステムテスト
- ST-CTX: Context Assemblerテスト
- ST-CONTRA: 矛盾検出テスト
- ST-RT: リアルタイム通信テスト
- ST-E2E: エンドツーエンドテスト
"""
