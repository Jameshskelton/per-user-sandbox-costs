#!/usr/bin/env python3
"""
inspect_raw.py -- what actually happened inside one call.

  python3 inspect_raw.py raw/phase_a/arch-e1__synth_preset_quality__1.json

Reuses run.py's parsers, so what you see here is exactly what the harness
recorded. Pass several files to compare panels side by side:

  python3 inspect_raw.py raw/phase_a/arch-e1__synth_preset_*.json
"""

import json
import sys

from run import (
    count_search_calls,
    extract_text,
    find_outer_usage,
    find_role_usage,
    parse_contract,
)


def one(path):
    with open(path) as f:
        raw = json.load(f)

    print("=" * 74)
    print(path.split("/")[-1])
    print("=" * 74)

    roles = find_role_usage(raw)
    if not roles:
        print("PANEL: none found -- the synthesis tool did not run for this call.")
    else:
        print(f"PANEL: {len(roles)} roles")
        print(f"  {'role':8} {'model':26} {'in':>9} {'out':>7} {'cache':>9} status")
        for m in roles:
            print(f"  {str(m.get('role')):8} {str(m.get('model')):26} "
                  f"{m.get('input_tokens') or 0:>9} {m.get('output_tokens') or 0:>7} "
                  f"{m.get('cache_read_input_tokens') or 0:>9} {m.get('status')}")
        panel = [m.get("model") for m in roles if m.get("role") == "panel"]
        judge = [m.get("model") for m in roles if m.get("role") == "judge"]
        print(f"  -> panel: {panel}")
        print(f"  -> judge: {judge}")

    outer = find_outer_usage(raw)
    print(f"\nBILLED USAGE: prompt={outer.get('prompt_tokens')} "
          f"completion={outer.get('completion_tokens')} "
          f"total={outer.get('total_tokens')} "
          f"cache_read={outer.get('cache_read_input_tokens')}")

    if roles:
        r_in = sum(m.get("input_tokens") or 0 for m in roles)
        r_out = sum(m.get("output_tokens") or 0 for m in roles)
        print(f"SYNTHESIS STEP (outer minus roles): "
              f"input={(outer.get('prompt_tokens') or 0) - r_in} "
              f"output={(outer.get('completion_tokens') or 0) - r_out}")

    n = count_search_calls(raw)
    print(f"\nWEB SEARCH CALLS: {n}", end="")
    if n:
        print(f"   -> ${n * 10 / 1000:.3f} in search fees at $10/1000 requests")
        for node in json.dumps(raw, indent=0).splitlines():
            if '"query"' in node:
                print("   query:", node.strip()[:140])
    else:
        print()

    parsed = parse_contract(extract_text(raw))
    print(f"\nCONTRACT: {parsed if parsed else 'VIOLATION -- no parseable trailer'}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        one(p)
