# G88 G81 RI3D Gaussian NeRSemble Held-Out Render

Date: 2026-05-28

Premise:

```text
Render RI3D Gaussian reconstructions trained from G81 pseudo-supervision arms into the exact NeRSemble source and local held-out K/R/T cameras. Alignment uses source RGB alpha/mask and held-out camera metadata as a frustum guard, but never held-out RGB/masks.
```

Verdict:

```text
PASS_G81_RI3D_GAUSSIAN_NERSEMBLE_HELDOUT_RENDER_READY
```

Arms:

| arm | variant | source IoU | mean eval coverage | prediction root |
| --- | --- | ---: | ---: | --- |
| naive_pseudo_view_supervision | g81_naive_pseudo_source_anchor | 0.338371 | 0.295674 | /data1/workspace/airulan/3dv_work/runs/g91_g81_ri3d_nersemble_heldout_iter80_splat8_lite/g81_naive_pseudo_source_anchor/predictions |
| identity_confidence_aware_pseudo_view_supervision | g81_identity_confidence_aware_source_anchor | 0.317577 | 0.295789 | /data1/workspace/airulan/3dv_work/runs/g91_g81_ri3d_nersemble_heldout_iter80_splat8_lite/g81_identity_confidence_aware_source_anchor/predictions |

Renderer contract:

```text
3DGS PLY point approximation rendered by z-buffer splats into official NeRSemble intrinsics/world_2_cam; this is a diagnostic renderer, not the RI3D differentiable Gaussian rasterizer.
```

Missing requirements:

```text
none
```

Decision:

```text
Both G81 RI3D arms produced held-out camera prediction PNGs for G55 evaluation.
```

Next gate:

```text
Run G55 evaluator for naive and identity/confidence-aware prediction roots, then rerun G84 three-arm contract.
```
