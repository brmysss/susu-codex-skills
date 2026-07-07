# Page and Diagram Specification

Read this file before designing the final note page.

## Page Shape

Use a calm long-note layout similar to mobile article screenshots:

- Max content width: 720-860 px for the HTML page; center the page.
- Background: warm off-white or near-white; cards only for repeated callouts or diagrams.
- Typography: strong title, small metadata row, readable body text, short paragraphs.
- Captions: label SVG captions with `图解`; label real frame captions with `视频时间戳`
  only when screenshots are truly needed.
- Ordering per chapter: text summary, SVG diagram; add a real frame screenshot only for
  interface/tool/demo chapters where the screen is evidence.
- Do not use visible text that explains the mechanics of the generated page.
- Add a restrained source footer at the bottom. Include uploader, title, duration, platform,
  video ID/link, and a small QR code aligned to the right when possible.

## Chapter Writing

Do not force every chapter into the same fields. Choose what the content needs:

- Problem: what the speaker is trying to solve.
- Trap: what the viewer may misunderstand or do wrong.
- Steps: what to do in sequence.
- Conclusion: the chapter's actionable takeaway.
- Quote: one short source-language quote when it carries the idea better.
- Visual anchor: what appears on screen, such as a menu, chart, console line, timeline,
  slide title, or hand-drawn sketch.

Use plain Chinese. Keep sentences short. Prefer concrete verbs. Include timestamps in a
format that can be linked back to the source, such as `00:06:52`.

## SVG Selection Rules

Pick the diagram form from the chapter's content:

- Process or operation: step path, swimlane, loop, or forked flow.
- Concept explanation: hierarchy, layers, hub-spoke map, or relationship graph.
- Time/change: timeline, before/after progression, or phase stack.
- Comparison: matrix, two-column contrast, spectrum, or tradeoff map.
- Risk/mistake: checklist, decision tree, danger path, or guardrail map.
- Data: simplified chart, annotated number cards, or proportional bars.
- Cause/effect: causal chain, feedback loop, or dependency graph.

Each SVG must include:

- At least 3 chapter-specific keywords or phrases.
- Visible relationships: arrows, grouping, layering, axes, or labels.
- A short caption under the SVG beginning with `图解：`.

Never reuse a generic shell. Do not draw decorative shapes that could fit any chapter.

## Screenshot Frame Selection

Do not extract frames for talking-head, lecture, interview, podcast, commentary, or
concept-only videos unless a specific visible object is essential to the explanation.

For UI, console, editor, document, canvas, design, coding, or tool-operation videos:

1. Identify the chapter time range.
2. Pick the timestamp with the clearest screen state: menus open, code/result visible,
   important slide visible, canvas arranged, or before/after shown.
3. Use `ffmpeg` precise extraction through `scripts/extract_frame.py` with `-q:v 1`.
4. Name the file with the chapter/stage and seconds, e.g. `frames/chapter-04-892s.jpg`.
5. Caption the image with `视频时间戳：00:14:52`.

For long videos, sample several candidates across the chapter, inspect thumbnails, then
export the final chosen timestamp at full quality.

## HTML Requirements

- Inline all CSS.
- Inline SVG markup directly in the HTML.
- Reference screenshots and thumbnails with relative paths only when used.
- Reference a generated QR SVG/PNG with a relative path, or inline the QR SVG. Keep it small
  and visually subordinate to the note content.
- Escape transcript text and URLs safely.
- Use stable image sizes: set `max-width: 100%`, `height: auto`, and avoid layout shifts.
- Use readable mobile styling: no viewport-scaled fonts, no negative letter spacing.

Recommended capture command when Playwright is available:

```bash
node -e '
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1400 }, deviceScaleFactor: 2 });
  await page.goto("file://" + process.cwd() + "/index.html");
  await page.screenshot({ path: "page.png", fullPage: true });
  const broken = await page.$$eval("img", imgs => imgs.filter(img => !img.complete || img.naturalWidth === 0).map(img => img.getAttribute("src")));
  if (broken.length) throw new Error("Broken images: " + broken.join(", "));
  await browser.close();
})();
'
```

If Playwright is unavailable, use Chrome headless directly and still inspect the resulting
PNG before slicing.
