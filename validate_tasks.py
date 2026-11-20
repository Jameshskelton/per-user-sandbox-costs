#!/usr/bin/env python3
"""
validate_tasks.py -- check tasks.jsonl before spending money on runs.

  python3 validate_tasks.py tasks.jsonl

Checks structure, then the things that silently break the analysis:
options that don't appear verbatim in the prompt, duplicate ids,
leftover placeholders, and the closed/open balance.
"""

import json
import re
import sys
from collections import Counter, defaultdict

PLACEHOLDER = re.compile(r"\[[A-Z][A-Z _/-]{3,}\]")
REQUIRED = ("task_id", "use_case", "prompt")


def main(path):
    errors, warns, notes = [], [], []
    tasks = []

    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                tasks.append((n, json.loads(line)))
            except json.JSONDecodeError as e:
                errors.append(f"line {n}: invalid JSON -- {e}")

    if not tasks:
        print("no parseable tasks")
        return 1

    ids = Counter(t.get("task_id") for _, t in tasks)
    for tid, cnt in ids.items():
        if cnt > 1:
            errors.append(f"duplicate task_id '{tid}' appears {cnt} times")

    by_use = defaultdict(int)
    closed = open_ended = 0
    opt_counts = Counter()

    for n, t in tasks:
        tid = t.get("task_id", f"line{n}")
        for k in REQUIRED:
            if not t.get(k):
                errors.append(f"{tid}: missing or empty '{k}'")

        prompt = t.get("prompt") or ""
        opts = t.get("options") or []
        tags = t.get("tags") or []
        by_use[t.get("use_case", "?")] += 1

        m = PLACEHOLDER.search(prompt)
        if m:
            errors.append(f"{tid}: unfilled placeholder {m.group(0)} still in prompt")

        if opts:
            closed += 1
            opt_counts[len(opts)] += 1
            if len(opts) < 2:
                errors.append(f"{tid}: only {len(opts)} option")
            if len(opts) == 3:
                warns.append(f"{tid}: only 3 options -- coincidental agreement inflates")
            if len(set(o.lower().strip() for o in opts)) != len(opts):
                errors.append(f"{tid}: duplicate options")
            # run.py renders the option list into the prompt, so options do not
            # need to appear in the prompt text itself. Only flag a mismatch that
            # suggests the prompt contradicts the options array.
            low = prompt.lower()
            if any(o.lower().strip() in low for o in opts) and \
               not all(o.lower().strip() in low for o in opts):
                notes.append(
                    f"{tid}: prompt mentions some option names in prose -- fine for "
                    "evidence-bearing prompts, just check for wording drift"
                )
            generic = sum(1 for o in opts if len(o.split("-")) > 6)
            if generic:
                notes.append(f"{tid}: {generic} very long option label(s); "
                             "shorter labels are easier for models to return exactly")
        else:
            open_ended += 1
            if "C" in tags:
                warns.append(f"{tid}: tagged [C] but has no options array")

        if "RECOMMENDATION:" in prompt:
            errors.append(f"{tid}: prompt already contains the output contract "
                          "-- run.py appends it, so it would appear twice")

        if len(prompt) < 120:
            warns.append(f"{tid}: prompt is only {len(prompt)} chars -- thin tasks "
                         "may not trigger substantive panel work")

        for tag in tags:
            if tag not in ("C", "O", "E", "H", "M", "R", "S", "W", "D"):
                notes.append(f"{tid}: unrecognized tag '{tag}'")

    print(f"parsed {len(tasks)} tasks\n")
    print("by use_case:", dict(by_use))
    print(f"closed-choice: {closed}   open-ended: {open_ended}")
    tiers = Counter("easy" if "E" in (t.get("tags") or []) else
                    "hard" if "H" in (t.get("tags") or []) else "untiered"
                    for _, t in tasks)
    print("difficulty tiers:", dict(tiers))
    if tiers["hard"] == 0:
        warns.append("no tasks tagged H -- divergence cannot be interpreted; "
                     "add a hard tier before publishing")
    if tiers["untiered"] > 3:
        warns.append(f"{tiers['untiered']} tasks carry neither E nor H -- they will "
                     "land in the 'unlabeled' row and weaken the split")
    print("options per closed task:", dict(sorted(opt_counts.items())))
    lens = sorted(len(t.get("prompt") or "") for _, t in tasks)
    print(f"prompt length: min {lens[0]}, median {lens[len(lens)//2]}, max {lens[-1]}\n")

    for label, items in (("ERROR", errors), ("WARN", warns), ("NOTE", notes)):
        for i in items:
            print(f"[{label}] {i}")

    if not errors:
        print("\nno blocking errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "tasks.jsonl"))
