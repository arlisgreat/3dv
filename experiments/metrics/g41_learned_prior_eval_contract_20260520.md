# G41 Learned-Prior Evaluation Contract

Date: 2026-05-20

Verdict:

```text
PASS_EVAL_CONTRACT_BLOCK_QUALITY_UNTIL_CAMERA_ALIGNED_EXPORT
```

Question:

```text
Can the current learned-prior smoke be interpreted as reconstruction quality on the real-GT benchmark?
```

Current LAM wrapper status:

| item | value |
| --- | --- |
| exports_animation_mp4 | true |
| save_ply_enabled | False |
| save_img_enabled | False |
| camera_aligned_multiface_render_available | false |
| heldout_metrics_available | false |
| geometry_metric_available | false |
| privacy_safe_media_sync | false_for_multiface_identifiable_outputs |

Required outputs before any learned-prior quality claim:

```text
Render the predicted Gaussian/head representation under held-out Multiface K/R/T cameras.
Compute held-out PSNR/SSIM/LPIPS against masked real GT views without using held-out images for supervision.
Export or sample a geometry representation and compare to GT mesh/point cloud with scale/alignment recorded.
Keep Multiface identifiable RGB/video/mesh artifacts local unless explicit artifact/privacy review approves sync.
Record model training distribution and whether the benchmark is in-domain, near-domain, or out-of-domain.
Run manual/VLM visual audit on private contact sheets before interpreting metrics.
```

Blocked interpretations:

```text
A LAM animation MP4 is not a held-out reconstruction metric.
A successful face tracker/FLAME fitting stage is not proof of 360 geometry quality.
CC0 positive-control failure in LAM does not invalidate the CC0 geometry gate; it only blocks LAM input-distribution use.
No pseudo-view candidate pool can be promoted into training/evaluation data from this smoke.
```

Decision:

```text
G41 closes the current learned-prior smoke loop: execution is proven locally, but quality evaluation is blocked until camera-aligned render or geometry export is integrated. The next milestone should be a method/adapter implementation milestone, not more ungated MP4 generation.
```
