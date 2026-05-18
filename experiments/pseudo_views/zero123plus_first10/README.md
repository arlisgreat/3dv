# Zero123++ First10 Pilot

Pseudo multi-view outputs for the Wikimedia Commons `first10` pilot inputs.

Generation command template:

```bash
python scripts/zero123plus_batch.py \
  --manifest experiments/inputs/first10/manifest.csv \
  --out-root experiments/pseudo_views/zero123plus_first10 \
  --steps 20 \
  --seed 42 \
  --device cuda:0
```

Each sample directory contains `input_square.png`, `grid.png`, six split view PNGs, and `metadata.json`.
