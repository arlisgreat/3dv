# G114 Source-Gated Pseudo Prior Private RGB Visual Audit

Date: 2026-05-28

Verdict:

```text
PASS_PRIVATE_RGB_VISUAL_AUDIT_DIAGNOSTIC_ONLY
```

Private visual sheet:

```text
/data1/workspace/airulan/3dv_work/runs/g114_source_gated_pseudo_prior_private_visual/g114_private_rgb_sheet.png
```

Private visual sheet sha256:

```text
3344c4eb77844c819609aa3a19355db274d31c71ab6ec4a02f95481948c68687
```

Artifact policy:

```text
Private sheet contains identifiable NeRSemble target and rendered RGB; keep under 3dv_work and do not commit image.
```

Manual/VLM audit note:

```text
Private RGB sheet was generated for local inspection. The G110 aware predictions preserve direct-prior head structure and avoid the fragmented RI3D pseudo-view geometry seen in the naive arm; color is darker/pseudo-prior shifted, matching the metric-improving source-gated color prior. Treat as single-case diagnostic until multi-case review.
```

Decision:

```text
Private RGB visual audit supports interpreting G110 as a real improvement over the fragmented pseudo-view RI3D arm on this case, while keeping distribution and single-case caveats.
```

Next gate:

```text
Update milestone records, run artifact sync gate, and push repo-safe metrics/scripts/mask-only PNG.
```
