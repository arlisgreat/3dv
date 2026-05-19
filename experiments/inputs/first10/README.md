# First10 Web Headshot Inputs

This directory holds the manifest for the first10 pilot set.

Input images are crawled from Wikimedia Commons through `scripts/data/collect_wikimedia_headshots.py`.
The repository tracks the source manifest and experiment outputs, but keeps raw downloaded inputs out of
Git by default. The generated pseudo-view PNGs and reconstruction MP4s under `experiments/` are publishable
result records.

Default local paths after collection:

```text
experiments/inputs/first10/raw/
experiments/inputs/first10/processed/
experiments/inputs/first10/manifest.csv
experiments/figures/first10_wikimedia_contact_sheet.png
experiments/inputs/first10/cutouts/
experiments/inputs/first10/cutouts_manifest.csv
experiments/figures/first10_cutout_inputs.png
```

Every sample row records source URL, Commons file page, license, attribution fields, and sha256 for the
processed input used by the models.

The `cutouts/` directory contains subject-only gray-background inputs generated
with `scripts/data/make_first10_cutouts.py` for the Zero123++ input-format
ablation. The local `rembg` model cache is not tracked.
