# Pseudo Views

Generated pseudo-view PNGs are experiment results and should be committed
with their `metadata.json` files and summary tables.

Current local smoke output:

```text
zero123plus_smoke/teaser_low_steps10/
zero123plus_first10/
zero123plus_first10_steps75/
```

The tracked metadata records model id, seed, steps, grid layout, and view
azimuth/elevation. The PNG outputs are tracked for reproducible review.

The first10 pilot uses `steps=20`; treat it as a diagnostic pass, not a final
face-quality result. Several outputs show identity and geometry drift, which is
the expected failure signal for the pseudo-view study.

The second first10 pass uses `steps=75`; it improves many samples but still
contains unsafe pseudo views. Use the view-budget CSVs before feeding generated
views into downstream reconstruction.
