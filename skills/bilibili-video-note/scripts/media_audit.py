#!/usr/bin/env python3
"""Audit metadata, media, and Whisper transcript durations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def metadata_duration(info: dict[str, Any]) -> float | None:
    value = info.get("duration")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def last_transcript_end(data: Any) -> float | None:
    segments = None
    if isinstance(data, dict):
        segments = data.get("segments")
    elif isinstance(data, list):
        segments = data

    if not isinstance(segments, list) or not segments:
        return None

    ends: list[float] = []
    for segment in segments:
        if isinstance(segment, dict) and isinstance(segment.get("end"), (int, float)):
            ends.append(float(segment["end"]))
    return max(ends) if ends else None


def ratio(a: float, b: float) -> float:
    if not a or not b:
        return 1.0
    return abs(a - b) / max(a, b)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--info-json", required=True, type=Path)
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--transcript-json", type=Path)
    parser.add_argument("--max-diff-ratio", type=float, default=0.05)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    info = load_json(args.info_json)
    meta_duration = metadata_duration(info)
    media_duration = ffprobe_duration(args.media)
    media_diff_ratio = ratio(meta_duration, media_duration) if meta_duration else None

    transcript_end = None
    transcript_gap_seconds = None
    transcript_diff_ratio = None
    if args.transcript_json and args.transcript_json.exists():
        transcript_end = last_transcript_end(load_json(args.transcript_json))
        if transcript_end is not None:
            transcript_gap_seconds = abs(media_duration - transcript_end)
            transcript_diff_ratio = ratio(media_duration, transcript_end)

    report = {
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url"),
        "duration_metadata_seconds": meta_duration,
        "duration_media_seconds": media_duration,
        "media_diff_ratio": media_diff_ratio,
        "media_ok": media_diff_ratio is None or media_diff_ratio <= args.max_diff_ratio,
        "transcript_final_end_seconds": transcript_end,
        "transcript_gap_seconds": transcript_gap_seconds,
        "transcript_diff_ratio": transcript_diff_ratio,
        "transcript_ok": transcript_diff_ratio is None
        or transcript_diff_ratio <= args.max_diff_ratio,
        "max_diff_ratio": args.max_diff_ratio,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0 if report["media_ok"] and report["transcript_ok"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        raise SystemExit(exc.returncode or 1)
