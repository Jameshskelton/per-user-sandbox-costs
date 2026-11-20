# Model synthesis: measured results

Records analyzed: 746 successful calls across 25 tasks.
Price snapshot: 2026-07-28

## 0. Tool firing rate

A synthesis call only counts if the response contained a panel/judge usage block.

| config | calls | fired | firing rate |
| --- | --- | --- | --- |
| synth_all4 | 75 | 75 | 100% (75/75) |
| synth_all4_low | 23 | 23 | 100% (23/23) |
| synth_frontier_judge | 25 | 25 | 100% (25/25) |
| synth_heavy2 | 90 | 90 | 100% (90/90) |
| synth_judge_off | 25 | 25 | 100% (25/25) |
| synth_judge_on | 25 | 25 | 100% (25/25) |
| synth_light2 | 25 | 25 | 100% (25/25) |
| synth_open2_plus_frontier | 25 | 25 | 100% (25/25) |
| synth_preset_balanced | 69 | 69 | 100% (69/69) |
| synth_preset_budget | 24 | 24 | 100% (24/24) |
| synth_preset_quality | 25 | 25 | 100% (25/25) |
## 1. Disagreement across the four standalone models

- Closed-choice tasks compared: 19 of 25 (6 open-ended tasks excluded from all agreement metrics — free-text answers cannot be matched across runs)
- Tasks where the four models did not all agree: **39% (7/18)**
- Tasks excluded (missing or unparsed response): 1 ['arch-h2']

### Divergence by task difficulty

Tag tasks `E` when the evidence is dispositive and `H` when it genuinely
underdetermines the answer. This split is the spine of the argument:
a panel cannot add value where a single model already has enough to go on.

| difficulty | tasks | divergent |
| --- | --- | --- |
| easy | 7 | 0% (0/7) |
| hard | 11 | 64% (7/11) |

Pairwise agreement (frontier model included):

| pair | agree |
| --- | --- |
| single_glm_high vs single_kimi_high | 83% (15/18) |
| single_glm_high vs single_qwen_high | 79% (15/19) |
| single_glm_high vs single_deepseek_high | 72% (13/18) |
| single_glm_high vs single_frontier_high | 95% (18/19) |
| single_kimi_high vs single_qwen_high | 89% (16/18) |
| single_kimi_high vs single_deepseek_high | 72% (13/18) |
| single_kimi_high vs single_frontier_high | 83% (15/18) |
| single_qwen_high vs single_deepseek_high | 67% (12/18) |
| single_qwen_high vs single_frontier_high | 79% (15/19) |
| single_deepseek_high vs single_frontier_high | 78% (14/18) |

## 2. Self-disagreement floor (same model, 3 reps)

- single_glm_high disagreeing with itself: **16% (3/19)**
- Cross-model divergence minus sampling floor: **23 pp**
  (This is the headline. It is the disagreement attributable to model choice
   rather than to sampling variance.)

### Confidence when models disagree

- divergent tasks: {'high': 20, 'medium': 8}
- convergent tasks: {'high': 41, 'medium': 3}

## 2b. Run-to-run stability

Same config, same task, repeated runs. Asks a different question from
section 6: not *does synthesis change the answer* but *does synthesis give
the same answer twice*. Stability is a real thing to buy even when the
answer itself doesn't change.

| config | tasks | all reps identical | pairwise agreement | mean distinct answers |
| --- | --- | --- | --- | --- |
| single_frontier_high | 19 | 95% (18/19) | 96% (55/57) | 1.05 |
| single_glm_high | 19 | 84% (16/19) | 89% (51/57) | 1.16 |
| synth_all4 | 19 | 89% (17/19) | 93% (53/57) | 1.11 |
| synth_heavy2 | 19 | 74% (14/19) | 82% (47/57) | 1.26 |
| synth_preset_balanced | 18 | 94% (17/18) | 96% (44/46) | 1.06 |

**synth_heavy2 is 7 pp LESS stable than single_glm_high** (82% vs 89% pairwise agreement).

No meaningful stability gain. Synthesis costs a large multiple, answers
no more consistently, and differs from a single model no more often than
that model differs from itself. On this task class the case does not close
in the tool's favour.

### Stability by difficulty

| config | difficulty | pairwise agreement |
| --- | --- | --- |
| synth_heavy2 | easy | 100% (21/21) |
| synth_heavy2 | hard | 72% (26/36) |
| single_glm_high | easy | 100% (21/21) |
| single_glm_high | hard | 83% (30/36) |
| synth_preset_balanced | easy | 100% (21/21) |
| synth_preset_balanced | hard | 92% (23/25) |

## 3. Cost and tokens per config

| config | calls | median total tokens | median cost | x baseline | cache read share |
| --- | --- | --- | --- | --- | --- |
| single_deepseek_high | 24 | 1226 | $0.0002 | 0x | n/a |
| single_frontier_high | 75 | 439 | $0.0075 | 1x | n/a |
| single_glm_high | 95 | 1492 | $0.0055 | 1x | 77% |
| single_glm_high_search | 25 | 1972 | $0.0067 | 1x | 49% |
| single_glm_low | 23 | 3068 | $0.0124 | 2x | n/a |
| single_kimi_high | 24 | 5209 | $0.0162 | 3x | n/a |
| single_kimi_low | 24 | 5927 | $0.0185 | 3x | n/a |
| single_qwen_high | 25 | 1254 | $0.0006 | 0x | n/a |
| synth_all4 | 75 | 110453 | $0.2233 | 41x | 33% |
| synth_all4_low | 23 | 154332 | $0.2829 | 52x | 31% |
| synth_frontier_judge | 25 | 74518 | $0.2124 | 39x | 34% |
| synth_heavy2 | 90 | 95395 | $0.1928 | 35x | 36% |
| synth_judge_off | 25 | 81456 | $0.1571 | 29x | 27% |
| synth_judge_on | 25 | 29536 | $0.1179 | 21x | 25% |
| synth_light2 | 25 | 30491 | $0.0737 | 13x | 22% |
| synth_open2_plus_frontier | 25 | 96876 | $0.2007 | 37x | 36% |
| synth_preset_balanced | 69 | 150730 | $0.3190 | 58x | 32% |
| synth_preset_budget | 24 | 63016 | $0.1415 | 26x | 25% |
| synth_preset_quality | 25 | 92533 | $0.5117 | 93x | 25% |

### Panel work imbalance (input tokens by role)

| config | role:model | median input tokens | median output tokens |
| --- | --- | --- | --- |
| synth_all4 | panel:glm-5.2 | 11054 | 2380 |
| synth_all4 | panel:kimi-k2.6 | 32350 | 4149 |
| synth_all4 | panel:alibaba-qwen3-32b | 994 | 1460 |
| synth_all4 | panel:deepseek-4-flash | 1097 | 453 |
| synth_all4 | judge:glm-5.2 | 17241 | 1905 |
| synth_all4_low | panel:glm-5.2 | 30718 | 2852 |
| synth_all4_low | panel:kimi-k2.6 | 18247 | 3456 |
| synth_all4_low | panel:alibaba-qwen3-32b | 988 | 1302 |
| synth_all4_low | panel:deepseek-4-flash | 1074 | 504 |
| synth_all4_low | judge:glm-5.2 | 35252 | 3365 |
| synth_frontier_judge | panel:glm-5.2 | 10478 | 2603 |
| synth_frontier_judge | panel:kimi-k2.6 | 16776 | 4182 |
| synth_frontier_judge | judge:openai-gpt-5.6-sol | 2156 | 645 |
| synth_heavy2 | panel:glm-5.2 | 11453 | 2825 |
| synth_heavy2 | panel:kimi-k2.6 | 27954 | 4082 |
| synth_heavy2 | judge:glm-5.2 | 16181 | 1743 |
| synth_judge_off | panel:glm-5.2 | 11443 | 3343 |
| synth_judge_off | panel:alibaba-qwen3-32b | 1002 | 1558 |
| synth_judge_off | panel:deepseek-4-flash | 1089 | 425 |
| synth_judge_off | judge:kimi-k2.6 | 23271 | 4139 |
| synth_judge_on | panel:glm-5.2 | 964 | 2018 |
| synth_judge_on | panel:alibaba-qwen3-32b | 988 | 1566 |
| synth_judge_on | panel:deepseek-4-flash | 1097 | 419 |
| synth_judge_on | judge:glm-5.2 | 2894 | 1124 |
| synth_light2 | panel:alibaba-qwen3-32b | 988 | 1116 |
| synth_light2 | panel:deepseek-4-flash | 1097 | 453 |
| synth_light2 | judge:glm-5.2 | 13236 | 1737 |
| synth_open2_plus_frontier | panel:glm-5.2 | 965 | 2201 |
| synth_open2_plus_frontier | panel:kimi-k2.6 | 37558 | 5301 |
| synth_open2_plus_frontier | panel:openai-gpt-5.6-sol | 709 | 156 |
| synth_open2_plus_frontier | judge:glm-5.2 | 15613 | 2093 |
| synth_preset_balanced | panel:glm-5.2 | 12703 | 2364 |
| synth_preset_balanced | panel:kimi-k2.6 | 19964 | 4588 |
| synth_preset_balanced | judge:glm-5.2 | 37449 | 3157 |
| synth_preset_budget | panel:openai-gpt-5.6-luna | 709 | 272 |
| synth_preset_budget | panel:deepseek-4-flash | 1091 | 460 |
| synth_preset_budget | judge:glm-5.2 | 13614 | 2894 |
| synth_preset_quality | panel:openai-gpt-5.6-sol | 709 | 161 |
| synth_preset_quality | panel:anthropic-claude-fable-5 | 17429 | 2333 |
| synth_preset_quality | judge:glm-5.2 | 28446 | 3205 |

### What each preset actually contains

Composition is not documented -- this table is derived from role_usage.

| preset | panel models observed | judge observed |
| --- | --- | --- |
| balanced | glm-5.2, kimi-k2.6 | glm-5.2 |
| budget | deepseek-4-flash, openai-gpt-5.6-luna | glm-5.2 |
| quality | anthropic-claude-fable-5, openai-gpt-5.6-sol | glm-5.2 |

If a preset's panel varies across tasks, say so -- it means composition
is dynamic and cost is not predictable from the preset name alone.

## 4. Latency

### Phase B — sequential, clean

| config | n | median ms | max ms | median x baseline | p95 |
| --- | --- | --- | --- | --- | --- |
| single_glm_high | 16 | 28500 | 501043 | 1.0x | n too small |
| synth_heavy2 | 13 | 216364 | 526005 | 7.6x | n too small |

_With n < 20 the nearest-rank p95 is just the maximum, so it is suppressed._
_Use median for the headline and quote max separately as the worst case._

### Phase A — measured under concurrency, USE WITH CARE

These calls ran in parallel, so absolute values are inflated by queuing
and contention against your own other requests. **Do not quote these as
percentiles or as precise multiples.** They are usable for one thing: the
order-of-magnitude gap between single-model and synthesis calls, which is
far larger than any contention effect.

| config | n | median ms | max ms | median x baseline | p95 |
| --- | --- | --- | --- | --- | --- |
| single_deepseek_high | 19 | 69985 | 579922 | 1.5x | n too small |
| single_frontier_high | 75 | 5585 | 321937 | 0.1x | 297098 |
| single_glm_high | 71 | 46824 | 573220 | 1.0x | 383205 |
| single_glm_high_search | 25 | 53592 | 436737 | 1.1x | 329369 |
| single_glm_low | 21 | 147270 | 578491 | 3.1x | 563562 |
| single_kimi_high | 21 | 88148 | 279322 | 1.9x | 272285 |
| single_kimi_low | 23 | 139743 | 321631 | 3.0x | 233917 |
| single_qwen_high | 24 | 37061 | 150009 | 0.8x | 137596 |
| synth_all4 | 61 | 309712 | 779532 | 6.6x | 681697 |
| synth_all4_low | 17 | 427492 | 1049618 | 9.1x | n too small |
| synth_frontier_judge | 24 | 214618 | 570288 | 4.6x | 485056 |
| synth_heavy2 | 68 | 301496 | 567333 | 6.4x | 490576 |
| synth_judge_off | 21 | 306270 | 519766 | 6.5x | 488010 |
| synth_judge_on | 20 | 166550 | 591456 | 3.6x | 397682 |
| synth_light2 | 22 | 330604 | 599033 | 7.1x | 570182 |
| synth_open2_plus_frontier | 23 | 273604 | 543366 | 5.8x | 503588 |
| synth_preset_balanced | 55 | 322180 | 1152633 | 6.9x | 585458 |
| synth_preset_budget | 19 | 270259 | 643732 | 5.8x | n too small |
| synth_preset_quality | 20 | 254155 | 439993 | 5.4x | 402178 |

**The structural argument needs no timing data at all:** a synthesis call
cannot return until the slowest panel model finishes, then the judge reads
every panel output, then the synthesizer writes the answer. Three serial
stages, the first of which is a max() across the panel. That is why the gap
is large and why it widens with panel size regardless of what you measure.

## 5. Judge self-preference

Restricted to tasks where the standalone panel members disagreed.

| arm | judge | judge on panel | final answer == judge's own standalone answer |
| --- | --- | --- | --- |
| synth_judge_on | glm-5.2 | yes | 86% (6/7) |
| synth_judge_off | kimi-k2.6 | no | 57% (4/7) |

Chance baseline with a 3-model panel is roughly 33%. n = 7 and 7 tasks -- state it in the article.

## 6. Does the answer actually change?

Each row: how often two configs picked a different option on the same task.

| comparison | differs | interpretation |
| --- | --- | --- |
| synth_heavy2 vs single_glm_high | 5% (1/19) | published panel vs. one of its own members |
| synth_heavy2 vs single_frontier_high | 11% (2/19) | published panel vs. a frontier single model -- the claim being tested |
| synth_open2_plus_frontier vs synth_heavy2 | 11% (2/19) | adding a frontier model to the published open panel |
| synth_frontier_judge vs synth_heavy2 | 16% (3/19) | same panel, frontier judge -- does a stronger judge change the outcome |
| synth_all4 vs synth_heavy2 | 16% (3/19) | adding the two light models |
| synth_preset_balanced vs synth_heavy2 | 7% (1/15) | preset vs. hand-configured panel |
| synth_preset_quality vs synth_preset_balanced | 13% (2/15) | moving up the preset dial -- does the expensive tier answer differently |
| synth_preset_balanced vs synth_preset_budget | 36% (5/14) | moving down the preset dial |
| synth_preset_quality vs single_frontier_high | 16% (3/19) | top preset vs. a frontier single model |
| synth_heavy2_search vs synth_heavy2 | _no data_ | web search on vs. off |
| synth_all4_low vs synth_all4 | 12% (2/17) | reasoning effort low vs. high |

A difference rate is not a quality claim -- it says the answer changed,
not that it improved. Say so explicitly in the article.

### The two comparisons that matter, split by difficulty

| comparison | difficulty | differs |
| --- | --- | --- |
| synth_heavy2 vs single_glm_high | easy | 0% (0/7) |
| synth_heavy2 vs single_glm_high | hard | 8% (1/12) |
| synth_heavy2 vs single_frontier_high | easy | 0% (0/7) |
| synth_heavy2 vs single_frontier_high | hard | 17% (2/12) |

If the panel only changes answers on hard tasks, that is the decision rule:
spend on a panel when the evidence underdetermines the answer, not otherwise.

## 7. Data hygiene

| config | contract violations | partial failures | effort dropped |
| --- | --- | --- | --- |
| single_deepseek_high | 0% (0/24) | 0 | 0 |
| single_frontier_high | 0% (0/75) | 0 | 0 |
| single_glm_high | 0% (0/95) | 0 | 0 |
| single_glm_high_search | 16% (4/25) | 0 | 0 |
| single_glm_low | 0% (0/23) | 0 | 0 |
| single_kimi_high | 0% (0/24) | 0 | 0 |
| single_kimi_low | 0% (0/24) | 0 | 0 |
| single_qwen_high | 0% (0/25) | 0 | 0 |
| synth_all4 | 7% (5/75) | 17 | 0 |
| synth_all4_low | 9% (2/23) | 6 | 0 |
| synth_frontier_judge | 0% (0/25) | 2 | 0 |
| synth_heavy2 | 3% (3/90) | 8 | 0 |
| synth_judge_off | 0% (0/25) | 4 | 0 |
| synth_judge_on | 0% (0/25) | 7 | 0 |
| synth_light2 | 0% (0/25) | 5 | 0 |
| synth_open2_plus_frontier | 0% (0/25) | 3 | 0 |
| synth_preset_balanced | 13% (9/69) | 9 | 0 |
| synth_preset_budget | 8% (2/24) | 5 | 0 |
| synth_preset_quality | 4% (1/25) | 8 | 0 |

- Failed calls excluded: 128

### How recommendations were resolved

- number: 56 distinct answers
- substring: 2 distinct answers
