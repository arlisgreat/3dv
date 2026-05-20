# G40 Learned-Prior LAM Smoke

Date: 2026-05-20

Verdict:

```text
PASS_LOCAL_LEARNED_PRIOR_SMOKE_NO_QUALITY_CLAIM
```

Purpose:

```text
Run the first learned-prior/feed-forward/head-anchored Gaussian smoke after G39, while keeping real-GT privacy and distribution limits explicit.
```

G40a Multiface local-only smoke:

| field | value |
| --- | --- |
| status | success_local_only |
| model | LAM-20K |
| model_family | feed_forward_head_anchored_gaussian |
| input | Multiface debug E001 frame 000102 camera 400017 train view |
| input_sha256 | adce56e250e2198abb17e1e055eb4ae4944c5a9b37e966c6e692283658ed2565 |
| gpu | CUDA_VISIBLE_DEVICES=1 |
| command | bash scripts/server/03_run_lam_sample.sh <private_multiface_rgb> configs/inference/lam-20k-8gpu.yaml model_zoo/lam_models/releases/lam/lam-20k/step_045500/ assets/sample_motion/export/Look_In_My_Eyes/ |
| environment_patch | patches/lam/torch26_vgghead_torchscript_load.patch |
| environment_patch_exists | True |
| artifact_policy | private media moved to 3dv_work; repo sync includes hashes/metrics only |
| manual_visual_audit | PASS_LOCAL_SMOKE_ONLY. The private contact sheet shows a coherent animatable head across frames, but with visible green color cast, soft/blurred shoulder-neck support, and no held-out camera alignment. It is an execution/distribution smoke, not a reconstruction-quality result. |

Private output hashes:

| basename | size_bytes | sha256 |
| --- | ---: | --- |
| 400017_000102.mp4 | 457383 | da95da754db552a97da6aeaa41eea792ad133504a55d7607e8c9581e1af55d63 |
| 400017_000102_audio.mp4 | 732444 | e25a6b43c5223aaef93c7d21a6a6434dbe45bb734a1bab129509de835654c6ad |
| g40a_private_video_audit_sheet.png | 148317 | 4cc2b8ccc6185f226c82fed55323f8c4f1e88f24eac2f7420c433e42acea95e0 |

Manual/VLM-style visual audit:

```text
PASS_LOCAL_SMOKE_ONLY. The private contact sheet shows a coherent animatable head across frames, but with visible green color cast, soft/blurred shoulder-neck support, and no held-out camera alignment. It is an execution/distribution smoke, not a reconstruction-quality result.
```

G40b CC0 positive-control LAM smoke:

| field | value |
| --- | --- |
| status | blocked |
| input | experiments/gt_cases/wikimedia_blender_head_cc0/views/rgb_00_az000.png |
| reason | The CC0 rendered point-splat head is repo-safe but outside LAM's natural portrait input distribution; LAM face tracking failed before avatar generation. |
| observed_error | UnboundLocalError: local variable 'face_landmarks' referenced before assignment |
| interpretation | CC0 case remains useful for geometry/camera pipeline gates, not for LAM feed-forward input smoke. |

Decision:

```text
G40 confirms that the real-GT input can drive the available feed-forward Gaussian baseline locally, but it does not create a quality claim. Next work must build or integrate a method that can render held-out Multiface cameras or export geometry for GT metrics. Identifiable Multiface PNG/MP4 remain out of GitHub sync until explicit artifact review.
```
