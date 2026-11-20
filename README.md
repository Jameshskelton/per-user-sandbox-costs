# Model synthesis measurement harness

Four files. `configs.json` defines the arms, `tasks.jsonl` holds your questions,
`run.py` makes the calls, `analyze.py` produces `metrics.md`.

## Setup

```bash
pip install requests
export DO_INFERENCE_KEY=...
```

Fill in `prices.json` (USD per 1M tokens, plus the cache-read rate) and set
`_snapshot_date`. If you can't find a cache-read rate, set it equal to `input`
and say in the article that cost is an upper bound.

## Order of operations

```bash
# 1. See what you're about to spend. Makes no calls.
python3 run.py --phase a --dry-run

# 2. Smoke test: 2 tasks, all configs. Confirm responses parse.
python3 run.py --phase a --limit 2
python3 analyze.py --results results.jsonl

# 3. STOP HERE and extrapolate cost from step 2 before continuing.
#    A 4-model synthesis call was observed at ~374,000 tokens.

# 4. Full collection pass.
python3 run.py --phase a --concurrency 4

# 5. Latency pass. Sequential by force. Only these timings are valid.
python3 run.py --phase b --latency-tasks 7

# 6. Results.
python3 analyze.py --out metrics.md
```

Safe to interrupt and re-run at any point — completed calls are skipped.

## Call volume

17 calls per task (reps included) x 21 tasks = ~357 calls in phase A,
plus ~63 in phase B. The `synth_*` arms dominate the cost.

## Things that will need your attention

- **`tasks.jsonl` is the real work.** Three examples are included; write 18 more
  from the corpus in the spec. Every task needs an `options` array — that's what
  makes the recommendations comparable without a human rater.
- **Web search arms are disabled** in `configs.json` because the field names
  aren't known yet. When you find them, put them in `extra_tool` / `extra_top`
  and set `"enabled": true`.
- **If qwen or deepseek reject `reasoning_effort`**, the runner drops it and
  retries automatically, flagging `effort_dropped`. Check that column in section 7
  of `metrics.md` — if either model dropped it, say so in the article, because
  it explains the panel work imbalance.
- **The judge arms need a panel that actually disagrees.** If section 5 reports
  n < 5, `analyze.py` will tell you to swap the panel using the pairwise
  agreement table. Re-run only those two configs:
  `python3 run.py --phase a --only-config synth_judge_on --only-config synth_judge_off`

## One thing to watch in the output

Token multiples and cost multiples diverge sharply — in testing, a config at
163x the baseline's tokens came out at 45x the cost, because cache reads are
cheap and two of the four panel models are small. **Quote cost, not tokens.**
