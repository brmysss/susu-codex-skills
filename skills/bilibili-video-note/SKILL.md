---
name: bilibili-video-note
description: Turn Bilibili or other online video links into offline visual-note pages and long-image slices. Use when the user provides a Bilibili/video URL and asks for video notes, AI study notes, transcript-based summaries, chaptered visual cards, SVG diagrams from video content, real frame screenshots, offline HTML, or shareable long PNG note images.
---

# Bilibili Video Note

## Output Contract

Create a self-contained output folder for each video:

```text
video-note-output/
├── index.html
├── page.png
├── structured-note.md      # summary-first, source-grounded learning note
├── slices/
├── frames/                 # only for UI/tool/demo videos that need evidence frames
├── media/
│   ├── info.json
│   ├── audio.mp3
│   └── source-video.ext
├── transcript/
│   ├── transcript.json
│   └── transcript.zh.md
└── audit/
    ├── media-audit.json
    └── render-notes.md
```

Generate `index.html` as a single offline page with inline CSS and inline SVG. Reference
real screenshots only when the video is an interface, tool, document, console, canvas,
editing, or operation demo where the screen state is evidence.

For course, lecture, interview, talk, commentary, and other knowledge-heavy videos, also
generate `structured-note.md` before the visual page. This note is the faithful study layer:
it must organize all important points in a summary-first structure and ground each point in
timestamped source quotes.

## Workflow

1. Create a clean working directory. Store every generated file under it.
2. Fetch metadata with `yt-dlp` and preserve Bilibili details: title, uploader, bvid/aid,
   part title/index, description, tags, chapters, thumbnail, upload date, webpage URL,
   and duration.
3. Download best audio and convert to mp3. Download video only when screenshots are needed
   or when audio extraction from the video is more reliable.
4. Run `scripts/media_audit.py` against `info.json`, the mp3, and later the Whisper JSON.
   If media duration differs from metadata by more than 5%, retry with another format or
   mark the note with an explicit anomaly.
5. Transcribe with Whisper. Use Chinese `turbo` with language `zh`; use English
   `small.en`, then translate the transcript to Chinese. Verify the final segment end is
   close to audio duration.
6. Segment by the video's natural structure, not a fixed template. Use Bilibili chapters,
   part boundaries, transcript topic shifts, slide/interface changes, and speaker signposts.
7. For knowledge-heavy videos, read `references/structured-note-spec.md` and create
   `structured-note.md` from the full transcript before designing the visual page. Each
   section must use the order `结构化概括 -> 要点拆解 -> 原文依据`; clearly treat the
   summary as the agent's grounded synthesis, then cite timestamped author/source quotes.
8. Read `references/page-spec.md` before writing the page. For each chapter, write concise
   plain-language notes with timestamps, key claims, traps, steps, conclusions, quotes, and
   visual anchors. Use `structured-note.md` as the primary content map when it exists; the
   visual page may condense, but should not contradict or invent beyond the structured note.
9. Generate a custom SVG diagram for each chapter from that chapter's real content. Use
   relationship arrows, labels, keywords, and structure; never use decorative or repeated
   placeholder diagrams.
10. Classify the visual need. For talking-head, lecture, interview, podcast, commentary,
   or concept-only videos, do not add video keyframes; the page should read like a visual
   article with chapter text and SVG diagrams. For interface, console, editor, document,
   canvas, or tutorial videos, extract one real frame per chapter with
   `scripts/extract_frame.py`. Pick the clearest information-dense frame inside that
   chapter.
11. Build the offline HTML in the order `正文 -> SVG 图解` for concept/talking-head videos,
   and `正文 -> SVG 图解 -> 视频时间戳截图` only for operation/demo chapters.
12. Add a source footer at the bottom with uploader, title, duration, source platform,
   video ID/link, and a QR code to the original video when a QR generator is available.
13. Render with headless Chrome or Playwright to a full-page PNG. Check image loading,
   whitespace, overlap, font sizing, and whether every SVG and screenshot appears.
14. Slice the tall PNG with `scripts/slice_tall_image.py`, keeping about 100 px overlap so
   headings are not cut.

## Commands

Fetch metadata and media:

```bash
yt-dlp --cookies-from-browser chrome --write-info-json --write-thumbnail \
  --skip-download -o "media/%(title).160B.%(ext)s" "$VIDEO_URL"

yt-dlp --cookies-from-browser chrome -f "ba/bestaudio/best" \
  -x --audio-format mp3 --audio-quality 0 \
  -o "media/audio.%(ext)s" "$VIDEO_URL"
```

Download video for screenshots:

```bash
yt-dlp --cookies-from-browser chrome -f "bv*+ba/best" \
  --merge-output-format mp4 -o "media/source-video.%(ext)s" "$VIDEO_URL"
```

Audit durations:

```bash
python3 "$SKILL_DIR/scripts/media_audit.py" \
  --info-json media/info.json \
  --media media/audio.mp3 \
  --transcript-json transcript/transcript.json \
  --max-diff-ratio 0.05 \
  --out audit/media-audit.json
```

Extract a frame:

```bash
python3 "$SKILL_DIR/scripts/extract_frame.py" \
  --video media/source-video.mp4 \
  --time 00:06:52 \
  --label "chapter-03-key-interface" \
  --out-dir frames
```

Slice the rendered long image:

```bash
python3 "$SKILL_DIR/scripts/slice_tall_image.py" \
  --input page.png \
  --out-dir slices \
  --slice-height 1800 \
  --overlap 100
```

## Quality Gates

- Metadata is complete enough to cite title, uploader, URL, duration, and Bilibili part data
  when present.
- `media-audit.json` reports `media_ok: true`; if false, the page calls out the anomaly.
- Transcript final segment is within 5% of audio duration, or the gap is investigated.
- `structured-note.md` exists for knowledge-heavy videos and follows
  `结构化概括 -> 要点拆解 -> 原文依据`. Every meaningful summary point is backed by
  timestamped source quotes, and important topic shifts or Q&A items are not collapsed away.
- Every chapter has a timestamp that jumps back to the source video.
- Every SVG is derived from chapter-specific content and contains meaningful labels.
- Talking-head/concept chapters do not include video keyframes. Interface/tutorial
  chapters include one real frame screenshot unless no video file is available; note the
  omission if screenshots cannot be extracted.
- The page footer cites the original video source and provides a scannable QR code or a
  visible source link when QR generation is unavailable.
- The final HTML opens offline, images are relative, and the long PNG has no blank page,
  overlapping text, missing images, or clipped headings.
