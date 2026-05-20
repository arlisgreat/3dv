# G39 Learned-Prior / Feed-Forward / Head-Anchored Gaussian Method Gate

Date: 2026-05-20

Verdict:

```text
PASS_REAL_GT_DATA_VLM_METHOD_GATE_LOCAL_ONLY
```

Premise:

```text
The next credible method route is learned-prior / feed-forward / head-anchored Gaussian head reconstruction, not longer RI3D optimization over pseudo-view candidates.
```

Application alignment:

```text
The application proposal targets single-image full-head modeling by replacing PanoHead's NeRF rendering with Gaussian representation, using diffusion only as an audited prior for invisible regions, using Transformer-style consistency, and anchoring geometry with FLAME/FaceVerse/3DMM.
```

Method positioning:

| item | status | implication |
| --- | --- | --- |
| LAM-20K | local_runnable_feed_forward_head_anchored_gaussian_baseline | Use only as a baseline/smoke until camera-aligned held-out rendering or geometry export is available; LAM uses FLAME canonical points as Transformer queries for Gaussian attributes. |
| PanoLAM / OMEGA / FFAvatar / Any3DAvatar | latest_method_direction_not_locally_integrated | They define the correct scientific direction: feed-forward full-head priors, FLAME/UV or structured Gaussian scaffolds, dense multi-view supervision, and benchmark metrics. |
| RI3D G21-G33 | closed_numerical_plumbing_route | Keep as diagnostic evidence only; do not scale training without a new method premise. |
| Zero123++ downstream candidate pools | diagnostic_candidate_pool_only | May inform failure taxonomy or conditional priors after VLM audit, never GT training views. |

Gate checks:

| check | value |
| --- | --- |
| real_gt_case_status | True |
| real_gt_view_count_6_to_12 | True |
| g21_vlm_manual_gate_passed | True |
| g36_method_redesign_gate_passed | True |
| g37_distribution_audit_passed | True |
| g38_artifact_sync_gate_passed | True |
| lam_feed_forward_baseline_available_locally | True |
| pseudo_view_training_blocked | True |
| private_multiface_media_export_blocked | True |

Distribution statement:

```text
LAM-20K is documented as trained on VFHQ + NeRSemble. The current real-GT case is Multiface: a nearby multi-view head-capture domain but not proven in-distribution for the released LAM weights. Therefore LAM-on-Multiface can be interpreted only as local qualitative or plumbing evidence unless we obtain camera-aligned render/geometry outputs and compare against held-out views/GT geometry.
```

Authorized next experiments:

```text
G40a: optional local-only LAM smoke on one Multiface train view; record command, hashes, timing, and manual/VLM notes only; no identifiable media sync.
G40b: repo-safe LAM smoke on the CC0 synthetic positive-control front view; sync MP4/PNG/JSON/MD, but label it positive-control only.
G41: design a true head-anchored Gaussian scaffold/adapter that can render held-out cameras or export mesh/point-cloud for GT metrics before any quality claim.
```

Blocked actions:

```text
Do not train or evaluate reconstruction quality on experiments/downstream_datasets.
Do not use Multiface GT mesh as input to a single-image method; it is evaluation geometry only.
Do not publish identifiable Multiface RGB, generated avatar videos, meshes, or textured assets without artifact/privacy review.
Do not claim learned-prior quality from LAM videos alone; require held-out camera-aligned metrics or geometry metrics.
Do not restart longer RI3D training from G33 as a method milestone.
```

Literature anchors:

| work | date | source | signal |
| --- | --- | --- | --- |
| LAM | 2025-02-25 / revised 2025-04-04 | https://arxiv.org/abs/2502.17796 | Single-forward-pass Gaussian head; FLAME canonical points query Transformer image features. |
| PanoLAM | 2025-09-09 / revised 2025-10-10 | https://arxiv.org/abs/2509.07552 | One-shot full-head Gaussian synthesis; FLAME sparse points plus transformer, synthetic 3D-GAN priors. |
| SEGA | 2025-04-19 / revised 2026-03-11 | https://arxiv.org/abs/2504.14373 | Single-image drivable Gaussian head avatar with FLAME-based hierarchical UV Gaussian splatting. |
| OMEGA-Avatar | 2026-02-12 | https://arxiv.org/abs/2602.11693 | Feed-forward 360 full-head animatable Gaussian avatar with semantic-aware mesh deformation and UV fusion. |
| Any3DAvatar | 2026-04-15 | https://arxiv.org/abs/2604.13856 | Structured Plucker-aware Gaussian scaffold and one-step conditional denoising for single-image full-head reconstruction. |
| MeshLAM | 2026-04-23 | https://arxiv.org/abs/2604.22865 | Feed-forward one-shot animatable mesh head; useful successor signal for topology and texture anchoring. |
| FFAvatar | 2026-05-14 | https://arxiv.org/abs/2605.15320 | Few-shot feed-forward Gaussian head reconstruction with multi-view fusion, FLAME prediction, and NeRSemble metrics. |

Decision:

```text
Open G40 only as gated learned-prior smoke/positive-control work. The real-GT/data/VLM premise is satisfied locally, but model-quality claims remain blocked until a head-anchored method produces held-out camera-aligned renders or GT geometry metrics.
```
