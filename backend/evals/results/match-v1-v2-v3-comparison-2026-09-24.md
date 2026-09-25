# Match v1/v2/v3 three-version comparison

## Protocol

- Date: 2026-09-24
- Model: `gpt-5.6-luna`
- Prompt versions: `match-v1`, `match-v2`, `match-v3`
- Dataset: the same unchanged current `MATCHING_EVAL_CASES` for every version
- Cases: 33
- Runs per case: 3
- Total runs per prompt: 99
- Workflow: the same matching LangGraph for every version
- Structural validation and retry limit: unchanged, maximum 3 attempts
- Semantic labels and metrics: unchanged
- Production prompt selection after the benchmark: `match-v3`

The current dataset has 33 cases. The older frozen match-v1 and match-v2
artifacts used the earlier 17-case dataset, so their numbers are not directly
comparable with this run.

No prompts or expected labels were changed during this benchmark. No retries
were added outside the existing LangGraph workflow.

## Aggregate results

| Metric | match-v1 | match-v2 | match-v3 |
| --- | ---: | ---: | ---: |
| Total runs | 99 | 99 | 99 |
| Coverage pass@1 | 94/99 (95.0%) | 94/99 (95.0%) | 91/99 (91.9%) |
| Coverage pass@3 | 97/99 (98.0%) | 96/99 (97.0%) | 97/99 (98.0%) |
| Repair opportunities | 5 | 5 | 8 |
| Repair recoveries | 3/5 (60.0%) | 2/5 (40.0%) | 6/8 (75.0%) |
| Retry exhaustion | 2/99 (2.0%) | 3/99 (3.0%) | 2/99 (2.0%) |
| Status accuracy | 67/99 (67.7%) | 77/99 (77.8%) | 96/99 (97.0%) |
| Evidence-source accuracy | 76/99 (76.8%) | 80/99 (80.8%) | 95/99 (96.0%) |
| Strict semantic accuracy | 65/99 (65.7%) | 71/99 (71.7%) | 94/99 (95.0%) |

Structural reliability and semantic correctness are different measurements.
`match-v3` had three fewer first-attempt structural passes than v2, but recovered
six of eight repair opportunities, matched v1's 98.0% pass@3 result, and had two
retry exhaustions. Its semantic scores were substantially higher.

Compared with match-v2, match-v3 improved strict semantic accuracy by 23 passing
runs and 23.3 percentage points (71/99 to 94/99). Status accuracy improved by
19 passing runs, and evidence-source accuracy improved by 15 passing runs.

## Per-case strict semantic consistency

| Case | match-v1 | match-v2 | match-v3 | v2 to v3 |
| --- | ---: | ---: | ---: | --- |
| Mixed Evidence | 3/3 | 3/3 | 3/3 | Unchanged |
| Insufficient Years | 3/3 | 3/3 | 3/3 | Unchanged |
| Strong Direct Evidence | 3/3 | 3/3 | 3/3 | Unchanged |
| No Evidence | 3/3 | 3/3 | 3/3 | Unchanged |
| Insufficient Context Without Exact Keyword | 2/3 | 3/3 | 3/3 | Unchanged |
| Framework Context Supports Language | 0/3 | 1/3 | 3/3 | Improved |
| Backend Framework Context Supports Language | 0/3 | 2/3 | 2/3 | Unchanged |
| Concrete Tool Evidence Supports Broader Concept | 3/3 | 3/3 | 3/3 | Unchanged |
| Skills Plus Strong Context | 3/3 | 3/3 | 3/3 | Unchanged |
| Next.js Does Not Reliably Establish TypeScript | 3/3 | 3/3 | 3/3 | Unchanged |
| Container Experience Without Orchestration | 3/3 | 3/3 | 3/3 | Unchanged |
| Compound AND Requirement Partially Satisfied | 3/3 | 3/3 | 3/3 | Unchanged |
| Compound OR Requirement Satisfied | 3/3 | 3/3 | 3/3 | Unchanged |
| AWS Platform and Lambda Are Separate Requirements | 3/3 | 0/3 | 2/3 | Improved |
| Experience Exactly Meets Minimum | 1/3 | 2/3 | 2/3 | Unchanged |
| Overlapping Experience Does Not Add Linearly | 3/3 | 2/3 | 3/3 | Improved |
| Leadership Signals Without People Management | 0/3 | 3/3 | 3/3 | Unchanged |
| Effective Verbal and Written Communication Is Not Assessable | 1/3 | 1/3 | 3/3 | Improved |
| Generic Cross-Functional Collaboration Is Not Assessable | 1/3 | 0/3 | 3/3 | Improved |
| Concrete Product and Design Collaboration Is Missing | 3/3 | 3/3 | 3/3 | Unchanged |
| Validation and Debugging Do Not Establish High Attention to Detail | 0/3 | 0/3 | 3/3 | Improved |
| Broad Software Work Does Not Establish Attention to Detail | 0/3 | 2/3 | 3/3 | Improved |
| Documentation Does Not Establish Excellent Communication Quality | 0/3 | 0/3 | 3/3 | Improved |
| Executive Presentation Is Directly Demonstrated | 3/3 | 3/3 | 3/3 | Unchanged |
| Leadership Scope Is Directly Demonstrated | 3/3 | 3/3 | 3/3 | Unchanged |
| Azure and Python Do Not Establish AWS | 3/3 | 3/3 | 3/3 | Unchanged |
| Multitasking Effectiveness Is Not Assessable | 0/3 | 1/3 | 3/3 | Improved |
| Cross-Functional Activity Does Not Establish Strong Collaboration | 0/3 | 0/3 | 3/3 | Improved |
| Product and Design Collaboration Experience Is Demonstrated | 3/3 | 3/3 | 3/3 | Unchanged |
| Technical Documentation Experience Is Demonstrated | 3/3 | 3/3 | 3/3 | Unchanged |
| Developer Tooling Capability Remains Resume Assessable | 3/3 | 3/3 | 3/3 | Unchanged |
| Hardware and Switch Experience Remains Resume Assessable | 3/3 | 3/3 | 3/3 | Unchanged |
| Onsite Internship Availability Remains Not Assessable | 0/3 | 0/3 | 1/3 | Improved |

From v2 to v3, 11 cases improved, 22 were unchanged, and none regressed in
strict semantic consistency. From v1 to v2, seven cases improved, three
regressed, and 23 were unchanged.

## Recurring failure modes

- Exact evidence-source attribution remains stricter and less stable than status
  classification. Correct status decisions sometimes omit an expected redundant
  `SKILLS` source, especially for AWS and duration-based Python cases.
- Framework-to-language inference remains somewhat unstable. FastAPI/SQLAlchemy
  context occasionally produces `matched` where the expected result is
  `partial`.
- Availability/location requirements remain difficult structurally. The onsite
  internship case caused retry exhaustion for all versions and remained only
  1/3 semantically consistent for v3.
- Match-v1 and match-v2 frequently treated evidence of an activity as proof of a
  subjective quality, or returned `missing` instead of `not_assessable`.
  Match-v3 corrected these distinctions consistently for communication quality,
  attention to detail, multitasking effectiveness, and collaboration strength.
- Three runs per case expose output variability, but this benchmark is too small
  to support claims of statistical significance.

## Conclusion

On this unchanged 33-case benchmark, match-v3 improves strict semantic accuracy
over match-v2 from 71.7% to 95.0%. It also improves status and evidence-source
accuracy while preserving comparable pass@3 structural reliability. This result
does not by itself justify a production change; the production selection was
already match-v3 and was intentionally left unchanged.

## Raw outputs

- [match-v1 raw output](match-v1-three-version-comparison-raw.txt)
- [match-v2 raw output](match-v2-three-version-comparison-raw.txt)
- [match-v3 raw output](match-v3-three-version-comparison-raw.txt)
