# LAM First10 Pilot

LAM baseline reconstructions for the Wikimedia Commons `first10` pilot inputs.

Generation command template:

```bash
python scripts/lam_batch.py \
  --manifest data_manifest.csv \
  --out-root experiments/reconstructions/lam_first10 \
  --skip-existing
```

Each successful sample directory contains MP4 render outputs and `metadata.json`. Logs stay under
`/data1/workspace/airulan/3dv_work/logs/lam_first10/`.
