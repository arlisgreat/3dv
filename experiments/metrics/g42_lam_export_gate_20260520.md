# G42 LAM Geometry/Frame Export Gate

Date: 2026-05-20

Verdict:

```text
PASS_LAM_EXPORT_LOCAL_ONLY_NO_QUALITY_CLAIM
```

Purpose:

```text
Verify whether the learned-prior LAM route can export frames and geometry-like artifacts that could become inputs to a later held-out camera or geometry metric adapter.
```

Export summary:

| field | value |
| --- | --- |
| private_run_root | /data1/workspace/airulan/3dv_work/runs/g42_lam_export_multiface_local_20260520 |
| render_png_count | 50 |
| per_frame_ply_count | 50 |
| canonical_gaussian_vertices | 20018 |
| frame0_gaussian_vertices | 20018 |
| shaped_mesh_counts | {'vertices': 5023, 'faces': 9976} |
| textured_mesh_counts | {'vertices': 20018, 'faces': 9976} |
| repo_sync_policy | hashes/metrics only; private RGB/PNG/MP4/PLY/OBJ remain under 3dv_work |

Key private output hashes:

| basename | exists | size_bytes | sha256 |
| --- | --- | ---: | --- |
| 400017_000102.mp4 | True | 90118 | 559679b77b33093ec115c66c2ca2ecfb53b6ea3ec3a5b58375d932a8ab603235 |
| 400017_000102_audio.mp4 | True | 366397 | 971d5e4f46bd1f1b7450e115b1cb682918b6c3099d41926fb3ab37248be314bd |
| g42_private_render_frame_sheet.png | True | 135696 | eceef9964de78f45e83d93c0ad978bf040ca5268b2632a236961c4c2f797750e |
| 400017_000102_gs_offset.ply | True | 1361639 | 3b5797c0d398a4a8f48fc8b6759b147b79544478572626193e5ac044c9d37888 |
| 400017_000102_shaped_mesh.obj | True | 345179 | 977b0910bd5af2852b9db78021515da8a3f8e080a2d4217caded19560d63f1fb |
| 400017_000102_textured_mesh.obj | True | 1550293 | 16fedf824f055f4aeaec84933e484c5c0564dd378b47c9b7a76b4c8f96cf8c71 |
| 0000.png | True | 156736 | d6d4f48a8ef7c8a240c7402007c3616bebb10bf4a5eeb477b228bcb4170c1f7d |
| 0000.ply | True | 1361639 | c04553f20a22cb79078422b4c0c78673d10102fd87af30175ef01c88b925dd8a |

Manual/VLM-style visual audit:

```text
PASS_LOCAL_EXPORT_ONLY. The private frame sheet shows a coherent animated head and exported frames, but it still has green color cast, blurred shoulder/neck support, and background residuals. These frames are not Multiface held-out camera renders.
```

Environment notes:

```text
A direct env-python command failed because torch was missing from base Python.
A second direct command reached LAM but nvdiffrast JIT failed because ninja was not on PATH.
The passing run used conda activate lam, env124.sh, CUDA_VISIBLE_DEVICES=1, and test_sample=true.
```

Decision:

```text
G42 proves LAM can export canonical Gaussian PLY, per-frame Gaussian PLYs, PNG frames, and mesh OBJs locally. It still does not prove reconstruction quality because the exported renders use LAM motion cameras, not held-out Multiface cameras, and the coordinate relation to GT geometry remains unvalidated.
```
