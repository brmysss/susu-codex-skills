# Structured Note Specification

Use this file when creating `structured-note.md` for knowledge-heavy videos such as
courses, lectures, interviews, talks, podcasts, commentary, and Q&A.

## Purpose

`structured-note.md` is the faithful study layer. It is not a visual article and not a
quote dump. It should help the user learn and review the full content by combining:

1. structure,
2. concise synthesis,
3. complete point coverage,
4. timestamped source evidence.

## Required Format

Use this order for every meaningful section:

```markdown
### 1.1 Section Title

**结构化概括**

State the synthesized conclusion in plain Chinese. Make clear that this is a grounded
summary, not necessarily the author's exact wording.

**要点拆解**

- Break the conclusion into concrete sub-points.
- Name categories, steps, roles, distinctions, causes, traps, or actions.
- Include enough detail that the user can understand the structure before reading quotes.

**原文依据**

- `00:00:24` "Source quote..."
- `00:00:33` "Source quote..."
```

Do not use the older formats:

- quote-only outlines with no summary,
- "忠实整理 / 学习抓手" study essays,
- coverage tables as the main note.

## Summary Rules

- The section title and `结构化概括` may be the agent's synthesis, but it must be grounded
  in the transcript.
- Do not present a synthesized section title as if it were a direct quote.
- When useful, explicitly say "这是对作者...的归纳" or "这是作者明确表达的结论".
- Prefer compact, high-signal summaries over polished article prose.
- Avoid adding outside frameworks unless the source clearly supports them.

## Point Coverage Rules

- Cover all important claims, distinctions, examples, steps, and Q&A answers.
- Do not collapse many Q&A items into one vague "Q&A" block when they contain separate
  advice.
- Use the video's natural structure: main lecture, subtopics, transitions, and Q&A clusters.
- For long Q&A, group related questions, but preserve each distinct answer as its own
  subsection when it gives a separate actionable point.
- A visual long page may condense content later; `structured-note.md` should preserve the
  learning map.

## Quote Rules

- Each subsection needs source quotes with timestamps unless it is a top-level overview.
- Quotes should be short enough to scan but sufficient to prove the summary.
- Prefer multiple timestamped short quotes over one long quote.
- Clean obvious transcription artifacts and hidden Unicode noise for readability.
- Lightly correct obvious ASR mistakes only when the intended word is clear, such as
  recurring names or terms. Do not silently rewrite the author's meaning.
- If a term was corrected, note it near the top of the file.

## Recommended File Header

```markdown
# Title | 结构化要点笔记

> 来源：...
> 总时长：...
> 版本目标：先结构化概括，再列要点，最后用作者原文证明。
> 阅读约定：
> - **结构化概括**：根据作者原话归纳出的结论，不是作者逐字原话。
> - **要点拆解**：把概括拆成可复盘的知识点。
> - **原文依据**：作者在课程中的原话或接近原话，带时间戳。
```

## Example

```markdown
### 1.1 吸金作者要同时具备四类能力

**结构化概括**

这是对作者开场定义的归纳：作者认为"吸金作者"不是单项写作能力，而是四类能力叠加。

**要点拆解**

- 真实成果和生活状态：做得好、活得好。
- 认知底座：见识、认知要到位。
- 表达技术：要能把经验和观点表达出来。
- 营销销售：要懂营销，要能卖东西。

**原文依据**

- `00:00:24` "诸位你要成为一个吸金的作者，第一你是不是要做得好，活得好啊。"
- `00:00:33` "第二个你的见识，你的认知是不是得到位。"
- `00:00:40` "第三个你的表达技术是不是得过关。"
- `00:00:49` "第四个你是不是得懂营销。"
- `00:00:58` "你得卖东西。"
```

## Relationship To Visual Page

Use `structured-note.md` as the content map for `index.html`.

- The visual page can select the strongest sections and compress details.
- The visual page should include short source quotes for credibility.
- SVG diagrams should be based on the structured note's real concepts and relationships.
- If a point appears in the visual page, it should be traceable back to `structured-note.md`
  and then to transcript timestamps.

