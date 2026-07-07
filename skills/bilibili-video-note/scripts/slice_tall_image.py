#!/usr/bin/env python3
"""Slice a tall PNG/JPEG into overlapping image segments with ffmpeg."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def probe_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    return int(stream["width"]), int(stream["height"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--slice-height", type=int, default=1800)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--prefix", default="slice")
    parser.add_argument("--ext", default="png", choices=["png", "jpg", "webp"])
    args = parser.parse_args()

    if args.overlap >= args.slice_height:
        raise ValueError("--overlap must be smaller than --slice-height")

    width, height = probe_size(args.input)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    step = args.slice_height - args.overlap
    manifest = []
    y = 0
    index = 1
    while y < height:
        crop_height = min(args.slice_height, height - y)
        out_path = args.out_dir / f"{args.prefix}-{index:02d}.{args.ext}"
        vf = f"crop={width}:{crop_height}:0:{y}"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(args.input), "-vf", vf, str(out_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        manifest.append(
            {
                "file": out_path.name,
                "y": y,
                "width": width,
                "height": crop_height,
            },
        )
        if y + crop_height >= height:
            break
        y += step
        index += 1

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
