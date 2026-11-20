# Rebuild measurement

How long does it take to rebuild a sandbox that lost its state? This directory times a fresh
`git clone` plus dependency install, the floor of what a returning user waits for on a provider
that doesn't preserve the environment.

## Environment (run of November 19, 2026)

| Setting | Value |
|---|---|
| Platform | DigitalOcean Harness Runtime (public preview), sandbox with no agent (`harness: none`) |
| Sandbox size | `mars-2vcpu-4gb` (2 vCPU, 4 GB memory) |
| Region | `ric1` |
| Date | 2026-11-19, 21:24–21:26 (sandbox clock) |
| Caches | npm and pip caches cleared before every run |
| Runs | 3 per repository, each in a fresh directory; the median is reported |

Tool versions (git, Node.js, npm, Python) were those in the Harness Runtime base image on that date and were not recorded.

## What it measures

| Repository | Install command |
|---|---|
| [pallets/flask](https://github.com/pallets/flask) | `python3 -m venv .venv && .venv/bin/pip install -q -e . pytest` |
| [expressjs/express](https://github.com/expressjs/express) | `npm install --no-audit --no-fund` |
| [fastify/fastify](https://github.com/fastify/fastify) | `npm install --no-audit --no-fund` |

Each run is a full `git clone` of the default branch followed by the install. Repositories were cloned at whatever commit their default branch pointed to at run time.

**Not measured:** build steps, starting servers, running tests, restarting processes on top of saved files, and model tokens spent re-reading context. Network speed varies by provider and region.

## Results

Medians of 3 runs (every run is in `results/rebuild-results-2026-11-19.csv`):

| Repository | Clone (s) | Install (s) | Total (s) |
|---|---|---|---|
| Flask | 0.7 | 5.1 | 5.8 |
| Express | 0.6 | 12.0 | 12.7 |
| Fastify | 0.7 | 22.2 | 23.0 |

Every run was within 0.6 seconds of its repository's median. The cost model uses the Express median (12.7 s) as the full-rebuild time.

## Reproduce it

Requirements: `doctl` with the `harness-runtime` commands, authenticated to a DigitalOcean account (see `requirements.txt`). Running the test uses a few minutes of Harness Runtime compute.

```bash
# 1. Create the sandbox
doctl harness-runtime create --spec ./rebuild-test.yaml

# 2. Upload the script and start it once, in the background
doctl harness-runtime upload rebuild-test --local-file ./measure_rebuild.py --workspace-path measure_rebuild.py
doctl harness-runtime exec rebuild-test --workdir /workspace -- sh -c "setsid nohup python3 measure_rebuild.py > measure.log 2>&1 &"

# 3. Check progress until the last line reads DONE (a few minutes)
doctl harness-runtime exec rebuild-test -- tail -5 /workspace/measure.log

# 4. Save the results and remove the sandbox
doctl harness-runtime exec rebuild-test -- cat /workspace/measure.log
doctl harness-runtime download rebuild-test --workspace-path rebuild-results.csv --save-to ./rebuild-results.csv
doctl harness-runtime remove rebuild-test
```

The script runs in the background with a lock file, because a long-running foreground `exec` can be retried by the client and start a second copy. To time your own repository, add a line to `REPOS` at the top of `measure_rebuild.py`.

`rebuild-test.yaml` sets `keep_warm: true` so the sandbox isn't paused mid-measurement. Remove the sandbox when you're done; it bills until removed.
