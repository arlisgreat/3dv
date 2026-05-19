# First10 Candidate Pool Visual Audit

Date: 2026-05-19

## Verdict

The existing `experiments/downstream_datasets/` candidate pools are not good
enough to stand as a reconstruction premise.

This is not a small wording issue. The selected pseudo views contain many
obvious visual failures:

```text
split bodies / duplicated partial people
rotated full-photo cards instead of rotated heads
cropped head/body fragments
large blank or gray regions
side/back views with weak or missing identity evidence
mask-accepted regions that are still not semantically valid head views
```

The VLM/manual visual check therefore blocks reconstruction training from these
candidate pools.

## Audited Figure

```text
experiments/figures/first10_candidate_pool_visual_audit_20260519.png
```

The figure compares the historical `raw75_budget4` and
`cutout75_budget4_masked` candidate pools. It intentionally shows the selected
candidates, not only the metrics, because the metrics were too weak to catch
the main failures.

## Impact On Prior Milestones

G8-G14 remain useful as execution and failure-diagnosis records, but their
scientific interpretation is downgraded:

```text
They do not prove that a sound pseudo-view supervision protocol failed.
They prove that weakly screened candidate pools plus RI3D do not produce stable
single-image head reconstruction.
```

Any future milestone must pass a data audit gate before running GPU
reconstruction:

```text
1. structural audit of manifests, paths, roles, reject rates, and coverage
2. visual/VLM audit of generated PNG candidates
3. explicit premise statement: diagnostic-only vs reconstruction-training
4. written gate verdict in experiments/metrics/
5. MILESTONES.md updated before the experiment starts
```

## Replanned Direction

The next milestone is not more RI3D training. It is candidate-pool recovery:

```text
regenerate or repair pseudo views
use stricter VLM/manual image-quality filtering
require head-level semantic validity, not just CLIP/reliability/mask scores
only export reconstruction candidates after the gate passes
```
