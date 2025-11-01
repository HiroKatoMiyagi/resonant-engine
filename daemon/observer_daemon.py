#!/usr/bin/env python3
import subprocess
import time
import datetime
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "observer_daemon.log")
try:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
except Exception as e:
    print(f"💥 Failed to create log directory: {e}", flush=True)
    LOG_PATH = "/tmp/observer_daemon.log"  # fallback
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    except Exception as inner_e:
        print(f"💥 Secondary log path creation failed: {inner_e}", flush=True)
CHECK_INTERVAL = 10  # 10 seconds

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"Error running '{command}': {result.stderr.strip()}")
        return result.stdout.strip()
    except Exception as e:
        log(f"Exception running '{command}': {e}")
        return ""

def main():
    import sys
    sys.stdout = open(1, 'w', encoding='utf-8', buffering=1)  # 強制フラッシュ設定
    print("🧩 observer_daemon.py main() entered", flush=True)
    print("🪶 STEP 1: Entered main()", flush=True)
    LOCK_FILE = "/private/tmp/observer_daemon.lock"

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
            if diff_output:
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