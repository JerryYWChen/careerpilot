## Policy-corrected baseline

After reviewing the evaluation policy and correcting four ground-truth
expectations, the frozen match-v1 benchmark produced:

- Coverage pass@1: 51/51 (100.0%)
- Coverage pass@3: 51/51 (100.0%)
- Retry exhaustion: 0/51 (0.0%)
- Status accuracy: 43/51 (84.3%)
- Evidence-source accuracy: 40/51 (78.4%)
- Strict semantic accuracy: 38/51 (74.5%)

The production matching prompt was unchanged.

The earlier pre-policy-review run produced 70.6% status accuracy,
64.7% evidence-source accuracy, and 58.8% strict semantic accuracy.
The difference reflects corrected evaluation ground truth rather than
an improvement to the model or prompt.