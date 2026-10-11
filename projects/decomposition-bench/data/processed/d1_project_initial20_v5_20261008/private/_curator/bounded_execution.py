"""Run a candidate with live time/output bounds; preserve failed denominators."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time


def terminate_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    else:
        process.kill()


def evaluate(candidate, cases, timeout_seconds=20, output_limit=1024 * 1024):
    count = len(json.loads(Path(cases).read_text(encoding="utf-8")))
    command = [sys.executable, str(Path(__file__).with_name("evaluate_candidate.py")),
               "--candidate", str(Path(candidate).resolve()), "--cases", str(Path(cases).resolve())]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streams = [bytearray(), bytearray()]
    exceeded = threading.Event()
    lock = threading.Lock()
    total = [0]

    def drain(pipe, index):
        while True:
            chunk = os.read(pipe.fileno(), 4096)
            if not chunk:
                break
            with lock:
                remaining = max(0, output_limit - total[0])
                streams[index].extend(chunk[:remaining])
                total[0] += len(chunk)
                if total[0] > output_limit:
                    exceeded.set()

    readers = [threading.Thread(target=drain, args=(pipe, index), daemon=True)
               for index, pipe in enumerate([process.stdout, process.stderr])]
    started = time.monotonic()
    for reader in readers:
        reader.start()
    failure = None
    while process.poll() is None:
        if exceeded.is_set():
            failure = "output_limit"
            break
        if time.monotonic() - started >= timeout_seconds:
            failure = "timeout"
            break
        time.sleep(0.02)
    if failure:
        terminate_tree(process)
    process.wait(timeout=6)
    for reader in readers:
        reader.join(timeout=1)
    if exceeded.is_set():
        failure = "output_limit"
    if not failure and process.returncode:
        failure = "process_error"
    if not failure:
        try:
            result = json.loads(streams[0].decode("utf-8"))
        except (UnicodeError, ValueError):
            failure = "invalid_evaluation_output"
    if failure:
        result = {"cases": count, "passed": 0, "all_pass": False,
                  "results": [], "execution_error": failure,
                  "stderr_tail": streams[1].decode("utf-8", errors="replace")[-2000:]}
    result["execution_seconds"] = time.monotonic() - started
    result["captured_output_bytes"] = sum(map(len, streams))
    return result
