#!/usr/bin/env python3
"""Summarize the RI3D first2 downstream pilot into repo publishable artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


VARIANTS = ("raw75_all6", "raw75_budget4", "cutout75_budget4_masked")
SAMPLES = ("web_clean_frontal_03", "web_clean_frontal_01")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def ply_vertices(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("rb") as f:
        for raw in f:
            line = raw.decode("ascii", errors="ignore").strip()
            if line.startswith("element vertex "):
                return int(line.split()[-1])
            if line == "end_header":
                break
    return None


def final_loss(log_text: str) -> tuple[float | None, int | None]:
    matches = re.findall(r"Loss=([0-9.]+), n=([0-9]+)", log_text)
    if not matches:
        return None, None
    loss, n_splats = matches[-1]
    return float(loss), int(n_splats)


def extract_namespace_value(log_text: str, key: str) -> str | None:
    match = re.search(rf"{key}=('([^']*)'|([^,\)]+))", log_text)
    if not match:
        return None
    return match.group(2) if match.group(2) is not None else match.group(3)


def scene_tags(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        for sample in SAMPLES:
            scene = data_root / variant / sample
            if not scene.exists():
                continue
            transforms = load_json(scene / "transforms.json")
            view_count = len(transforms["frames"])
            rows.append(
                {
                    "variant": variant,
                    "sample_id": sample,
                    "view_count": view_count,
                    "tag": f"{sample}_{variant}_{view_count}v",
                    "scene": scene,
                    "image_size": transforms["w"],
                }
            )
    return rows


def copy_render_outputs(run_root: Path, export_root: Path, row: dict[str, Any], iteration: int) -> dict[str, str]:
    tag = row["tag"]
    render_dir = run_root / "output" / "gs_init" / tag / "render" / f"ours_{iteration}"
    outputs: dict[str, str] = {}
    for src_name, suffix in (("video.mp4", "rgb"), ("videoD.mp4", "depth")):
        src = render_dir / src_name
        if not src.exists():
            continue
        dst = export_root / f"{tag}_{suffix}.mp4"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        outputs[f"render_{suffix}_mp4"] = str(dst)
    return outputs


def choose_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_input_contact_sheet(rows: list[dict[str, Any]], output: Path, thumb: int = 96) -> None:
    font = choose_font(13)
    label_h = 34
    pad = 8
    max_views = max(row["view_count"] for row in rows)
    width = pad * 2 + max_views * thumb
    height = pad + len(rows) * (label_h + thumb + pad)
    sheet = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    y = pad
    for row in rows:
        label = f"{row['sample_id']} | {row['variant']} | {row['view_count']} views"
        draw.text((pad, y), label, fill=(20, 20, 20), font=font)
        y += label_h
        image_paths = sorted((row["scene"] / "images").glob("*.png"))
        for idx, image_path in enumerate(image_paths):
            image = Image.open(image_path).convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
            sheet.paste(image, (pad + idx * thumb, y))
        y += thumb + pad
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def first_video_frame(path: Path) -> Image.Image | None:
    try:
        import cv2  # type: ignore
    except Exception:
        return None
    cap = cv2.VideoCapture(str(path))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


def make_render_contact_sheet(rows: list[dict[str, Any]], export_root: Path, output: Path, thumb: int = 120) -> None:
    font = choose_font(13)
    label_h = 34
    pad = 8
    cells: list[tuple[dict[str, Any], Image.Image]] = []
    for row in rows:
        frame = first_video_frame(export_root / f"{row['tag']}_rgb.mp4")
        if frame is None:
            continue
        cells.append((row, frame.convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)))
    if not cells:
        return
    width = pad * 2 + 3 * thumb
    height = pad + len(cells) * (label_h + thumb + pad)
    sheet = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    y = pad
    for row, image in cells:
        label = f"{row['sample_id']} | {row['variant']}"
        draw.text((pad, y), label, fill=(20, 20, 20), font=font)
        y += label_h
        sheet.paste(image, (pad, y))
        y += thumb + pad
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_observations(
    *,
    path: Path,
    rows: list[dict[str, Any]],
    export_root: Path,
    data_root: Path,
    run_root: Path,
    metrics_csv: Path,
    input_figure: Path,
    render_figure: Path,
    iteration: int,
    run_name: str,
) -> None:
    by_sample: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_sample.setdefault(row["sample_id"], []).append(row)

    best_lines: list[str] = []
    for sample_id, sample_rows in sorted(by_sample.items()):
        valid_rows = [row for row in sample_rows if row["final_loss"] is not None]
        if not valid_rows:
            continue
        best = min(valid_rows, key=lambda row: row["final_loss"])
        best_lines.append(f"{sample_id}: best training loss is {best['variant']} ({best['final_loss']:.7f}).")

    if iteration <= 100:
        quality_note = [
            "The rendered videos are smoke-quality only: several views still show rotated full-photo/background artifacts.",
            "Some 4-view depth videos may emit zero-range depth normalization warnings; use RGB renders and longer runs for judgment.",
            "This is not yet a final quality claim; it is a gate that justifies longer iter runs and visual inspection.",
        ]
        next_lines = [
            "Run the same 160px protocol at 500-1500 iterations for first2.",
            "Use rendered video inspection plus identity-filter tags before expanding beyond first2.",
            "Keep RI3D PLYs in the ignored downstream output area unless a size-reviewed branch is created.",
        ]
    else:
        quality_note = [
            "This is a longer first2 milestone, but still a two-sample gate rather than a final first10/first50 claim.",
            "Use the RGB/depth videos together with loss; low training loss alone does not prove better identity or geometry.",
            "If filtered variants do not visibly improve over raw75_budget4, the next method step must change supervision roles before scaling data.",
        ]
        next_lines = [
            "Compare RGB/depth videos frame-by-frame against the iter50 smoke and the input contact sheet.",
            "Make the RI3D downstream loader consume identity_supervision, geometry_only, identity_reject, and mask_reject roles.",
            "Expand beyond first2 only after the filtered path wins on rendered quality, not just on training loss.",
        ]

    lines = [
        f"# {run_name} downstream observations",
        "",
        "Date: 2026-05-19",
        "",
        "GitHub issue: https://github.com/arlisgreat/3dv/issues/10",
        "",
        "Purpose:",
        "",
        "```text",
        "Close the first downstream 3D loop before expanding first10 to first30/first50.",
        "Compare raw all-6 pseudo views, raw CLIP/reliability budget4, and cutout+mask budget4.",
        "```",
        "",
        "Run:",
        "",
        "```bash",
        f"GPU=0 ITERATIONS={iteration} DATA_ROOT={data_root} OUT_ROOT={run_root} bash scripts/run_ri3d_first2.sh",
        f"GPU=0 ITERATION={iteration} DATA_ROOT={data_root} RUN_ROOT={run_root} bash scripts/render_ri3d_first2.sh",
        (
            f"python scripts/summarize_ri3d_first2.py --data-root {data_root} "
            f"--run-root {run_root} --export-root {export_root} "
            f"--metrics-csv {metrics_csv} --observations {path} "
            f"--input-figure {input_figure} --render-figure {render_figure} "
            f"--iteration {iteration} --run-name {run_name}"
        ),
        "```",
        "",
        "Published artifacts:",
        "",
        "```text",
        str(metrics_csv),
        str(input_figure),
        str(render_figure),
        f"{export_root}/",
        "```",
        "",
        "Summary:",
        "",
        "| sample | variant | views | final loss | splats | rgb mp4 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        loss = "" if row["final_loss"] is None else f"{row['final_loss']:.7f}"
        splats = "" if row["point_count"] is None else str(row["point_count"])
        mp4 = "yes" if row.get("render_rgb_mp4") else "missing"
        lines.append(
            f"| {row['sample_id']} | {row['variant']} | {row['view_count']} | {loss} | {splats} | {mp4} |"
        )

    lines.extend(
        [
            "",
            "Observations:",
            "",
            "```text",
            "The pipeline is now end-to-end executable through RI3D on two first10 samples.",
            "raw75_all6 has more splats and higher training loss in both samples, so more views are not automatically better.",
            *best_lines,
            *quality_note,
            "```",
            "",
            "Next iteration:",
            "",
            "```text",
            *next_lines,
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("experiments/ri3d_datasets/first2_160"))
    parser.add_argument("--run-root", type=Path, default=Path("experiments/downstream_3d/ri3d_first2_160_iter50"))
    parser.add_argument("--export-root", type=Path, default=Path("experiments/reconstructions/ri3d_first2_160_iter50"))
    parser.add_argument("--metrics-csv", type=Path, default=Path("experiments/metrics/ri3d_first2_160_iter50.csv"))
    parser.add_argument("--observations", type=Path, default=Path("experiments/metrics/ri3d_first2_160_iter50_observations.md"))
    parser.add_argument("--input-figure", type=Path, default=Path("experiments/figures/ri3d_first2_160_iter50_inputs.png"))
    parser.add_argument("--render-figure", type=Path, default=Path("experiments/figures/ri3d_first2_160_iter50_renders.png"))
    parser.add_argument("--iteration", type=int, default=50)
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_name = args.run_name or args.export_root.name
    rows = scene_tags(args.data_root)
    args.export_root.mkdir(parents=True, exist_ok=True)

    output_rows: list[dict[str, Any]] = []
    for row in rows:
        tag = row["tag"]
        train_log = args.run_root / "logs" / f"{tag}_train.log"
        init_ply = args.run_root / "debug" / "gs_init" / tag / "point_cloud" / "iteration_1" / "point_cloud.ply"
        train_ply = args.run_root / "output" / "gs_init" / tag / "point_cloud" / f"iteration_{args.iteration}" / "point_cloud.ply"
        log_text = read_text(train_log) if train_log.exists() else ""
        loss, n_splats = final_loss(log_text)
        rendered = copy_render_outputs(args.run_root, args.export_root, row, args.iteration)
        output_rows.append(
            {
                "tag": tag,
                "sample_id": row["sample_id"],
                "variant": row["variant"],
                "view_count": row["view_count"],
                "image_size": row["image_size"],
                "iterations": int(extract_namespace_value(log_text, "iterations") or args.iteration),
                "final_loss": loss,
                "progress_splats": n_splats,
                "point_count": ply_vertices(train_ply),
                "init_ply_bytes": init_ply.stat().st_size if init_ply.exists() else None,
                "train_ply_bytes": train_ply.stat().st_size if train_ply.exists() else None,
                "train_log": str(train_log),
                **rendered,
            }
        )

    args.metrics_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "tag",
        "sample_id",
        "variant",
        "view_count",
        "image_size",
        "iterations",
        "final_loss",
        "progress_splats",
        "point_count",
        "init_ply_bytes",
        "train_ply_bytes",
        "train_log",
        "render_rgb_mp4",
        "render_depth_mp4",
    ]
    with args.metrics_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    write_json(
        args.export_root / "summary.json",
        {
            "data_root": str(args.data_root),
            "run_root": str(args.run_root),
            "iteration": args.iteration,
            "rows": output_rows,
        },
    )
    write_json(
        args.export_root / "metadata.json",
        {
            "name": run_name,
            "date": "2026-05-19",
            "description": f"RI3D first2 downstream 160px {args.iteration}-iteration videos exported from ignored raw outputs.",
            "source_run_root": str(args.run_root),
            "metrics_csv": str(args.metrics_csv),
        },
    )
    (args.export_root / "README.md").write_text(
        f"# {run_name}\n\n"
        f"Exported RGB/depth MP4 flythroughs for the RI3D first2 {args.iteration}-iteration pilot. "
        "Raw PLYs and RI3D working directories stay under ignored `experiments/downstream_3d/`.\n",
        encoding="utf-8",
    )

    make_input_contact_sheet(rows, args.input_figure)
    make_render_contact_sheet(rows, args.export_root, args.render_figure)
    write_observations(
        path=args.observations,
        rows=output_rows,
        export_root=args.export_root,
        data_root=args.data_root,
        run_root=args.run_root,
        metrics_csv=args.metrics_csv,
        input_figure=args.input_figure,
        render_figure=args.render_figure,
        iteration=args.iteration,
        run_name=run_name,
    )

    print(f"Wrote {args.metrics_csv}")
    print(f"Wrote {args.observations}")
    print(f"Wrote {args.input_figure}")
    if args.render_figure.exists():
        print(f"Wrote {args.render_figure}")
    print(f"Exported videos to {args.export_root}")


if __name__ == "__main__":
    main()
