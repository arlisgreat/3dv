# Pseudo Views

Generated pseudo-view PNGs are experiment results and should be committed
with their `metadata.json` files and summary tables.

Current local smoke output:

```text
zero123plus_smoke/teaser_low_steps10/
zero123plus_first10/
zero123plus_first10_steps75/
zero123plus_first10_cutout_steps75/
trusted_region_masks_steps75_budget4/
trusted_region_masks_cutout75_budget4/
```

The tracked metadata records model id, seed, steps, grid layout, and view
azimuth/elevation. The PNG outputs are tracked for reproducible review.

The first10 pilot uses `steps=20`; treat it as a diagnostic pass, not a final
face-quality result. Several outputs show identity and geometry drift, which is
the expected failure signal for the pseudo-view study.

The second first10 pass uses `steps=75`; it improves many samples but still
contains unsafe pseudo views. Use the view-budget CSVs before feeding generated
views into downstream reconstruction.

The cutout pass uses subject-only gray-background inputs. It reduces
photo-frame/background rotation failures and is the preferred pseudo-view
frontend for the next reconstruction experiment.
