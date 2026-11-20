"""Measure how long a cold rebuild (git clone + dependency install) takes.

Run inside a fresh Harness Runtime sandbox (harness: none, mars-2vcpu-4gb).
Each repo is rebuilt RUNS times in a fresh directory, with package caches
cleared before every run, to approximate a sandbox that lost its state.

Results:  /workspace/rebuild-results.csv   (one row per step per run)
Progress: /workspace/measure.log           (ends with a line reading DONE)
"""
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time

RUNS = 3
WORK = "/workspace/rebuild-test"
OUT = "/workspace/rebuild-results.csv"
LOCK = "/workspace/.measure-lock"

# name, clone URL, install commands (run inside the cloned repo)
REPOS = [
    ("express", "https://github.com/expressjs/express.git",
     ["npm install --no-audit --no-fund"]),
    ("fastify", "https://github.com/fastify/fastify.git",
     ["npm install --no-audit --no-fund"]),
    ("flask", "https://github.com/pallets/flask.git",
     ["python3 -m venv .venv", ".venv/bin/pip install -q -e . pytest"]),
]

CLEAR_CACHES = "npm cache clean --force >/dev/null 2>&1; python3 -m pip cache purge >/dev/null 2>&1; true"


def log(msg):
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def timed(cmd, cwd):
    start = time.monotonic()
    proc = subprocess.run(cmd, shell=True, cwd=cwd,
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        log(f"  FAILED ({proc.returncode}): {cmd}\n{proc.stderr[-800:]}")
    return elapsed, proc.returncode


def main():
    # Guard against the command being started twice
    try:
        os.mkdir(LOCK)
    except FileExistsError:
        log("Another measurement is already running (or finished). Remove /workspace/.measure-lock to rerun.")
        sys.exit(0)

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "run", "clone_s", "install_s", "total_s", "ok"])

    totals = {}
    for name, url, installs in REPOS:
        for run in range(1, RUNS + 1):
            shutil.rmtree(WORK, ignore_errors=True)
            os.makedirs(WORK)
            subprocess.run(CLEAR_CACHES, shell=True)
            log(f"{name} run {run}: cloning")
            clone_s, rc1 = timed(f"git clone --quiet {url} {name}", WORK)
            repo_dir = os.path.join(WORK, name)
            install_s, rc2 = 0.0, 1
            if rc1 == 0:
                log(f"{name} run {run}: installing")
                install_s, rc2 = 0.0, 0
                for cmd in installs:
                    s, rc = timed(cmd, repo_dir)
                    install_s += s
                    if rc != 0:
                        rc2 = rc
                        break
            ok = rc1 == 0 and rc2 == 0
            total = clone_s + install_s
            with open(OUT, "a", newline="") as f:
                csv.writer(f).writerow([name, run, f"{clone_s:.1f}", f"{install_s:.1f}", f"{total:.1f}", ok])
            log(f"{name} run {run}: clone {clone_s:.1f}s, install {install_s:.1f}s, total {total:.1f}s, ok={ok}")
            if ok:
                totals.setdefault(name, []).append(total)

    for name, vals in totals.items():
        log(f"SUMMARY {name}: median {statistics.median(vals):.1f}s over {len(vals)} runs")
    shutil.rmtree(WORK, ignore_errors=True)
    log("DONE")


if __name__ == "__main__":
    main()
