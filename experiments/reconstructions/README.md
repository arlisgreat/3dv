# Reconstructions

Reconstruction MP4 videos are experiment results and should be committed with
their `metadata.json` files and summary tables. Meshes, ply files, weights,
and full intermediate outputs still stay local unless explicitly reviewed.

Current local smoke output:

```text
lam_smoke/status_look_in_my_eyes/
lam_first10/
```

The tracked metadata records input, motion, model checkpoint path, output
hashes, CUDA env, GPU id, and package versions. The MP4 outputs are tracked
for reproducible review.

The first10 pilot exports one silent render MP4 and one audio-attached MP4 per
sample under `lam_first10/<sample_id>_look_in_my_eyes/`.
