# G37 Model/Data Distribution Audit

Date: 2026-05-20

Verdict:

```text
PASS_DISTRIBUTION_AUDIT_NO_NEW_QUALITY_CLAIM
```

Question:

```text
Are the models and test data close enough to the model/input premise that results can be interpreted?
```

Audit table:

| route | data | distribution verdict | interpretation |
| --- | --- | --- | --- |
| LAM first10 qualitative baseline | 10 web portraits, no GT cameras/mesh | IN_INPUT_FORM_BUT_NO_GT | 10/10 LAM runs produced MP4s. This is a qualitative one-shot portrait baseline only; there is no held-out real-GT metric on first10. |
| Zero123++ pseudo-view candidate pools | experiments/downstream_datasets/* | OUT_OF_RECONSTRUCTION_GT_DISTRIBUTION | Generated views are candidate priors with known identity/geometry/grid failures. They cannot be used as train/test data for a reconstruction-quality claim. |
| RI3D on old pseudo-view exports | experiments/ri3d_datasets/first2* | MISMATCHED_INPUT_PREMISE | RI3D assumes coherent sparse views of a scene. Historical exports came from generated candidate views and are downgraded to diagnostic artifact/failure evidence. |
| RI3D G21-G33 Multiface local compact case | 9 real captured views, cameras, masks, local mesh | REAL_GT_PREMISE_PASS_BUT_METHOD_QUALITY_NOT_SUPPORTED | The data premise is valid for local held-out benchmark plumbing. G33 held-out metrics remain init-level ({'SSIM': 0.5905788938204447, 'PSNR': 4.268513361612956, 'LPIPS': 0.5011390447616577}), so results are numerical/plumbing evidence, not a method-quality win. |
| Next learned-prior/feed-forward head method | LAM/PanoLAM/OMEGA/FFAvatar-style model on Multiface/H3DS/FaceScape/NeRSemble-style real GT | CONDITIONAL_ON_EXPLICIT_IN_OR_OUT_DISTRIBUTION_STATEMENT | Before running, record the model training/evaluation distribution, whether Multiface/H3DS/FaceScape/NeRSemble is in-distribution, and which held-out views/geometry metrics are used. |

Mandatory rule for the next milestone:

```text
Every method milestone must declare model training/evaluation distribution, test benchmark source, in/out-of-distribution status, held-out split, and visual/VLM gate before GPU work.
```

Decision:

```text
Current results can be analyzed as qualitative baseline, diagnostic pseudo-view failure evidence, or real-GT plumbing/numerical smoke only. No existing result supports a reconstruction-quality claim.
```
