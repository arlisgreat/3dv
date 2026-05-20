#!/usr/bin/env python3
"""Diagnose the RI3D train loss path on the real-GT adapter.

The script writes compact tensor statistics only. It does not save RGB renders,
PLYs, or raw media.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from random import randint, seed
from types import SimpleNamespace
from typing import Any


DATE = "2026-05-20"
PASS_VERDICT = "PASS_RI3D_LOSS_PATH_NUMERICAL_HEALTH"
BLOCKED_VERDICT = "BLOCKED_RI3D_LOSS_PATH_NUMERICAL_HEALTH"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tensor_stats(tensor: Any) -> dict[str, Any]:
    import torch

    item: dict[str, Any] = {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
    }
    finite = torch.isfinite(tensor)
    item["finite"] = bool(finite.all().item())
    item["nonfinite_count"] = int((~finite).sum().item())
    finite_vals = tensor[finite]
    if finite_vals.numel() > 0:
        item.update(
            {
                "min": float(finite_vals.min().detach().cpu().item()),
                "max": float(finite_vals.max().detach().cpu().item()),
                "mean": float(finite_vals.mean().detach().cpu().item()),
            }
        )
    return item


def scalar_value(value: Any) -> dict[str, Any]:
    import torch

    if isinstance(value, torch.Tensor):
        return {
            "value": float(value.detach().cpu().item()),
            "finite": bool(torch.isfinite(value).detach().cpu().item()),
        }
    return {"value": float(value), "finite": True}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ri3d-root", type=Path, default=Path("external/ri3d"))
    parser.add_argument("--adapter-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/datasets/multiface_debug_e001/ri3d_real_camera_adapter_000102"))
    parser.add_argument("--ply-path", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g25_ri3d_multiface_init_smoke_20260520/point_cloud/iteration_1/point_cloud.ply"))
    parser.add_argument("--run-root", type=Path, default=Path("/data1/workspace/airulan/3dv_work/runs/g28_ri3d_loss_path_probe_20260520"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/metrics/g28_ri3d_loss_path_diagnosis_20260520.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/metrics/g28_ri3d_loss_path_diagnosis_20260520.md"))
    parser.add_argument("--device", default="cuda")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path.cwd()
    ri3d_root = (repo / args.ri3d_root).resolve() if not args.ri3d_root.is_absolute() else args.ri3d_root
    args.run_root.mkdir(parents=True, exist_ok=True)
    seed(0)

    sys.path.insert(0, str(ri3d_root))
    os.chdir(ri3d_root)

    import torch
    from gaussian_renderer import render
    from scene import GaussianModel, Scene
    from utils.loss_utils import l1_loss, monodisp, ssim
    torch.manual_seed(0)

    model_args = SimpleNamespace(
        sh_degree=2,
        source_path=str(args.adapter_root),
        model_path=str(args.run_root),
        images="images",
        resolution=1,
        white_background=True,
        data_device=args.device,
        eval=False,
    )
    opt_args = SimpleNamespace(
        max_num_splats=5_000_000,
        iterations=10,
        position_lr_init=0.00016,
        position_lr_final=0.0000016,
        position_lr_delay_mult=0.01,
        position_lr_max_steps=30_000,
        feature_lr=0.0025,
        opacity_lr=0.05,
        scaling_lr=0.0,
        rotation_lr=0.001,
        percent_dense=0.01,
        lambda_dssim=0.2,
        lambda_silhouette=0.01,
        densification_interval=100,
        opacity_reset_interval=400,
        remove_outliers_interval=500,
        densify_from_iter=500,
        densify_until_iter=6000,
        densify_grad_threshold=0.0002,
        start_sample_pseudo=400000,
        end_sample_pseudo=1000000,
        sample_pseudo_interval=10,
        random_background=False,
    )
    pipe_args = SimpleNamespace(convert_SHs_python=False, compute_cov3D_python=False, debug=False)
    extra_args = SimpleNamespace(
        sparse_view_num=6,
        use_mask=False,
        pointcloud_mask_filter=False,
        pointcloud_conf_threshold=0.0,
        pointcloud_min_points=256,
        pointcloud_points_per_view=0,
        pointcloud_use_frame_mask=True,
        init_pcd_name="origin",
        transform_the_world=False,
        mono_depth_weight=0.0,
        random_background=False,
        data_device=args.device,
        white_background=True,
        resolution=1,
        is_renderrr=False,
    )

    bg = torch.tensor([1.0, 1.0, 1.0], dtype=torch.float32, device=args.device)
    gaussians = GaussianModel(model_args.sh_degree, extra_args.sparse_view_num, spherical_gaussians=True)
    scene = Scene(model_args, gaussians, shuffle=False, extra_opts=extra_args, load_ply=str(args.ply_path))
    gaussians.training_setup(opt_args)
    def probe_view(viewpoint: Any, do_backward: bool = False) -> dict[str, Any]:
        render_pkg = render(viewpoint, gaussians, pipe_args, bg)
        image = render_pkg["render"]
        gt = viewpoint.original_image.to(image.dtype).cuda()
        l1 = l1_loss(image, gt)
        lssim = 1.0 - ssim(image, gt)
        lssim_clamped = 1.0 - ssim(image.clamp(0.0, 1.0), gt)
        mono_depth = getattr(viewpoint, "mono_depth", None)
        depth_loss = None
        loss_current_formula_with_depth_zero = None
        if mono_depth is not None:
            disp_mono = 1.0 / mono_depth.clamp(1e-6).reshape(-1)
            disp_render = 1.0 / render_pkg["rendered_depth"].clamp(1e-6).reshape(-1)
            _, _, depth_loss = monodisp(disp_mono, disp_render, "l1")
        loss_default = (1.0 - 0.2) * l1 + 0.2 * lssim
        loss_lambda_zero_current = (1.0 - 0.0) * l1 + 0.0 * lssim
        loss_lambda_zero_guarded = l1
        if depth_loss is not None:
            loss_current_formula_with_depth_zero = loss_lambda_zero_current + 0.0 * depth_loss
        if do_backward:
            loss_current_formula_with_depth_zero.backward()
            gaussians.optimizer.step()
            gaussians.optimizer.zero_grad(set_to_none=True)
        checks = {
            "render_finite": torch.isfinite(image).all().item(),
            "gt_finite": torch.isfinite(gt).all().item(),
            "mono_depth_present": mono_depth is not None,
            "mono_depth_finite": torch.isfinite(mono_depth).all().item() if mono_depth is not None else True,
            "l1_finite": torch.isfinite(l1).item(),
            "ssim_finite": torch.isfinite(lssim).item(),
            "ssim_clamped_finite": torch.isfinite(lssim_clamped).item(),
            "depth_loss_finite": torch.isfinite(depth_loss).item() if depth_loss is not None else True,
            "default_loss_finite": torch.isfinite(loss_default).item(),
            "lambda_zero_current_loss_finite": torch.isfinite(loss_lambda_zero_current).item(),
            "lambda_zero_guarded_loss_finite": torch.isfinite(loss_lambda_zero_guarded).item(),
            "current_formula_with_zero_depth_weight_finite": torch.isfinite(loss_current_formula_with_depth_zero).item() if loss_current_formula_with_depth_zero is not None else True,
            "alpha_finite": torch.isfinite(render_pkg["rendered_alpha"]).all().item(),
            "depth_finite": torch.isfinite(render_pkg["rendered_depth"]).all().item(),
        }
        return {
            "viewpoint": getattr(viewpoint, "image_name", "unknown"),
            "checks": checks,
            "tensor_stats": {
                "render": tensor_stats(image),
                "gt": tensor_stats(gt),
                "alpha": tensor_stats(render_pkg["rendered_alpha"]),
                "depth": tensor_stats(render_pkg["rendered_depth"]),
                "mono_depth": tensor_stats(mono_depth) if mono_depth is not None else None,
            },
            "loss_terms": {
                "l1": scalar_value(l1),
                "lssim": scalar_value(lssim),
                "lssim_clamped_render": scalar_value(lssim_clamped),
                "depth_loss_monodisp": scalar_value(depth_loss) if depth_loss is not None else {"value": None, "finite": True},
                "loss_default_lambda_0_2": scalar_value(loss_default),
                "loss_lambda_zero_current_formula": scalar_value(loss_lambda_zero_current),
                "loss_lambda_zero_guarded_l1_only": scalar_value(loss_lambda_zero_guarded),
                "loss_current_formula_with_zero_depth_weight": scalar_value(loss_current_formula_with_depth_zero) if loss_current_formula_with_depth_zero is not None else {"value": None, "finite": True},
            },
        }

    per_view = [probe_view(viewpoint) for viewpoint in scene.getTrainCameras()]
    viewpoint_probe = per_view[0]

    train_loop: list[dict[str, Any]] = []
    viewpoint_stack = scene.getTrainCameras().copy()
    for iteration in range(1, 11):
        if not viewpoint_stack:
            viewpoint_stack = scene.getTrainCameras().copy()
        viewpoint = viewpoint_stack.pop(randint(0, len(viewpoint_stack) - 1))
        item = probe_view(viewpoint, do_backward=True)
        item["iteration"] = iteration
        train_loop.append(item)

    checks = {
        "all_train_view_losses_finite": all(item["checks"]["current_formula_with_zero_depth_weight_finite"] for item in per_view),
        "all_train_loop_losses_finite": all(item["checks"]["current_formula_with_zero_depth_weight_finite"] for item in train_loop),
        "all_train_loop_render_finite": all(item["checks"]["render_finite"] for item in train_loop),
        "any_train_loop_loss_nonfinite_after_step": any(not item["checks"]["current_formula_with_zero_depth_weight_finite"] for item in train_loop),
        **{f"first_view_{key}": value for key, value in viewpoint_probe["checks"].items()},
    }
    failed = [key for key, value in checks.items() if not bool(value)]
    verdict = PASS_VERDICT if not failed else BLOCKED_VERDICT
    first_nonfinite = next((item for item in train_loop if not item["checks"]["current_formula_with_zero_depth_weight_finite"]), None)
    likely_source = (
        f"Training loop becomes non-finite at iteration {first_nonfinite['iteration']} on view {first_nonfinite['viewpoint']}."
        if first_nonfinite is not None
        else "All probed train-loop losses remained finite; G27 NaN may depend on train_gs-only state not reproduced here."
    )
    first_view_source = (
        "Mono-depth branch returns non-finite values; train_gs computes depth_loss even when mono_depth_weight=0, so 0*NaN keeps the total loss NaN."
        if viewpoint_probe["checks"]["l1_finite"] and viewpoint_probe["checks"]["ssim_finite"] and not viewpoint_probe["checks"]["depth_loss_finite"] and not viewpoint_probe["checks"]["current_formula_with_zero_depth_weight_finite"]
        else "SSIM branch returns non-finite values; train_gs computes SSIM even when lambda_dssim=0, so 0*NaN keeps the total loss NaN."
        if viewpoint_probe["checks"]["l1_finite"] and not viewpoint_probe["checks"]["ssim_finite"] and not viewpoint_probe["checks"]["lambda_zero_current_loss_finite"] and viewpoint_probe["checks"]["lambda_zero_guarded_loss_finite"]
        else "First-view source is finite."
    )
    payload = {
        "date": DATE,
        "gate": "G28",
        "verdict": verdict,
        "seed": 0,
        "adapter_root": str(args.adapter_root),
        "ply_path": str(args.ply_path),
        "run_root": str(args.run_root),
        "first_viewpoint": viewpoint_probe["viewpoint"],
        "checks": checks,
        "failed_checks": failed,
        "first_view_probe": viewpoint_probe,
        "per_view_probe": per_view,
        "train_loop_probe": train_loop,
        "likely_source": likely_source,
        "first_view_source": first_view_source,
        "artifact_policy": "No RGB renders, PLYs, or raw media are written by this diagnosis; only compact metrics are committed.",
    }
    os.chdir(repo)
    write_json(repo / args.output_json, payload)
    lines = [
        "# G28 RI3D Loss-Path Diagnosis",
        "",
        f"Date: {DATE}",
        "",
        "Verdict:",
        "",
        "```text",
        verdict,
        "```",
        "",
        "Checks:",
        "",
        "| Check | Result |",
        "| --- | --- |",
        *[f"| {key} | {'PASS' if value else 'BLOCK'} |" for key, value in checks.items()],
        "",
        "Loss terms:",
        "",
        "| Term | Finite | Value |",
        "| --- | --- | ---: |",
    ]
    for key, value in payload["first_view_probe"]["loss_terms"].items():
        lines.append(f"| {key} | {'yes' if value['finite'] else 'no'} | {value['value']} |")
    lines.extend(
        [
            "",
            "Train loop probe:",
            "",
            "| Iter | View | Loss finite | Render finite | L1 | Depth loss |",
            "| ---: | --- | --- | --- | ---: | ---: |",
        ]
    )
    for item in train_loop:
        lines.append(
            f"| {item['iteration']} | {item['viewpoint']} | "
            f"{'yes' if item['checks']['current_formula_with_zero_depth_weight_finite'] else 'no'} | "
            f"{'yes' if item['checks']['render_finite'] else 'no'} | "
            f"{item['loss_terms']['l1']['value']} | {item['loss_terms']['depth_loss_monodisp']['value']} |"
        )
    lines.extend(
        [
            "",
            "Render range:",
            "",
            "```text",
            f"render min={payload['first_view_probe']['tensor_stats']['render'].get('min')} max={payload['first_view_probe']['tensor_stats']['render'].get('max')} nonfinite={payload['first_view_probe']['tensor_stats']['render']['nonfinite_count']}",
            f"gt min={payload['first_view_probe']['tensor_stats']['gt'].get('min')} max={payload['first_view_probe']['tensor_stats']['gt'].get('max')} nonfinite={payload['first_view_probe']['tensor_stats']['gt']['nonfinite_count']}",
            f"rendered_depth min={payload['first_view_probe']['tensor_stats']['depth'].get('min')} max={payload['first_view_probe']['tensor_stats']['depth'].get('max')} nonfinite={payload['first_view_probe']['tensor_stats']['depth']['nonfinite_count']}",
            f"mono_depth min={payload['first_view_probe']['tensor_stats']['mono_depth'].get('min') if payload['first_view_probe']['tensor_stats']['mono_depth'] else None} max={payload['first_view_probe']['tensor_stats']['mono_depth'].get('max') if payload['first_view_probe']['tensor_stats']['mono_depth'] else None} nonfinite={payload['first_view_probe']['tensor_stats']['mono_depth']['nonfinite_count'] if payload['first_view_probe']['tensor_stats']['mono_depth'] else None}",
            "```",
            "",
            "Likely source:",
            "",
            "```text",
            likely_source,
            "```",
            "",
            "Artifact policy:",
            "",
            "```text",
            payload["artifact_policy"],
            "```",
            "",
            "Next gate:",
            "",
            "```text",
            "G29 should patch the RI3D loss path to skip zero-weight non-finite terms, especially mono-depth loss when mono_depth_weight=0, then rerun the G27 tiny training gate.",
            "```",
            "",
        ]
    )
    (repo / args.output_md).parent.mkdir(parents=True, exist_ok=True)
    (repo / args.output_md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(verdict)
    print(likely_source)


if __name__ == "__main__":
    main()
