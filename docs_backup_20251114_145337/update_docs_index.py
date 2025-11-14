#!/usr/bin/env python3
"""
Resonant Engine ドキュメントインデックス自動更新スクリプト

使い方:
    python update_docs_index.py

機能:
    - /docs配下のディレクトリとファイルを自動スキャン
    - カテゴリー別に分類してindex.htmlを生成
    - 更新日時を自動で記録
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class DocumentScanner:
    """ドキュメントディレクトリをスキャンしてindex.htmlを生成"""
    
    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        self.exclude_patterns = {
            '.DS_Store', '__pycache__', '.git', '.pyc',
            'update_docs_index.py', 'index.html'
        }
        self.exclude_dirs = {'canvas', 'design', 'specs', 'templates'}
        
    def scan(self) -> Dict[str, List[Dict]]:
        """ドキュメントをスキャンしてカテゴリー別に分類"""
        documents = defaultdict(list)
        
        # Phase別ドキュメント
        for phase in ['Phase0', 'Phase1', 'Phase2', 'Phase3']:
            phase_docs = self._scan_phase(phase)
            if phase_docs:
                documents[f'phase_{phase.lower()}'] = phase_docs
        
        # Yunoドキュメント
        yuno_docs = self._scan_directory('Yuno')
        if yuno_docs:
            documents['yuno'] = yuno_docs
        
        # アーキテクチャドキュメント
        arch_docs = self._scan_architecture()
        if arch_docs:
            documents['architecture'] = arch_docs
        
        # エラーリカバリー
        error_docs = self._scan_error_recovery()
        if error_docs:
            documents['error_recovery'] = error_docs
        
        # 統合・セットアップ
        integration_docs = self._scan_integration()
        if integration_docs:
            documents['integration'] = integration_docs
        
        # 実装ロードマップ
        roadmap_docs = self._scan_roadmap()
        if roadmap_docs:
            documents['roadmap'] = roadmap_docs
        
        # アウトプット
        output_docs = self._scan_directory('output')
        if output_docs:
            documents['output'] = output_docs
        
        # テンプレート・ユーティリティ
        utility_docs = self._scan_utilities()
        if utility_docs:
            documents['utilities'] = utility_docs
        
        # その他
        misc_docs = self._scan_misc()
        if misc_docs:
            documents['misc'] = misc_docs
        
        return documents
    
    def _scan_phase(self, phase_name: str) -> List[Dict]:
        """Phaseディレクトリをスキャン"""
        phase_dir = self.docs_dir / phase_name
        if not phase_dir.exists():
            return []
        
        docs = []
        for file in sorted(phase_dir.glob('*.md')):
            if file.name not in self.exclude_patterns:
                docs.append({
                    'title': self._format_title(file.stem),
                    'path': f'{phase_name}/{file.name}',
                    'badge': self._determine_badge(file.name)
                })
        return docs
    
    def _scan_directory(self, dir_name: str) -> List[Dict]:
        """指定ディレクトリをスキャン"""
        target_dir = self.docs_dir / dir_name
        if not target_dir.exists():
            return []
        
        docs = []
        
        # ファイルを拡張子でグループ化
        file_groups = self._group_by_basename(target_dir)
        
        for basename, formats in sorted(file_groups.items()):
            if basename not in self.exclude_patterns:
                docs.append({
                    'title': self._format_title(basename),
                    'path': f'{dir_name}/{basename}',
                    'formats': formats,
                    'badge': self._determine_badge(basename)
                })
        
        return docs
    
    def _group_by_basename(self, directory: Path) -> Dict[str, List[str]]:
        """ファイルをベース名でグループ化（拡張子が違うだけのファイルをまとめる）"""
        groups = defaultdict(list)
        
        for file in directory.iterdir():
            if file.is_file() and file.name not in self.exclude_patterns:
                # .md, .html, .pdfなどの拡張子を検出
                if file.suffix in ['.md', '.html', '.pdf', '.txt', '.log', '.py']:
                    groups[file.stem].append(file.suffix)
        
        return groups
    
    def _scan_architecture(self) -> List[Dict]:
        """アーキテクチャ関連ドキュメントをスキャン"""
        docs = []
        arch_files = [
            'complete_architecture_design.md',
            'dashboard_platform_design.md',
            'architecture/kiro_v3.1_architecture.md'
        ]
        
        for file_path in arch_files:
            full_path = self.docs_dir / file_path
            if full_path.exists():
                docs.append({
                    'title': self._format_title(Path(file_path).stem),
                    'path': file_path,
                    'description': self._get_description(Path(file_path).stem)
                })
        
        return docs
    
    def _scan_error_recovery(self) -> List[Dict]:
        """エラーリカバリー関連ドキュメントをスキャン"""
        docs = []
        pattern = re.compile(r'^error_recovery_.*\.md$')
        
        for file in sorted(self.docs_dir.glob('error_recovery_*.md')):
            if pattern.match(file.name):
                docs.append({
                    'title': self._format_title(file.stem),
                    'path': file.name,
                    'badge': self._determine_badge(file.name)
                })
        
        return docs
    
    def _scan_integration(self) -> List[Dict]:
        """統合・セットアップ関連ドキュメントをスキャン"""
        docs = []
        integration_files = [
            'integration_design.md',
            'integration_complete.md',
            'notion_setup_guide.md',
            'notion_integration_summary.md',
            'quick_start_unified_stream.md',
            'setup/validation_checklist.md'
        ]
        
        for file_path in integration_files:
            full_path = self.docs_dir / file_path
            if full_path.exists():
                docs.append({
                    'title': self._format_title(Path(file_path).stem),
                    'path': file_path,
                    'description': self._get_description(Path(file_path).stem)
                })
        
        return docs
    
    def _scan_roadmap(self) -> List[Dict]:
        """実装ロードマップ関連ドキュメントをスキャン"""
        docs = []
        roadmap_files = [
            'implementation_roadmap_postgres.md',
            'cloud_migration_strategy.md'
        ]
        
        for file_path in roadmap_files:
            full_path = self.docs_dir / file_path
            if full_path.exists():
                docs.append({
                    'title': self._format_title(Path(file_path).stem),
                    'path': file_path,
                    'description': self._get_description(Path(file_path).stem)
                })
        
        return docs
    
    def _scan_utilities(self) -> List[Dict]:
        """テンプレート・ユーティリティをスキャン"""
        docs = []
        utility_files = [
            'report_template.md',
            'env_template.txt',
            'create_resonant_total_archive.py',
            'create_resonant_total_chronicle_v4_raw.py',
            'create_resonant_total_chronicle_v5_expanded.py'
        ]
        
        for file_path in utility_files:
            full_path = self.docs_dir / file_path
            if full_path.exists():
                docs.append({
                    'title': self._format_title(Path(file_path).stem),
                    'path': file_path
                })
        
        return docs
    
    def _scan_misc(self) -> List[Dict]:
        """その他のドキュメントをスキャン"""
        docs = []
        misc_files = [
            'html/github_webhook_receiver_spec.html',
            'history/dir_restructure_commit.log',
            'persistence_check.log',
            'phase3_test.txt'
        ]
        
        for file_path in misc_files:
            full_path = self.docs_dir / file_path
            if full_path.exists():
                docs.append({
                    'title': self._format_title(Path(file_path).stem),
                    'path': file_path
                })
        
        return docs
    
    def _format_title(self, filename: str) -> str:
        """ファイル名を読みやすいタイトルに変換"""
        # アンダースコアをスペースに
        title = filename.replace('_', ' ')
        # 各単語の先頭を大文字に
        title = ' '.join(word.capitalize() for word in title.split())
        return title
    
    def _determine_badge(self, filename: str) -> str:
        """ファイル名からバッジタイプを判定"""
        filename_lower = filename.lower()
        
        if 'completion' in filename_lower or 'complete' in filename_lower:
            return '完了'
        elif 'guide' in filename_lower:
            return 'ガイド'
        elif 'design' in filename_lower or 'spec' in filename_lower:
            return '設計'
        elif 'implementation' in filename_lower:
            return '実装'
        elif 'test' in filename_lower:
            return 'テスト'
        elif 'review' in filename_lower:
            return 'レビュー'
        
        return ''
    
    def _get_description(self, filename: str) -> str:
        """ファイル名から説明文を生成"""
        descriptions = {
            'complete_architecture_design': 'システム全体のアーキテクチャ設計書',
            'kiro_v3.1_architecture': '前身システムのアーキテクチャ参照',
            'dashboard_platform_design': '統合ダッシュボードプラットフォーム設計',
            'implementation_roadmap_postgres': 'PostgreSQL移行の実装ロードマップ（Yuno承認済み A+評価）',
            'cloud_migration_strategy': 'Oracle Cloud Free Tier移行戦略',
            'integration_design': 'システム統合設計',
            'integration_complete': '統合完了報告',
            'notion_setup_guide': 'Notion統合セットアップガイド',
            'notion_integration_summary': 'Notion統合サマリー',
            'quick_start_unified_stream': '統一ストリームクイックスタート',
            'validation_checklist': '検証チェックリスト'
        }
        
        return descriptions.get(filename, '')


class HTMLGenerator:
    """index.htmlを生成"""
    
    def __init__(self):
        self.update_date = datetime.now().strftime('%Y-%m-%d')
    
    def generate(self, documents: Dict[str, List[Dict]]) -> str:
        """HTMLを生成"""
        html = self._get_html_header()
        html += self._generate_content(documents)
        html += self._get_html_footer()
        
        return html
    
    def _get_html_header(self) -> str:
        """HTMLヘッダー部分を生成"""
        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resonant Engine ドキュメント</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}
        
        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 1.8rem;
            color: #667eea;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
        }}
        
        .doc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        
        .doc-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .doc-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            border-color: #667eea;
        }}
        
        .doc-card h3 {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: #2d3748;
        }}
        
        .doc-card p {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }}
        
        .doc-card a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            display: inline-block;
            margin-top: 0.5rem;
            margin-right: 0.5rem;
        }}
        
        .doc-card a:hover {{
            color: #764ba2;
            text-decoration: underline;
        }}
        
        .doc-list {{
            list-style: none;
            margin-top: 1rem;
        }}
        
        .doc-list li {{
            background: #f8f9fa;
            margin-bottom: 0.5rem;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            transition: all 0.2s ease;
        }}
        
        .doc-list li:hover {{
            background: #e9ecef;
            transform: translateX(4px);
        }}
        
        .doc-list a {{
            color: #2d3748;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .doc-list a:hover {{
            color: #667eea;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #667eea;
            color: white;
            border-radius: 12px;
            font-size: 0.85rem;
            margin-left: 0.5rem;
        }}
        
        .badge.complete {{
            background: #48bb78;
        }}
        
        .badge.guide {{
            background: #4299e1;
        }}
        
        .badge.design {{
            background: #ed8936;
        }}
        
        .badge.implementation {{
            background: #4299e1;
        }}
        
        .badge.test {{
            background: #9f7aea;
        }}
        
        .badge.review {{
            background: #38b2ac;
        }}
        
        footer {{
            background: #2d3748;
            color: white;
            text-align: center;
            padding: 1.5rem;
            font-size: 0.9rem;
        }}
        
        .update-note {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 2rem;
            color: #856404;
        }}
        
        .subsection-title {{
            font-size: 1.3rem;
            color: #764ba2;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌊 Resonant Engine</h1>
            <p>自己反省型アーキテクチャシステム - ドキュメントポータル</p>
        </header>
        
        <div class="content">
            <div class="update-note">
                <strong>📝 更新履歴:</strong> 最終更新日 {self.update_date}
            </div>
'''
    
    def _generate_content(self, documents: Dict[str, List[Dict]]) -> str:
        """コンテンツ部分を生成"""
        content = ''
        
        # アーキテクチャ概要
        if 'architecture' in documents:
            content += self._generate_architecture_section(documents['architecture'])
        
        # フェーズ別ドキュメント
        phase_sections = {k: v for k, v in documents.items() if k.startswith('phase_')}
        if phase_sections:
            content += self._generate_phase_sections(phase_sections)
        
        # 実装ロードマップ
        if 'roadmap' in documents:
            content += self._generate_roadmap_section(documents['roadmap'])
        
        # Yunoドキュメント
        if 'yuno' in documents:
            content += self._generate_yuno_section(documents['yuno'])
        
        # エラーリカバリー
        if 'error_recovery' in documents:
            content += self._generate_error_recovery_section(documents['error_recovery'])
        
        # 統合・セットアップ
        if 'integration' in documents:
            content += self._generate_integration_section(documents['integration'])
        
        # アウトプット
        if 'output' in documents:
            content += self._generate_output_section(documents['output'])
        
        # テンプレート・ユーティリティ
        if 'utilities' in documents:
            content += self._generate_utilities_section(documents['utilities'])
        
        # その他
        if 'misc' in documents:
            content += self._generate_misc_section(documents['misc'])
        
        return content
    
    def _generate_architecture_section(self, docs: List[Dict]) -> str:
        """アーキテクチャセクション生成"""
        html = '''
            <!-- アーキテクチャ概要 -->
            <section class="section">
                <h2 class="section-title">📐 アーキテクチャ概要</h2>
                <div class="doc-grid">
'''
        
        for doc in docs:
            description = doc.get('description', '')
            html += f'''
                    <div class="doc-card">
                        <h3>{doc['title']}</h3>
                        <p>{description}</p>
                        <a href="{doc['path']}">📄 閲覧する</a>
                    </div>
'''
        
        html += '''
                </div>
            </section>
'''
        return html
    
    def _generate_phase_sections(self, phase_sections: Dict[str, List[Dict]]) -> str:
        """フェーズセクション生成"""
        html = '''
            <!-- フェーズ別ドキュメント -->
            <section class="section">
                <h2 class="section-title">🚀 フェーズ別実装ドキュメント</h2>
'''
        
        phase_names = {
            'phase_phase0': ('Phase 0: 基盤改善', '#48bb78'),
            'phase_phase1': ('Phase 1: SQLite実装（スキップ）', '#48bb78'),
            'phase_phase2': ('Phase 2: 改善項目', '#48bb78'),
            'phase_phase3': ('Phase 3: PostgreSQL実装', '#48bb78')
        }
        
        for phase_key in sorted(phase_sections.keys()):
            docs = phase_sections[phase_key]
            phase_title, color = phase_names.get(phase_key, (phase_key.replace('_', ' ').title(), '#48bb78'))
            
            html += f'''
                <h3 class="subsection-title" style="color: {color};">{phase_title}</h3>
                <ul class="doc-list">
'''
            
            for doc in docs:
                badge = doc.get('badge', '')
                badge_html = f' <span class="badge">{badge}</span>' if badge else ''
                html += f'''
                    <li><a href="{doc['path']}">{doc['title']}</a>{badge_html}</li>
'''
            
            html += '''
                </ul>
'''
        
        html += '''
            </section>
'''
        return html
    
    def _generate_roadmap_section(self, docs: List[Dict]) -> str:
        """ロードマップセクション生成"""
        html = '''
            <!-- 実装ロードマップ -->
            <section class="section">
                <h2 class="section-title">🗺️ 実装ロードマップ</h2>
                <div class="doc-grid">
'''
        
        for doc in docs:
            description = doc.get('description', '')
            html += f'''
                    <div class="doc-card">
                        <h3>{doc['title']}</h3>
                        <p>{description}</p>
                        <a href="{doc['path']}">📄 閲覧する</a>
                    </div>
'''
        
        html += '''
                </div>
            </section>
'''
        return html
    
    def _generate_yuno_section(self, docs: List[Dict]) -> str:
        """Yunoセクション生成"""
        # reviewキーワードを含むファイルとそれ以外を分離
        main_docs = [d for d in docs if 'review' not in d['path'].lower() and 
                     'notion' not in d['path'].lower()]
        review_docs = [d for d in docs if 'review' in d['path'].lower() or 
                       'notion' in d['path'].lower()]
        
        html = '''
            <!-- Yunoドキュメント -->
            <section class="section">
                <h2 class="section-title">🧠 Yuno - 思想・設計文書</h2>
                <div class="doc-grid">
'''
        
        for doc in main_docs:
            formats = doc.get('formats', ['.md'])
            if len(formats) == 1:
                html += f'''
                    <div class="doc-card">
                        <h3>{doc['title']}</h3>
                        <a href="{doc['path']}{formats[0]}">📄 閲覧する</a>
                    </div>
'''
            else:
                # 複数フォーマットがある場合
                html += f'''
                    <div class="doc-card">
                        <h3>{doc['title']}</h3>
'''
                for fmt in formats:
                    fmt_label = fmt.upper().replace('.', '')
                    html += f'''
                        <a href="{doc['path']}{fmt}">📄 {fmt_label}</a>
'''
                html += '''
                    </div>
'''
        
        html += '''
                </div>
'''
        
        if review_docs:
            html += '''
                <h3 class="subsection-title">レビュー・対話記録</h3>
                <ul class="doc-list">
'''
            
            for doc in review_docs:
                formats = doc.get('formats', ['.md'])
                html += f'''
                    <li><a href="{doc['path']}{formats[0]}">{doc['title']}</a></li>
'''
            
            html += '''
                </ul>
'''
        
        html += '''
            </section>
'''
        return html
    
    def _generate_error_recovery_section(self, docs: List[Dict]) -> str:
        """エラーリカバリーセクション生成"""
        html = '''
            <!-- エラーリカバリー -->
            <section class="section">
                <h2 class="section-title">🔧 エラーリカバリー実装</h2>
                <ul class="doc-list">
'''
        
        for doc in docs:
            badge = doc.get('badge', '')
            badge_html = f' <span class="badge">{badge}</span>' if badge else ''
            html += f'''
                    <li><a href="{doc['path']}">{doc['title']}</a>{badge_html}</li>
'''
        
        html += '''
                </ul>
            </section>
'''
        return html
    
    def _generate_integration_section(self, docs: List[Dict]) -> str:
        """統合・セットアップセクション生成"""
        html = '''
            <!-- 統合・セットアップ -->
            <section class="section">
                <h2 class="section-title">🔗 統合・セットアップ</h2>
                <div class="doc-grid">
'''
        
        for doc in docs:
            description = doc.get('description', '')
            html += f'''
                    <div class="doc-card">
                        <h3>{doc['title']}</h3>
                        <p>{description}</p>
                        <a href="{doc['path']}">📄 閲覧する</a>
                    </div>
'''
        
        html += '''
                </div>
            </section>
'''
        return html
    
    def _generate_output_section(self, docs: List[Dict]) -> str:
        """アウトプットセクション生成"""
        html = '''
            <!-- 成果物・アウトプット -->
            <section class="section">
                <h2 class="section-title">📊 成果物・アウトプット</h2>
                <ul class="doc-list">
'''
        
        for doc in docs:
            formats = doc.get('formats', ['.md'])
            format_links = ''
            for fmt in formats:
                fmt_label = fmt.upper().replace('.', '')
                format_links += f' <a href="{doc["path"]}{fmt}">({fmt_label})</a>'
            
            html += f'''
                    <li>{doc['title']}{format_links}</li>
'''
        
        html += '''
                </ul>
            </section>
'''
        return html
    
    def _generate_utilities_section(self, docs: List[Dict]) -> str:
        """ユーティリティセクション生成"""
        html = '''
            <!-- テンプレート・ユーティリティ -->
            <section class="section">
                <h2 class="section-title">🛠️ テンプレート・ユーティリティ</h2>
                <ul class="doc-list">
'''
        
        for doc in docs:
            html += f'''
                    <li><a href="{doc['path']}">{doc['title']}</a></li>
'''
        
        html += '''
                </ul>
            </section>
'''
        return html
    
    def _generate_misc_section(self, docs: List[Dict]) -> str:
        """その他セクション生成"""
        html = '''
            <!-- その他 -->
            <section class="section">
                <h2 class="section-title">📝 その他</h2>
                <ul class="doc-list">
'''
        
        for doc in docs:
            html += f'''
                    <li><a href="{doc['path']}">{doc['title']}</a></li>
'''
        
        html += '''
                </ul>
            </section>
'''
        return html
    
    def _get_html_footer(self) -> str:
        """HTMLフッター部分を生成"""
        return '''
        </div>
        
        <footer>
            <p>Resonant Engine - 自己反省型アーキテクチャシステム</p>
            <p style="margin-top: 0.5rem; opacity: 0.8;">Yuno (GPT-5) × Kana (Claude) × Tsumu (Cursor)</p>
        </footer>
    </div>
</body>
</html>'''


def main():
    """メイン処理"""
    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent
    
    print(f"📁 ドキュメントディレクトリ: {script_dir}")
    print("🔍 ドキュメントをスキャン中...")
    
    # ドキュメントをスキャン
    scanner = DocumentScanner(str(script_dir))
    documents = scanner.scan()
    
    # スキャン結果を表示
    total_docs = sum(len(docs) for docs in documents.values())
    print(f"✅ {total_docs} 件のドキュメントを検出")
    
    for category, docs in documents.items():
        print(f"  - {category}: {len(docs)} 件")
    
    # HTMLを生成
    print("\n🔨 index.htmlを生成中...")
    generator = HTMLGenerator()
    html_content = generator.generate(documents)
    
    # index.htmlを保存
    output_path = script_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✨ 完了！ {output_path}")
    print(f"\nブラウザで開く:")
    print(f"  open {output_path}")


if __name__ == '__main__':
    main()
