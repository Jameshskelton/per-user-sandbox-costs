# Model synthesis: measured results

Records analyzed: 58 successful calls across 25 tasks.
Price snapshot: 2026-07-28

## 0. Tool firing rate

A synthesis call only counts if the response contained a panel/judge usage block.

| config | calls | fired | firing rate |
| --- | --- | --- | --- |
| synth_all4 | 6 | 6 | 100% (6/6) |
| synth_all4_low | 2 | 2 | 100% (2/2) |
| synth_frontier_judge | 2 | 2 | 100% (2/2) |
| synth_heavy2 | 6 | 6 | 100% (6/6) |
| synth_judge_off | 2 | 2 | 100% (2/2) |
| synth_judge_on | 2 | 2 | 100% (2/2) |
| synth_light2 | 2 | 2 | 100% (2/2) |
| synth_open2_plus_frontier | 2 | 2 | 100% (2/2) |
| synth_preset_balanced | 6 | 6 | 100% (6/6) |
| synth_preset_budget | 2 | 2 | 100% (2/2) |
| synth_preset_quality | 2 | 2 | 100% (2/2) |
## 1. Disagreement across the four standalone models

- Tasks where the four models did not all agree: **0% (0/2)**
- Tasks excluded (missing or unparsed response): 23 ['arch-e3', 'arch-h1', 'arch-h2', 'arch-h3', 'arch-h4', 'arch-h5', 'policy-e1', 'policy-e2', 'policy-h1', 'policy-h2', 'policy-h3', 'inc-e1', 'inc-e2', 'inc-h1', 'inc-h2', 'inc-h3', 'inc-h4', 'research-01', 'research-02', 'research-03', 'research-04', 'research-05', 'research-06']

### Divergence by task difficulty

Tag tasks `E` when the evidence is dispositive and `H` when it genuinely
underdetermines the answer. This split is the spine of the argument:
a panel cannot add value where a single model already has enough to go on.

| difficulty | tasks | divergent |
| --- | --- | --- |
| easy | 2 | 0% (0/2) |

> **No tasks tagged `H`.** Every task carries a dispositive clue, so a
> near-zero divergence rate is expected and cannot support a general
> claim that ensembling does not help. Add a hard tier before publishing.

Pairwise agreement (frontier model included):

| pair | agree |
| --- | --- |
| single_glm_high vs single_kimi_high | 100% (2/2) |
| single_glm_high vs single_qwen_high | 100% (2/2) |
| single_glm_high vs single_deepseek_high | 100% (2/2) |
| single_glm_high vs single_frontier_high | 100% (2/2) |
| single_kimi_high vs single_qwen_high | 100% (2/2) |
| single_kimi_high vs single_deepseek_high | 100% (2/2) |
| single_kimi_high vs single_frontier_high | 100% (2/2) |
| single_qwen_high vs single_deepseek_high | 100% (2/2) |
| single_qwen_high vs single_frontier_high | 100% (2/2) |
| single_deepseek_high vs single_frontier_high | 100% (2/2) |

## 2. Self-disagreement floor (same model, 3 reps)

- single_glm_high disagreeing with itself: **0% (0/2)**
- Cross-model divergence minus sampling floor: **0 pp**
  (This is the headline. It is the disagreement attributable to model choice
   rather than to sampling variance.)

### Confidence when models disagree

- divergent tasks: {}
- convergent tasks: {'high': 8}

## 3. Cost and tokens per config

| config | calls | median total tokens | median cost | x baseline | cache read share |
| --- | --- | --- | --- | --- | --- |
| single_deepseek_high | 2 | 825 | $0.0002 | 0x | n/a |
| single_frontier_high | 6 | 368 | $0.0067 | 3x | n/a |
| single_glm_high | 6 | 646 | $0.0021 | 1x | 71% |
| single_glm_high_search | 2 | 1640 | $0.0055 | 3x | 50% |
| single_glm_low | 2 | 1136 | $0.0044 | 2x | n/a |
| single_kimi_high | 2 | 3370 | $0.0103 | 5x | 45% |
| single_kimi_low | 2 | 5460 | $0.0171 | 8x | n/a |
| single_qwen_high | 2 | 1401 | $0.0007 | 0x | n/a |
| synth_all4 | 6 | 122436 | $0.2226 | 104x | 38% |
| synth_all4_low | 2 | 237678 | $0.3796 | 178x | 40% |
| synth_frontier_judge | 2 | 76721 | $0.2658 | 125x | 19% |
| synth_heavy2 | 6 | 162016 | $0.2923 | 137x | 34% |
| synth_judge_off | 2 | 71976 | $0.1648 | 77x | 12% |
| synth_judge_on | 2 | 60711 | $0.1422 | 67x | 18% |
| synth_light2 | 2 | 45810 | $0.0986 | 46x | 26% |
| synth_open2_plus_frontier | 2 | 112423 | $0.2353 | 110x | 31% |
| synth_preset_balanced | 6 | 242506 | $0.4020 | 189x | 41% |
| synth_preset_budget | 2 | 67880 | no prices | 105x (tokens) | 30% |
| synth_preset_quality | 2 | 134969 | no prices | 209x (tokens) | 37% |

### Panel work imbalance (input tokens by role)

| config | role:model | median input tokens | median output tokens |
| --- | --- | --- | --- |
| synth_all4 | panel:glm-5.2 | 11972 | 2781 |
| synth_all4 | panel:kimi-k2.6 | 37664 | 6423 |
| synth_all4 | panel:alibaba-qwen3-32b | 923 | 1065 |
| synth_all4 | panel:deepseek-4-flash | 1033 | 488 |
| synth_all4 | judge:glm-5.2 | 43052 | 2810 |
| synth_all4_low | panel:glm-5.2 | 27316 | 3944 |
| synth_all4_low | panel:kimi-k2.6 | 10364 | 4594 |
| synth_all4_low | panel:alibaba-qwen3-32b | 923 | 1015 |
| synth_all4_low | panel:deepseek-4-flash | 42760 | 1089 |
| synth_all4_low | judge:glm-5.2 | 87629 | 4246 |
| synth_frontier_judge | panel:glm-5.2 | 30737 | 3514 |
| synth_frontier_judge | panel:kimi-k2.6 | 17616 | 3348 |
| synth_frontier_judge | judge:openai-gpt-5.6-sol | 16660 | 926 |
| synth_heavy2 | panel:glm-5.2 | 13275 | 3117 |
| synth_heavy2 | panel:kimi-k2.6 | 33215 | 5756 |
| synth_heavy2 | judge:glm-5.2 | 37796 | 2190 |
| synth_judge_off | panel:glm-5.2 | 12297 | 3051 |
| synth_judge_off | panel:alibaba-qwen3-32b | 4212 | 1703 |
| synth_judge_off | panel:deepseek-4-flash | 1032 | 451 |
| synth_judge_off | judge:kimi-k2.6 | 22175 | 4861 |
| synth_judge_on | panel:glm-5.2 | 14023 | 2821 |
| synth_judge_on | panel:alibaba-qwen3-32b | 923 | 1779 |
| synth_judge_on | panel:deepseek-4-flash | 1032 | 506 |
| synth_judge_on | judge:glm-5.2 | 19452 | 1455 |
| synth_light2 | panel:alibaba-qwen3-32b | 923 | 1489 |
| synth_light2 | panel:deepseek-4-flash | 1032 | 445 |
| synth_light2 | judge:glm-5.2 | 23400 | 1939 |
| synth_open2_plus_frontier | panel:glm-5.2 | 16271 | 3494 |
| synth_open2_plus_frontier | panel:kimi-k2.6 | 36438 | 5875 |
| synth_open2_plus_frontier | panel:openai-gpt-5.6-sol | 641 | 165 |
| synth_open2_plus_frontier | judge:glm-5.2 | 32431 | 2826 |
| synth_preset_balanced | panel:glm-5.2 | 24952 | 4142 |
| synth_preset_balanced | panel:kimi-k2.6 | 35353 | 3914 |
| synth_preset_balanced | judge:glm-5.2 | 100249 | 5126 |
| synth_preset_budget | panel:openai-gpt-5.6-luna | 641 | 337 |
| synth_preset_budget | panel:deepseek-4-flash | 1032 | 508 |
| synth_preset_budget | judge:glm-5.2 | 24316 | 2674 |
| synth_preset_quality | panel:openai-gpt-5.6-sol | 641 | 147 |
| synth_preset_quality | panel:anthropic-claude-fable-5 | 23496 | 2797 |
| synth_preset_quality | judge:glm-5.2 | 63348 | 4604 |

### What each preset actually contains

Composition is not documented -- this table is derived from role_usage.

| preset | panel models observed | judge observed |
| --- | --- | --- |
| balanced | glm-5.2, kimi-k2.6 | glm-5.2 |
| budget | deepseek-4-flash, openai-gpt-5.6-luna | glm-5.2 |
| quality | anthropic-claude-fable-5, openai-gpt-5.6-sol | glm-5.2 |

If a preset's panel varies across tasks, say so -- it means composition
is dynamic and cost is not predictable from the preset name alone.

## 4. Latency (phase B, sequential only)

_No phase B records. Run `run.py --phase b`._

## 5. Judge self-preference

Restricted to tasks where the standalone panel members disagreed.

| arm | judge | judge on panel | final answer == judge's own standalone answer |
| --- | --- | --- | --- |
| synth_judge_on | glm-5.2 | yes | n/a |
| synth_judge_off | kimi-k2.6 | no | n/a |

Chance baseline with a 3-model panel is roughly 33%. n = 0 and 0 tasks -- state it in the article.

> **Not enough divergent tasks to say anything.** The judge panel
> (glm + qwen + deepseek) agreed with itself on almost everything, so there
> was nothing for the judge to decide. Swap the judge-arm panel to two models
> that actually disagree -- check the pairwise table in section 1 and pick the
> lowest-agreement pair -- then re-run only synth_judge_on / synth_judge_off.

## 6. Does the answer actually change?

Each row: how often two configs picked a different option on the same task.

| comparison | differs | interpretation |
| --- | --- | --- |
| synth_heavy2 vs single_glm_high | 0% (0/2) | published panel vs. one of its own members |
| synth_heavy2 vs single_frontier_high | 0% (0/2) | published panel vs. a frontier single model -- the claim being tested |
| synth_open2_plus_frontier vs synth_heavy2 | 0% (0/2) | adding a frontier model to the published open panel |
| synth_frontier_judge vs synth_heavy2 | 0% (0/2) | same panel, frontier judge -- does a stronger judge change the outcome |
| synth_all4 vs synth_heavy2 | 0% (0/2) | adding the two light models |
| synth_preset_balanced vs synth_heavy2 | 0% (0/2) | preset vs. hand-configured panel |
| synth_preset_quality vs synth_preset_balanced | 0% (0/2) | moving up the preset dial -- does the expensive tier answer differently |
| synth_preset_balanced vs synth_preset_budget | 50% (1/2) | moving down the preset dial |
| synth_preset_quality vs single_frontier_high | 0% (0/2) | top preset vs. a frontier single model |
| synth_heavy2_search vs synth_heavy2 | _no data_ | web search on vs. off |
| synth_all4_low vs synth_all4 | 0% (0/2) | reasoning effort low vs. high |

A difference rate is not a quality claim -- it says the answer changed,
not that it improved. Say so explicitly in the article.

### The two comparisons that matter, split by difficulty

| comparison | difficulty | differs |
| --- | --- | --- |
| synth_heavy2 vs single_glm_high | easy | 0% (0/2) |
| synth_heavy2 vs single_frontier_high | easy | 0% (0/2) |

If the panel only changes answers on hard tasks, that is the decision rule:
spend on a panel when the evidence underdetermines the answer, not otherwise.

## 7. Data hygiene

| config | contract violations | partial failures | effort dropped |
| --- | --- | --- | --- |
| single_deepseek_high | 0% (0/2) | 0 | 0 |
| single_frontier_high | 0% (0/6) | 0 | 0 |
| single_glm_high | 0% (0/6) | 0 | 0 |
| single_glm_high_search | 0% (0/2) | 0 | 0 |
| single_glm_low | 0% (0/2) | 0 | 0 |
| single_kimi_high | 0% (0/2) | 0 | 0 |
| single_kimi_low | 0% (0/2) | 0 | 0 |
| single_qwen_high | 0% (0/2) | 0 | 0 |
| synth_all4 | 0% (0/6) | 0 | 0 |
| synth_all4_low | 0% (0/2) | 0 | 0 |
| synth_frontier_judge | 0% (0/2) | 0 | 0 |
| synth_heavy2 | 0% (0/6) | 0 | 0 |
| synth_judge_off | 0% (0/2) | 0 | 0 |
| synth_judge_on | 0% (0/2) | 0 | 0 |
| synth_light2 | 0% (0/2) | 0 | 0 |
| synth_open2_plus_frontier | 0% (0/2) | 0 | 0 |
| synth_preset_balanced | 0% (0/6) | 0 | 0 |
| synth_preset_budget | 0% (0/2) | 0 | 0 |
| synth_preset_quality | 0% (0/2) | 0 | 0 |

- Failed calls excluded: 2

### How recommendations were resolved

- number: 5 distinct answers
- substring: 1 distinct answers
