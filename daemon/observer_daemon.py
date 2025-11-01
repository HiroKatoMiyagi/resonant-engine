#!/usr/bin/env python3
# 🧩 observer_daemon.py
# 改善案適用済み:
#  - duplicate detection (intent_hash & commit)
#  - unified log_hypothesis_event()
#  - phase=external_sync_validation 付与

# noqa: S603, S607  # subprocess usage intentionally allowed for controlled git commands
import sys
import os
sys.path.append(os.path.dirname(__file__))  # allow importing from daemon directory
import subprocess
import time
import datetime
from daemon import log_archiver
from daemon.hypothesis_trace import HypothesisTrace

 # --- Ensure absolute and consistent logs directory ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "observer_daemon.log")
# Add constant for hypothesis trace log path
HYPOTHESIS_LOG_PATH = os.path.join(LOG_DIR, "hypothesis_trace_log.json")

CONFIG_PATH = os.path.join(BASE_DIR, "config.txt")

def load_check_interval(default=10):
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                value = f.read().strip()
                if value.isdigit():
                    return int(value)
        return default
    except Exception:
        return default

CHECK_INTERVAL = load_check_interval()

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_hypothesis_event(event_type, hyp_id, status=None, phase=None):
    """Unified logger for HypothesisTrace events with optional phase tag."""
    phase_tag = f"[Phase: {phase}] " if phase else ""
    if event_type == "record":
        log(f"[🧠 Hypothesis Recorded] {phase_tag}{hyp_id}: observer_daemon外部更新検知")
    elif event_type == "update":
        log(f"[✅ Hypothesis Updated] {phase_tag}{hyp_id} → {status}")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Error running '{command}': {result.stderr.strip()}")
        return result.stdout.strip()
    except Exception as e:
        log(f"Exception running '{command}': {e}")
        return ""

LOCK_FILE = "/Users/zero/Projects/resonant-engine/daemon/pids/observer_daemon.lock"

def main():
    import sys
    sys.stdout = open(1, 'w', encoding='utf-8', buffering=1)  # 強制フラッシュ設定
    print("🧩 observer_daemon.py main() entered", flush=True)
    print("🪶 STEP 1: Entered main()", flush=True)

    print("🪶 STEP 2: Checking lock file existence...", flush=True)
    # Clean stale lock files older than 5 minutes
    if os.path.exists(LOCK_FILE):
        age = time.time() - os.path.getmtime(LOCK_FILE)
        print(f"🪶 STEP 3: Lock file exists, age={age}s", flush=True)
        if age > 300:  # 5分超過なら削除
            print("⚠️ stale lock detected — removing old lock file.", flush=True)
            os.remove(LOCK_FILE)
        else:
            print("⚠️ observer_daemon is already running. Exiting.", flush=True)
            import sys
            sys.exit(0)
    else:
        open(LOCK_FILE, "w").close()
        print("🪶 STEP 4: Lock file created successfully.", flush=True)

    import atexit
    atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)
    print("🪶 STEP 5: atexit cleanup registered.", flush=True)

    print("🧩 LOCK_FILE check passed, continuing main loop setup...", flush=True)

    print("🔍 observer_daemon started — writing to", LOG_PATH, flush=True)
    log("✅ observer_daemon initialized.")
    try:
        log_archiver.archive("boot")
    except Exception as e:
        log(f"[archive] failed at boot: {e}")
    print("✅ observer_daemon initialized.", flush=True)
    log("🔍 observer_daemon active…")
    print(">>> entering loop", flush=True)
    log(">>> entering loop")
    print("🪶 STEP 6: Setup complete. Entering main loop...", flush=True)
    while True:
        print("🪶 LOOP: Iteration start", flush=True)
        try:
            run_command("git fetch origin main")
            print("🪶 LOOP: git fetch complete", flush=True)
            diff_output = run_command("git diff --stat HEAD..origin/main")
            print("🪶 LOOP: diff check complete", flush=True)
            last_commit_msg = run_command("git log -1 --pretty=%B origin/main").strip()
            if "auto_reflect" in last_commit_msg:
                log("[🌀 Reflection] Self-generated update detected — skipping pull.")
                try:
                    log_archiver.archive("self_reflection_skip")
                except Exception as e:
                    log(f"[archive] failed during auto_reflect: {e}")
            elif "external_update" in last_commit_msg:
                log("[🪞 External Resonance] External update detected — pulling latest changes.")
                # --- Debounce: skip if last recorded commit is identical ---
                last_record_file = os.path.join(LOG_DIR, "last_commit.txt")
                last_commit = run_command("git rev-parse origin/main").strip()
                prev_commit = ""
                if os.path.exists(last_record_file):
                    with open(last_record_file, "r") as f:
                        prev_commit = f.read().strip()
                if prev_commit == last_commit:
                    log(f"[⏸️ Debounce] Skipping duplicate external update for commit {last_commit}.")
                    time.sleep(CHECK_INTERVAL)
                    continue
                with open(last_record_file, "w") as f:
                    f.write(last_commit)

                pull_output = run_command("git pull origin main")
                # --- Step 1: result_diff連携強化 ---
                result_diff = run_command("git diff origin/main..HEAD")
                diff_path = os.path.join(LOG_DIR, f"result_diff_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                with open(diff_path, "w") as diff_file:
                    diff_file.write(result_diff)
                log(f"[🔍 result_diff captured] saved to {diff_path}")

                try:
                    log_archiver.archive("external_update_pull")
                    tracer = HypothesisTrace(log_path=HYPOTHESIS_LOG_PATH)
                    hyp_id = tracer.record(
                        intent_text="observer_daemon外部更新検知",
                        expected_effect="外部commitをpullして同期",
                        target_files=["daemon/observer_daemon.py"]
                    )
                    log_hypothesis_event("record", hyp_id, phase="external_sync_validation")
                    if not hasattr(tracer, "update"):
                        log("[⚠️ result_diff integration skipped: HypothesisTrace.update() not supporting result_diff_path]")
                    with open(diff_path, "r") as df:
                        diff_content = df.read()
                    tracer.update(
                        hyp_id,
                        "validated",
                        pull_output or "差分同期完了",
                        related_commit=run_command("git rev-parse HEAD"),
                        phase="external_sync_validation",
                        result_diff=diff_content
                    )
                    log_hypothesis_event("update", hyp_id, "validated", phase="external_sync_validation")
                except Exception as e:
                    log(f"[archive] failed during external_update: {e}")
            elif diff_output:
                log("🔔 Detected updates on remote main branch:")
                log(diff_output)
            else:
                log("No updates detected.")
        except Exception as e:
            log(f"Main loop exception: {e}")
            print(f"❌ Exception in main loop: {e}", flush=True)
        time.sleep(CHECK_INTERVAL)
        print("🪶 LOOP: sleeping", flush=True)

if __name__ == "__main__":
    try:
        print("🧠 observer_daemon.py starting...", flush=True)
        main()
        print("✅ observer_daemon.py finished execution.", flush=True)
    except Exception as e:
        print(f"💥 Exception during startup: {e}", flush=True)
        import traceback
        traceback.print_exc()
    import atexit
    atexit.register(lambda: log_archiver.archive("atexit"))