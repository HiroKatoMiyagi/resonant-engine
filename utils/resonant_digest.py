#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resonant Digest Generator - 開発文脈自動生成
============================================
イベントストリームから直近の開発活動を分析し、
AI（Cursor）が理解できる形式で開発文脈を生成する。

出力形式:
- マークダウン形式
- .cursorrulesに注入可能
- 時系列で整理された開発履歴
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# utils/ からの import
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream


class ResonantDigestGenerator:
    """
    開発文脈を自動生成するジェネレータ
    
    機能:
    1. 直近N日間のイベントを分析
    2. 意図、行動、結果を分類
    3. マークダウン形式で出力
    4. .cursorrulesに注入可能な形式
    """
    
    def __init__(self):
        self.stream = get_stream()
    
    def generate_digest(self, days: int = 7, output_format: str = "markdown") -> str:
        """
        直近N日間の開発文脈を生成
        
        Args:
            days: 分析対象の日数（デフォルト: 7日）
            output_format: 出力形式（"markdown" または "cursorrules"）
        
        Returns:
            生成された開発文脈の文字列
        """
        since = datetime.now() - timedelta(days=days)
        
        # 全イベントを取得
        events = self.stream.query(since=since, limit=1000)
        
        if not events:
            return self._empty_digest(days)
        
        # イベントを分類
        intents = [e for e in events if e["event_type"] == "intent"]
        actions = [e for e in events if e["event_type"] == "action"]
        results = [e for e in events if e["event_type"] == "result"]
        observations = [e for e in events if e["event_type"] == "observation"]
        hypotheses = [e for e in events if e["event_type"] == "hypothesis"]
        
        # ソース別に分類
        by_source = {}
        for event in events:
            source = event["source"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(event)
        
        # マークダウン生成
        if output_format == "cursorrules":
            return self._generate_cursorrules_format(intents, actions, results, observations, by_source, days)
        else:
            return self._generate_markdown_format(intents, actions, results, observations, by_source, days)
    
    def _empty_digest(self, days: int) -> str:
        """イベントがない場合の空のダイジェスト"""
        return f"""# Resonant Engine - 開発文脈ダイジェスト

**期間**: 直近{days}日間
**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 サマリー

イベントが記録されていません。開発を開始すると、ここに活動履歴が表示されます。

---
"""
    
    def _generate_markdown_format(self, 
                                  intents: List[Dict], 
                                  actions: List[Dict], 
                                  results: List[Dict],
                                  observations: List[Dict],
                                  by_source: Dict[str, List[Dict]],
                                  days: int) -> str:
        """マークダウン形式で生成"""
        lines = []
        
        lines.append(f"# Resonant Engine - 開発文脈ダイジェスト")
        lines.append("")
        lines.append(f"**期間**: 直近{days}日間")
        lines.append(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # サマリー
        lines.append("## 📊 サマリー")
        lines.append("")
        lines.append(f"- **意図**: {len(intents)}件")
        lines.append(f"- **行動**: {len(actions)}件")
        lines.append(f"- **結果**: {len(results)}件")
        lines.append(f"- **観測**: {len(observations)}件")
        lines.append("")
        
        # 主要な意図
        if intents:
            lines.append("## 🎯 主要な開発意図")
            lines.append("")
            for intent in intents[-10:]:  # 最新10件
                intent_text = intent["data"].get("intent", "")
                context = intent["data"].get("context", "")
                timestamp = intent["timestamp"][:19].replace("T", " ")
                lines.append(f"- **{timestamp}**: {intent_text}")
                if context:
                    lines.append(f"  - 文脈: {context}")
            lines.append("")
        
        # 最近の活動（ソース別）
        if by_source:
            lines.append("## 🔄 最近の活動（ソース別）")
            lines.append("")
            for source, events in sorted(by_source.items()):
                if len(events) > 0:
                    lines.append(f"### {source}")
                    lines.append("")
                    for event in events[-5:]:  # 各ソース最新5件
                        timestamp = event["timestamp"][:19].replace("T", " ")
                        event_type = event["event_type"]
                        data_summary = self._summarize_data(event["data"])
                        lines.append(f"- **{timestamp}** [{event_type}]: {data_summary}")
                    lines.append("")
        
        # 重要な結果
        important_results = [r for r in results if r["data"].get("status") == "error" or r["data"].get("status") == "success"]
        if important_results:
            lines.append("## ✅ 重要な結果")
            lines.append("")
            for result in important_results[-10:]:
                timestamp = result["timestamp"][:19].replace("T", " ")
                status = result["data"].get("status", "unknown")
                status_icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
                lines.append(f"- **{timestamp}** {status_icon} {status}")
                if "error" in result["data"]:
                    error_msg = str(result["data"]["error"])[:100]
                    lines.append(f"  - エラー: {error_msg}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append(f"*生成元: Resonant Engine Event Stream*")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_cursorrules_format(self,
                                     intents: List[Dict],
                                     actions: List[Dict],
                                     results: List[Dict],
                                     observations: List[Dict],
                                     by_source: Dict[str, List[Dict]],
                                     days: int) -> str:
        """Cursor Rules形式で生成（.cursorrulesに注入用）"""
        lines = []
        
        lines.append("# Resonant Engine - Recent Development Context")
        lines.append("")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append(f"*Period: Last {days} days*")
        lines.append("")
        lines.append("## Recent Development Intentions")
        lines.append("")
        
        if intents:
            for intent in intents[-10:]:
                intent_text = intent["data"].get("intent", "")
                context = intent["data"].get("context", "")
                timestamp = intent["timestamp"][:19].replace("T", " ")
                lines.append(f"- [{timestamp}] {intent_text}")
                if context:
                    lines.append(f"  Context: {context}")
        else:
            lines.append("- No recent intents recorded")
        
        lines.append("")
        lines.append("## Recent System Activities")
        lines.append("")
        
        # 主要なアクティビティを時系列で
        all_recent = sorted(intents + actions + results, key=lambda x: x["timestamp"], reverse=True)[:20]
        for event in all_recent:
            timestamp = event["timestamp"][:19].replace("T", " ")
            event_type = event["event_type"]
            source = event["source"]
            data_summary = self._summarize_data(event["data"])
            lines.append(f"- [{timestamp}] {event_type} from {source}: {data_summary}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
    
    def _summarize_data(self, data: Dict[str, Any]) -> str:
        """イベントデータを簡潔に要約"""
        if isinstance(data, dict):
            # 主要なキーを優先的に表示
            if "intent" in data:
                return data["intent"]
            elif "action" in data:
                action = data["action"]
                if "target" in data:
                    return f"{action} ({data['target']})"
                return action
            elif "status" in data:
                status = data["status"]
                if "error" in data:
                    return f"{status} - {str(data['error'])[:50]}"
                return status
            elif "spec_name" in data:
                return f"spec: {data['spec_name']}"
            else:
                # 最初の2つのキーを表示
                keys = list(data.keys())[:2]
                return ", ".join(f"{k}={str(data[k])[:30]}" for k in keys)
        return str(data)[:100]
    
    def save_to_cursorrules(self, days: int = 7, cursorrules_path: Optional[Path] = None):
        """
        生成したダイジェストを.cursorrulesに追加
        
        Args:
            days: 分析対象の日数
            cursorrules_path: .cursorrulesファイルのパス（Noneの場合は自動検出）
        """
        if cursorrules_path is None:
            cursorrules_path = Path(__file__).parent.parent / ".cursorrules"
        
        digest = self.generate_digest(days=days, output_format="cursorrules")
        
        # .cursorrulesが存在する場合は、既存の内容を読み込む
        existing_content = ""
        if cursorrules_path.exists():
            existing_content = cursorrules_path.read_text(encoding="utf-8")
            
            # 既存のResonant Engineセクションを削除
            lines = existing_content.split("\n")
            new_lines = []
            skip_section = False
            for line in lines:
                if line.strip().startswith("# Resonant Engine - Recent Development Context"):
                    skip_section = True
                elif skip_section and line.strip().startswith("---"):
                    skip_section = False
                    continue
                elif skip_section:
                    continue
                new_lines.append(line)
            existing_content = "\n".join(new_lines)
        
        # 新しいダイジェストを追加
        new_content = existing_content.rstrip() + "\n\n" + digest
        
        cursorrules_path.write_text(new_content, encoding="utf-8")
        print(f"✅ Resonant Digestを.cursorrulesに追加しました: {cursorrules_path}")


# ============================================
# CLI実行
# ============================================

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Resonant Digest Generator")
    parser.add_argument("--days", type=int, default=7, help="分析対象の日数（デフォルト: 7）")
    parser.add_argument("--format", choices=["markdown", "cursorrules"], default="markdown", 
                       help="出力形式（デフォルト: markdown）")
    parser.add_argument("--output", type=str, help="出力ファイルパス（指定しない場合は標準出力）")
    parser.add_argument("--update-cursorrules", action="store_true", 
                       help=".cursorrulesファイルを更新")
    
    args = parser.parse_args()
    
    generator = ResonantDigestGenerator()
    
    if args.update_cursorrules:
        generator.save_to_cursorrules(days=args.days)
    else:
        digest = generator.generate_digest(days=args.days, output_format=args.format)
        
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(digest, encoding="utf-8")
            print(f"✅ ダイジェストを保存しました: {output_path}")
        else:
            print(digest)


if __name__ == "__main__":
    main()


