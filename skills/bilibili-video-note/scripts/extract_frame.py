#!/usr/bin/env python3
"""Extract one high-quality video frame with ffmpeg."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def parse_time(value: str) -> float:
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    raise ValueError(f"Unsupported timestamp: {value}")


def format_time(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", value.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "frame"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--time", required=True, help="Seconds, MM:SS, or HH:MM:SS")
    parser.add_argument("--label", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--ext", default="jpg", choices=["jpg", "png", "webp"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    seconds = parse_time(args.time)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{slugify(args.label)}-{int(seconds)}s.{args.ext}"

    command = [
        "ffmpeg",
        "-y",
        "-ss",
        format_time(seconds),
        "-i",
        str(args.video),
        "-frames:v",
        "1",
        "-q:v",
        "1",
        str(out_path),
    ]

    if args.dry_run:
        print(" ".join(command))
        return 0

    subprocess.run(command, check=True)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
