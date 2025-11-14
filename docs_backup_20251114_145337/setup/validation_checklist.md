# 🧾 Validation Checklist — Kiro v3.1

## フェーズ別確認項目

### G1: Secrets準備
- [x] `.env` に Notion / OpenAI / GitHub / Cloudflare キーを設定
- [x] `.env.example` を作成・リポジトリ管理外に設定

### G2: 初期構築
- [x] n8n / Notion / OpenAI 疎通テスト成功
- [x] `curl_test.sh` によるWebhook受信確認

### G3: ディレクトリ再編
- [x] `/Users/zero/Projects/kiro-v3.1` に統一
- [x] `.git/config` 再設定済

### G4: ドキュメント整備（現在完了）
- [x] `architecture/kiro_v3.1_architecture.md` 生成
- [x] `setup/validation_checklist.md` 生成
- [x] `history/dir_restructure_commit.log` 生成

### G5: Git整合
- [x] Remote名を `origin` に統一
- [x] `main` → `origin/main` 同期確認済
- [x] `git status` クリーン

### G6: 自動化検証（次段階）
- [ ] n8n Workflow #1 作成（Notion → OpenAI）
- [ ] Webhook動作テスト
- [ ] GitHub Issue/PR自動生成検証

---

## 🪶 Atlas補足
本チェックリストは、擬似Kiro環境のフェーズ進行を監査可能な形で文書化する。  
以降は n8n Workflow の整備フェーズ（G6）へ移行。
