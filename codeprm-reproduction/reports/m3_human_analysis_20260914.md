# M3 human decomposition analysis

M3 uses the 10 development problems sampled before execution results were unblinded. Human scores were recorded on blind labels A/B, then mapped back to JSON or skeleton only after the CSV was complete.

## Blind quality scores

Scores sum five criteria, each 0--2, so the maximum is 10.

| Protocol | Candidate count | Mean score / 10 | Median score / 10 |
| --- | ---: | ---: | ---: |
| json | 10 | 6.50 | 7.5 |
| skeleton | 10 | 7.00 | 6.5 |

Per-problem blind score pairs:

| Problem | JSON score | Skeleton score | Higher-scoring protocol |
| --- | ---: | ---: | --- |
| apps-train-2652 | 8 | 7 | JSON |
| apps-train-2653 | 8 | 6 | JSON |
| apps-train-2654 | 7 | 10 | skeleton |
| apps-train-2656 | 8 | 7 | JSON |
| apps-train-2657 | 6 | 6 | tie |
| apps-train-2658 | 5 | 10 | skeleton |
| apps-train-2661 | 8 | 6 | JSON |
| apps-train-2664 | 8 | 4 | JSON |
| apps-train-2668 | 2 | 5 | skeleton |
| apps-train-2671 | 5 | 9 | skeleton |

## Same-subset execution comparison

Every method below is recomputed on these same 10 problem IDs. Full-pass denominators are all 10; candidate coverage is shown separately.

| Method | Candidate coverage | Public full pass | Private full pass | Private test rate | Unique programs evaluated |
| --- | ---: | ---: | ---: | ---: | ---: |
| M0 direct | 10/10 | 5/10 | 3/10 | 0.615 (32/52) | 33 |
| M1 plan-first | 10/10 | 6/10 | 5/10 | 0.654 (34/52) | 32 |
| M2a skeleton | 9/10 | 5/10 | 6/10 | 0.694 (34/49) | 50 |
| M2b JSON | 9/10 | 4/10 | 3/10 | 0.600 (30/50) | 46 |
| M3 human | 8/10 | 3/10 | 3/10 | 0.361 (13/36) | 26 |

## Interpretation

The human-authored decompositions are a structural reference, not a learned policy. They reached 8/10 candidate coverage and 3/10 private full pass on this sample. Their result does not exceed the automatic M1 baseline on the same questions; therefore the current evidence does not justify RL training. The human scores are still useful: they identify interface precision, dependency clarity, and boundary-condition coverage as the likely bottlenecks for the automatic decomposition policy.

M3 implementation failures are recorded in the raw implementation JSONL. No private result was used to write or select the human decomposition.
