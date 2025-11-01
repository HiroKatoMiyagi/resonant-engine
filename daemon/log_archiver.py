

#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path

DAEMON_DIR = Path(__file__).parent
REPO_ROOT = DAEMON_DIR.parent
LOG_DIR = DAEMON_DIR / "logs"
SRC_LOG = LOG_DIR / "observer_daemon.log"

def run(cmd: str) -> str:
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout.strip()
    except Exception as e:
        return f"__ERR__:{e}"

def safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""

def archive(reason: str):
    # Prepare archive directory (by date)
    day = dt.datetime.now().strftime("%Y-%m-%d")
    archive_dir = LOG_DIR / "archive" / day
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Compute metadata
    local_head = run("git -C \"%s\" rev-parse HEAD" % REPO_ROOT)
    remote_head = run("git -C \"%s\" rev-parse origin/main" % REPO_ROOT)
    last_msg = run("git -C \"%s\" log -1 --pretty=%%s" % REPO_ROOT)
    env_tag = os.environ.get("ENV_TAG", "")
    stat = run("git -C \"%s\" diff --stat HEAD..origin/main" % REPO_ROOT)

    # Copy current log if present
    copied_log = None
    if SRC_LOG.exists():
        copied_log = archive_dir / ("observer_daemon_%s.log" % dt.datetime.now().strftime("%H%M%S"))
        try:
            shutil.copy2(SRC_LOG, copied_log)
        except Exception:
            copied_log = None

    # Build metadata.json
    meta = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "repo_root": str(REPO_ROOT),
        "local_head": local_head,
        "remote_head": remote_head,
        "last_remote_msg": last_msg,
        "env_tag": env_tag,
        "pending_diff_stat": stat,
        "copied_log": str(copied_log) if copied_log else "",
    }
    (archive_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Emit a short navigation pointer for Git messages or external tools
    reflect_link = f"[ReflectLink:{archive_dir}]"
    # Append a lightweight pointer file as well
    (archive_dir / "REFLECT_LINK.txt").write_text(reflect_link + "\n", encoding="utf-8")

    # Also summarize to a journal for quick grep
    journal = LOG_DIR / "archive_journal.jsonl"
    with open(journal, "a", encoding="utf-8") as jf:
        jf.write(json.dumps(meta, ensure_ascii=False) + "\n")

    # Best-effort console message
    print(f"🗃 archived -> {archive_dir}")
    print(reflect_link)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reason", default="manual", help="archival reason tag")
    args = parser.parse_args()
    archive(args.reason)

if __name__ == "__main__":
    main()