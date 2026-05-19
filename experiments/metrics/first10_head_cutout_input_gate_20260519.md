# First10 Head-Cutout Input Gate

Date: 2026-05-19

Gate verdict:

```text
PASS_FOR_GENERATION_PROBE
```

Artifacts:

```text
scripts/data/make_first10_head_crops.py
experiments/inputs/first10/head_cutouts/
experiments/inputs/first10/head_cutouts_manifest.csv
experiments/figures/first10_head_cutout_inputs.png
```

VLM/manual inspection:

```text
The head_cutouts contact sheet is substantially better than the old full-body
or subject-level candidate inputs. It centers head/neck or head/shoulder regions
on neutral gray backgrounds for all first10 samples.
```

Limits:

```text
This gate only approves a small Zero123++ generation probe. It does not approve
any candidate pool for reconstruction training.
```
