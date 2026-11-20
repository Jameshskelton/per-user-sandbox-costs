#!/usr/bin/env python3
"""
run.py -- execute the model-synthesis measurement runs.

Phase A (collection):  all configs, all tasks, concurrent. Cost/output data.
Phase B (latency):     configs marked "latency": true, STRICTLY SEQUENTIAL.
                       Only these timings are valid for percentiles.

Everything is append-only and resumable. Every raw response body is saved.

  export DO_INFERENCE_KEY=...
  python3 run.py --phase a --dry-run
  python3 run.py --phase a --limit 2          # smoke test on 2 tasks
  python3 run.py --phase a
  python3 run.py --phase b --latency-tasks 7
"""

import argparse
import json
import os
import pathlib
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

LOCK = threading.Lock()


# ---------------------------------------------------------------- request body

OUTPUT_CONTRACT = """

End your response with exactly these three lines and nothing after them:

RECOMMENDATION: <the number of your chosen option, then its exact text>
CONFIDENCE: <high | medium | low>
TOP_RISK: <one sentence>"""


def build_body(cfg, task):
    prompt = task["prompt"].rstrip()

    # Render the closed option set into the prompt, numbered. Numbering matters:
    # models routinely paraphrase a "verbatim" label into a full sentence, which
    # then fails normalization. A leading integer is unambiguous to parse.
    opts = task.get("options") or []
    if opts:
        rendered = "\n".join(f"{i}. {o}" for i, o in enumerate(opts, 1))
        prompt += ("\n\nChoose exactly one of the following numbered options:\n"
                   + rendered
                   + "\n\nDo not propose an option that is not listed.")

    prompt += OUTPUT_CONTRACT

    body = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
    }
    if cfg.get("reasoning_effort"):
        body["reasoning_effort"] = cfg["reasoning_effort"]

    if cfg["kind"] == "synthesis":
        tool = {"type": "model_synthesis"}
        # A preset defines the panel and reasoning depth itself. Don't send
        # analysis_models, a judge, or reasoning_effort alongside it.
        if cfg.get("preset"):
            tool["preset"] = cfg["preset"]
        if cfg.get("analysis_models"):
            tool["analysis_models"] = cfg["analysis_models"]
        if cfg.get("judge"):
            tool["model"] = cfg["judge"]
        if cfg.get("reasoning_effort"):
            tool["reasoning_effort"] = cfg["reasoning_effort"]
        tool.update(cfg.get("extra_tool") or {})
        body["tools"] = [tool]

    # additional tool objects (e.g. web_search) alongside the primary tool
    for extra in cfg.get("extra_tools") or []:
        body.setdefault("tools", []).append(extra)

    # documented for server-side tools: "auto" lets the model decide,
    # "required" forces invocation before responding
    if cfg.get("tool_choice"):
        body["tool_choice"] = cfg["tool_choice"]

    body.update(cfg.get("extra_top") or {})
    return body


# ------------------------------------------------------- response introspection
# The per-role usage block ("models": [{role: panel, ...}]) is nested inside the
# response and in at least one observed case appeared as an escaped JSON string.
# So: walk everything, and try to parse strings as JSON too.


def walk_nodes(node, depth=0):
    if depth > 12:
        return
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from walk_nodes(v, depth + 1)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v, depth + 1)
    elif isinstance(node, str) and len(node) > 20 and node.lstrip()[:1] in "{[":
        try:
            yield from walk_nodes(json.loads(node), depth + 1)
        except Exception:
            return


def find_role_usage(raw):
    """Return the list of per-role usage dicts (panel/judge), or []."""
    for node in walk_nodes(raw):
        if not isinstance(node, dict):
            continue
        models = node.get("models")
        if (
            isinstance(models, list)
            and models
            and isinstance(models[0], dict)
            and "role" in models[0]
            and "input_tokens" in models[0]
        ):
            return models
    return []


def find_outer_usage(raw):
    """Billing usage: the top-level block using prompt_tokens/completion_tokens."""
    u = raw.get("usage")
    if isinstance(u, dict) and "prompt_tokens" in u:
        return u
    for node in walk_nodes(raw):
        if isinstance(node, dict) and "prompt_tokens" in node and "total_tokens" in node:
            return node
    return {}


def extract_text(raw):
    try:
        msg = raw["choices"][0]["message"]
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(p.get("text", "") for p in content if isinstance(p, dict))
    except Exception:
        pass
    return ""


def count_search_calls(raw):
    """
    Count web search invocations. Billed per request ($10/1000), invisible to
    token accounting. Handles both observed shapes: a `web_search_call` block,
    and a `tool_use` annotation with name == "web_search".
    """
    n = 0
    for node in walk_nodes(raw):
        if not isinstance(node, dict):
            continue
        if node.get("type") == "web_search_call":
            n += 1
        elif node.get("name") == "web_search" and (
            "call_id" in node or "arguments" in node
        ):
            n += 1
    return n


CONTRACT_RE = re.compile(
    r"RECOMMENDATION:\s*(?P<rec>.+?)\s*[\r\n]+\s*CONFIDENCE:\s*(?P<conf>high|medium|low)"
    r"\s*[\r\n]+\s*TOP_RISK:\s*(?P<risk>.+)",
    re.IGNORECASE | re.DOTALL,
)


def parse_contract(text):
    matches = list(CONTRACT_RE.finditer(text or ""))
    if not matches:
        return None
    m = matches[-1]
    return {
        "recommendation": m.group("rec").strip().strip("*` "),
        "confidence": m.group("conf").strip().lower(),
        "top_risk": " ".join(m.group("risk").split())[:400],
    }


# ------------------------------------------------------------------ single call


def do_call(session, endpoint, key, cfg, task, rep, phase, raw_dir, timeout, max_retries):
    body = build_body(cfg, task)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    effort_dropped = False
    attempt = 0
    last_err = None

    while attempt <= max_retries:
        attempt += 1
        t0 = time.time()
        try:
            r = session.post(endpoint, headers=headers, json=body, timeout=timeout)
            t1 = time.time()
            status = r.status_code
            text_body = r.text

            # Some models may not accept reasoning_effort. Drop it once and retry.
            if status == 400 and "reasoning_effort" in text_body and not effort_dropped:
                body.pop("reasoning_effort", None)
                if "tools" in body:
                    body["tools"][0].pop("reasoning_effort", None)
                effort_dropped = True
                last_err = "400 reasoning_effort -> retrying without it"
                continue

            if status in (429, 500, 502, 503, 504) and attempt <= max_retries:
                last_err = f"HTTP {status}"
                time.sleep(min(60, 4 * attempt + random.random() * 3))
                continue

            try:
                raw = r.json()
            except Exception:
                raw = {"_unparseable_body": text_body[:20000]}

            fname = f"{task['task_id']}__{cfg['id']}__{rep}.json"
            (raw_dir / fname).write_text(json.dumps(raw, indent=2)[:4_000_000])

            roles = find_role_usage(raw)
            outer = find_outer_usage(raw)
            text = extract_text(raw)
            parsed = parse_contract(text)
            # web search is billed per request and is invisible to token
            # accounting, so count invocations explicitly.
            search_calls = count_search_calls(raw)

            return {
                "task_id": task["task_id"],
                "use_case": task.get("use_case"),
                "config_id": cfg["id"],
                "rep": rep,
                "attempt": attempt,
                "retried": attempt > 1,
                "phase": phase,
                "kind": cfg["kind"],
                "top_level_model": cfg["model"],
                "judge_model": cfg.get("judge"),
                "judge_on_panel": cfg.get("judge_on_panel"),
                "analysis_models": cfg.get("analysis_models") or [],
                "reasoning_effort": cfg.get("reasoning_effort"),
                "tool_choice": cfg.get("tool_choice"),
                "search_calls": search_calls,
                "effort_dropped": effort_dropped,
                "http_status": status,
                "error": None if status == 200 else text_body[:600],
                "latency_ms": int((t1 - t0) * 1000),
                "t_send": t0,
                "outer_usage": outer,
                "role_usage": roles,
                "role_statuses": {
                    f"{m.get('role')}:{m.get('model')}": m.get("status") for m in roles
                },
                "partial_failure": any(
                    m.get("status") not in (None, "success") for m in roles
                ),
                "response_text": text,
                "parsed": parsed,
                "contract_violation": parsed is None,
                "raw_path": f"raw/{fname}",
            }

        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
            if attempt <= max_retries:
                time.sleep(min(60, 4 * attempt))
                continue

    return {
        "task_id": task["task_id"],
        "config_id": cfg["id"],
        "rep": rep,
        "attempt": attempt,
        "retried": True,
        "phase": phase,
        "http_status": None,
        "error": last_err,
        "latency_ms": None,
        "outer_usage": {},
        "role_usage": [],
        "response_text": "",
        "parsed": None,
        "contract_violation": True,
    }


# ------------------------------------------------------------------------ main


def load_jsonl(p):
    out = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["a", "b"], required=True)
    ap.add_argument("--tasks", default="tasks.jsonl")
    ap.add_argument("--configs", default="configs.json")
    ap.add_argument("--out", default="results.jsonl")
    ap.add_argument("--raw-dir", default="raw")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None, help="first N tasks only")
    ap.add_argument("--only-config", action="append", default=None)
    ap.add_argument("--latency-tasks", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("DO_INFERENCE_KEY")
    if not key and not args.dry_run:
        sys.exit("DO_INFERENCE_KEY not set")

    conf = json.loads(pathlib.Path(args.configs).read_text())
    tasks = load_jsonl(args.tasks)
    configs = [c for c in conf["configs"] if c.get("enabled", True)]
    if args.only_config:
        configs = [c for c in configs if c["id"] in args.only_config]

    if args.phase == "b":
        configs = [c for c in configs if c.get("latency")]
        tasks = tasks[: args.latency_tasks]
        concurrency = 1
    else:
        if args.limit:
            tasks = tasks[: args.limit]
        concurrency = args.concurrency

    raw_dir = pathlib.Path(args.raw_dir) / f"phase_{args.phase}"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = pathlib.Path(args.out)

    done = set()
    if out_path.exists():
        for rec in load_jsonl(out_path):
            if rec.get("http_status") == 200:
                done.add((rec["task_id"], rec["config_id"], rec["rep"], rec.get("phase")))

    jobs = []
    for cfg in configs:
        for task in tasks:
            for rep in range(1, int(cfg.get("reps", 1)) + 1):
                if (task["task_id"], cfg["id"], rep, args.phase) in done:
                    continue
                jobs.append((cfg, task, rep))

    print(f"phase {args.phase}: {len(tasks)} tasks x {len(configs)} configs")
    print(f"{len(jobs)} calls to make, {len(done)} already complete, concurrency {concurrency}")
    if args.dry_run:
        by_cfg = {}
        for cfg, _, _ in jobs:
            by_cfg[cfg["id"]] = by_cfg.get(cfg["id"], 0) + 1
        for k, v in sorted(by_cfg.items()):
            print(f"  {k:26s} {v}")
        print("\nRun --limit 2 first, check the cost in analyze.py, then extrapolate.")
        return

    session = requests.Session()
    fh = out_path.open("a")
    n_done = 0

    def submit(job):
        cfg, task, rep = job
        return do_call(
            session, conf["endpoint"], key, cfg, task, rep, args.phase,
            raw_dir, conf.get("timeout_s", 600), conf.get("max_retries", 2),
        )

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {ex.submit(submit, j): j for j in jobs}
        for fut in as_completed(futures):
            cfg, task, rep = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:  # noqa: BLE001
                rec = {
                    "task_id": task["task_id"], "config_id": cfg["id"], "rep": rep,
                    "phase": args.phase, "http_status": None, "error": repr(e),
                    "outer_usage": {}, "role_usage": [], "parsed": None,
                    "contract_violation": True, "latency_ms": None,
                }
            with LOCK:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                n_done += 1
                flag = "" if rec.get("http_status") == 200 else "  !! " + str(rec.get("error"))[:120]
                print(
                    f"[{n_done}/{len(jobs)}] {rec['task_id']} {rec['config_id']} "
                    f"rep{rep} {rec.get('latency_ms')}ms "
                    f"tok={rec.get('outer_usage', {}).get('total_tokens')}{flag}"
                )

    fh.close()
    print("done ->", out_path)


if __name__ == "__main__":
    main()
