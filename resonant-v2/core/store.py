"""SQLite の単一ファイルに全アクセスを集約するモジュール。

設計方針（docs/v2/resonant_engine_v2_spec.md 参照）:
- 常駐プロセスなし。呼ばれるたびに connect() して使い捨てる。
- 判定はしない。証拠（failed な attempts）を取得して返すだけ。
- FTS5 trigram は「意味の近さ」ではなく「3文字以上の完全一致部分文字列」を検出する。
  paraphrase 全体は拾えないが、識別子・ファイル名・エラー文言・繰り返し語彙は拾える。
  取りこぼしが誤検知よりコストが高いため、再現率(recall)を優先した OR 結合にしている。
"""
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone

ASCII_TOKEN_RE = re.compile(r'[A-Za-z0-9_./:\-]{3,}')
CJK_RUN_RE = re.compile(r'[一-鿿぀-ヿ]+')

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS attempts (
  id              INTEGER PRIMARY KEY,
  created_at      TEXT NOT NULL,
  session_id      TEXT,
  project         TEXT NOT NULL,
  branch          TEXT,
  proposal        TEXT NOT NULL,
  outcome         TEXT NOT NULL DEFAULT 'pending',
  failure_signal  TEXT,
  evidence        TEXT,
  resolved_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_proj_outcome
  ON attempts(project, outcome, created_at);

CREATE VIRTUAL TABLE IF NOT EXISTS attempts_fts USING fts5(
  proposal, failure_signal,
  content='attempts', content_rowid='id',
  tokenize='trigram'
);

CREATE TRIGGER IF NOT EXISTS attempts_ai AFTER INSERT ON attempts BEGIN
  INSERT INTO attempts_fts(rowid, proposal, failure_signal)
  VALUES (new.id, new.proposal, new.failure_signal);
END;

CREATE TRIGGER IF NOT EXISTS attempts_ad AFTER DELETE ON attempts BEGIN
  INSERT INTO attempts_fts(attempts_fts, rowid, proposal, failure_signal)
  VALUES ('delete', old.id, old.proposal, old.failure_signal);
END;

CREATE TRIGGER IF NOT EXISTS attempts_au AFTER UPDATE ON attempts BEGIN
  INSERT INTO attempts_fts(attempts_fts, rowid, proposal, failure_signal)
  VALUES ('delete', old.id, old.proposal, old.failure_signal);
  INSERT INTO attempts_fts(rowid, proposal, failure_signal)
  VALUES (new.id, new.proposal, new.failure_signal);
END;

CREATE TABLE IF NOT EXISTS injections (
  id                      INTEGER PRIMARY KEY,
  created_at              TEXT NOT NULL,
  project                 TEXT NOT NULL,
  session_id              TEXT,
  query_snippet           TEXT,
  hit_count               INTEGER NOT NULL,
  marked_useful           INTEGER NOT NULL DEFAULT 0,
  marked_false_positive   INTEGER NOT NULL DEFAULT 0
);
"""


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_project_root(cwd):
    """cwd から .git を遡って探し、プロジェクトルートを決める。
    見つからなければ cwd 自身をルート扱いにする（単一ファイルの作業でも動く）。"""
    d = os.path.abspath(cwd or os.getcwd())
    start = d
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return start
        d = parent


def get_branch(project_root):
    try:
        out = subprocess.run(
            ["git", "-C", project_root, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            branch = out.stdout.strip()
            return branch or None
    except Exception:
        pass
    return None


def get_db_path(project_root):
    d = os.path.join(project_root, ".resonant")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "attempts.db")


def connect(project_root):
    path = get_db_path(project_root)
    conn = sqlite3.connect(path, timeout=5)
    conn.executescript(SCHEMA)
    return conn


def insert_pending(conn, session_id, project, branch, proposal):
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO attempts(created_at, session_id, project, branch, proposal, outcome) "
        "VALUES (?, ?, ?, ?, ?, 'pending')",
        (now, session_id, project, branch, proposal),
    )
    conn.commit()
    return cur.lastrowid


def mark_latest_pending_failed(conn, session_id, project, failure_signal, evidence):
    """同一セッションの pending を優先し、無ければプロジェクト内の最新 pending を確定させる。"""
    cur = conn.execute(
        "SELECT id FROM attempts "
        "WHERE project=? AND outcome='pending' "
        "ORDER BY (CASE WHEN session_id = ? THEN 0 ELSE 1 END), created_at DESC "
        "LIMIT 1",
        (project, session_id),
    )
    row = cur.fetchone()
    if not row:
        return False
    now = _now_iso()
    conn.execute(
        "UPDATE attempts SET outcome='failed', failure_signal=?, evidence=?, resolved_at=? "
        "WHERE id=?",
        (failure_signal, evidence, now, row[0]),
    )
    conn.commit()
    return True


def list_failed(conn, project, limit=20):
    cur = conn.execute(
        "SELECT id, created_at, branch, proposal, failure_signal, evidence "
        "FROM attempts WHERE project=? AND outcome='failed' "
        "ORDER BY created_at DESC LIMIT ?",
        (project, limit),
    )
    cols = ["id", "created_at", "branch", "proposal", "failure_signal", "evidence"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _build_fts_query(text, limit=60):
    """検索クエリを『含まれる3文字以上の断片のいずれか』に緩和する。
    trigram tokenizer はフレーズ全体の完全一致を要求するため、
    全文をそのまま渡すと言い換えを一切拾えない（実験で確認済み）。
    ASCII識別子（ファイル名・env var・エラーコード）と、
    CJKの連続領域から得た3文字スライディングウィンドウを OR で結合する。
    """
    text = (text or "")[:200]
    terms = set()
    terms.update(ASCII_TOKEN_RE.findall(text))
    for run in CJK_RUN_RE.findall(text):
        for i in range(len(run) - 2):
            terms.add(run[i:i + 3])
    if not terms:
        return None
    terms = list(terms)[:limit]
    escaped = [t.replace('"', '""') for t in terms]
    return " OR ".join(f'"{t}"' for t in escaped)


def search_failed(conn, project, query_text, limit=5):
    fts_query = _build_fts_query(query_text)
    if not fts_query:
        return []
    try:
        cur = conn.execute(
            "SELECT a.id, a.created_at, a.branch, a.proposal, a.failure_signal, a.evidence "
            "FROM attempts_fts f "
            "JOIN attempts a ON a.id = f.rowid "
            "WHERE attempts_fts MATCH ? AND a.outcome = 'failed' AND a.project = ? "
            "ORDER BY rank LIMIT ?",
            (fts_query, project, limit),
        )
    except sqlite3.OperationalError:
        return []
    cols = ["id", "created_at", "branch", "proposal", "failure_signal", "evidence"]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def log_injection(conn, project, session_id, query_snippet, hit_count):
    now = _now_iso()
    conn.execute(
        "INSERT INTO injections(created_at, project, session_id, query_snippet, hit_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (now, project, session_id, query_snippet, hit_count),
    )
    conn.commit()


def mark_last_injection(conn, project, useful):
    cur = conn.execute(
        "SELECT id FROM injections WHERE project=? ORDER BY created_at DESC LIMIT 1",
        (project,),
    )
    row = cur.fetchone()
    if not row:
        return False
    col = "marked_useful" if useful else "marked_false_positive"
    conn.execute(f"UPDATE injections SET {col}=1 WHERE id=?", (row[0],))
    conn.commit()
    return True


def stats(conn, project):
    def count(sql, *params):
        return conn.execute(sql, params).fetchone()[0]

    return {
        "total": count("SELECT COUNT(*) FROM attempts WHERE project=?", project),
        "failed": count("SELECT COUNT(*) FROM attempts WHERE project=? AND outcome='failed'", project),
        "injections": count("SELECT COUNT(*) FROM injections WHERE project=?", project),
        "useful": count("SELECT COUNT(*) FROM injections WHERE project=? AND marked_useful=1", project),
        "false_positive": count("SELECT COUNT(*) FROM injections WHERE project=? AND marked_false_positive=1", project),
    }
