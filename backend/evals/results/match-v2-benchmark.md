## Frozen match-v2 benchmark

Evaluation configuration:

- Model: gpt-5.6-luna
- Prompt version: match-v2
- Evaluation dataset: frozen 17-case policy-corrected benchmark
- Runs per case: 3
- Total runs: 51

Results:

- Coverage pass@1: 51/51 (100.0%)
- Coverage pass@3: 51/51 (100.0%)
- Repair recovery: 0/0 (N/A)
- Retry exhaustion: 0/51 (0.0%)
- Status accuracy: 48/51 (94.1%)
- Evidence-source accuracy: 43/51 (84.3%)
- Strict semantic accuracy: 42/51 (82.3%)

### Comparison with frozen match-v1 baseline

| Metric | match-v1 | match-v2 |
| --- | ---: | ---: |
| Status accuracy | 43/51 (84.3%) | 48/51 (94.1%) |
| Evidence-source accuracy | 40/51 (78.4%) | 43/51 (84.3%) |
| Strict semantic accuracy | 38/51 (74.5%) | 42/51 (82.3%) |

The model and frozen 17-case dataset were unchanged between these benchmark
runs. Scoring, deterministic validation and retry behavior, and LangGraph
behavior were also unchanged. The improvement came from the versioned matching
evidence-policy prompt introduced in match-v2.

### Remaining failure patterns

- React/Redux to JavaScript strong contextual evidence remains somewhat
  unstable.
- Some evidence-source failures occur when the model returns a sufficient
  source such as `EXPERIENCE` while omitting a redundant expected `SKILLS`
  source.
- These source-attribution differences should not be treated as status
  failures.
