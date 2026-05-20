# Iteration Ideas: Real-GT And Guarded Losses

Date: 2026-05-20

## Current Position

```text
The experiment is no longer trying to prove web pseudo-view training. The stable
position is gate-first: pseudo views are diagnostic candidates until a real-GT
benchmark, data/VLM audit, adapter contract, guarded loss health, and held-out
evaluation all pass.
```

G28-G33 update the iteration plan:

```text
G28: train-loop NaN source class is zero-weight branch contamination after
     optimizer steps.
G29: L1-only train10 clears after skipping zero-weight SSIM/silhouette/depth
     branches.
G30: held-out eval still runs, but metrics match init-only G26.
G31: SSIM-only and silhouette-only train10 are finite; mono-depth-only is NaN.
G32: clamping monodisp scale denominators fixes depth-only train10 NaN.
G33: combined guarded train10 is finite, but held-out eval is still init-level.
G34: route reset closes longer RI3D training as a method-quality milestone.
G35: no additional ready public/local real-GT benchmark is available locally.
G36: method direction resets toward learned-prior/feed-forward/head-anchored
     Gaussian reconstruction under real-GT gates.
```

Therefore the next valid experiment was not a longer run. It was:

```text
G31: guarded component audit.
Enable SSIM, silhouette, and mono-depth supervision one at a time with finite
assertions before loss.backward(). Stop on any non-finite component or no
held-out improvement.
```

## Recent Work Alignment

Primary-source scan:

| Work | Source | Relevance |
| --- | --- | --- |
| LAM: Large Avatar Model for One-shot Animatable Gaussian Head | https://arxiv.org/abs/2502.17796 | Single-image Gaussian head reconstruction is moving toward learned feed-forward priors with FLAME canonical queries and Transformer image features. |
| Avat3r: Large Animatable Gaussian Reconstruction Model for High-fidelity 3D Head Avatars | https://arxiv.org/abs/2502.20220 | Few-image avatar reconstruction relies on a learned large reconstruction model and multi-view training prior, not ad hoc pseudo-view GT. |
| FaceLift: Single Image to 3D Head with View Generation and GS-LRM | https://arxiv.org/abs/2412.17812 | Generated side/back views are used inside a trained GS-LRM reconstructor, supporting the idea that pseudo views need model/gate context. |
| RI3D: Few-Shot Gaussian Splatting With Repair and Inpainting Diffusion Priors | https://arxiv.org/abs/2503.10860 | RI3D assumes coherent sparse inputs and staged repair/inpainting; it does not validate malformed candidate pools as reconstruction supervision. |
| PanoLAM: Large Avatar Model for Gaussian Full-Head Synthesis from One-shot Unposed Image | https://arxiv.org/abs/2509.07552 | Full-head single-image Gaussian synthesis is also moving toward synthetic-data-trained feed-forward full-head priors. |
| GAGAvatar: Generalizable and Animatable Gaussian Head Avatar | https://arxiv.org/abs/2410.07971 | One-shot animatable Gaussian heads are framed as generalized learned reconstruction, again requiring benchmarked priors. |
| Multiface dataset | https://github.com/facebookresearch/multiface | The local G21 route is aligned with real captured multi-view data, cameras, tracked meshes, and headpose. |
| H3DS route | https://pypi.org/project/h3ds/ | Remains the preferred full-head benchmark route if access/license is available. |

## Best Experimental Story

```text
1. The original proposal goal needs diffusion pseudo views, full-head priors,
   Gaussian representation, and 3DMM/FLAME structure.
2. The sprint found that unaudited web pseudo views are too weak for training:
   split-grid bugs, distortions, identity drift, and candidate-pool mismatch
   break the premise.
3. The credible route pivots to real-GT gate-first validation.
4. The local Multiface compact case passes benchmark premise locally, but
   current RI3D remains only adapter/init/eval/numerical plumbing.
5. G29 fixes one numerical class, but G30 proves this is not yet a quality gain.
```

## G31 Plan

Run only compact, local-only gates:

```text
G31a: lambda_dssim > 0, silhouette=0, mono_depth=0.
G31b: lambda_dssim=0, silhouette > 0, mono_depth=0, mask finite checks.
G31c: lambda_dssim=0, silhouette=0, mono_depth > 0, depth finite checks.
G31d: if and only if G31a-c pass, combine the stable components for train10.
G31e: held-out eval with --not_saveimages --not_generate_video.
```

Acceptance:

```text
all losses finite before backward
no PNG/JPG/JPEG/MP4/PLY committed
held-out metrics recorded
explicit no-quality-claim unless improvement is both numerical and visually/VLM
audited on repo-safe derived artifacts
```

## G31-G33 Outcome

```text
G31a SSIM-only: finite.
G31b silhouette-only: finite but no metric change.
G31c/G31d mono-depth-only: NaN before monodisp guard.
G32a/G32b depth-only after monodisp guard: finite.
G33 combined guarded train10: finite.
G33 held-out eval: SSIM 0.5905789, PSNR 4.2685, LPIPS 0.5011, matching G26/G30.
```

Updated stop condition:

```text
The numerical-smoke loop is closed, but quality is not. Do not scale RI3D
iterations from this setup as a method result; the next scientific step is
method redesign or stronger public real-GT benchmark access. Pseudo views can
only re-enter as audited conditional priors, never as ground-truth training
views.
```
