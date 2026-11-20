#!/usr/bin/env python3
"""
analyze.py -- turn results.jsonl into the five numbers the article needs.

  python3 analyze.py --results results.jsonl --tasks tasks.jsonl --out metrics.md

Computes:
  1. Disagreement rate across the four standalone models
  2. Self-disagreement floor (same model, 3 reps) -- makes #1 interpretable
  3. Cost per config, with cache-aware pricing and per-role attribution
  4. p95 latency ratios (phase B only)
  5. Judge self-preference (on-panel vs off-panel judge)
  Plus: panel work imbalance, panel-composition effect, contract violations.
"""

import argparse

import json
import itertools
import re
import pathlib
import statistics
from collections import Counter, defaultdict

SINGLE_HIGH = [
    "single_glm_high",
    "single_kimi_high",
    "single_qwen_high",
    "single_deepseek_high",
]
# The headline divergence rate stays on the four panel-candidate models so it means
# "would a panel of these disagree". The frontier model is included in the pairwise
# table only, where it answers a different question: how often does it agree with each.
PAIRWISE = SINGLE_HIGH + ["single_frontier_high"]
NOISE_CONFIG = "single_glm_high"
BASELINE = "single_glm_high"


def load_jsonl(p):
    out = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


MATCH_MODES = {}  # raw answer -> how it was resolved


def _clean(s):
    return " ".join(str(s).lower().split()).strip(" .*`\"'")


def _words(s):
    return {w for w in re.split(r"[^a-z0-9]+", s.lower()) if len(w) > 2}


def norm_rec(raw, options):
    """Map a RECOMMENDATION line onto the task's closed option set."""
    if raw is None:
        return None
    s = _clean(raw)
    if not options:
        return s or None
    opts = [o.lower().strip() for o in options]

    # 1. leading option number -- the reliable path
    m = re.match(r"^(?:option\s*)?(\d{1,2})\b", s)
    if m:
        i = int(m.group(1)) - 1
        if 0 <= i < len(opts):
            MATCH_MODES[s] = "number"
            return opts[i]

    # 2. exact, then substring
    if s in opts:
        MATCH_MODES[s] = "exact"
        return s
    for o in opts:
        if o in s or s in o:
            MATCH_MODES[s] = "substring"
            return o

    # 3. word-overlap fallback. Flagged, never silent: a paraphrase like
    #    "fine-tune a small transformer classifier" has to be reviewed by hand.
    sw = _words(s.replace("-", " "))
    scored = sorted(
        ((len(_words(o.replace("-", " ")) & sw) / max(1, len(_words(o.replace("-", " ")))), o)
         for o in opts), reverse=True)
    best, runner = scored[0], (scored[1] if len(scored) > 1 else (0.0, None))
    if best[0] >= 0.6 and best[0] - runner[0] >= 0.2:
        MATCH_MODES[s] = "overlap-review"
        return best[1]

    MATCH_MODES[s] = "unmatched"
    return f"UNMATCHED::{s[:60]}"


def pct(n, d):
    return "n/a" if not d else f"{100.0 * n / d:.0f}% ({n}/{d})"


def p(vals, q):
    if not vals:
        return None
    vs = sorted(vals)
    k = max(0, min(len(vs) - 1, int(round(q * (len(vs) - 1)))))
    return vs[k]


# ------------------------------------------------------------------- cost model


def price_block(prices, model):
    return (prices.get("models") or {}).get(model) or {}


def cost_of_usage(prices, model, inp, out, cache_read):
    pb = price_block(prices, model)
    if pb.get("input") is None or pb.get("output") is None:
        return None
    cache_rate = pb.get("cache_read")
    if cache_rate is None:
        cache_rate = pb["input"]
    uncached = max(0, (inp or 0) - (cache_read or 0))
    return (
        uncached * pb["input"] / 1e6
        + (cache_read or 0) * cache_rate / 1e6
        + (out or 0) * pb["output"] / 1e6
    )


def record_cost(prices, rec):
    """
    Per-role attribution where available, plus the synthesis residual, plus
    web-search request charges (billed per request, not per token).
    Returns (cost_or_None, residual_dict, warning_or_None).
    """
    # web search is billed per request and is invisible to token accounting
    search_rate = prices.get("web_search_per_1000_requests")
    search_cost = 0.0
    if search_rate is not None:
        search_cost = (rec.get("search_calls") or 0) * search_rate / 1000.0

    outer = rec.get("outer_usage") or {}
    o_in = outer.get("prompt_tokens") or 0
    o_out = outer.get("completion_tokens") or 0
    o_cache = outer.get("cache_read_input_tokens") or 0
    roles = rec.get("role_usage") or []

    if not roles:
        c = cost_of_usage(prices, rec.get("top_level_model"), o_in, o_out, o_cache)
        return (None if c is None else c + search_cost), None, None

    total = 0.0
    missing = False
    r_in = r_out = r_cache = 0
    for m in roles:
        ri = m.get("input_tokens") or 0
        ro = m.get("output_tokens") or 0
        rc = m.get("cache_read_input_tokens") or 0
        r_in += ri
        r_out += ro
        r_cache += rc
        c = cost_of_usage(prices, m.get("model"), ri, ro, rc)
        if c is None:
            missing = True
        else:
            total += c

    resid = {
        "input_tokens": o_in - r_in,
        "output_tokens": o_out - r_out,
        "cache_read_input_tokens": o_cache - r_cache,
    }
    warn = None
    if resid["input_tokens"] < 0 or resid["output_tokens"] < 0:
        warn = "negative residual (outer < sum of roles) -- check attribution"

    c = cost_of_usage(
        prices,
        rec.get("top_level_model"),
        max(0, resid["input_tokens"]),
        max(0, resid["output_tokens"]),
        max(0, resid["cache_read_input_tokens"]),
    )
    if c is None:
        missing = True
    else:
        total += c

    return (None if missing else total + search_cost), resid, warn


# ------------------------------------------------------------------------ main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results.jsonl")
    ap.add_argument("--tasks", default="tasks.jsonl")
    ap.add_argument("--prices", default="prices.json")
    ap.add_argument("--out", default="metrics.md")
    args = ap.parse_args()

    recs = [r for r in load_jsonl(args.results) if r.get("http_status") == 200]
    tasks = {t["task_id"]: t for t in load_jsonl(args.tasks)}
    prices = json.loads(pathlib.Path(args.prices).read_text())

    # index: (config, task, rep) -> record  (last write wins)
    idx = {}
    by_cfg = defaultdict(list)
    for r in recs:
        idx[(r["config_id"], r["task_id"], r.get("rep", 1))] = r
        by_cfg[r["config_id"]].append(r)

    def rec_of(cfg, task_id, rep=1):
        return idx.get((cfg, task_id, rep))

    def choice(cfg, task_id, rep=1):
        r = rec_of(cfg, task_id, rep)
        if not r or not r.get("parsed"):
            return None
        return norm_rec(r["parsed"].get("recommendation"), tasks.get(task_id, {}).get("options"))

    def difficulty(tid):
        tags = set(tasks.get(tid, {}).get("tags") or [])
        if "H" in tags:
            return "hard"
        if "E" in tags:
            return "easy"
        return "unlabeled"

    # Open-ended tasks have no option set, so norm_rec returns raw prose. Two runs
    # of the same model will never produce identical prose, which would register as
    # 100% disagreement and 0% stability. They must be excluded from every
    # agreement metric. Cost, latency and search data for them remain valid.
    CLOSED = [t for t in tasks if tasks[t].get("options")]
    OPEN = [t for t in tasks if not tasks[t].get("options")]

    L = []
    W = L.append
    W("# Model synthesis: measured results\n")
    W(f"Records analyzed: {len(recs)} successful calls across {len(tasks)} tasks.")
    W(f"Price snapshot: {prices.get('_snapshot_date')}\n")

    # ---- 0: did the tool actually run? ----------------------------------
    W("## 0. Tool firing rate\n")
    W("A synthesis call only counts if the response contained a panel/judge usage block.\n")
    W("| config | calls | fired | firing rate |")
    W("| --- | --- | --- | --- |")
    fire_tot = fire_hit = 0
    for cfg in sorted({r["config_id"] for r in recs if r.get("kind") == "synthesis"}):
        rs = [r for r in recs if r["config_id"] == cfg]
        hit = sum(1 for r in rs if r.get("role_usage"))
        fire_tot += len(rs)
        fire_hit += hit
        W(f"| {cfg} | {len(rs)} | {hit} | {pct(hit, len(rs))} |")
    if fire_tot and fire_hit < fire_tot:
        W(f"\n> **{fire_tot - fire_hit} of {fire_tot} synthesis calls did not invoke the tool.**")
        W("> Those calls are single-model calls wearing a synthesis label. Every cost,")
        W("> latency and recommendation number for those configs below is contaminated.")
        W("> Fix this before reading anything else.")

    # ---- 1 & 2: disagreement --------------------------------------------
    W("## 1. Disagreement across the four standalone models\n")
    divergent, convergent, incomplete = [], [], []
    for tid in CLOSED:
        picks = {c: choice(c, tid) for c in SINGLE_HIGH}
        if any(v is None for v in picks.values()):
            incomplete.append(tid)
            continue
        (divergent if len(set(picks.values())) > 1 else convergent).append(tid)

    n_cmp = len(divergent) + len(convergent)
    W(f"- Closed-choice tasks compared: {len(CLOSED)} of {len(tasks)} "
      f"({len(OPEN)} open-ended tasks excluded from all agreement metrics — "
      f"free-text answers cannot be matched across runs)")
    W(f"- Tasks where the four models did not all agree: **{pct(len(divergent), n_cmp)}**")
    W(f"- Tasks excluded (missing or unparsed response): {len(incomplete)} {incomplete or ''}")

    W("\n### Divergence by task difficulty\n")
    W("Tag tasks `E` when the evidence is dispositive and `H` when it genuinely")
    W("underdetermines the answer. This split is the spine of the argument:")
    W("a panel cannot add value where a single model already has enough to go on.\n")
    W("| difficulty | tasks | divergent |")
    W("| --- | --- | --- |")
    for tier in ("easy", "hard", "unlabeled"):
        d = [t for t in divergent if difficulty(t) == tier]
        c = [t for t in convergent if difficulty(t) == tier]
        if d or c:
            W(f"| {tier} | {len(d) + len(c)} | {pct(len(d), len(d) + len(c))} |")
    if not any(difficulty(t) == "hard" for t in divergent + convergent):
        W("\n> **No tasks tagged `H`.** Every task carries a dispositive clue, so a")
        W("> near-zero divergence rate is expected and cannot support a general")
        W("> claim that ensembling does not help. Add a hard tier before publishing.")

    # pairwise
    W("\nPairwise agreement (frontier model included):\n")
    W("| pair | agree |")
    W("| --- | --- |")
    for i in range(len(PAIRWISE)):
        for j in range(i + 1, len(PAIRWISE)):
            a, b = PAIRWISE[i], PAIRWISE[j]
            same = tot = 0
            for tid in CLOSED:
                x, y = choice(a, tid), choice(b, tid)
                if x and y:
                    tot += 1
                    same += x == y
            W(f"| {a} vs {b} | {pct(same, tot)} |")

    W("\n## 2. Self-disagreement floor (same model, 3 reps)\n")
    self_div = self_tot = 0
    for tid in CLOSED:
        pk = [choice(NOISE_CONFIG, tid, rep) for rep in (1, 2, 3)]
        if any(v is None for v in pk):
            continue
        self_tot += 1
        self_div += len(set(pk)) > 1
    W(f"- {NOISE_CONFIG} disagreeing with itself: **{pct(self_div, self_tot)}**")
    if n_cmp and self_tot:
        cross = 100.0 * len(divergent) / n_cmp
        floor = 100.0 * self_div / self_tot
        W(f"- Cross-model divergence minus sampling floor: **{cross - floor:.0f} pp**")
        W("  (This is the headline. It is the disagreement attributable to model choice")
        W("   rather than to sampling variance.)")

    # confidence on divergent vs convergent
    W("\n### Confidence when models disagree\n")
    for label, group in (("divergent", divergent), ("convergent", convergent)):
        conf = defaultdict(int)
        for tid in group:
            for c in SINGLE_HIGH:
                r = rec_of(c, tid)
                if r and r.get("parsed"):
                    conf[r["parsed"].get("confidence")] += 1
        W(f"- {label} tasks: {dict(conf)}")

    # ---- 2b: run-to-run stability ---------------------------------------
    W("\n## 2b. Run-to-run stability\n")
    W("Same config, same task, repeated runs. Asks a different question from")
    W("section 6: not *does synthesis change the answer* but *does synthesis give")
    W("the same answer twice*. Stability is a real thing to buy even when the")
    W("answer itself doesn't change.\n")

    def stability(cfg, tids=None):
        unanimous = considered = 0
        agree_pairs = total_pairs = 0
        distinct = []
        for tid in (tids if tids is not None else CLOSED):
            picks = []
            for rep in range(1, 6):
                v = choice(cfg, tid, rep)
                if v is not None and not str(v).startswith("UNMATCHED"):
                    picks.append(v)
            if len(picks) < 2:
                continue
            considered += 1
            unanimous += len(set(picks)) == 1
            distinct.append(len(set(picks)))
            for a, b in itertools.combinations(picks, 2):
                total_pairs += 1
                agree_pairs += a == b
        return {
            "tasks": considered,
            "unanimous": unanimous,
            "pairs": total_pairs,
            "agree": agree_pairs,
            "mean_distinct": (sum(distinct) / len(distinct)) if distinct else None,
        }

    multi = sorted(
        c for c in by_cfg
        if sum(1 for r in by_cfg[c] if (r.get("rep") or 1) > 1) > 0
    )
    W("| config | tasks | all reps identical | pairwise agreement | mean distinct answers |")
    W("| --- | --- | --- | --- | --- |")
    stab = {}
    for cfg in multi:
        s = stability(cfg)
        stab[cfg] = s
        if not s["tasks"]:
            continue
        md = f"{s['mean_distinct']:.2f}" if s["mean_distinct"] else "n/a"
        W(f"| {cfg} | {s['tasks']} | {pct(s['unanimous'], s['tasks'])} | "
          f"{pct(s['agree'], s['pairs'])} | {md} |")

    def pw(cfg):
        s = stab.get(cfg) or {}
        return (100.0 * s["agree"] / s["pairs"]) if s.get("pairs") else None

    a, b = pw("synth_heavy2"), pw(BASELINE)
    if a is not None and b is not None:
        W(f"\n**{('synth_heavy2 is %.0f pp more stable' % (a - b)) if a > b else ('synth_heavy2 is %.0f pp LESS stable' % (b - a))} "
          f"than {BASELINE}** ({a:.0f}% vs {b:.0f}% pairwise agreement).")
        if a > b + 10:
            W("\nSynthesis is buying stability rather than different answers. That is a")
            W("legitimate thing to pay for -- reproducibility, fewer coin-flip outcomes")
            W("on repeated runs -- and it is the strongest remaining case for the tool.")
            W("Frame it as variance reduction, not as accuracy.")
        elif abs(a - b) <= 10:
            W("\nNo meaningful stability gain. Synthesis costs a large multiple, answers")
            W("no more consistently, and differs from a single model no more often than")
            W("that model differs from itself. On this task class the case does not close")
            W("in the tool's favour.")
        else:
            W("\nSynthesis is *less* stable than a single model. If this holds, the extra")
            W("moving parts (panel sampling, judge selection, synthesis rewrite) are")
            W("adding variance rather than removing it. Check partial-failure rates for")
            W("this arm before publishing -- degraded panels would explain it.")

    W("\n### Stability by difficulty\n")
    W("| config | difficulty | pairwise agreement |")
    W("| --- | --- | --- |")
    for cfg in [c for c in ("synth_heavy2", BASELINE, "synth_preset_balanced") if c in stab]:
        for tier in ("easy", "hard", "unlabeled"):
            tids = [t for t in CLOSED if difficulty(t) == tier]
            s = stability(cfg, tids)
            if s["pairs"]:
                W(f"| {cfg} | {tier} | {pct(s['agree'], s['pairs'])} |")

    # ---- 3: cost ---------------------------------------------------------
    W("\n## 3. Cost and tokens per config\n")
    W("| config | calls | median total tokens | median cost | x baseline | cache read share |")
    W("| --- | --- | --- | --- | --- | --- |")
    per_cfg_tok, per_cfg_cost, per_cfg_share, warnings = {}, {}, {}, []

    # first pass: compute everything so the baseline exists before printing
    for cfg in sorted(by_cfg):
        toks, costs, cshare = [], [], []
        for r in by_cfg[cfg]:
            u = r.get("outer_usage") or {}
            if u.get("total_tokens"):
                toks.append(u["total_tokens"])
                pt = u.get("prompt_tokens") or 0
                if pt:
                    cshare.append((u.get("cache_read_input_tokens") or 0) / pt)
            c, _, warn = record_cost(prices, r)
            if warn:
                warnings.append(f"{r['task_id']}/{cfg}: {warn}")
            if c is not None:
                costs.append(c)
        per_cfg_tok[cfg] = statistics.median(toks) if toks else None
        per_cfg_cost[cfg] = statistics.median(costs) if costs else None
        per_cfg_share[cfg] = statistics.median(cshare) if cshare else None

    base_cost = per_cfg_cost.get(BASELINE)
    for cfg in sorted(by_cfg):
        cshare = per_cfg_share[cfg]
        ratio = ""
        if per_cfg_cost.get(cfg) and base_cost:
            ratio = "%.0fx" % (per_cfg_cost[cfg] / base_cost)
        elif per_cfg_tok.get(cfg) and per_cfg_tok.get(BASELINE):
            ratio = "%.0fx (tokens)" % (per_cfg_tok[cfg] / per_cfg_tok[BASELINE])
        W(
            f"| {cfg} | {len(by_cfg[cfg])} | "
            f"{int(per_cfg_tok[cfg]) if per_cfg_tok[cfg] else 'n/a'} | "
            f"{('$%.4f' % per_cfg_cost[cfg]) if per_cfg_cost[cfg] else 'no prices'} | "
            f"{ratio} | "
            f"{('%.0f%%' % (100 * cshare)) if cshare else 'n/a'} |"
        )
    if all(v is None for v in per_cfg_cost.values()):
        W("\n**prices.json is unfilled -- token ratios only. Fill it before publishing cost claims.**")
    for w in warnings[:10]:
        W(f"\n> warning: {w}")

    # ---- panel work imbalance -------------------------------------------
    W("\n### Panel work imbalance (input tokens by role)\n")
    W("| config | role:model | median input tokens | median output tokens |")
    W("| --- | --- | --- | --- |")
    role_tok = defaultdict(lambda: defaultdict(lambda: ([], [])))
    for r in recs:
        for m in r.get("role_usage") or []:
            k = f"{m.get('role')}:{m.get('model')}"
            role_tok[r["config_id"]][k][0].append(m.get("input_tokens") or 0)
            role_tok[r["config_id"]][k][1].append(m.get("output_tokens") or 0)
    for cfg in sorted(role_tok):
        for k, (ins, outs) in role_tok[cfg].items():
            W(f"| {cfg} | {k} | {int(statistics.median(ins))} | {int(statistics.median(outs))} |")

    # ---- what the presets actually contain -------------------------------
    preset_cfgs = sorted(c for c in by_cfg if c.startswith("synth_preset_"))
    if preset_cfgs:
        W("\n### What each preset actually contains\n")
        W("Composition is not documented -- this table is derived from role_usage.\n")
        W("| preset | panel models observed | judge observed |")
        W("| --- | --- | --- |")
        for cfg in preset_cfgs:
            panel, judge = set(), set()
            for r in by_cfg[cfg]:
                for m in r.get("role_usage") or []:
                    (panel if m.get("role") == "panel" else judge).add(m.get("model"))
            W(f"| {cfg.replace('synth_preset_', '')} | "
              f"{', '.join(sorted(panel)) or 'none observed'} | "
              f"{', '.join(sorted(judge)) or 'none observed'} |")
        W("\nIf a preset's panel varies across tasks, say so -- it means composition")
        W("is dynamic and cost is not predictable from the preset name alone.")

    # ---- 4: latency ------------------------------------------------------
    W("\n## 4. Latency\n")
    lat = defaultdict(list)
    lat_a = defaultdict(list)
    for r in recs:
        if r.get("retried") or not r.get("latency_ms"):
            continue
        (lat if r.get("phase") == "b" else lat_a)[r["config_id"]].append(r["latency_ms"])

    def lat_table(d, base_key):
        base_med = statistics.median(d[base_key]) if d.get(base_key) else None
        W("| config | n | median ms | max ms | median x baseline | p95 |")
        W("| --- | --- | --- | --- | --- | --- |")
        for cfg in sorted(d):
            v = d[cfg]
            med = statistics.median(v)
            ratio = f"{med / base_med:.1f}x" if base_med else ""
            p95 = f"{p(v, 0.95)}" if len(v) >= 20 else "n too small"
            W(f"| {cfg} | {len(v)} | {int(med)} | {max(v)} | {ratio} | {p95} |")

    if lat:
        W("### Phase B — sequential, clean\n")
        lat_table(lat, BASELINE)
        W("\n_With n < 20 the nearest-rank p95 is just the maximum, so it is suppressed._")
        W("_Use median for the headline and quote max separately as the worst case._")

    if lat_a:
        W("\n### Phase A — measured under concurrency, USE WITH CARE\n")
        W("These calls ran in parallel, so absolute values are inflated by queuing")
        W("and contention against your own other requests. **Do not quote these as")
        W("percentiles or as precise multiples.** They are usable for one thing: the")
        W("order-of-magnitude gap between single-model and synthesis calls, which is")
        W("far larger than any contention effect.\n")
        lat_table(lat_a, BASELINE)
        if not lat:
            W("\n> No phase B data. If you publish latency from this table, say")
            W("> explicitly that it was measured under concurrent load, report medians")
            W("> rather than percentiles, and round hard — 'minutes versus seconds',")
            W("> not '137x'.")

    if not lat and not lat_a:
        W("_No latency data._")

    W("\n**The structural argument needs no timing data at all:** a synthesis call")
    W("cannot return until the slowest panel model finishes, then the judge reads")
    W("every panel output, then the synthesizer writes the answer. Three serial")
    W("stages, the first of which is a max() across the panel. That is why the gap")
    W("is large and why it widens with panel size regardless of what you measure.")

    # ---- 5: judge self-preference ---------------------------------------
    W("\n## 5. Judge self-preference\n")
    W("Restricted to tasks where the standalone panel members disagreed.\n")

    def judge_pref(synth_cfg, judge_standalone_cfg, panel_standalone_cfgs):
        hits = tot = 0
        detail = []
        for tid in CLOSED:
            panel_picks = [choice(c, tid) for c in panel_standalone_cfgs]
            if any(x is None for x in panel_picks) or len(set(panel_picks)) < 2:
                continue
            final = choice(synth_cfg, tid)
            own = choice(judge_standalone_cfg, tid)
            if final is None or own is None:
                continue
            tot += 1
            hit = final == own
            hits += hit
            detail.append((tid, final, own, hit))
        return hits, tot, detail

    panel_sc = ["single_glm_high", "single_qwen_high", "single_deepseek_high"]
    on_hits, on_tot, _ = judge_pref("synth_judge_on", "single_glm_high", panel_sc)
    off_hits, off_tot, _ = judge_pref("synth_judge_off", "single_kimi_high", panel_sc)

    W("| arm | judge | judge on panel | final answer == judge's own standalone answer |")
    W("| --- | --- | --- | --- |")
    W(f"| synth_judge_on | glm-5.2 | yes | {pct(on_hits, on_tot)} |")
    W(f"| synth_judge_off | kimi-k2.6 | no | {pct(off_hits, off_tot)} |")
    W(f"\nChance baseline with a 3-model panel is roughly 33%. n = {on_tot} and {off_tot} tasks -- state it in the article.")
    if min(on_tot, off_tot) < 5:
        W("\n> **Not enough divergent tasks to say anything.** The judge panel")
        W("> (glm + qwen + deepseek) agreed with itself on almost everything, so there")
        W("> was nothing for the judge to decide. Swap the judge-arm panel to two models")
        W("> that actually disagree -- check the pairwise table in section 1 and pick the")
        W("> lowest-agreement pair -- then re-run only synth_judge_on / synth_judge_off.")

    # ---- answer differences between configs -----------------------------
    W("\n## 6. Does the answer actually change?\n")
    W("Each row: how often two configs picked a different option on the same task.\n")
    W("| comparison | differs | interpretation |")
    W("| --- | --- | --- |")
    PAIRS = [
        ("synth_heavy2", "single_glm_high",
         "published panel vs. one of its own members"),
        ("synth_heavy2", "single_frontier_high",
         "published panel vs. a frontier single model -- the claim being tested"),
        ("synth_open2_plus_frontier", "synth_heavy2",
         "adding a frontier model to the published open panel"),
        ("synth_frontier_judge", "synth_heavy2",
         "same panel, frontier judge -- does a stronger judge change the outcome"),
        ("synth_all4", "synth_heavy2",
         "adding the two light models"),
        ("synth_preset_balanced", "synth_heavy2",
         "preset vs. hand-configured panel"),
        ("synth_preset_quality", "synth_preset_balanced",
         "moving up the preset dial -- does the expensive tier answer differently"),
        ("synth_preset_balanced", "synth_preset_budget",
         "moving down the preset dial"),
        ("synth_preset_quality", "single_frontier_high",
         "top preset vs. a frontier single model"),
        ("synth_heavy2_search", "synth_heavy2",
         "web search on vs. off"),
        ("synth_all4_low", "synth_all4",
         "reasoning effort low vs. high"),
    ]
    for a, b, why in PAIRS:
        diff = same = 0
        for tid in CLOSED:
            x, y = choice(a, tid), choice(b, tid)
            if x is None or y is None:
                continue
            if x == y:
                same += 1
            else:
                diff += 1
        if diff + same == 0:
            W(f"| {a} vs {b} | _no data_ | {why} |")
        else:
            W(f"| {a} vs {b} | {pct(diff, diff + same)} | {why} |")
    W("\nA difference rate is not a quality claim -- it says the answer changed,")
    W("not that it improved. Say so explicitly in the article.")

    W("\n### The two comparisons that matter, split by difficulty\n")
    W("| comparison | difficulty | differs |")
    W("| --- | --- | --- |")
    for a, b in (("synth_heavy2", "single_glm_high"),
                 ("synth_heavy2", "single_frontier_high")):
        for tier in ("easy", "hard", "unlabeled"):
            d = s = 0
            for tid in CLOSED:
                if difficulty(tid) != tier:
                    continue
                x, y = choice(a, tid), choice(b, tid)
                if x is None or y is None:
                    continue
                if x == y:
                    s += 1
                else:
                    d += 1
            if d + s:
                W(f"| {a} vs {b} | {tier} | {pct(d, d + s)} |")
    W("\nIf the panel only changes answers on hard tasks, that is the decision rule:")
    W("spend on a panel when the evidence underdetermines the answer, not otherwise.")

    # ---- hygiene ---------------------------------------------------------
    W("\n## 7. Data hygiene\n")
    viol = defaultdict(lambda: [0, 0])
    for r in recs:
        k = r.get("config_id")
        viol[k][1] += 1
        viol[k][0] += bool(r.get("contract_violation"))
    W("| config | contract violations | partial failures | effort dropped |")
    W("| --- | --- | --- | --- |")
    for cfg in sorted(viol):
        pf = sum(1 for r in by_cfg[cfg] if r.get("partial_failure"))
        ed = sum(1 for r in by_cfg[cfg] if r.get("effort_dropped"))
        W(f"| {cfg} | {pct(viol[cfg][0], viol[cfg][1])} | {pf} | {ed} |")

    all_recs = load_jsonl(args.results)
    W(f"\n- Failed calls excluded: {len(all_recs) - len(recs)}")

    W("\n### How recommendations were resolved\n")
    mode_counts = Counter(MATCH_MODES.values())
    for mode in ("number", "exact", "substring", "overlap-review", "unmatched"):
        if mode_counts.get(mode):
            W(f"- {mode}: {mode_counts[mode]} distinct answers")
    review = [s for s, m in MATCH_MODES.items() if m == "overlap-review"]
    unmatched = [s for s, m in MATCH_MODES.items() if m == "unmatched"]
    if review:
        W("\n**Review these by hand — matched on word overlap, not on the option label:**")
        for s in review[:15]:
            W(f"- `{s[:110]}`")
    if unmatched:
        W("\n**Unmatched — these tasks drop out of every comparison:**")
        for s in unmatched[:15]:
            W(f"- `{s[:110]}`")
    if mode_counts.get("overlap-review", 0) + mode_counts.get("unmatched", 0) > \
            0.15 * max(1, sum(mode_counts.values())):
        W("\n> More than 15% of answers needed fallback matching. The output contract")
        W("> is not holding. Check whether the numbered format reached these arms.")

    text = "\n".join(L) + "\n"
    pathlib.Path(args.out).write_text(text)
    print(text)


if __name__ == "__main__":
    main()
