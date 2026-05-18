#!/usr/bin/env python3
"""Collect a small licensed web headshot pilot set from Wikimedia Commons."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "arlisgreat-3dv-paper-sprint/0.1 (research data curation)"


@dataclass(frozen=True)
class SourceSpec:
    sample_id: str
    group: str
    input_yaw: str
    query: str
    notes: str
    title: str | None = None


DEFAULT_SPECS = [
    SourceSpec("web_clean_frontal_01", "clean_frontal", "0", "official portrait", "clean frontal web portrait", "File:President Barack Obama.jpg"),
    SourceSpec("web_clean_frontal_02", "clean_frontal", "0", "headshot portrait woman", "clean frontal web portrait", "File:Gudrun Lerchbaum.jpg"),
    SourceSpec("web_clean_frontal_03", "clean_frontal", "0", "headshot portrait man", "clean frontal web portrait", "File:Alexander Freeman Headshot.jpg"),
    SourceSpec("web_mild_side_01", "mild_side", "30", "three-quarter portrait", "mild side or three-quarter portrait", "File:Photograph of Henry Wellcome (three-quarter face with beard) Wellcome M0007847.jpg"),
    SourceSpec("web_mild_side_02", "mild_side", "-30", "three-quarter portrait", "mild side or three-quarter portrait", "File:Three-quarter face portrait of man with beard LCCN2006688331.jpg"),
    SourceSpec("web_glasses_01", "glasses", "0", "portrait glasses photograph", "glasses portrait", "File:Okonjo-Iweala, Ngozi (2008 portrait).jpg"),
    SourceSpec("web_glasses_02", "glasses", "0", "portrait glasses photograph", "glasses portrait", "File:Big glasses.jpg"),
    SourceSpec("web_complex_hair_01", "complex_hair", "0", "curly hair portrait photograph", "complex hair portrait", "File:Curly hair and freckles man (Unsplash).jpg"),
    SourceSpec("web_complex_hair_02", "complex_hair", "0", "curly hair portrait photograph", "complex hair portrait", "File:Portrait of Muslim man.jpg"),
    SourceSpec("web_occlusion_lowq_01", "occlusion_lowq", "unknown", "portrait face mask photograph", "occlusion or lower-quality portrait", "File:Balaclava as suggested fashion piece for winter 2018 - modelled by ModelTanja.jpg"),
]


MANIFEST_COLUMNS = [
    "sample_id",
    "input_path",
    "group",
    "input_yaw",
    "source_title",
    "source_page",
    "source_url",
    "license",
    "artist",
    "credit",
    "sha256",
    "width",
    "height",
    "query",
    "notes",
]


def request_json(params: dict[str, Any]) -> dict[str, Any]:
    params = {**params, "format": "json", "formatversion": "2"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    return " ".join(text.split())


def ext(meta: dict[str, Any], key: str) -> str:
    node = meta.get(key) or {}
    if isinstance(node, dict):
        return clean_html(str(node.get("value", "")))
    return clean_html(str(node))


def acceptable_license(name: str) -> bool:
    lowered = name.lower()
    return any(
        token in lowered
        for token in ["cc ", "cc-", "cc0", "creative commons", "public domain", "pd-", "no restrictions", "fal", "free art license"]
    )


def search_candidates(query: str, limit: int) -> list[dict[str, Any]]:
    data = request_json(
        {
            "action": "query",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": query,
            "gsrlimit": str(limit),
            "prop": "imageinfo|info",
            "inprop": "url",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "1024",
        }
    )
    pages = data.get("query", {}).get("pages", [])
    return pages if isinstance(pages, list) else []


def title_candidate(title: str) -> list[dict[str, Any]]:
    data = request_json(
        {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "imageinfo|info",
            "inprop": "url",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "1024",
        }
    )
    pages = data.get("query", {}).get("pages", [])
    return pages if isinstance(pages, list) else []


def choose_candidate(spec: SourceSpec, used_pageids: set[int], limit: int) -> dict[str, Any]:
    candidates = title_candidate(spec.title) if spec.title else search_candidates(spec.query, limit)
    for page in candidates:
        pageid = int(page.get("pageid", -1))
        if pageid in used_pageids:
            continue
        imageinfo = page.get("imageinfo") or []
        if not imageinfo:
            continue
        info = imageinfo[0]
        mime = str(info.get("mime", ""))
        if not mime.startswith("image/"):
            continue
        width = int(info.get("width") or 0)
        height = int(info.get("height") or 0)
        if min(width, height) < 384:
            continue
        meta = info.get("extmetadata") or {}
        license_name = ext(meta, "LicenseShortName") or ext(meta, "UsageTerms")
        if not acceptable_license(license_name):
            continue
        thumb = info.get("thumburl") or info.get("url")
        if not thumb:
            continue
        return {"page": page, "info": info, "meta": meta, "download_url": thumb}
    raise RuntimeError(f"No acceptable Wikimedia Commons candidate for {spec.sample_id}: {spec.query}")


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = resp.read()
    path.write_bytes(data)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_square(src: Path, dst: Path, size: int) -> tuple[int, int]:
    image = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    width, height = image.size
    side = max(width, height)
    canvas = Image.new("RGB", (side, side), (127, 127, 127))
    canvas.paste(image, ((side - width) // 2, (side - height) // 2))
    canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
    canvas.save(dst)
    return width, height


def make_contact_sheet(rows: list[dict[str, str]], out_path: Path, thumb: int = 192) -> None:
    cols = 5
    label_h = 42
    pad = 12
    sheet_w = cols * thumb + (cols + 1) * pad
    sheet_h = ((len(rows) + cols - 1) // cols) * (thumb + label_h + pad) + pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, row in enumerate(rows):
        r = idx // cols
        c = idx % cols
        x = pad + c * (thumb + pad)
        y = pad + r * (thumb + label_h + pad)
        image = Image.open(row["input_path"]).convert("RGB").resize((thumb, thumb), Image.Resampling.LANCZOS)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb + 4), row["sample_id"], fill=(0, 0, 0))
        draw.text((x, y + thumb + 22), row["group"], fill=(80, 80, 80))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def repo_rel(path: Path, repo: Path) -> str:
    return str(path.relative_to(repo))


def write_root_manifest(repo: Path, rows: list[dict[str, str]]) -> None:
    out = repo / "data_manifest.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "input_path", "group", "input_yaw", "notes"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in ["sample_id", "input_path", "group", "input_yaw", "notes"]})


def collect(repo: Path, size: int, limit: int, sleep: float, overwrite: bool) -> list[dict[str, str]]:
    root = repo / "experiments" / "inputs" / "first10"
    raw_dir = root / "raw"
    proc_dir = root / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    used_pageids: set[int] = set()
    for spec in DEFAULT_SPECS:
        chosen = choose_candidate(spec, used_pageids, limit)
        page = chosen["page"]
        info = chosen["info"]
        meta = chosen["meta"]
        used_pageids.add(int(page["pageid"]))

        suffix = Path(urllib.parse.urlparse(chosen["download_url"]).path).suffix or ".jpg"
        raw_path = raw_dir / f"{spec.sample_id}{suffix}"
        proc_path = proc_dir / f"{spec.sample_id}.png"
        if overwrite or not raw_path.exists():
            download(chosen["download_url"], raw_path)
            time.sleep(sleep)
        width, height = make_square(raw_path, proc_path, size)

        license_name = ext(meta, "LicenseShortName") or ext(meta, "UsageTerms")
        source_page = page.get("fullurl") or f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(str(page.get('title', '')))}"
        row = {
            "sample_id": spec.sample_id,
            "input_path": repo_rel(proc_path, repo),
            "group": spec.group,
            "input_yaw": spec.input_yaw,
            "source_title": str(page.get("title", "")),
            "source_page": str(source_page),
            "source_url": str(info.get("url", "")),
            "license": license_name,
            "artist": ext(meta, "Artist"),
            "credit": ext(meta, "Credit"),
            "sha256": sha256(proc_path),
            "width": str(width),
            "height": str(height),
            "query": spec.query,
            "notes": spec.notes,
        }
        rows.append(row)

    manifest = root / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    contact_rows = [{**row, "input_path": str(repo / row["input_path"])} for row in rows]
    make_contact_sheet(contact_rows, repo / "experiments" / "figures" / "first10_wikimedia_contact_sheet.png")
    write_root_manifest(repo, rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    rows = collect(repo, args.size, args.limit, args.sleep, args.overwrite)
    print(f"Collected {len(rows)} Wikimedia headshot inputs")
    for row in rows:
        print(f"{row['sample_id']}: {row['source_title']} ({row['license']})")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"collect_wikimedia_headshots.py failed: {exc}", file=sys.stderr)
        raise
