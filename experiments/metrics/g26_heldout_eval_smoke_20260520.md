# G26 Held-Out Eval Smoke

Date: 2026-05-20

Verdict:

```text
PASS_HELDOUT_RENDER_EVAL_SMOKE
NO_TRAINING_STARTED_IN_G26
```

Scope:

```text
Render and evaluate the 3 held-out Multiface views from the G25 RI3D
initialization. This is a render/eval plumbing gate, not a quality claim.
```

Command:

```bash
PYTHONPATH=/data1/workspace/airulan/3dv/external/ri3d \
python scripts/render.py \
  -s /data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102 \
  -m /data1/workspace/airulan/3dv_work/runs/g25_ri3d_multiface_init_smoke_20260520 \
  -r 1 --sparse_view_num 6 --sh_degree 2 --white_background --iteration 1 \
  --skip_train --not_saveimages --not_generate_video --use_mask True \
  --postfix _g26_eval
```

Numeric result:

| Metric | Value |
| --- | ---: |
| held-out views | 3 |
| SSIM | 0.5905788938 |
| PSNR | 4.2685133616 |
| LPIPS | 0.5011390448 |

Artifact policy:

```text
--not_saveimages was used. No PNG/JPEG/MP4 files were produced under the G26
eval output directory. Only compact metrics are committed.
```

Interpretation:

```text
G26 proves that held-out render/evaluation executes from the G25 initialization.
The metrics are poor, as expected for an init-only point cloud, and must not be
reported as reconstruction quality.
```

Next gate:

```text
G27 may run a tiny real-GT training smoke from the G25 initialization. It must
stay local-only and be followed by a separate held-out evaluation gate before
any quality discussion.
```
